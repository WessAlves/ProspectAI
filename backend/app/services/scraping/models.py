"""
Modelo de dados para resultados de scraping.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ScrapedBusiness:
    """Dados de uma empresa/negócio extraído."""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    category: Optional[str] = None
    opening_hours: Optional[Dict[str, str]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    photos: List[str] = field(default_factory=list)
    extra_data: Dict[str, Any] = field(default_factory=dict)
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    source: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "website": self.website,
            "email": self.email,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "category": self.category,
            "opening_hours": self.opening_hours,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "place_id": self.place_id,
            "photos": self.photos,
            "extra_data": self.extra_data,
            "scraped_at": self.scraped_at.isoformat(),
            "source": self.source,
        }


@dataclass
class ScrapedContact:
    """Dados de contato extraído de um site."""
    source_url: str
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    social_media: Dict[str, str] = field(default_factory=dict)
    contact_forms: List[str] = field(default_factory=list)
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "source_url": self.source_url,
            "emails": self.emails,
            "phones": self.phones,
            "social_media": self.social_media,
            "contact_forms": self.contact_forms,
            "scraped_at": self.scraped_at.isoformat(),
        }


@dataclass
class ScrapeResult:
    """Resultado completo de uma operação de scraping."""
    success: bool
    businesses: List[ScrapedBusiness] = field(default_factory=list)
    total_found: int = 0
    query: str = ""
    location: str = ""
    error: Optional[str] = None
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "success": self.success,
            "businesses": [b.to_dict() for b in self.businesses],
            "total_found": self.total_found,
            "query": self.query,
            "location": self.location,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }
