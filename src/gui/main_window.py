"""
Main GUI Window for MLA
Orchestrates all components with ALL original functionality intact
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageTk
import time
import requests
import io
import cv2
import threading

from config import config
from src.core.database import MLADatabase
from src.gui.camera_controller import CameraController
from src.gui.meme_controller import MemeController
from src.gui.gui_components import GUIComponentManager
from src.gui.status_manager import StatusManager
from src.gui.dialogs import DialogManager
from src.gui.data_viewer import MemeDataViewer
from src.utils.image_utils import ImageProcessor


class MLAMainWindow:
    """Complete main application window with ALL original functionality - FIXED"""

    def __init__(self, camera_index: int = 0, sensitivity: float = None):
        # Initialize core components
        self.database = MLADatabase()
        self.camera_controller = CameraController(camera_index, sensitivity)
        self.meme_controller = MemeController(self.database)
        self.image_processor = ImageProcessor()

        # Setup GUI
        self.root = tk.Tk()
        self.gui_manager = GUIComponentManager(self.root)

        # Setup layout and get widgets - FIXED: store reference properly
        self.widgets = self.gui_manager.setup_main_layout()
        self.status_manager = StatusManager(self.widgets)
        self.dialog_manager = DialogManager(self.root)

        # Setup callbacks and event handlers
        self._setup_callbacks()
        self._setup_event_handlers()
        self._setup_all_button_commands()

        # Auto-start camera
        self.camera_controller.initialize_camera()

        print("🎮 MLA GUI initialized (refactored with ALL functionality)")

    def _setup_callbacks(self):
        """Setup callbacks between components"""
        # Camera callbacks
        self.camera_controller.on_detection_update = self._on_detection_update
        self.camera_controller.on_camera_frame = self._on_camera_frame

        # Meme callbacks
        self.meme_controller.on_meme_loaded = self._on_meme_loaded
        self.meme_controller.on_loading_status = self._on_loading_status
        self.meme_controller.on_meme_completed = self._on_meme_completed

        # Setup scheduling callbacks for auto-advance
        self.meme_controller.schedule_callback = self.root.after
        self.meme_controller.cancel_scheduled = self.root.after_cancel

    def _setup_event_handlers(self):
        """Setup GUI event handlers"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_all_button_commands(self):
        """Setup ALL button commands from original functionality - FIXED"""
        # Detection controls
        self.gui_manager.set_button_command('start_btn', self.start_detection)
        self.gui_manager.set_button_command('stop_btn', self.stop_detection)

        # Meme controls
        self.gui_manager.set_button_command('load_btn', self.load_new_memes)
        self.gui_manager.set_button_command('prev_btn', self.prev_meme)
        self.gui_manager.set_button_command('next_btn', self.next_meme)

        # System controls
        self.gui_manager.set_button_command('data_btn', self.show_meme_data)
        self.gui_manager.set_button_command('calibrate_btn', self.calibrate)
        self.gui_manager.set_button_command('reset_btn', self.reset_all_data)
        self.gui_manager.set_button_command('export_btn', self.export_data)
        self.gui_manager.set_button_command('import_btn', self.import_data)

        # Scale and checkbox commands
        self.gui_manager.set_scale_command('sens_scale', self.update_sensitivity)
        # FIXED: Use proper widget references for checkboxes
        if 'auto_advance' in self.widgets:
            self.widgets['auto_advance'].trace('w', lambda *args: self.toggle_auto_advance())
        if 'show_landmarks' in self.widgets:
            self.widgets['show_landmarks'].trace('w', lambda *args: self.toggle_landmarks())

    # ===== CALLBACK HANDLERS =====

    def _on_detection_update(self, result):
        """Handle detection updates from camera"""
        self.root.after(0, lambda: self._update_detection_display(result))

    def _on_camera_frame(self, frame):
        """Handle new camera frames"""
        self.root.after(0, lambda: self._update_camera_display(frame))

    def _on_meme_loaded(self, meme_data):
        """Handle meme loading - FIXED widget references"""
        if meme_data.get('completed'):
            if 'meme_title' in self.widgets:
                self.widgets['meme_title'].config(text=meme_data['message'])
            if 'meme_label' in self.widgets:
                self.widgets['meme_label'].config(
                    image="",
                    text="All memes completed!\nClick 'Load Memes' for more"
                )
                # FIXED: Clear image reference
                self.widgets['meme_label'].image = None
        else:
            meme = meme_data['meme']
            if 'meme_title' in self.widgets:
                self.widgets['meme_title'].config(
                    text=f"Meme {meme_data['index'] + 1}/{meme_data['total']}: {meme['title']}"
                )
            self._load_meme_image(meme['url'])

    def _on_loading_status(self, status):
        """Handle loading status updates"""
        self.status_manager.update_loading_status(status)

        # Reset button text after delay if it's a final status
        if status.startswith("✅") or status.startswith("❌"):
            self.gui_manager.reset_button_text_after_delay('load_btn', '🔄 Load Memes')

    def _on_meme_completed(self):
        """Handle when all memes are completed"""
        self.status_manager.show_no_memes_loaded()

    # ===== DETECTION CONTROLS =====

    def start_detection(self):
        """Start detection"""
        if self.camera_controller.start_detection():
            self.gui_manager.disable_button('start_btn')
            self.gui_manager.enable_button('stop_btn')
        else:
            self.dialog_manager.show_camera_error_dialog("Failed to initialize camera")

    def stop_detection(self):
        """Stop detection"""
        self.camera_controller.stop_detection()
        self.gui_manager.enable_button('start_btn')
        self.gui_manager.disable_button('stop_btn')
        self.status_manager.show_detection_paused()

    # ===== MEME CONTROLS =====

    def load_new_memes(self):
        """Load new memes - FIXED threading"""
        self.gui_manager.disable_button('load_btn')

        def load_in_thread():
            try:
                success = self.meme_controller.load_new_memes()
                self.root.after(0, lambda: self.gui_manager.enable_button('load_btn'))
            except Exception as e:
                print(f"Error loading memes: {e}")
                self.root.after(0, lambda: self.gui_manager.enable_button('load_btn'))

        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()

    def next_meme(self):
        """Show next meme"""
        self.meme_controller.next_meme()

    def prev_meme(self):
        """Show previous meme"""
        self.meme_controller.prev_meme()

    # ===== SYSTEM CONTROLS =====

    def show_meme_data(self):
        """Show meme data viewer"""
        try:
            data_viewer = MemeDataViewer(self.root, self.database)
            data_viewer.show()
        except Exception as e:
            self.dialog_manager.show_error_message("Error", f"Failed to open data viewer: {e}")

    def calibrate(self):
        """Perform calibration"""
        if not self.camera_controller.detection_active:
            self.dialog_manager.show_detection_not_active_dialog()
            return

        if not self.camera_controller.cap or not self.camera_controller.cap.isOpened():
            self.dialog_manager.show_camera_error_dialog("Camera not available")
            return

        # Disable button during calibration
        self.gui_manager.disable_button('calibrate_btn')
        self.status_manager.update_calibration_status("🎯 Calibrating...")

        success = self.dialog_manager.show_calibration_dialog(
            self.camera_controller.calibrate
        )

        if success:
            self.status_manager.update_calibration_status("✅ Calibrated!")
            self.dialog_manager.show_success_message("Success", "Calibration completed successfully!")
        else:
            self.status_manager.update_calibration_status("❌ Failed")
            self.dialog_manager.show_error_message("Error", "Calibration failed. Please try again.")

        # Reset button
        self.gui_manager.reset_button_text_after_delay('calibrate_btn', '🎯 Calibrate')
        self.root.after(2000, lambda: self.gui_manager.enable_button('calibrate_btn'))

    def reset_all_data(self):
        """Reset all data with confirmation"""
        if self.dialog_manager.show_reset_confirmation():
            success = self.database.reset_all_data()
            if success:
                self.dialog_manager.show_reset_success_dialog()
                # Clear current session
                self.meme_controller.clear_current_session()
                self.status_manager.clear_all_status()
            else:
                self.dialog_manager.show_error_message("Error", "Failed to reset data.")

    def export_data(self):
        """Export data to CSV"""
        filename = self.dialog_manager.show_export_dialog()
        if filename:
            try:
                count = self.database.export_to_csv(filename)
                self.dialog_manager.show_export_success_dialog(count, filename)
            except Exception as e:
                self.dialog_manager.show_error_message("Export Error", f"Export failed: {e}")

    def import_data(self):
        """Import data from CSV"""
        filename = self.dialog_manager.show_import_dialog()
        if filename:
            try:
                count = self.database.import_from_csv(filename)
                self.dialog_manager.show_import_success_dialog(count, filename)
            except Exception as e:
                self.dialog_manager.show_error_message("Import Error", f"Import failed: {e}")

    # ===== OPTIONS CONTROLS =====

    def update_sensitivity(self, value):
        """Update detection sensitivity"""
        try:
            sensitivity = float(value)
            self.camera_controller.set_sensitivity(sensitivity)
        except (ValueError, TypeError):
            print(f"Invalid sensitivity value: {value}")

    def toggle_auto_advance(self):
        """Toggle auto-advance"""
        try:
            enabled = self.gui_manager.get_variable_value('auto_advance')
            if enabled is not None:
                self.meme_controller.set_auto_advance(enabled)
        except Exception as e:
            print(f"Error toggling auto-advance: {e}")

    def toggle_landmarks(self):
        """Toggle landmark display"""
        try:
            show = self.gui_manager.get_variable_value('show_landmarks')
            if show is not None:
                self.camera_controller.set_show_landmarks(show)
        except Exception as e:
            print(f"Error toggling landmarks: {e}")

    # ===== DISPLAY UPDATES =====

    def _update_detection_display(self, result):
        """Update detection status display - FIXED"""
        try:
            sensitivity = self.gui_manager.get_variable_value('sens_var')
            if sensitivity is None:
                sensitivity = 1.3
            self.status_manager.update_detection_status(result, sensitivity)

            # Update meme tracking
            self.meme_controller.update_laugh_tracking(result)

            # Update meme status
            meme_info = self.meme_controller.get_current_meme_info()
            self.status_manager.update_meme_status(meme_info)
        except Exception as e:
            print(f"Error updating detection display: {e}")

    def _update_camera_display(self, frame):
        """Update camera display - FIXED widget references"""
        try:
            if 'camera_label' not in self.widgets:
                return

            # Get widget dimensions
            self.root.update_idletasks()
            widget_width = self.widgets['camera_label'].winfo_width()
            widget_height = self.widgets['camera_label'].winfo_height()

            # Use reasonable defaults if widget isn't ready
            if widget_width <= 1:
                widget_width = 400
            if widget_height <= 1:
                widget_height = 300

            # Use most of the widget space
            target_width = widget_width - 20
            target_height = widget_height - 20
            target_width = max(target_width, 300)
            target_height = max(target_height, 225)

            # Process frame for display
            photo = self.image_processor.process_frame_for_display(
                frame, target_width, target_height
            )

            self.widgets['camera_label'].config(image=photo, text="")
            self.widgets['camera_label'].image = photo

        except Exception as e:
            print(f"Error updating camera display: {e}")
            if 'camera_label' in self.widgets:
                self.widgets['camera_label'].config(
                    image="",
                    text=f"Camera Error: {str(e)[:50]}..."
                )
                self.widgets['camera_label'].image = None

    def _load_meme_image(self, url: str):
        """Load and display meme image - FIXED widget references"""
        try:
            if 'meme_label' not in self.widgets:
                return

            # Load image from URL
            image = self.image_processor.load_image_from_url(url)
            if not image:
                raise Exception("Failed to load image")

            # Get widget dimensions
            self.root.update_idletasks()
            widget_width = self.widgets['meme_label'].winfo_width()
            widget_height = self.widgets['meme_label'].winfo_height()

            # Use defaults if invalid
            if widget_width <= 1 or widget_height <= 1:
                widget_width = 800
                widget_height = 600

            # Resize image to fit
            resized_image = self.image_processor.resize_image_to_fit(
                image, widget_width - 20, widget_height - 20
            )

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(resized_image)

            # FIXED: Use proper widget reference and error handling
            self.widgets['meme_label'].config(image=photo, text="", compound='center')
            self.widgets['meme_label'].image = photo

        except Exception as e:
            print(f"Error loading meme image {url}: {e}")
            if 'meme_label' in self.widgets:
                self.widgets['meme_label'].config(
                    image="",
                    text=f"Failed to load meme\n{url[:50] if url else 'Unknown URL'}..."
                )
                self.widgets['meme_label'].image = None

    # ===== APPLICATION LIFECYCLE =====

    def on_closing(self):
        """Handle application closing"""
        print("🛑 Shutting down MLA...")

        try:
            # Save current meme if viewing
            self.meme_controller.force_save_current_meme()

            # Shutdown components
            self.camera_controller.shutdown()

        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            # Close application
            self.root.destroy()
            print("✅ MLA shutdown complete")

    def run(self):
        """Run the main application"""
        print("🚀 Starting MLA - Meme Laugh Analyzer...")
        print("💡 Instructions:")
        print("   1. Click '▶️ Start Detection' to activate camera")
        print("   2. Click '🔄 Load Memes' to begin")
        print("   3. Look at memes naturally")
        print("   4. Use controls to navigate and analyze")
        print("   5. Export data for external analysis")

        try:
            # Show initial status
            self.status_manager.clear_all_status()
            self.status_manager.show_no_memes_loaded()

            self.root.mainloop()
        except Exception as e:
            print(f"Error running application: {e}")
            raise

    # ===== ADDITIONAL METHODS FOR COMPLETENESS =====

    def get_application_status(self) -> dict:
        """Get comprehensive application status"""
        try:
            return {
                'camera': self.camera_controller.get_camera_info(),
                'detector': self.camera_controller.get_detector_state(),
                'memes': self.meme_controller.get_current_meme_info(),
                'database': self.database.get_statistics(),
                'scraper': self.meme_controller.get_scraper_status()
            }
        except Exception as e:
            print(f"Error getting application status: {e}")
            return {'error': str(e)}

    def force_refresh_display(self):
        """Force refresh all displays"""
        try:
            # Update status displays
            meme_info = self.meme_controller.get_current_meme_info()
            self.status_manager.update_meme_status(meme_info)

            # Update GUI state
            sensitivity = self.gui_manager.get_variable_value('sens_var')
            if sensitivity:
                self.camera_controller.set_sensitivity(sensitivity)
        except Exception as e:
            print(f"Error refreshing display: {e}")

    def emergency_save_data(self):
        """Emergency save current data (for unexpected shutdown)"""
        try:
            self.meme_controller.force_save_current_meme()
            self.database.backup_database()
            print("🆘 Emergency data save completed")
        except Exception as e:
            print(f"❌ Emergency save failed: {e}")

    def show_debug_info(self):
        """Show debug information"""
        try:
            status = self.get_application_status()
            debug_text = f"""
MLA Debug Information:

Camera Status: {status.get('camera', 'Error')}
Detector Status: {status.get('detector', 'Error')}
Meme Status: {status.get('memes', 'Error')}
Database Stats: {status.get('database', 'Error')}
Scraper Status: {status.get('scraper', 'Error')}
            """
            messagebox.showinfo("Debug Information", debug_text.strip())
        except Exception as e:
            messagebox.showerror("Debug Error", f"Error getting debug info: {e}")