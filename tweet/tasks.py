from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import PropertyInquiry, PropertyShare, PropertyVisit


@shared_task
def aggregate_daily_analytics():
    since = timezone.now() - timedelta(days=1)

    return {
        "shares": PropertyShare.objects.filter(created_at__gte=since).count(),
        "visits": PropertyVisit.objects.filter(visited_at__gte=since).count(),
        "inquiries": PropertyInquiry.objects.filter(created_at__gte=since).count(),
    }

@shared_task
def record_property_visit(share_id, user_id, ip_address, user_agent):
    """Async task to record a property visit without blocking the user response."""
    return PropertyVisit.objects.create(
        share_id=share_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    ).id
