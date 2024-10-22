from celery import shared_task
from django.utils import timezone
from .models import Pilgrim
from datetime import timedelta

@shared_task
def update_expired_tokens():
    # Get the current time
    now = timezone.now()
    # Update records where valid_until is less than now
    Pilgrim.objects.filter(valid_until__lt=now).update(is_expired=True)
