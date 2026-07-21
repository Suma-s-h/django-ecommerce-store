from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order

_old_statuses = {}


@receiver(pre_save, sender=Order)
def track_order_status(sender, instance, **kwargs):
    if instance.pk:
        old = Order.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
        _old_statuses[instance.pk] = old


@receiver(post_save, sender=Order)
def send_order_email(sender, instance, created, **kwargs):
    if created:
        subject = f'Order #{instance.id} Confirmed — ShopDjango'
        message = render_to_string('emails/order_placed.txt', {'order': instance})
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email], fail_silently=True)
    else:
        old_status = _old_statuses.pop(instance.pk, None)
        if old_status and old_status != instance.status:
            subject = f'Order #{instance.id} Update — {instance.get_status_display()}'
            message = render_to_string('emails/order_status_changed.txt', {'order': instance})
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email], fail_silently=True)
