"""
Módulo de scraping.
"""

from app.services.scraping.models import ScrapedBusiness, ScrapedContact, ScrapeResult
from app.services.scraping.base import BaseScraper
from app.services.scraping.google_scraper import GoogleScraper
from app.services.scraping.google_maps_scraper import GoogleMapsScraper
from app.services.scraping.instagram_scraper import InstagramScraper

__all__ = [
    "ScrapedBusiness",
    "ScrapedContact", 
    "ScrapeResult",
    "BaseScraper",
    "GoogleScraper",
    "GoogleMapsScraper",
    "InstagramScraper",
]
