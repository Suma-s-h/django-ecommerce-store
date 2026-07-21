from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.utils import timezone
from store.models import Product


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(100)],
        help_text='Percentage discount (1–100)',
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.code} ({self.discount_percent}% off)'

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid = models.BooleanField(default=False)
    stripe_payment_intent = models.CharField(max_length=250, blank=True)
    notes = models.TextField(blank=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    discount = models.PositiveSmallIntegerField(default=0)  # cached % at time of order

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'Order #{self.id}'

    def get_items_total(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_discount_amount(self):
        if self.discount:
            return self.get_items_total() * Decimal(self.discount) / 100
        return Decimal('0')

    def get_total_cost(self):
        return self.get_items_total() - self.get_discount_amount()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity}x {self.product}'

    def get_cost(self):
        return self.price * self.quantity
