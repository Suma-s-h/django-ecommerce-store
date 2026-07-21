from .models import Category


def wishlist_count(request):
    if request.user.is_authenticated:
        wishlist = getattr(request.user, 'wishlist', None)
        return {'wishlist_count': wishlist.products.count() if wishlist else 0}
    return {'wishlist_count': 0}


def nav_categories(request):
    return {'nav_categories': Category.objects.all()[:8]}
