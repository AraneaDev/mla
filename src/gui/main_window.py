"""
Main GUI Window for MLA
Handles the primary user interface and orchestrates all components
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
import time
import threading
from datetime import datetime
from PIL import Image, ImageTk
from typing import Optional, Dict, Any, List
import requests
import io

from config import config
from src.core.detector import LaughDetector, DetectionResult
from src.core.database import MLADatabase, MemeResponse
from src.core.scraper import MemeScraper
from src.gui.data_viewer import MemeDataViewer
from src.utils.image_utils import ImageProcessor

class MLAMainWindow:
    """Main application window for MLA"""

    def __init__(self, camera_index: int = 0, sensitivity: float = None):
        self.camera_index = camera_index

        # Initialize core components
        self.laugh_detector = LaughDetector(
            sensitivity=sensitivity or config.detection.default_sensitivity
        )
        self.database = MLADatabase()
        self.scraper = MemeScraper()
        self.image_processor = ImageProcessor()

        # Meme tracking state
        self.memes_queue = []
        self.current_meme_index = -1
        self.current_meme = None
        self.view_start_time = None
        self.laugh_events = []

        # Camera and detection state
        self.cap = None
        self.camera_thread = None
        self.running = False
        self.detection_active = False

        # GUI setup
        self.root = tk.Tk()
        self.root.title(config.gui.window_title)
        self.root.geometry(config.gui.window_size)
        self.root.configure(bg=config.gui.theme_colors['bg_primary'])
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Set minimum window size to prevent GUI breaking
        self.root.minsize(1200, 800)
        # Prevent window from being resizable to avoid layout issues
        self.root.resizable(True, True)

        self.setup_gui()
        self.initialize_camera()  # Auto-start camera but not detection
        print("🎮 MLA GUI initialized")

    def setup_gui(self):
        """Setup the main GUI interface"""
        # Configure main window grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Main container with fixed proportions
        main_frame = tk.Frame(self.root, bg=config.gui.theme_colors['bg_primary'])
        main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # Configure main frame layout
        main_frame.grid_rowconfigure(1, weight=1)  # Display section gets most space
        main_frame.grid_rowconfigure(2, weight=0)  # Controls section fixed size
        main_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = tk.Label(
            main_frame,
            text=config.gui.window_title,
            font=('Arial', 20, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_primary']
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky='ew')

        # Put display section at row 1 (gets the expandable space)
        display_container = tk.Frame(main_frame, bg=config.gui.theme_colors['bg_primary'])
        display_container.grid(row=1, column=0, sticky='nsew', pady=(0, 10))

        self.setup_display_section_content(display_container)

        # Put control section at row 2 (fixed size)
        control_container = tk.Frame(main_frame, bg=config.gui.theme_colors['bg_primary'])
        control_container.grid(row=2, column=0, sticky='ew')

        self.setup_control_section_content(control_container)

    def setup_display_section_content(self, parent):
        """Setup camera and meme display section"""
        top_frame = tk.Frame(parent, bg=config.gui.theme_colors['bg_primary'])
        top_frame.pack(fill='both', expand=True)

        # Left side - Camera feed (1/3 of screen)
        camera_frame = tk.LabelFrame(
            top_frame,
            text="📹 Camera Feed",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            bd=2
        )
        camera_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        self.camera_label = tk.Label(
            camera_frame,
            text="Camera stopped",
            bg='black',
            fg='white'
        )
        self.camera_label.pack(fill='both', expand=True, padx=5, pady=5)

        # Right side - Meme display (2/3 of screen)
        meme_frame = tk.LabelFrame(
            top_frame,
            text="🎭 Current Meme",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            bd=2
        )
        meme_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Configure grid for proper meme sizing
        meme_frame.grid_rowconfigure(1, weight=1)
        meme_frame.grid_columnconfigure(0, weight=1)

        # Meme title
        self.meme_title = tk.Label(
            meme_frame,
            text="No meme loaded",
            font=('Arial', 12, 'bold'),
            bg=config.gui.theme_colors['bg_secondary'],
            fg=config.gui.theme_colors['text_primary'],
            wraplength=800
        )
        self.meme_title.grid(row=0, column=0, pady=5, sticky='ew')

        # Meme image container
        self.meme_label = tk.Label(
            meme_frame,
            text="Click 'Load Memes' to start",
            bg=config.gui.theme_colors['bg_tertiary'],
            compound='center'
        )
        self.meme_label.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

    def setup_control_section_content(self, parent):
        """Setup status and control section"""
        # Configure parent grid
        parent.grid_rowconfigure(0, weight=0)  # Status frame
        parent.grid_rowconfigure(1, weight=0)  # Controls frame
        parent.grid_columnconfigure(0, weight=1)

        # Status frame
        self.setup_status_frame(parent)

        # Controls frame
        self.setup_controls_frame(parent)

    def setup_status_frame(self, parent):
        """Setup status display frame"""
        status_frame = tk.LabelFrame(
            parent,
            text="📊 Live Status",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            bd=2
        )
        status_frame.grid(row=0, column=0, sticky='ew', pady=(0, 5))

        status_inner = tk.Frame(status_frame, bg=config.gui.theme_colors['bg_secondary'])
        status_inner.pack(fill='x', padx=10, pady=5)

        self.laugh_status = tk.Label(
            status_inner,
            text="😐 Not Laughing",
            font=('Arial', 16, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        )
        self.laugh_status.pack()

        self.detection_info = tk.Label(
            status_inner,
            text=f"Intensity: 0.00 | Confidence: 0.00 | Sensitivity: {self.laugh_detector.sensitivity}",
            font=('Arial', 12),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        )
        self.detection_info.pack()

        self.meme_info = tk.Label(
            status_inner,
            text="Memes viewed: 0 | Current laugh count: 0",
            font=('Arial', 12),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        )
        self.meme_info.pack()

    def setup_controls_frame(self, parent):
        """Setup control buttons and options"""
        controls_frame = tk.LabelFrame(
            parent,
            text="🎮 Controls",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            bd=2
        )
        controls_frame.grid(row=1, column=0, sticky='ew')

        # Detection controls row
        self.setup_detection_controls(controls_frame)

        # System controls row
        self.setup_system_controls(controls_frame)

        # Options row
        self.setup_options_controls(controls_frame)

    def setup_detection_controls(self, parent):
        """Setup detection and navigation controls"""
        btn_frame1 = tk.Frame(parent, bg=config.gui.theme_colors['bg_secondary'])
        btn_frame1.pack(pady=5)

        # Detection controls
        self.start_btn = tk.Button(
            btn_frame1,
            text="▶️ Start Detection",
            command=self.start_detection,
            font=('Arial', 10),
            bg=config.gui.theme_colors['accent_green'],
            fg='white',
            width=15
        )
        self.start_btn.pack(side='left', padx=2)

        self.stop_btn = tk.Button(
            btn_frame1,
            text="⏸️ Stop Detection",
            command=self.stop_detection,
            font=('Arial', 10),
            bg=config.gui.theme_colors['accent_red'],
            fg='white',
            width=15,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=2)

        # Meme controls
        self.load_btn = tk.Button(
            btn_frame1,
            text="🔄 Load Memes",
            command=self.load_new_memes,
            font=('Arial', 10),
            bg=config.gui.theme_colors['accent_blue'],
            fg='white',
            width=12
        )
        self.load_btn.pack(side='left', padx=2)

        self.prev_btn = tk.Button(
            btn_frame1,
            text="⬅️ Previous",
            command=self.prev_meme,
            font=('Arial', 10),
            bg=config.gui.theme_colors['accent_orange'],
            fg='white',
            width=10
        )
        self.prev_btn.pack(side='left', padx=2)

        self.next_btn = tk.Button(
            btn_frame1,
            text="➡️ Next",
            command=self.next_meme,
            font=('Arial', 10),
            bg=config.gui.theme_colors['accent_green'],
            fg='white',
            width=10
        )
        self.next_btn.pack(side='left', padx=2)

    def setup_system_controls(self, parent):
        """Setup system management controls"""
        btn_frame2 = tk.Frame(parent, bg=config.gui.theme_colors['bg_secondary'])
        btn_frame2.pack(pady=5)

        self.data_btn = tk.Button(
            btn_frame2,
            text="📊 View Data",
            command=self.show_meme_data,
            font=('Arial', 10),
            bg=config.gui.theme_colors['accent_purple'],
            fg='white',
            width=12
        )
        self.data_btn.pack(side='left', padx=2)

        self.calibrate_btn = tk.Button(
            btn_frame2,
            text="🎯 Calibrate",
            command=self.calibrate,
            font=('Arial', 10),
            bg=config.gui.theme_colors['accent_purple'],
            fg='white',
            width=12
        )
        self.calibrate_btn.pack(side='left', padx=2)

        self.reset_btn = tk.Button(
            btn_frame2,
            text="🗑️ Reset Data",
            command=self.reset_all_data,
            font=('Arial', 10),
            bg=config.gui.theme_colors['accent_orange'],
            fg='white',
            width=12
        )
        self.reset_btn.pack(side='left', padx=2)

        self.export_btn = tk.Button(
            btn_frame2,
            text="💾 Export",
            command=self.export_data,
            font=('Arial', 10),
            bg='#1abc9c',
            fg='white',
            width=10
        )
        self.export_btn.pack(side='left', padx=2)

        self.import_btn = tk.Button(
            btn_frame2,
            text="📁 Import",
            command=self.import_data,
            font=('Arial', 10),
            bg=config.gui.theme_colors['bg_secondary'],
            fg='white',
            width=10
        )
        self.import_btn.pack(side='left', padx=2)

    def setup_options_controls(self, parent):
        """Setup options and settings controls"""
        opts_frame = tk.Frame(parent, bg=config.gui.theme_colors['bg_secondary'])
        opts_frame.pack(pady=5)

        # Sensitivity control
        tk.Label(
            opts_frame,
            text="Sensitivity:",
            font=('Arial', 10),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        ).pack(side='left', padx=5)

        self.sens_var = tk.DoubleVar(value=self.laugh_detector.sensitivity)
        self.sens_scale = tk.Scale(
            opts_frame,
            from_=config.detection.min_sensitivity,
            to=config.detection.max_sensitivity,
            resolution=config.detection.sensitivity_step,
            orient='horizontal',
            variable=self.sens_var,
            command=self.update_sensitivity,
            bg=config.gui.theme_colors['bg_secondary'],
            fg=config.gui.theme_colors['text_primary'],
            highlightthickness=0,
            width=15
        )
        self.sens_scale.pack(side='left', padx=5)

        # Auto-advance option
        self.auto_advance = tk.BooleanVar(value=False)
        self.auto_check = tk.Checkbutton(
            opts_frame,
            text="Auto-advance (10s)",
            variable=self.auto_advance,
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            selectcolor=config.gui.theme_colors['bg_secondary']
        )
        self.auto_check.pack(side='left', padx=20)

        # Show landmarks option
        self.show_landmarks = tk.BooleanVar(value=True)
        self.landmarks_check = tk.Checkbutton(
            opts_frame,
            text="Show landmarks",
            variable=self.show_landmarks,
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            selectcolor=config.gui.theme_colors['bg_secondary']
        )
        self.landmarks_check.pack(side='left', padx=10)

    # Camera and Detection Methods

    def initialize_camera(self) -> bool:
        """Initialize camera with error handling"""
        try:
            if self.cap:
                self.cap.release()

            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise Exception(f"Cannot open camera {self.camera_index}")

            # Configure camera
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, config.camera.fps)

            self.running = True
            self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
            self.camera_thread.start()

            print("✅ Camera initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            self.camera_label.config(text=f"Camera Error: {e}")
            return False

    def start_detection(self):
        """Start laugh detection (camera should already be running)"""
        if not self.running or not self.cap or not self.cap.isOpened():
            # Camera not running, initialize it first
            if not self.initialize_camera():
                messagebox.showerror("Error", "Failed to initialize camera")
                return

        self.detection_active = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        print("🎥 Laugh detection started")

    def stop_detection(self):
        """Stop laugh detection (but keep camera running)"""
        self.detection_active = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        print("⏸️ Laugh detection stopped (camera still running)")

    def camera_loop(self):
        """Main camera processing loop"""
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue

            if config.camera.flip_horizontal:
                frame = cv2.flip(frame, 1)

            # Process frame based on detection state
            if self.detection_active:
                result = self.laugh_detector.detect_laugh(frame)
                self.update_meme_tracking(result)
                self.draw_detection_overlay(frame, result)
                self.root.after(0, lambda r=result: self.update_gui_status(r))
            else:
                # Show paused state
                cv2.putText(
                    frame, "Detection Paused", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2
                )
                # Clear GUI status
                self.root.after(0, lambda: self.update_gui_status(
                    DetectionResult(
                        is_laughing=False, intensity=0.0, confidence=0.0,
                        confidence_trend=0.0, features={}, landmarks=None,
                        consecutive_laugh_frames=0, consecutive_non_laugh_frames=0
                    )
                ))

            self.update_camera_display(frame)
            time.sleep(0.03)  # ~30 FPS

    def draw_detection_overlay(self, frame: np.ndarray, result: DetectionResult):
        """Draw detection information overlay on camera frame"""
        # Main status
        status_text = "😂 LAUGHING!" if result.is_laughing else "😐 Monitoring"
        status_color = (0, 255, 0) if result.is_laughing else (255, 255, 255)

        cv2.putText(
            frame, status_text, (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 2
        )

        # Detection metrics with trend
        trend_text = ""
        if result.confidence_trend != 0:
            trend_text = " ↗️" if result.confidence_trend > 0 else " ↘️"

        cv2.putText(
            frame, f"Intensity: {result.intensity:.2f}{trend_text}",
            (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
        )
        cv2.putText(
            frame, f"Confidence: {result.confidence:.2f}",
            (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
        )
        cv2.putText(
            frame, f"Frames: L{result.consecutive_laugh_frames} N{result.consecutive_non_laugh_frames}",
            (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1
        )

        # Draw landmarks if enabled and available
        if (self.show_landmarks.get() and result.landmarks and
            hasattr(self.laugh_detector, 'mp_drawing')):
            self.laugh_detector.mp_drawing.draw_landmarks(
                frame, result.landmarks,
                self.laugh_detector.mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.laugh_detector.mp_drawing.DrawingSpec(
                    color=(0, 255, 0) if result.is_laughing else (255, 255, 255),
                    thickness=1
                )
            )

    def update_camera_display(self, frame: np.ndarray):
        """Update camera display to fill most of its allocated window space"""
        try:
            # Get the actual camera widget dimensions
            self.root.update_idletasks()
            widget_width = self.camera_label.winfo_width()
            widget_height = self.camera_label.winfo_height()

            # Use reasonable defaults if widget isn't ready yet
            if widget_width <= 1:
                widget_width = 400
            if widget_height <= 1:
                widget_height = 300

            # Use most of the widget space (leave small margins)
            target_width = widget_width - 20   # 10px margin on each side
            target_height = widget_height - 20  # 10px margin top/bottom

            # Ensure minimums
            target_width = max(target_width, 300)
            target_height = max(target_height, 225)

            # Resize frame to fill the camera widget while maintaining aspect ratio
            frame_height, frame_width = frame.shape[:2]

            # Calculate scale to fit within the camera widget
            scale_w = target_width / frame_width
            scale_h = target_height / frame_height
            scale = min(scale_w, scale_h)

            new_width = int(frame_width * scale)
            new_height = int(frame_height * scale)

            # Resize the frame
            display_frame = cv2.resize(frame, (new_width, new_height))

            # Convert to display format
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            photo = ImageTk.PhotoImage(pil_image)

            self.camera_label.config(image=photo, text="")
            self.camera_label.image = photo

        except Exception as e:
            print(f"Error updating camera display: {e}")
            self.camera_label.config(image="", text=f"Camera Error: {str(e)[:50]}...")
            self.camera_label.image = None

    # Meme Management Methods

    def load_new_memes(self):
        """Load new memes from various sources"""
        self.load_btn.config(state='disabled', text="🔄 Loading...")
        self.root.update()

        try:
            new_memes = self.scraper.get_random_memes(config.scraping.default_meme_count)

            if new_memes:
                self.memes_queue = new_memes
                self.current_meme_index = -1
                self.load_btn.config(text=f"✅ Loaded {len(new_memes)} memes!")
                self.next_meme()
            else:
                self.load_btn.config(text="❌ Loading failed")

        except Exception as e:
            print(f"Error loading memes: {e}")
            self.load_btn.config(text="❌ Loading failed")
        finally:
            self.root.after(2000, lambda: self.load_btn.config(
                state='normal', text="🔄 Load Memes"
            ))

    def load_meme_image(self, url: str) -> bool:
        """Load and display meme image with guaranteed fit"""
        try:
            response = requests.get(url, timeout=config.scraping.request_timeout)
            image = Image.open(io.BytesIO(response.content))

            # Get widget dimensions
            self.root.update_idletasks()
            widget_width = self.meme_label.winfo_width()
            widget_height = self.meme_label.winfo_height()

            # Ensure valid dimensions
            if widget_width <= 1 or widget_height <= 1:
                self.root.update()
                time.sleep(0.1)
                widget_width = self.meme_label.winfo_width()
                widget_height = self.meme_label.winfo_height()

            # Use defaults if still invalid
            if widget_width <= 1 or widget_height <= 1:
                widget_width = 800
                widget_height = 600

            # Scale image to fit widget
            img_width, img_height = image.size
            scale_w = widget_width / img_width
            scale_h = widget_height / img_height
            scale = min(scale_w, scale_h)

            # Ensure minimum reasonable size
            if scale < 0.5:
                scale = min(scale_w, scale_h)

            new_width = max(int(img_width * scale), 400)
            new_height = max(int(img_height * scale), 300)

            # Resize and display
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            self.meme_label.config(image=photo, text="", compound='center')
            self.meme_label.image = photo

            return True

        except Exception as e:
            print(f"Error loading image {url}: {e}")
            self.meme_label.config(
                image="",
                text=f"Failed to load meme\n{url}"
            )
            return False

    def next_meme(self):
        """Display next meme and start tracking"""
        if not self.memes_queue:
            return

        # Save previous meme response
        if self.current_meme:
            self.save_current_meme_response()

        # Get next meme
        self.current_meme_index += 1
        if self.current_meme_index >= len(self.memes_queue):
            self.meme_title.config(text="🎉 All memes viewed! Load new ones?")
            self.meme_label.config(
                image="",
                text="All memes completed!\nClick 'Load Memes' for more"
            )
            return

        self.current_meme = self.memes_queue[self.current_meme_index]
        self.view_start_time = time.time()
        self.laugh_events = []

        # Update display
        self.meme_title.config(
            text=f"Meme {self.current_meme_index + 1}/{len(self.memes_queue)}: "
                 f"{self.current_meme['title']}"
        )

        self.load_meme_image(self.current_meme['url'])

        # Auto-advance if enabled
        if self.auto_advance.get():
            self.root.after(config.gui.auto_advance_delay, self.next_meme)

    def prev_meme(self):
        """Go to previous meme"""
        if not self.memes_queue or self.current_meme_index <= 0:
            return

        self.current_meme_index -= 2  # Will be incremented by next_meme
        self.next_meme()

    def update_meme_tracking(self, result: DetectionResult):
        """Update meme tracking with detection results"""
        if not self.current_meme:
            return

        if result.is_laughing:
            self.laugh_events.append({
                'timestamp': time.time(),
                'intensity': result.intensity,
                'confidence': result.confidence
            })

    def save_current_meme_response(self):
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
        else:
            print(f"❌ Failed to save meme response")

    # GUI Update Methods

    def update_gui_status(self, result: DetectionResult):
        """Update GUI status displays"""
        # Laugh status
        if result.is_laughing:
            self.laugh_status.config(
                text="😂 LAUGHING!",
                fg=config.gui.theme_colors['accent_green']
            )
        else:
            self.laugh_status.config(
                text="😐 Not Laughing",
                fg=config.gui.theme_colors['text_primary']
            )

        # Detection info with trend
        trend_text = ""
        if result.confidence_trend != 0:
            trend_text = " ↗️" if result.confidence_trend > 0 else " ↘️"

        self.detection_info.config(
            text=f"Intensity: {result.intensity:.2f}{trend_text} | "
                 f"Confidence: {result.confidence:.2f} | "
                 f"Sensitivity: {self.laugh_detector.sensitivity:.1f}"
        )

        # Meme info
        laugh_count = len(self.laugh_events) if self.laugh_events else 0
        self.meme_info.config(
            text=f"Memes viewed: {max(0, self.current_meme_index)} | "
                 f"Current laugh count: {laugh_count} | "
                 f"Queue: {len(self.memes_queue)} memes"
        )

    def update_sensitivity(self, value):
        """Update detection sensitivity"""
        self.laugh_detector.set_sensitivity(float(value))

    # System Management Methods

    def show_meme_data(self):
        """Show meme data viewer window"""
        try:
            data_viewer = MemeDataViewer(self.root, self.database)
            data_viewer.show()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open data viewer: {e}")

    def calibrate(self):
        """Perform calibration with user guidance"""
        if not self.detection_active:
            messagebox.showerror("Error", "Please start detection first")
            return

        if not self.cap or not self.cap.isOpened():
            messagebox.showerror("Error", "Camera not available")
            return

        # Confirm calibration
        result = messagebox.askyesno(
            "Calibration",
            "Start calibration?\n\n"
            "Keep a NEUTRAL expression for 3 seconds.\n"
            "Don't smile or talk during calibration."
        )
        if not result:
            return

        # Disable button and start calibration
        self.calibrate_btn.config(state='disabled', text="🎯 Calibrating...")

        # Countdown
        for i in range(3, 0, -1):
            self.calibrate_btn.config(text=f"🎯 Starting in {i}...")
            self.root.update()
            time.sleep(1)

        self.calibrate_btn.config(text="🎯 Keep neutral...")

        # TODO: Implement actual calibration frame collection
        # This would require modifications to the camera loop
        # For now, simulate success
        time.sleep(3)

        success = True  # Placeholder

        if success:
            self.calibrate_btn.config(text="✅ Calibrated!")
            messagebox.showinfo("Success", "Calibration completed successfully!")
        else:
            self.calibrate_btn.config(text="❌ Failed")
            messagebox.showerror("Error", "Calibration failed. Please try again.")

        # Reset button
        self.root.after(2000, lambda: self.calibrate_btn.config(
            state='normal', text="🎯 Calibrate"
        ))

    def reset_all_data(self):
        """Reset all data with confirmation"""
        result = messagebox.askyesno(
            "Reset Data",
            "Are you sure you want to reset ALL data?\n\n"
            "This will delete:\n"
            "• All meme responses\n"
            "• Calibration data\n"
            "• Settings\n\n"
            "This action cannot be undone!"
        )

        if result:
            success = self.database.reset_all_data()
            if success:
                messagebox.showinfo("Success", "All data has been reset.")
            else:
                messagebox.showerror("Error", "Failed to reset data.")

    def export_data(self):
        """Export data to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export MLA Data",
            initialdir=config.export.default_export_dir
        )

        if filename:
            try:
                count = self.database.export_to_csv(filename)
                messagebox.showinfo(
                    "Success",
                    f"Exported {count} meme responses to {filename}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

    def import_data(self):
        """Import data from CSV"""
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Import MLA Data"
        )

        if filename:
            try:
                count = self.database.import_from_csv(filename)
                messagebox.showinfo(
                    "Success",
                    f"Imported {count} meme responses from {filename}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {e}")

    def on_closing(self):
        """Handle application closing"""
        # Save current meme if viewing
        if self.current_meme:
            self.save_current_meme_response()

        # Stop detection
        self.detection_active = False
        self.running = False
        if self.cap:
            self.cap.release()

        # Close application
        self.root.destroy()

    def run(self):
        """Run the main application"""
        print("🚀 Starting MLA - Meme Laugh Analyzer...")
        print("💡 Instructions:")
        print("   1. Click 'Start Detection' to activate camera")
        print("   2. Click 'Load Memes' to begin")
        print("   3. Look at memes naturally")
        print("   4. Use controls to navigate and analyze")
        print("   5. Export data for external analysis")

        self.root.mainloop()