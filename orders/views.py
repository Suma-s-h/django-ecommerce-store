import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from cart.cart import Cart
from .models import Order, OrderItem, Coupon
from .forms import OrderCreateForm
from store.models import Product

stripe.api_key = settings.STRIPE_SECRET_KEY


# ── Checkout ─────────────────────────────────────────────────────────────────

def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # Stock check before touching the database
            stock_errors = []
            for item in cart:
                product = item['product']
                if item['quantity'] > product.stock:
                    if product.stock == 0:
                        stock_errors.append(f'"{product.name}" is out of stock.')
                    else:
                        stock_errors.append(
                            f'"{product.name}" only has {product.stock} left '
                            f'(you have {item["quantity"]} in cart).'
                        )
            if stock_errors:
                for err in stock_errors:
                    messages.error(request, err)
                return redirect('cart:cart_detail')

            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                coupon = cart.coupon
                if coupon:
                    order.coupon = coupon
                    order.discount = coupon.discount_percent
                order.save()
                for item in cart:
                    product = item['product']
                    qty = min(item['quantity'], product.stock)
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=item['price'],
                        quantity=qty,
                    )
                    Product.objects.filter(pk=product.pk, stock__gte=qty).update(
                        stock=F('stock') - qty
                    )

            # Stripe payment if keys are configured
            if settings.STRIPE_SECRET_KEY:
                try:
                    total_cents = int(order.get_total_cost() * 100)
                    shipping_cents = int(cart.get_shipping_cost() * 100)
                    intent = stripe.PaymentIntent.create(
                        amount=total_cents + shipping_cents,
                        currency='usd',
                        metadata={'order_id': order.id},
                    )
                    order.stripe_payment_intent = intent['id']
                    order.save(update_fields=['stripe_payment_intent'])
                    cart.clear()
                    request.session['payment_client_secret'] = intent['client_secret']
                    return redirect('orders:payment', order_id=order.id)
                except stripe.StripeError:
                    messages.warning(request, 'Payment setup failed — your order is saved. Please contact support.')

            cart.clear()
            messages.success(request, f'Order #{order.id} placed successfully!')
            return render(request, 'orders/order_created.html', {'order': order})
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
        form = OrderCreateForm(initial=initial)

    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


# ── Stripe payment page ───────────────────────────────────────────────────────

def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user and request.user != order.user:
        return redirect('store:product_list')
    client_secret = request.session.get('payment_client_secret', '')
    return render(request, 'orders/payment.html', {
        'order': order,
        'client_secret': client_secret,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })


def payment_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    payment_intent_id = request.GET.get('payment_intent', '')
    if payment_intent_id and settings.STRIPE_SECRET_KEY:
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if (intent['status'] == 'succeeded'
                    and str(intent['metadata'].get('order_id')) == str(order.id)):
                if not order.paid:
                    order.paid = True
                    order.save(update_fields=['paid'])
        except stripe.StripeError:
            pass
    request.session.pop('payment_client_secret', None)
    return render(request, 'orders/order_created.html', {'order': order})


# ── Stripe webhook ────────────────────────────────────────────────────────────

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    if not webhook_secret:
        return HttpResponse(status=400)
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)
    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        order_id = intent['metadata'].get('order_id')
        if order_id:
            Order.objects.filter(id=order_id, paid=False).update(paid=True)
    return HttpResponse(status=200)


# ── Coupon ────────────────────────────────────────────────────────────────────

@require_POST
def coupon_apply(request):
    code = request.POST.get('code', '').strip()
    cart = Cart(request)
    try:
        coupon = Coupon.objects.get(code__iexact=code)
        if coupon.is_valid():
            cart.set_coupon(coupon.id)
            messages.success(request, f'Coupon "{coupon.code}" applied — {coupon.discount_percent}% off!')
        else:
            messages.error(request, 'This coupon has expired or is inactive.')
    except Coupon.DoesNotExist:
        messages.error(request, f'"{code}" is not a valid coupon code.')
    return redirect('cart:cart_detail')


@require_POST
def coupon_remove(request):
    Cart(request).remove_coupon()
    messages.info(request, 'Coupon removed.')
    return redirect('cart:cart_detail')


# ── Order history ─────────────────────────────────────────────────────────────

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id, user=request.user,
    )
    return render(request, 'orders/order_detail.html', {'order': order})
