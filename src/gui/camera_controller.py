"""
Camera Controller Module
Handles camera operations and laugh detection
"""

import cv2
import numpy as np
import time
import threading
from datetime import datetime
from PIL import Image, ImageTk
from typing import Optional, Callable, Any
import tkinter as tk

from config import config
from src.core.detector import LaughDetector, DetectionResult


class CameraController:
    """Handles camera operations and detection processing"""

    def __init__(self, camera_index: int = 0, sensitivity: float = None):
        self.camera_index = camera_index
        self.laugh_detector = LaughDetector(
            sensitivity=sensitivity or config.detection.default_sensitivity
        )

        # Camera state
        self.cap = None
        self.camera_thread = None
        self.running = False
        self.detection_active = False

        # Callbacks for GUI updates
        self.on_detection_update: Optional[Callable[[DetectionResult], None]] = None
        self.on_camera_frame: Optional[Callable[[np.ndarray], None]] = None
        self.show_landmarks = True

        print("📹 CameraController initialized")

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
            self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
            self.camera_thread.start()

            print("✅ Camera initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            return False

    def start_detection(self):
        """Start laugh detection"""
        if not self.running or not self.cap or not self.cap.isOpened():
            if not self.initialize_camera():
                return False

        self.detection_active = True
        print("🎥 Laugh detection started")
        return True

    def stop_detection(self):
        """Stop laugh detection but keep camera running"""
        self.detection_active = False
        print("⏸️ Laugh detection stopped")

    def shutdown(self):
        """Shutdown camera and cleanup"""
        self.detection_active = False
        self.running = False
        if self.cap:
            self.cap.release()
        print("📹 Camera shutdown complete")

    def _camera_loop(self):
        """Main camera processing loop"""
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue

            if config.camera.flip_horizontal:
                frame = cv2.flip(frame, 1)

            if self.detection_active:
                result = self.laugh_detector.detect_laugh(frame)
                self._draw_detection_overlay(frame, result)

                # Notify GUI of detection update
                if self.on_detection_update:
                    self.on_detection_update(result)
            else:
                # Show paused state
                cv2.putText(
                    frame, "Detection Paused", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2
                )
                # Send empty result to clear GUI
                if self.on_detection_update:
                    empty_result = DetectionResult(
                        is_laughing=False, intensity=0.0, confidence=0.0,
                        confidence_trend=0.0, features={}, landmarks=None,
                        consecutive_laugh_frames=0, consecutive_non_laugh_frames=0
                    )
                    self.on_detection_update(empty_result)

            # Notify GUI of new frame
            if self.on_camera_frame:
                self.on_camera_frame(frame)

            time.sleep(0.03)  # ~30 FPS

    def _draw_detection_overlay(self, frame: np.ndarray, result: DetectionResult):
        """Draw detection information overlay on camera frame"""
        # Main status
        status_text = "😂 LAUGHING!" if result.is_laughing else "😐 Monitoring"
        status_color = (0, 255, 0) if result.is_laughing else (255, 255, 255)

        cv2.putText(frame, status_text, (10, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 2)

        # Detection metrics with trend
        trend_text = ""
        if result.confidence_trend != 0:
            trend_text = " ↗️" if result.confidence_trend > 0 else " ↘️"

        cv2.putText(frame, f"Intensity: {result.intensity:.2f}{trend_text}",
                   (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Confidence: {result.confidence:.2f}",
                   (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Frames: L{result.consecutive_laugh_frames} N{result.consecutive_non_laugh_frames}",
                   (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # Draw landmarks if enabled and available
        if (self.show_landmarks and result.landmarks and
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

    def calibrate(self) -> bool:
        """Perform calibration"""
        if not self.detection_active:
            return False

        if not self.cap or not self.cap.isOpened():
            return False

        # Collect calibration frames
        calibration_frames = []
        print("🎯 Collecting calibration data...")

        # Collect frames for 3 seconds
        start_time = time.time()
        while time.time() - start_time < 3.0:
            ret, frame = self.cap.read()
            if ret:
                if config.camera.flip_horizontal:
                    frame = cv2.flip(frame, 1)

                # Process frame to get landmarks
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.laugh_detector.face_mesh.process(rgb_frame)

                if results.multi_face_landmarks:
                    calibration_frames.append(results.multi_face_landmarks[0])

            time.sleep(0.1)

        # Perform calibration
        if calibration_frames:
            success = self.laugh_detector.calibrate(calibration_frames)
            print(f"✅ Calibration {'successful' if success else 'failed'}")
            return success
        else:
            print("❌ No face detected during calibration")
            return False

    def get_detector_state(self) -> dict:
        """Get current detector state"""
        return self.laugh_detector.get_state_info()

    def set_sensitivity(self, sensitivity: float):
        """Update detection sensitivity"""
        self.laugh_detector.set_sensitivity(sensitivity)

    def set_show_landmarks(self, show: bool):
        """Enable/disable landmark display"""
        self.show_landmarks = show

    def reset_detector_state(self):
        """Reset detector state"""
        self.laugh_detector.reset_state()

    def get_camera_info(self) -> dict:
        """Get camera information"""
        info = {
            'camera_index': self.camera_index,
            'is_running': self.running,
            'detection_active': self.detection_active,
            'camera_available': self.cap is not None and self.cap.isOpened()
        }

        if self.cap and self.cap.isOpened():
            info.update({
                'frame_width': self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                'frame_height': self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                'fps': self.cap.get(cv2.CAP_PROP_FPS)
            })

        return info