"""
Image Processing Utilities
Helper functions for image manipulation and processing
"""

import cv2
import numpy as np
from PIL import Image, ImageTk
from typing import Tuple, Optional
import requests
import io


class ImageProcessor:
    """Utility class for image processing operations"""

    def __init__(self):
        self.cache = {}

    def resize_image_to_fit(self, image: Image.Image,
                            target_width: int, target_height: int,
                            maintain_aspect: bool = True) -> Image.Image:
        """Resize image to fit within target dimensions"""
        if not maintain_aspect:
            return image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Calculate aspect ratio preserving resize
        img_width, img_height = image.size

        # Calculate scale factors
        scale_w = target_width / img_width
        scale_h = target_height / img_height

        # Use smaller scale to ensure image fits completely
        scale = min(scale_w, scale_h)

        # Calculate new dimensions
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def load_image_from_url(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """Load image from URL with error handling"""
        try:
            # Check cache first
            if url in self.cache:
                return self.cache[url].copy()

            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            image = Image.open(io.BytesIO(response.content))

            # Cache the image (limit cache size)
            if len(self.cache) < 50:  # Prevent unlimited cache growth
                self.cache[url] = image.copy()

            return image

        except Exception as e:
            print(f"Error loading image from {url}: {e}")
            return None

    def create_placeholder_image(self, width: int, height: int,
                                 text: str = "Image Not Available") -> Image.Image:
        """Create a placeholder image with text"""
        # Create image with light gray background
        image = Image.new('RGB', (width, height), color='lightgray')

        # This is a simple placeholder - in a full implementation,
        # you would add text rendering using PIL.ImageDraw
        return image

    def process_frame_for_display(self, frame: np.ndarray,
                                  target_width: int, target_height: int) -> ImageTk.PhotoImage:
        """Process OpenCV frame for Tkinter display"""
        try:
            # Resize frame to target dimensions while maintaining aspect ratio
            frame_height, frame_width = frame.shape[:2]

            # Calculate scale
            scale_w = target_width / frame_width
            scale_h = target_height / frame_height
            scale = min(scale_w, scale_h)

            # Resize
            new_width = int(frame_width * scale)
            new_height = int(frame_height * scale)
            resized_frame = cv2.resize(frame, (new_width, new_height))

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)

            # Convert to PhotoImage
            return ImageTk.PhotoImage(pil_image)

        except Exception as e:
            print(f"Error processing frame: {e}")
            # Return placeholder
            placeholder = self.create_placeholder_image(target_width, target_height, "Frame Error")
            return ImageTk.PhotoImage(placeholder)

    def validate_image_url(self, url: str) -> bool:
        """Validate if URL points to an image"""
        if not url or not isinstance(url, str):
            return False

        # Check file extension
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        url_lower = url.lower()

        if any(url_lower.endswith(ext) for ext in image_extensions):
            return True

        # Check known image hosting domains
        image_hosts = [
            'i.redd.it', 'i.imgur.com', 'imgur.com',
            'memedroid.com', 'imgflip.com', 'quickmeme.com'
        ]

        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return any(host in parsed.netloc for host in image_hosts)
        except Exception:
            return False

    def clear_cache(self):
        """Clear the image cache"""
        self.cache.clear()
        print("🧹 Image cache cleared")

    def get_cache_info(self) -> dict:
        """Get information about the image cache"""
        return {
            'cached_images': len(self.cache),
            'cache_urls': list(self.cache.keys())
        }