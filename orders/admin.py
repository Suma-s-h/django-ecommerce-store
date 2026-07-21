import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Order, OrderItem, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity', 'line_total']

    @admin.display(description='Line Total')
    def line_total(self, obj):
        return f'${obj.get_cost()}'


@admin.action(description='Export selected orders as CSV')
def export_orders_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Email', 'Address', 'City', 'Country',
                     'Status', 'Paid', 'Discount %', 'Total', 'Date'])
    for order in queryset.prefetch_related('items'):
        writer.writerow([
            order.id,
            f'{order.first_name} {order.last_name}',
            order.email,
            order.address,
            order.city,
            order.country,
            order.get_status_display(),
            'Yes' if order.paid else 'No',
            order.discount,
            order.get_total_cost(),
            order.created.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'status', 'paid', 'discount', 'order_total', 'created']
    list_filter = ['status', 'paid', 'created']
    list_editable = ['status', 'paid']
    inlines = [OrderItemInline]
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['created', 'updated', 'stripe_payment_intent', 'coupon', 'discount']
    date_hierarchy = 'created'
    actions = [export_orders_csv]

    @admin.display(description='Customer')
    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    @admin.display(description='Total')
    def order_total(self, obj):
        return f'${obj.get_total_cost()}'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'valid_from', 'valid_to', 'active']
    list_editable = ['active']
    list_filter = ['active']
    search_fields = ['code']
