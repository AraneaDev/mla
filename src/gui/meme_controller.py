"""
Meme Controller Module
Handles meme loading, management, and tracking
"""

import time
import requests
import io
from datetime import datetime
from PIL import Image, ImageTk
from typing import List, Dict, Any, Optional, Callable
import numpy as np

from config import config
from src.core.scraper import MemeScraper
from src.core.database import MLADatabase, MemeResponse
from src.core.detector import DetectionResult


class MemeController:
    """Handles meme operations and response tracking"""

    def __init__(self, database: MLADatabase):
        self.database = database
        self.scraper = MemeScraper()

        # Meme state
        self.memes_queue = []
        self.current_meme_index = -1
        self.current_meme = None
        self.view_start_time = None
        self.laugh_events = []

        # Auto-advance state
        self.auto_advance_active = False
        self.auto_advance_job = None

        # Callbacks
        self.on_meme_loaded: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_loading_status: Optional[Callable[[str], None]] = None
        self.on_meme_completed: Optional[Callable[[], None]] = None
        self.schedule_callback: Optional[Callable[[int, Callable], Any]] = None  # For scheduling auto-advance
        self.cancel_scheduled: Optional[Callable[[Any], None]] = None  # For canceling scheduled calls

        print("🎭 MemeController initialized")

    def load_new_memes(self, count: int = None):
        """Load new memes from various sources"""
        if self.on_loading_status:
            self.on_loading_status("🔄 Loading...")

        try:
            meme_count = count or config.scraping.default_meme_count
            new_memes = self.scraper.get_random_memes(meme_count)

            if new_memes:
                self.memes_queue = new_memes
                self.current_meme_index = -1

                if self.on_loading_status:
                    self.on_loading_status(f"✅ Loaded {len(new_memes)} memes!")

                self.next_meme()
                return True
            else:
                if self.on_loading_status:
                    self.on_loading_status("❌ Loading failed")
                return False

        except Exception as e:
            print(f"Error loading memes: {e}")
            if self.on_loading_status:
                self.on_loading_status("❌ Loading failed")
            return False

    def next_meme(self):
        """Display next meme and start tracking"""
        if not self.memes_queue:
            return False

        # Cancel any pending auto-advance
        self._cancel_auto_advance()

        # Save previous meme response
        if self.current_meme:
            self._save_current_meme_response()

        # Get next meme
        self.current_meme_index += 1
        if self.current_meme_index >= len(self.memes_queue):
            # All memes completed
            self.current_meme = None
            if self.on_meme_loaded:
                self.on_meme_loaded({
                    'completed': True,
                    'message': "🎉 All memes viewed! Load new ones?"
                })
            if self.on_meme_completed:
                self.on_meme_completed()
            return False

        self.current_meme = self.memes_queue[self.current_meme_index]
        self.view_start_time = time.time()
        self.laugh_events = []

        # Notify GUI
        if self.on_meme_loaded:
            self.on_meme_loaded({
                'meme': self.current_meme,
                'index': self.current_meme_index,
                'total': len(self.memes_queue),
                'completed': False
            })

        # Schedule auto-advance if enabled
        if self.auto_advance_active and self.schedule_callback:
            self.auto_advance_job = self.schedule_callback(
                config.gui.auto_advance_delay,
                self.next_meme
            )

        return True

    def prev_meme(self):
        """Go to previous meme"""
        if not self.memes_queue or self.current_meme_index <= 0:
            return False

        # Cancel auto-advance
        self._cancel_auto_advance()

        self.current_meme_index -= 2  # Will be incremented by next_meme
        return self.next_meme()

    def update_laugh_tracking(self, result: DetectionResult):
        """Update meme tracking with detection results"""
        if not self.current_meme:
            return

        if result.is_laughing:
            self.laugh_events.append({
                'timestamp': time.time(),
                'intensity': result.intensity,
                'confidence': result.confidence
            })

    def get_current_meme_info(self) -> Dict[str, Any]:
        """Get current meme information"""
        return {
            'current_meme': self.current_meme,
            'index': self.current_meme_index,
            'total_memes': len(self.memes_queue),
            'laugh_count': len(self.laugh_events) if self.laugh_events else 0,
            'has_memes': len(self.memes_queue) > 0,
            'can_go_prev': self.current_meme_index > 0,
            'can_go_next': self.current_meme_index < len(self.memes_queue) - 1
        }

    def set_auto_advance(self, enabled: bool):
        """Enable/disable auto-advance"""
        self.auto_advance_active = enabled

        if not enabled:
            self._cancel_auto_advance()
        elif self.current_meme and self.schedule_callback:
            # Schedule next advance
            self.auto_advance_job = self.schedule_callback(
                config.gui.auto_advance_delay,
                self.next_meme
            )

    def _cancel_auto_advance(self):
        """Cancel pending auto-advance"""
        if self.auto_advance_job and self.cancel_scheduled:
            self.cancel_scheduled(self.auto_advance_job)
            self.auto_advance_job = None

    def _save_current_meme_response(self):
        """Save current meme response to database"""
        if not self.current_meme or not self.view_start_time:
            return

        view_duration = time.time() - self.view_start_time
        laugh_detected = len(self.laugh_events) > 0

        if self.laugh_events:
            avg_intensity = np.mean([e['intensity'] for e in self.laugh_events])
            avg_confidence = np.mean([e['confidence'] for e in self.laugh_events])
            max_intensity = max([e['intensity'] for e in self.laugh_events])
        else:
            avg_intensity = avg_confidence = max_intensity = 0.0

        response = MemeResponse(
            meme_id=self.current_meme['id'],
            meme_url=self.current_meme['url'],
            meme_title=self.current_meme['title'],
            meme_source=self.current_meme['source'],
            timestamp=datetime.now(),
            viewed_duration=view_duration,
            laugh_detected=laugh_detected,
            laugh_intensity=avg_intensity,
            laugh_confidence=avg_confidence,
            laugh_count=len(self.laugh_events),
            max_intensity=max_intensity,
            meme_tags=self.current_meme['tags']
        )

        success = self.database.save_meme_response(response)
        if success:
            print(f"💾 Saved: {self.current_meme['title'][:30]}... | "
                  f"Laughed: {laugh_detected} | Score: {response.laugh_score:.0f}")

    def get_scraper_status(self) -> Dict[str, Any]:
        """Get scraper status"""
        return self.scraper.get_source_status()

    def reset_failed_sources(self):
        """Reset failed sources to retry them"""
        self.scraper.reset_failed_sources()

    def test_sources(self) -> Dict[str, bool]:
        """Test all meme sources"""
        sources = ['memedroid', 'reddit_memes', 'reddit_funny']
        results = {}

        for source in sources:
            try:
                results[source] = self.scraper.test_source(source)
            except Exception as e:
                print(f"Error testing {source}: {e}")
                results[source] = False

        return results

    def get_meme_statistics(self) -> Dict[str, Any]:
        """Get meme viewing statistics"""
        stats = self.database.get_statistics()

        # Add current session info
        stats['current_session'] = {
            'memes_in_queue': len(self.memes_queue),
            'current_index': self.current_meme_index,
            'current_meme_laughs': len(self.laugh_events) if self.laugh_events else 0,
            'auto_advance_enabled': self.auto_advance_active
        }

        return stats

    def clear_current_session(self):
        """Clear current meme session"""
        # Save current meme if viewing
        if self.current_meme:
            self._save_current_meme_response()

        # Cancel auto-advance
        self._cancel_auto_advance()

        # Clear state
        self.memes_queue = []
        self.current_meme_index = -1
        self.current_meme = None
        self.view_start_time = None
        self.laugh_events = []

        print("🧹 Meme session cleared")

    def force_save_current_meme(self):
        """Force save current meme response (for shutdown)"""
        if self.current_meme:
            self._save_current_meme_response()

    def get_queue_info(self) -> Dict[str, Any]:
        """Get detailed queue information"""
        return {
            'total_memes': len(self.memes_queue),
            'current_index': self.current_meme_index,
            'remaining_memes': len(self.memes_queue) - self.current_meme_index - 1,
            'sources_in_queue': list(set(meme.get('source', 'unknown') for meme in self.memes_queue)),
            'queue_empty': len(self.memes_queue) == 0
        }