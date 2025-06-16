"""
Status Manager Module
Handles status updates and display management
"""

import tkinter as tk
from typing import Dict, Any

from config import config
from src.core.detector import DetectionResult


class StatusManager:
    """Manages status display updates"""

    def __init__(self, widgets: Dict[str, tk.Widget]):
        self.widgets = widgets

    def update_detection_status(self, result: DetectionResult, sensitivity: float = 1.3):
        """Update detection status display"""
        # Laugh status
        if result.is_laughing:
            self.widgets['laugh_status'].config(
                text="😂 LAUGHING!",
                fg=config.gui.theme_colors['accent_green']
            )
        else:
            self.widgets['laugh_status'].config(
                text="😐 Not Laughing",
                fg=config.gui.theme_colors['text_primary']
            )

        # Detection info with trend
        trend_text = ""
        if result.confidence_trend != 0:
            trend_text = " ↗️" if result.confidence_trend > 0 else " ↘️"

        self.widgets['detection_info'].config(
            text=f"Intensity: {result.intensity:.2f}{trend_text} | "
                 f"Confidence: {result.confidence:.2f} | "
                 f"Sensitivity: {sensitivity:.1f}"
        )

    def update_meme_status(self, meme_info: Dict[str, Any]):
        """Update meme-related status"""
        viewed = max(0, meme_info.get('index', -1))
        laugh_count = meme_info.get('laugh_count', 0)
        total_memes = meme_info.get('total_memes', 0)

        self.widgets['meme_info'].config(
            text=f"Memes viewed: {viewed} | "
                 f"Current laugh count: {laugh_count} | "
                 f"Queue: {total_memes} memes"
        )

    def update_loading_status(self, status: str):
        """Update loading status on load button"""
        if 'load_btn' in self.widgets:
            self.widgets['load_btn'].config(text=status)

    def update_calibration_status(self, status: str):
        """Update calibration status on calibrate button"""
        if 'calibrate_btn' in self.widgets:
            self.widgets['calibrate_btn'].config(text=status)

    def clear_all_status(self):
        """Clear all status displays to default"""
        self.widgets['laugh_status'].config(
            text="😐 Not Laughing",
            fg=config.gui.theme_colors['text_primary']
        )

        self.widgets['detection_info'].config(
            text="Intensity: 0.00 | Confidence: 0.00 | Sensitivity: 1.3"
        )

        self.widgets['meme_info'].config(
            text="Memes viewed: 0 | Current laugh count: 0"
        )

    def show_detection_paused(self):
        """Show detection paused status"""
        self.widgets['laugh_status'].config(
            text="⏸️ Detection Paused",
            fg=config.gui.theme_colors['text_secondary']
        )

    def show_camera_error(self, error_msg: str):
        """Show camera error status"""
        self.widgets['laugh_status'].config(
            text=f"❌ Camera Error",
            fg=config.gui.theme_colors['accent_red']
        )

        self.widgets['detection_info'].config(
            text=f"Error: {error_msg[:50]}..."
        )

    def show_no_memes_loaded(self):
        """Show no memes loaded status"""
        self.widgets['meme_info'].config(
            text="No memes loaded | Click 'Load Memes' to start"
        )

    def update_session_stats(self, stats: Dict[str, Any]):
        """Update session statistics"""
        total = stats.get('total_memes', 0)
        laughed = stats.get('memes_laughed_at', 0)
        rate = stats.get('laugh_rate', 0)

        # Could add a session stats label if we had one
        # For now, integrate into meme_info
        current_info = self.widgets['meme_info'].cget('text')
        if not current_info.startswith("Session"):
            session_text = f" | Session laugh rate: {rate:.1f}%"
            self.widgets['meme_info'].config(text=current_info + session_text)