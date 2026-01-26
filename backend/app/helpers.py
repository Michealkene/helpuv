import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def format_price(cents: int) -> str:
    """Format price from cents to dollars"""
    return f"${cents / 100:.2f}"
def calculate_dataset_price(company_count: int, enrichment_level: str) -> int:
    """
    Calculate dataset price based on company count and enrichment level.
    
    Args:
        company_count: Number of companies in dataset
        enrichment_level: 'phone_only' or 'email_and_phone'
    
    Returns:
        Price in cents
    """
    # Pricing: $0.05 for phone-only, $0.10 for email_and_phone
    price_per_company = {
        'phone_only': 5,  # 5 cents per company
        'email_and_phone': 10,  # 10 cents per company
    }
    
    rate = price_per_company.get(enrichment_level, 5)  # Default to phone_only rate
    return company_count * rate
