# MLA - Meme Laugh Analyzer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-red.svg)](https://mediapipe.dev/)

> **Advanced meme response tracking and analysis system using computer vision and machine learning**

MLA is a comprehensive application that uses real-time facial expression analysis to detect and measure your laughter responses to memes. It combines computer vision, machine learning, and data analytics to provide insights into your sense of humor.

## 🎯 Features

### Core Functionality
- **Real-time Laugh Detection**: Advanced facial landmark analysis using MediaPipe
- **Meme Aggregation**: Automatically scrapes memes from multiple sources (Reddit, Memedroid)
- **Response Tracking**: Records laugh intensity, duration, confidence, and timing
- **Data Analytics**: Comprehensive analysis of your humor patterns
- **Smart Calibration**: Personalizes detection to your facial features

### Technical Highlights
- **Confidence Building**: Requires sustained detection to prevent false positives
- **Temporal Smoothing**: Analyzes trends over time for better accuracy
- **Multi-source Scraping**: Fetches diverse content from various platforms
- **Robust Database**: SQLite-based storage with full import/export capabilities
- **Professional GUI**: Intuitive interface with real-time feedback

### Data & Analytics
- **Laugh Scoring**: 0-100 scoring system based on intensity, confidence, and frequency
- **Source Analysis**: Compare humor preferences across different platforms
- **Export/Import**: CSV format for external analysis and backup
- **Visual Analytics**: Charts and graphs showing laugh patterns over time

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/username/mla.git
   cd mla
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running MLA

**Basic usage:**
```bash
python mla.py
```

**With custom settings:**
```bash
python mla.py --sensitivity 1.5 --camera 1 --debug
```

**Command line options:**
```bash
python mla.py --help
```

### First Time Setup

1. **Start Detection**: Click "▶️ Start Detection" to activate your camera
2. **Calibrate**: Click "🎯 Calibrate" and keep a neutral expression for 3 seconds
3. **Load Memes**: Click "🔄 Load Memes" to fetch fresh content
4. **Analyze**: Browse memes naturally - your reactions are automatically tracked!

## 📊 How It Works

### Detection Pipeline

1. **Face Detection**: MediaPipe identifies facial landmarks (468 points)
2. **Feature Extraction**: Analyzes mouth openness, eye crinkling, cheek movement
3. **Confidence Building**: Requires 3+ consecutive frames to trigger detection
4. **Temporal Analysis**: Tracks trends and patterns over time
5. **Scoring**: Combines multiple metrics into a 0-100 laugh score

### Laugh Detection Algorithm

```python
# Simplified version of the scoring algorithm
laugh_score = (
    mouth_openness * 0.4 +      # Mouth movement (40% weight)
    eye_crinkle * 0.3 +         # Duchenne marker (30% weight)  
    cheek_movement * 0.3        # Smile indication (30% weight)
) * sensitivity_multiplier
```

### Data Collection

MLA tracks comprehensive data for each meme:
- **Temporal**: Timestamp, viewing duration
- **Response**: Laugh detected (yes/no), intensity, confidence
- **Behavioral**: Number of laugh events, peak intensity
- **Content**: Meme URL, title, source, tags
- **Composite**: Calculated laugh score (0-100)

## 🎮 User Interface

### Main Window Components

- **Camera Feed (1/3 screen)**: Live video with detection overlay
- **Meme Display (2/3 screen)**: Current meme with proper scaling
- **Status Panel**: Real-time detection metrics and progress
- **Control Panel**: Navigation, settings, and system management

### Key Controls

| Button | Function |
|--------|----------|
| ▶️ Start Detection | Activate camera and laugh detection |
| ⏸️ Stop Detection | Pause detection to save resources |
| 🔄 Load Memes | Fetch new memes from multiple sources |
| ⬅️ Previous / ➡️ Next | Navigate through meme queue |
| 🎯 Calibrate | Personalize detection to your face |
| 📊 View Data | Open detailed analytics window |
| 💾 Export / 📁 Import | Data management and backup |

### Settings & Options

- **Sensitivity Slider**: Adjust detection threshold (0.5-3.0)
- **Auto-advance**: Automatically move to next meme after 10 seconds
- **Show Landmarks**: Display facial detection points on camera
- **Source Selection**: Choose which platforms to scrape memes from

## 📈 Data Analysis

### Laugh Scoring System

**Score Components:**
- **Intensity Score** (0-50 points): Based on facial expression strength
- **Confidence Score** (0-30 points): Detection algorithm certainty
- **Frequency Score** (0-20 points): Number of laugh events (capped at 5)

**Score Interpretation:**
- **80-100**: Hilarious! This really got you
- **60-79**: Genuinely funny, solid laugh
- **40-59**: Amusing, mild positive response  
- **20-39**: Slight amusement detected
- **0-19**: No significant laugh response

### Analytics Views

1. **All Memes**: Complete viewing history with scores
2. **Made Me Laugh**: Filtered view of positive responses only
3. **Source Analysis**: Performance comparison across platforms
4. **Statistics Dashboard**: Quick overview with key metrics

### Data Export Format

CSV exports include all tracked data:
```csv
meme_id,meme_url,meme_title,meme_source,timestamp,viewed_duration,laugh_detected,laugh_intensity,laugh_confidence,laugh_count,max_intensity,meme_tags,laugh_score
abc123,https://...,Funny Cat,reddit_memes,2024-01-15T10:30:00,5.2,true,0.85,0.92,3,0.91,"[""cats"",""funny""]",87
```

## 🔧 Configuration

### Default Settings

MLA comes with sensible defaults but can be customized:

```python
# config.py - Key settings
DETECTION_SENSITIVITY = 1.3        # Detection threshold multiplier
CAMERA_RESOLUTION = (1280, 720)    # Camera capture resolution  
MEME_BATCH_SIZE = 25               # Number of memes to load
AUTO_ADVANCE_DELAY = 10000         # Milliseconds between memes
```

### Advanced Configuration

For advanced users, modify `config.py` to customize:
- Detection algorithm parameters
- Source scraping configuration  
- GUI themes and layout
- Database and export settings

## 🛠️ Development

### Project Structure

```
mla/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── setup.py                 # Package configuration
├── mla.py                   # Main entry point
├── config.py                # Configuration settings
├── src/
│   ├── core/                # Core functionality
│   │   ├── detector.py      # Laugh detection engine
│   │   ├── database.py      # Data storage and retrieval
│   │   └── scraper.py       # Meme scraping system
│   ├── gui/                 # User interface
│   │   ├── main_window.py   # Main application window
│   │   └── data_viewer.py   # Analytics and data viewer
│   └── utils/               # Utility functions
│       └── image_utils.py   # Image processing helpers
├── data/                    # Database and generated files
├── exports/                 # CSV exports directory
├── tests/                   # Unit tests
└── docs/                    # Additional documentation
```

### Architecture Overview

**Core Components:**
- **LaughDetector**: MediaPipe-based facial analysis engine
- **MemeScraper**: Multi-source web scraping system  
- **MLADatabase**: SQLite-based data management
- **MLAMainWindow**: Tkinter-based GUI application

**Data Flow:**
1. Scraper fetches memes from web sources
2. GUI displays memes to user
3. Camera captures user's facial expressions
4. Detector analyzes expressions for laugh indicators
5. Database stores response data with timestamps
6. Analytics provide insights and visualizations

### Testing

Run the test suite:
```bash
pytest tests/ -v --cov=src
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the existing code style
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📋 Requirements

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **Hardware**: 
  - Webcam (built-in or USB)
  - 4GB+ RAM recommended
  - 1GB+ free disk space
- **Internet**: Required for meme scraping

### Python Dependencies

**Core:**
- `opencv-python` (≥4.8.0) - Computer vision
- `mediapipe` (≥0.10.0) - Facial landmark detection
- `numpy` (≥1.21.0) - Numerical computing
- `pandas` (≥1.3.0) - Data manipulation
- `requests` (≥2.25.0) - HTTP requests
- `beautifulsoup4` (≥4.9.0) - Web scraping
- `pillow` (≥8.0.0) - Image processing

**Visualization:**
- `matplotlib` (≥3.5.0) - Plotting
- `seaborn` (≥0.11.0) - Statistical visualization

See `requirements.txt` for complete list.

## 🚨 Troubleshooting

### Common Issues

**Camera not detected:**
```bash
# Try different camera indices
python mla.py --camera 1
python mla.py --camera 2
```

**Permission denied errors:**
- Ensure camera permissions are granted
- Run as administrator if necessary (Windows)
- Check camera isn't used by another application

**Poor detection accuracy:**
- Run calibration with neutral expression
- Adjust sensitivity slider
- Ensure good lighting conditions
- Position camera at eye level

**Meme loading failures:**
- Check internet connection
- Some sources may be temporarily unavailable
- Try loading memes again after a few minutes

**Performance issues:**
- Close other applications using camera
- Reduce camera resolution in config
- Stop detection when not actively using

### Debug Mode

Enable verbose logging:
```bash
python mla.py --debug
```

This provides detailed information about:
- Camera initialization
- Detection algorithm decisions
- Meme scraping results
- Database operations
- Error stacktraces

## 📚 Additional Resources

### Scientific Background
- [Facial Action Coding System (FACS)](https://en.wikipedia.org/wiki/Facial_Action_Coding_System)
- [Duchenne Markers](https://en.wikipedia.org/wiki/Duchenne_marker) - Genuine smile detection
- [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh.html) - Technical details

### Related Projects
- [OpenCV](https://opencv.org/) - Computer vision library
- [MediaPipe](https://mediapipe.dev/) - ML framework for live perception
- [Emotion Recognition Research](https://github.com/topics/emotion-recognition)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MediaPipe Team** - Excellent facial landmark detection
- **OpenCV Community** - Robust computer vision tools
- **Meme Communities** - Endless source of humor for testing
- **Beta Testers** - Valuable feedback and bug reports

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/username/mla/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/mla/discussions)
- **Email**: support@mla-project.com

---

**Disclaimer**: MLA is designed for entertainment and research purposes. All facial analysis is performed locally on your device - no biometric data is transmitted or stored externally. Please use responsibly and respect others' privacy.

---

Made with ❤️ and 😂 by the MLA Development Team