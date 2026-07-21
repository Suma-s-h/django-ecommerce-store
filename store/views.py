from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum, Count, F
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse
from .models import Category, Product, Wishlist, NewsletterSubscriber
from .forms import ReviewForm, ContactForm

PRODUCTS_PER_PAGE = 12
HOME_SECTION_SIZE = 8


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _wishlist_product_ids(user):
    if not user.is_authenticated:
        return set()
    wishlist = getattr(user, 'wishlist', None)
    return set(wishlist.products.values_list('id', flat=True)) if wishlist else set()


def about(request):
    return render(request, 'store/about.html')


def privacy_policy(request):
    return render(request, 'store/privacy_policy.html')


def terms(request):
    return render(request, 'store/terms.html')


@require_POST
def newsletter_subscribe(request):
    email = request.POST.get('email', '').strip()
    if not email:
        message, ok = 'Please enter a valid email address.', False
    else:
        _, created = NewsletterSubscriber.objects.get_or_create(email=email)
        message = 'Subscribed! Watch your inbox for deals.' if created else "You're already subscribed."
        ok = True
    if _is_ajax(request):
        return JsonResponse({'ok': ok, 'message': message})
    messages.success(request, message) if ok else messages.error(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'store:product_list'))


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            message = render_to_string('emails/contact_message.txt', form.cleaned_data)
            email = EmailMessage(
                subject=f"Contact form: {form.cleaned_data['subject']}",
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_FROM_EMAIL],
                reply_to=[form.cleaned_data['email']],
            )
            email.send(fail_silently=True)
            messages.success(request, "Thanks for reaching out — we'll get back to you soon!")
            return redirect('store:contact')
    else:
        form = ContactForm()
    return render(request, 'store/contact.html', {'form': form})


def product_list(request, category_slug=None):
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).select_related('category').prefetch_related('reviews')
    category = None

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created')

    featured = Product.objects.filter(featured=True, available=True) \
        .select_related('category').prefetch_related('reviews')[:4]

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'categories': categories,
        'products': page_obj,
        'page_obj': page_obj,
        'category': category,
        'query': query,
        'sort': sort,
        'featured': featured,
        'wishlisted_ids': _wishlist_product_ids(request.user),
    }

    # Homepage-only sections — skip the extra queries on filtered/category/search pages
    is_homepage = not category and not query
    if is_homepage:
        base_qs = Product.objects.filter(available=True).select_related('category').prefetch_related('reviews')
        context['new_arrivals'] = base_qs.order_by('-created')[:HOME_SECTION_SIZE]
        context['flash_sale'] = base_qs.filter(
            discount_price__isnull=False, discount_price__lt=F('price'),
        )[:HOME_SECTION_SIZE]
        context['best_sellers'] = base_qs.annotate(
            units_sold=Sum('orderitem__quantity')
        ).filter(units_sold__gt=0).order_by('-units_sold')[:HOME_SECTION_SIZE]
        context['trending'] = base_qs.annotate(
            fan_count=Count('wishlisted_by')
        ).filter(fan_count__gt=0).order_by('-fan_count')[:HOME_SECTION_SIZE]

    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category'),
        slug=slug, available=True,
    )
    related = Product.objects.filter(
        category=product.category, available=True,
    ).select_related('category').prefetch_related('reviews').exclude(id=product.id)[:4]

    reviews = product.reviews.select_related('user').all()
    review_form = ReviewForm()

    wishlisted_ids = _wishlist_product_ids(request.user)
    user_review = None
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
        'reviews': reviews,
        'review_form': review_form,
        'user_review': user_review,
        'in_wishlist': product.id in wishlisted_ids,
        'wishlisted_ids': wishlisted_ids,
    })


@login_required
@require_POST
def review_create(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    if product.reviews.filter(user=request.user).exists():
        messages.warning(request, 'You have already reviewed this product.')
        return redirect(product.get_absolute_url())
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, 'Review submitted — thank you!')
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(product.get_absolute_url())


@require_POST
def wishlist_toggle(request, product_id):
    if not request.user.is_authenticated:
        if _is_ajax(request):
            return JsonResponse({'login_required': True, 'login_url': settings.LOGIN_URL}, status=401)
        return redirect(f"{settings.LOGIN_URL}?next={request.META.get('HTTP_REFERER', '/')}")

    product = get_object_or_404(Product, id=product_id, available=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    if wishlist.products.filter(id=product.id).exists():
        wishlist.products.remove(product)
        in_wishlist = False
        message = f'"{product.name}" removed from wishlist.'
        messages.info(request, message)
    else:
        wishlist.products.add(product)
        in_wishlist = True
        message = f'"{product.name}" saved to wishlist.'
        messages.success(request, message)

    if _is_ajax(request):
        return JsonResponse({
            'in_wishlist': in_wishlist,
            'wishlist_count': wishlist.products.count(),
            'message': message,
        })
    return redirect(request.META.get('HTTP_REFERER', product.get_absolute_url()))


@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {
        'wishlist': wishlist,
        'wishlisted_ids': set(wishlist.products.values_list('id', flat=True)),
    })
