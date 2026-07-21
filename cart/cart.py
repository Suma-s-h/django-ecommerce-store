from decimal import Decimal
from store.models import Product

SHIPPING_THRESHOLD = Decimal('50.00')
SHIPPING_COST = Decimal('5.99')


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.final_price)}
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids).select_related('category')
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    # ── Coupon support ──────────────────────────────────────────────────────

    @property
    def coupon(self):
        coupon_id = self.session.get('coupon_id')
        if coupon_id:
            from orders.models import Coupon
            try:
                c = Coupon.objects.get(id=coupon_id)
                if c.is_valid():
                    return c
                # expired — remove silently
                del self.session['coupon_id']
                self.save()
            except Coupon.DoesNotExist:
                pass
        return None

    def set_coupon(self, coupon_id):
        self.session['coupon_id'] = coupon_id
        self.save()

    def remove_coupon(self):
        if 'coupon_id' in self.session:
            del self.session['coupon_id']
            self.save()

    def get_discount(self):
        if self.coupon:
            return (Decimal(self.coupon.discount_percent) / 100) * self.get_total_price()
        return Decimal('0')

    def get_discounted_subtotal(self):
        return self.get_total_price() - self.get_discount()

    # ── Shipping & totals ───────────────────────────────────────────────────

    def get_shipping_cost(self):
        """$5.99 shipping, free when discounted subtotal >= $50."""
        return Decimal('0') if self.get_discounted_subtotal() >= SHIPPING_THRESHOLD else SHIPPING_COST

    def get_grand_total(self):
        return self.get_discounted_subtotal() + self.get_shipping_cost()

    def remaining_for_free_shipping(self):
        remaining = SHIPPING_THRESHOLD - self.get_discounted_subtotal()
        return max(Decimal('0'), remaining)

    def clear(self):
        del self.session['cart']
        if 'coupon_id' in self.session:
            del self.session['coupon_id']
        self.save()
