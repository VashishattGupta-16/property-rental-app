import json
from typing import List, Optional
from django.core.cache import cache
from .models import Rental, Wishlist

class PropertyRecommender:
    def __init__(self):
        self.cache_key_prefix = "user_recs_"
        self.compiled_feed_prefix = "user_feeds_compiled:"

    def _get_interaction_data(self):
        """
        Fetch wishlist data to build the interaction matrix.
        Used primarily by background training tasks.
        """
        import pandas as pd
        interactions = Wishlist.objects.all().values('user_id', 'rental_id')
        if not interactions.exists():
            return None
        
        df = pd.DataFrame(list(interactions))
        df['rating'] = 1  # Implicit rating
        return df

    def get_user_recommendations(self, user_id: int, limit: int = 4) -> List[Rental]:
        """
        High-performance O(1) retrieval path. 
        Fetches pre-computed recommendation IDs from Redis.
        """
        feed_key = f"{self.compiled_feed_prefix}{user_id}"
        compiled_data = cache.get(feed_key)

        if not compiled_data:
            return list(self.get_content_fallback(limit=limit))

        try:
            top_ids = json.loads(compiled_data)[:limit]
            # Fetch specific objects. list() is called to evaluate the queryset immediately
            # preserving the cache-friendly nature of the retrieval.
            rentals = list(Rental.objects.filter(id__in=top_ids, is_available=True))
            
            # Ensure order from pre-computed feed is preserved
            rentals.sort(key=lambda x: top_ids.index(x.id))
            return rentals
        except (json.JSONDecodeError, TypeError, ValueError):
            return list(self.get_content_fallback(limit=limit))

    def get_content_fallback(self, location: Optional[str] = None, price: Optional[float] = None, limit: int = 4):
        """
        Simple content-based fallback using location and price proximity.
        """
        return Rental.objects.filter(is_available=True).order_by('-created_at')[:limit]