import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Category, Product, Review, Wishlist, NewsletterSubscriber

LOW_STOCK_THRESHOLD = 5


class LowStockFilter(admin.SimpleListFilter):
    title = 'stock level'
    parameter_name = 'stock_level'

    def lookups(self, request, model_admin):
        return [
            ('out', 'Out of stock'),
            ('low', f'Low stock (≤ {LOW_STOCK_THRESHOLD})'),
            ('ok', 'In stock'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'out':
            return queryset.filter(stock=0)
        if self.value() == 'low':
            return queryset.filter(stock__gt=0, stock__lte=LOW_STOCK_THRESHOLD)
        if self.value() == 'ok':
            return queryset.filter(stock__gt=LOW_STOCK_THRESHOLD)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'discount_price', 'stock_status', 'available', 'featured']
    list_filter = ['available', 'featured', 'category', LowStockFilter]
    list_editable = ['price', 'discount_price', 'available', 'featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    actions = ['mark_unavailable']

    @admin.display(description='Stock', ordering='stock')
    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color:red;font-weight:bold">&#x2717; Out of stock</span>')
        if obj.stock <= LOW_STOCK_THRESHOLD:
            return format_html('<span style="color:orange;font-weight:bold">&#x26A0; Low ({})</span>', obj.stock)
        return format_html('<span style="color:green">&#x2713; {}</span>', obj.stock)

    @admin.action(description='Mark selected products as unavailable')
    def mark_unavailable(self, request, queryset):
        queryset.update(available=False)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'title', 'created']
    list_filter = ['rating', 'created']
    search_fields = ['product__name', 'user__username', 'title']
    readonly_fields = ['product', 'user', 'created']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product_count']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['products']

    @admin.display(description='Products')
    def product_count(self, obj):
        return obj.products.count()


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at']
