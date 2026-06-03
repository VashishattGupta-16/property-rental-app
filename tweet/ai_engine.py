import re
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile

# Global singleton variable
_nlp_pipeline = None

def get_nlp_pipeline():
    """Lazy-loading singleton for spaCy model to prevent memory bloat in web workers."""
    global _nlp_pipeline
    if _nlp_pipeline is None:
        try:
            import spacy
            try:
                _nlp_pipeline = spacy.load("en_core_web_sm")
            except OSError:
                import os
                os.system("python -m spacy download en_core_web_sm")
                _nlp_pipeline = spacy.load("en_core_web_sm")
        except ImportError:
            raise ImportError("spacy is required for NLP features. Install it with: pip install spacy")
    return _nlp_pipeline

class ListingProcessor:
    @staticmethod
    def extract_listing_metadata(text):
        """
        Extracts structured data and SEO keywords from raw text.
        """
        nlp = get_nlp_pipeline()
        doc = nlp(text.lower())
        metadata = {
            "locations": [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC"]],
            "bhk_type": None,
            "keywords": [],
            "is_furnished": "furnished" in text.lower() and "unfurnished" not in text.lower()
        }

        # Regex for BHK types (e.g., 2BHK, 1 bhk, 3 bedroom)
        bhk_match = re.search(r'(\d)\s*(?:bhk|bedroom|br)', text.lower())
        if bhk_match:
            metadata["bhk_type"] = f"{bhk_match.group(1)}BHK"

        # Extract top SEO keywords (Nouns and Adjectives)
        keywords = [token.lemma_ for token in doc 
                    if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop and len(token.text) > 2]
        metadata["keywords"] = list(set(keywords))[:10]
        
        return metadata

    @staticmethod
    def parse_smart_query(query):
        """
        Converts a natural language search query into filter parameters.
        Example: "Luxury 2BHK in Mohali" -> {'location': 'Mohali', 'type': '2BHK'}
        """
        nlp = get_nlp_pipeline()
        doc = nlp(query)
        filters = {
            "location": None,
            "property_type": None,
            "keywords": []
        }
        
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                filters["location"] = ent.text
        
        bhk_match = re.search(r'(\d)\s*(?:bhk|bedroom)', query.lower())
        if bhk_match:
            filters["property_type"] = f"{bhk_match.group(1)}BHK"
            
        return filters

def optimize_listing_image(image_field, max_width=1200, quality=85):
    """
    Pillow-based compression and resizing.
    """
    if not image_field:
        return None

    img = Image.open(image_field)
    
    # Convert to RGB if necessary (handles PNG/RGBA to JPEG conversion)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Resize while maintaining aspect ratio
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int(float(img.height) * float(ratio))
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return ContentFile(output.read(), name=image_field.name)