"""
MLA - Meme Laugh Analyzer
Core package initialization
"""

__version__ = "1.0.0"
__author__ = "MLA Development Team"
__description__ = "Advanced meme response tracking and analysis system"

# src/core/__init__.py
"""
Core functionality for MLA
Contains the main detection, database, and scraping components
"""

from .detector import LaughDetector, DetectionResult
from .database import MLADatabase, MemeResponse
from .scraper import MemeScraper, ScrapingError

__all__ = [
    'LaughDetector',
    'DetectionResult',
    'MLADatabase',
    'MemeResponse',
    'MemeScraper',
    'ScrapingError'
]