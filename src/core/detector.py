"""
Laugh Detection Module
Advanced facial expression analysis and laugh detection using MediaPipe
"""

import cv2
import mediapipe as mp
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from config import config


@dataclass
class DetectionResult:
    """Results from laugh detection"""
    is_laughing: bool
    intensity: float
    confidence: float
    confidence_trend: float
    features: Dict[str, float]
    landmarks: Optional[Any]
    consecutive_laugh_frames: int
    consecutive_non_laugh_frames: int


class LaughDetector:
    """Advanced laugh detection using MediaPipe facial landmarks"""

    def __init__(self, sensitivity: float = None, debug: bool = False):
        # Initialize MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Configuration
        self.sensitivity = sensitivity or config.detection.default_sensitivity
        self.debug = debug

        # Facial landmark indices for MediaPipe face mesh
        self.MOUTH_LANDMARKS = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
        self.EYE_LANDMARKS = {
            'left': [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
            'right': [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        }

        # State tracking for confidence building
        self.baseline_landmarks = None
        self.laugh_history = []
        self.confidence_history = []
        self.is_laughing = False
        self.consecutive_laugh_frames = 0
        self.consecutive_non_laugh_frames = 0

        # Calibration data
        self.calibration_timestamp = None

        print(f"🤖 LaughDetector initialized (sensitivity: {self.sensitivity})")

    def calculate_mouth_openness(self, landmarks: np.ndarray) -> float:
        """Calculate mouth openness ratio"""
        if landmarks is None or len(landmarks) == 0 or len(landmarks) <= max(self.MOUTH_LANDMARKS):
            return 0.0

        try:
            mouth_points = [landmarks[i] for i in self.MOUTH_LANDMARKS if i < len(landmarks)]
            if len(mouth_points) < len(self.MOUTH_LANDMARKS):
                return 0.0

            # Calculate vertical mouth opening
            top_lip = np.mean([mouth_points[i] for i in [1, 2, 3]], axis=0)
            bottom_lip = np.mean([mouth_points[i] for i in [7, 8, 9]], axis=0)
            vertical_distance = np.linalg.norm(top_lip - bottom_lip)

            # Calculate mouth width for normalization
            left_corner = mouth_points[0]
            right_corner = mouth_points[6]
            mouth_width = np.linalg.norm(left_corner - right_corner)

            return vertical_distance / mouth_width if mouth_width > 0 else 0.0
        except (IndexError, ValueError) as e:
            if self.debug:
                print(f"Error in mouth openness calculation: {e}")
            return 0.0

    def calculate_eye_crinkle(self, landmarks: np.ndarray) -> float:
        """Calculate eye crinkle intensity (Duchenne marker)"""
        if landmarks is None or len(landmarks) == 0:
            return 0.0

        try:
            max_landmark_idx = max(max(self.EYE_LANDMARKS['left']), max(self.EYE_LANDMARKS['right']))
            if len(landmarks) <= max_landmark_idx:
                return 0.0

            left_eye_points = [landmarks[i] for i in self.EYE_LANDMARKS['left'] if i < len(landmarks)]
            right_eye_points = [landmarks[i] for i in self.EYE_LANDMARKS['right'] if i < len(landmarks)]

            if (len(left_eye_points) < len(self.EYE_LANDMARKS['left']) or
                    len(right_eye_points) < len(self.EYE_LANDMARKS['right'])):
                return 0.0

            def eye_openness(eye_points):
                top = np.mean(eye_points[1:4], axis=0)
                bottom = np.mean(eye_points[5:8], axis=0)
                height = np.linalg.norm(top - bottom)

                left = eye_points[0]
                right = eye_points[4]
                width = np.linalg.norm(left - right)

                return height / width if width > 0 else 0.0

            left_openness = eye_openness(left_eye_points)
            right_openness = eye_openness(right_eye_points)

            return (left_openness + right_openness) / 2
        except (IndexError, ValueError) as e:
            if self.debug:
                print(f"Error in eye crinkle calculation: {e}")
            return 0.0

    def calculate_cheek_movement(self, landmarks: np.ndarray) -> float:
        """Calculate cheek raising (smile/laugh indicator)"""
        if landmarks is None or len(landmarks) == 0 or len(landmarks) <= 345:
            return 0.0

        try:
            left_cheek = landmarks[116]
            right_cheek = landmarks[345]
            nose_tip = landmarks[1]

            left_elevation = nose_tip[1] - left_cheek[1]
            right_elevation = nose_tip[1] - right_cheek[1]

            return (left_elevation + right_elevation) / 2
        except (IndexError, ValueError) as e:
            if self.debug:
                print(f"Error in cheek movement calculation: {e}")
            return 0.0

    def analyze_facial_expression(self, landmarks) -> Dict[str, float]:
        """Comprehensive facial expression analysis"""
        if landmarks is None:
            return {
                'mouth_openness': 0.0, 'eye_crinkle': 0.0, 'cheek_movement': 0.0,
                'laugh_score': 0.0, 'confidence': 0.0
            }

        try:
            # Convert MediaPipe landmarks to numpy array
            landmarks_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])

            # Calculate individual features
            mouth_openness = self.calculate_mouth_openness(landmarks_array)
            eye_crinkle = self.calculate_eye_crinkle(landmarks_array)
            cheek_movement = self.calculate_cheek_movement(landmarks_array)

            # Advanced laugh scoring using configured weights
            laugh_score = (
                                  mouth_openness * config.detection.mouth_weight +
                                  (
                                              1.0 - eye_crinkle) * config.detection.eye_weight +  # Less eye opening = more squinting
                                  cheek_movement * config.detection.cheek_weight
                          ) * self.sensitivity

            # Calculate confidence based on feature consistency
            feature_values = [mouth_openness, (1.0 - eye_crinkle), cheek_movement]
            confidence = 1.0 - np.std(feature_values)  # Higher confidence when features align

            return {
                'mouth_openness': mouth_openness,
                'eye_crinkle': eye_crinkle,
                'cheek_movement': cheek_movement,
                'laugh_score': min(laugh_score, 1.0),
                'confidence': max(min(confidence, 1.0), 0.0)
            }
        except Exception as e:
            if self.debug:
                print(f"Error in facial expression analysis: {e}")
            return {
                'mouth_openness': 0.0, 'eye_crinkle': 0.0, 'cheek_movement': 0.0,
                'laugh_score': 0.0, 'confidence': 0.0
            }

    def detect_laugh(self, frame: np.ndarray) -> DetectionResult:
        """Main laugh detection function with confidence building over time"""
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        # Initialize result
        detection_result = DetectionResult(
            is_laughing=False,
            intensity=0.0,
            confidence=0.0,
            confidence_trend=0.0,
            features={},
            landmarks=None,
            consecutive_laugh_frames=self.consecutive_laugh_frames,
            consecutive_non_laugh_frames=self.consecutive_non_laugh_frames
        )

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]

            # Analyze facial expression
            features = self.analyze_facial_expression(face_landmarks)

            # Update detection result
            detection_result.features = features
            detection_result.landmarks = face_landmarks
            detection_result.intensity = features['laugh_score']
            detection_result.confidence = features['confidence']

            # Enhanced detection with confidence building
            raw_laugh_score = features['laugh_score']

            # Update histories for temporal analysis
            self.laugh_history.append(raw_laugh_score)
            self.confidence_history.append(features['confidence'])

            # Maintain history size
            if len(self.laugh_history) > config.detection.history_size:
                self.laugh_history.pop(0)
                self.confidence_history.pop(0)

            # Calculate temporal features for confidence building
            if len(self.laugh_history) >= 5:
                recent_trend = (
                        np.mean(self.laugh_history[-5:]) -
                        np.mean(self.laugh_history[-10:-5])
                ) if len(self.laugh_history) >= 10 else 0

                avg_confidence = (
                    np.mean(self.confidence_history[-config.detection.smoothing_window:])
                    if len(self.confidence_history) >= config.detection.smoothing_window
                    else features['confidence']
                )

                smoothed_score = (
                    np.mean(self.laugh_history[-config.detection.smoothing_window:])
                    if len(self.laugh_history) >= config.detection.smoothing_window
                    else raw_laugh_score
                )

                # Dynamic threshold calculation
                base_threshold = config.detection.base_threshold
                confidence_bonus = avg_confidence * 0.2
                trend_bonus = max(recent_trend * 2, 0)

                effective_threshold = base_threshold - confidence_bonus - trend_bonus
                effective_threshold = max(effective_threshold, config.detection.min_threshold)

                # Update consecutive frame counters
                if smoothed_score > effective_threshold:
                    self.consecutive_laugh_frames += 1
                    self.consecutive_non_laugh_frames = 0
                else:
                    self.consecutive_non_laugh_frames += 1
                    self.consecutive_laugh_frames = 0

                # Determine laughing state with hysteresis
                if not self.is_laughing:
                    # Require sustained detection to start laughing
                    detection_result.is_laughing = (
                            self.consecutive_laugh_frames >= config.detection.consecutive_frames_required
                    )
                else:
                    # Require sustained non-detection to stop laughing
                    detection_result.is_laughing = (
                            self.consecutive_non_laugh_frames < config.detection.consecutive_frames_to_stop
                    )

                # Update result with smoothed values
                detection_result.intensity = smoothed_score
                detection_result.confidence = avg_confidence
                detection_result.confidence_trend = recent_trend
            else:
                # Not enough history - be conservative
                detection_result.is_laughing = False

            # Update counters in result
            detection_result.consecutive_laugh_frames = self.consecutive_laugh_frames
            detection_result.consecutive_non_laugh_frames = self.consecutive_non_laugh_frames

            # Track state changes
            self._track_laugh_state_changes(detection_result)
        else:
            # No face detected - reset counters
            self.consecutive_laugh_frames = 0
            self.consecutive_non_laugh_frames = 0

        return detection_result

    def _track_laugh_state_changes(self, detection_result: DetectionResult):
        """Track when laugh states change"""
        if detection_result.is_laughing and not self.is_laughing:
            # Laugh started
            self.is_laughing = True
            if self.debug:
                print(f"😂 LAUGH STARTED! Intensity: {detection_result.intensity:.2f} | "
                      f"Confidence: {detection_result.confidence:.2f} | "
                      f"Consecutive frames: {self.consecutive_laugh_frames}")

        elif not detection_result.is_laughing and self.is_laughing:
            # Laugh ended
            self.is_laughing = False
            if self.debug:
                print(f"😐 Laugh ended. Intensity: {detection_result.intensity:.2f}")

    def calibrate(self, landmarks_list: List[Any]) -> bool:
        """Calibrate baseline from multiple neutral expressions"""
        if not landmarks_list:
            print("❌ No landmarks provided for calibration")
            return False

        print("🎯 Processing calibration data...")

        all_features = []
        for landmarks in landmarks_list:
            if landmarks:
                try:
                    landmarks_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
                    all_features.append(landmarks_array)
                except Exception as e:
                    if self.debug:
                        print(f"Error processing calibration landmark: {e}")
                    continue

        if all_features:
            self.baseline_landmarks = np.mean(all_features, axis=0)
            self.calibration_timestamp = datetime.now()
            print(f"✅ Calibration complete! Processed {len(all_features)} samples")
            return True
        else:
            print("❌ Calibration failed - no valid landmarks processed")
            return False

    def reset_state(self):
        """Reset detection state"""
        self.laugh_history.clear()
        self.confidence_history.clear()
        self.is_laughing = False
        self.consecutive_laugh_frames = 0
        self.consecutive_non_laugh_frames = 0
        print("🔄 Detection state reset")

    def get_state_info(self) -> Dict[str, Any]:
        """Get current detector state information"""
        return {
            'sensitivity': self.sensitivity,
            'is_calibrated': self.baseline_landmarks is not None,
            'calibration_time': self.calibration_timestamp.isoformat() if self.calibration_timestamp else None,
            'history_length': len(self.laugh_history),
            'current_state': 'laughing' if self.is_laughing else 'not_laughing',
            'consecutive_laugh_frames': self.consecutive_laugh_frames,
            'consecutive_non_laugh_frames': self.consecutive_non_laugh_frames
        }

    def set_sensitivity(self, sensitivity: float):
        """Update detection sensitivity"""
        self.sensitivity = max(
            config.detection.min_sensitivity,
            min(sensitivity, config.detection.max_sensitivity)
        )
        if self.debug:
            print(f"🎛️ Sensitivity updated to {self.sensitivity:.1f}")

    def draw_debug_overlay(self, frame: np.ndarray, result: DetectionResult) -> np.ndarray:
        """Draw debug information on frame"""
        if not self.debug or not result.landmarks:
            return frame

        # Draw face mesh
        self.mp_drawing.draw_landmarks(
            frame, result.landmarks,
            self.mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_drawing.DrawingSpec(
                color=(0, 255, 0) if result.is_laughing else (255, 255, 255),
                thickness=1
            )
        )

        # Draw feature information
        y_offset = 30
        for feature, value in result.features.items():
            text = f"{feature}: {value:.3f}"
            cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 255), 2)
            y_offset += 25

        return frame