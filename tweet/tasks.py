
import json
import pickle
from typing import List
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from django_redis import get_redis_connection
from django.core.cache import cache
from celery import shared_task
from .models import Rental, PropertyVisit, Wishlist
try:
    from .ai_engine import ListingProcessor, optimize_listing_image
except ImportError:
    ListingProcessor = None
    optimize_listing_image = None

try:
    from .recommender import PropertyRecommender
except ImportError:
    PropertyRecommender = None


@shared_task
def record_property_visit(share_id, user_id, ip_address, user_agent):
    """
    Record a single property visit by pushing it to the Redis visit stream.
    The `drain_visit_buffer` batch task will later ingest entries into the DB.
    This keeps request latency low and avoids direct DB writes in the request path.
    """
    try:
        con = get_redis_connection("default")
        payload = {
            "share_id": share_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "visited_at": timezone.now().isoformat(),
        }
        con.rpush("stream:property_visits", json.dumps(payload))
        return True
    except Exception:
        # Swallow exceptions to avoid breaking request flow; worker logs will contain errors
        return False

@shared_task
def drain_visit_buffer():
    """
    Drain Redis visit stream using an atomic rename to prevent race conditions.
    """
    con = get_redis_connection("default")
    
    if not con.exists("stream:property_visits"):
        return

    # Move current data to a processing key
    process_key = "stream:property_visits:ingest"
    con.rename("stream:property_visits", process_key)
    
    raw_logs = con.lrange(process_key, 0, -1)
    visits = []
    
    for raw in raw_logs:
        data = json.loads(raw)
        visits.append(PropertyVisit(
            share_id=data['share_id'],
            user_id=data['user_id'],
            ip_address=data['ip_address'],
            user_agent=data['user_agent'],
            visited_at=parse_datetime(data['visited_at'])
        ))
    
    if visits:
        PropertyVisit.objects.bulk_create(visits)
        con.delete(process_key)

@shared_task
def process_rental_ai_assets(rental_id):
    if ListingProcessor is None or optimize_listing_image is None:
        return "AI/Pillow dependencies missing, skipping."

    rental = Rental.objects.get(id=rental_id)
    
    # 1. NLP Metadata
    meta = ListingProcessor.extract_listing_metadata(f"{rental.title} {rental.description}")
    
    # 2. Pillow Optimization
    if rental.image:
        optimized = optimize_listing_image(rental.image)
        rental.image.save(rental.image.name, optimized, save=False)
    
    rental.save(update_fields=['image']) # Prevent recursion by specifying update_fields

@shared_task
def train_recommendation_model():
    """
    Offline training and feed pre-computation.
    Iterates over active users to generate top 12 property recommendations.
    """
    if PropertyRecommender is None:
        return "Recommendation dependencies (pandas/surprise) missing, skipping."

    from surprise import SVD, Dataset, Reader
    User = get_user_model()
    rec_engine = PropertyRecommender()
    df = rec_engine._get_interaction_data()
    
    if df is not None:
        reader = Reader(rating_scale=(0, 1))
        data = Dataset.load_from_df(df[['user_id', 'rental_id', 'rating']], reader)
        trainset = data.build_full_trainset()
        
        algo = SVD()
        algo.fit(trainset)
        
        # Pre-calculate top 12 for all active users
        active_users = User.objects.filter(is_active=True).values_list('id', flat=True)
        active_rentals = list(Rental.objects.filter(is_available=True).values_list('id', flat=True))
        
        for user_id in active_users:
            # Calculate scores for all items
            user_predictions = [
                (rid, algo.predict(user_id, rid).est) 
                for rid in active_rentals
            ]
            # Sort by score descending
            user_predictions.sort(key=lambda x: x[1], reverse=True)
            top_12_ids = [x[0] for x in user_predictions[:12]]
            
            # Push to Redis as thin JSON strings
            cache_key = f"user_feeds_compiled:{user_id}"
            cache.set(cache_key, json.dumps(top_12_ids), 86400 * 2) # 48hr TTL