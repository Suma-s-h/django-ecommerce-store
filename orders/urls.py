from django.urls import path
from . import views

app_name = 'orders'
urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('<int:order_id>/payment/', views.payment, name='payment'),
    path('<int:order_id>/payment/complete/', views.payment_complete, name='payment_complete'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('coupon/apply/', views.coupon_apply, name='coupon_apply'),
    path('coupon/remove/', views.coupon_remove, name='coupon_remove'),
    path('my-orders/', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
]
