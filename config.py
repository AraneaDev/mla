"""
Configuration settings for MLA - Meme Laugh Analyzer
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class DetectionConfig:
    """Laugh detection configuration"""
    default_sensitivity: float = 1.3
    min_sensitivity: float = 0.5
    max_sensitivity: float = 3.0
    sensitivity_step: float = 0.1

    # Detection thresholds
    base_threshold: float = 0.4
    min_threshold: float = 0.25
    consecutive_frames_required: int = 3
    consecutive_frames_to_stop: int = 5

    # History tracking
    history_size: int = 20
    smoothing_window: int = 10

    # Feature weights
    mouth_weight: float = 0.4
    eye_weight: float = 0.3
    cheek_weight: float = 0.3


@dataclass
class CameraConfig:
    """Camera configuration"""
    default_camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    fps: int = 30
    flip_horizontal: bool = True


@dataclass
class DatabaseConfig:
    """Database configuration"""
    default_db_path: str = "data/mla.db"
    backup_on_reset: bool = True
    auto_backup_interval: int = 3600  # seconds


@dataclass
class ScrapingConfig:
    """Meme scraping configuration"""
    default_meme_count: int = 25
    request_timeout: int = 10
    max_retries: int = 3

    # User agent for web requests
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    # Source configurations
    sources: Dict[str, Dict[str, Any]] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = {
                'memedroid': {
                    'enabled': True,
                    'weight': 0.4,
                    'pages': ['feed', 'tag/funny', 'tag/meme', 'tag/lol'],
                    'selectors': [
                        'article.gallery-item',
                        '.gallery-item',
                        'article[data-meme-id]',
                        '.meme-item'
                    ]
                },
                'reddit': {
                    'enabled': True,
                    'weight': 0.6,
                    'subreddits': [
                        'memes', 'funny', 'dankmemes',
                        'wholesomememes', 'me_irl', 'ProgrammerHumor'
                    ],
                    'sort_types': ['hot', 'new', 'top']
                }
            }


@dataclass
class GUIConfig:
    """GUI configuration"""
    window_title: str = "MLA - Meme Laugh Analyzer"
    window_size: str = "1600x1000"
    theme_colors: Dict[str, str] = None

    # Layout proportions
    camera_weight: float = 1.0  # 1/3 of screen
    meme_weight: float = 2.0  # 2/3 of screen

    # Auto-advance settings
    auto_advance_delay: int = 10000  # milliseconds

    def __post_init__(self):
        if self.theme_colors is None:
            self.theme_colors = {
                'bg_primary': '#2c3e50',
                'bg_secondary': '#34495e',
                'bg_tertiary': '#ecf0f1',
                'text_primary': 'white',
                'text_secondary': '#7f8c8d',
                'accent_green': '#2ecc71',
                'accent_red': '#e74c3c',
                'accent_blue': '#3498db',
                'accent_orange': '#f39c12',
                'accent_purple': '#9b59b6'
            }


@dataclass
class ExportConfig:
    """Data export configuration"""
    default_export_dir: str = "exports"
    csv_delimiter: str = ","
    date_format: str = "%Y-%m-%d %H:%M:%S"

    # CSV columns for export
    csv_columns: List[str] = None

    def __post_init__(self):
        if self.csv_columns is None:
            self.csv_columns = [
                'meme_id', 'meme_url', 'meme_title', 'meme_source',
                'timestamp', 'viewed_duration', 'laugh_detected',
                'laugh_intensity', 'laugh_confidence', 'laugh_count',
                'max_intensity', 'meme_tags', 'laugh_score'
            ]


class MLAConfig:
    """Main configuration class"""

    def __init__(self):
        self.detection = DetectionConfig()
        self.camera = CameraConfig()
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        self.gui = GUIConfig()
        self.export = ExportConfig()

        # Ensure data directories exist
        self._create_directories()

    def _create_directories(self):
        """Create necessary directories"""
        dirs_to_create = [
            os.path.dirname(self.database.default_db_path),
            self.export.default_export_dir,
        ]

        for dir_path in dirs_to_create:
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

    @classmethod
    def load_from_file(cls, config_path: str) -> 'MLAConfig':
        """Load configuration from file (future enhancement)"""
        # TODO: Implement configuration file loading
        return cls()

    def save_to_file(self, config_path: str):
        """Save configuration to file (future enhancement)"""
        # TODO: Implement configuration file saving
        pass


# Global configuration instance
config = MLAConfig()