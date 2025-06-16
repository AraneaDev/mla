#!/usr/bin/env python3
"""
MLA - Meme Laugh Analyzer
Main entry point for the application

A comprehensive system for analyzing human responses to memes using
computer vision and machine learning techniques.

Usage:
    python mla.py [options]

    Options:
        --sensitivity FLOAT     Detection sensitivity (0.5-3.0, default: 1.3)
        --camera INT           Camera index (default: 0)
        --config PATH          Path to configuration file
        --debug                Enable debug mode
        --version              Show version information
        --help                 Show this help message

Examples:
    python mla.py                           # Run with default settings
    python mla.py --sensitivity 1.5         # Higher sensitivity
    python mla.py --camera 1 --debug        # Use camera 1 with debug info
"""

import sys
import argparse
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from src.gui.main_window import MLAMainWindow
    from config import config
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Version information
__version__ = "1.0.0"
__author__ = "MLA Development Team"
__description__ = "Advanced meme response tracking and analysis system"

def print_version():
    """Print version information"""
    print(f"MLA - Meme Laugh Analyzer v{__version__}")
    print(f"Author: {__author__}")
    print(f"Description: {__description__}")
    print(f"Python: {sys.version}")

def print_system_info():
    """Print system and configuration information"""
    print("🔧 System Information:")
    print(f"   Project Root: {project_root}")
    print(f"   Database Path: {config.database.default_db_path}")
    print(f"   Export Directory: {config.export.default_export_dir}")
    print(f"   Default Sensitivity: {config.detection.default_sensitivity}")
    print(f"   Default Camera: {config.camera.default_camera_index}")

def validate_arguments(args):
    """Validate command line arguments"""
    errors = []

    # Validate sensitivity
    if not (config.detection.min_sensitivity <= args.sensitivity <= config.detection.max_sensitivity):
        errors.append(f"Sensitivity must be between {config.detection.min_sensitivity} and {config.detection.max_sensitivity}")

    # Validate camera index
    if args.camera < 0:
        errors.append("Camera index must be non-negative")

    # Validate config file if provided
    if args.config and not os.path.exists(args.config):
        errors.append(f"Configuration file not found: {args.config}")

    if errors:
        print("❌ Argument validation errors:")
        for error in errors:
            print(f"   • {error}")
        sys.exit(1)

def setup_environment():
    """Setup the application environment"""
    try:
        # Ensure required directories exist
        os.makedirs(config.database.default_db_path.rsplit('/', 1)[0], exist_ok=True)
        os.makedirs(config.export.default_export_dir, exist_ok=True)

        print("✅ Environment setup complete")
        return True

    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="MLA - Meme Laugh Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           Run with default settings
  %(prog)s --sensitivity 1.5         Higher sensitivity detection
  %(prog)s --camera 1 --debug        Use camera 1 with debug output
  %(prog)s --version                 Show version information

For more information, visit: https://github.com/username/mla
        """
    )

    parser.add_argument(
        '--sensitivity',
        type=float,
        default=config.detection.default_sensitivity,
        help=f'Detection sensitivity ({config.detection.min_sensitivity}-{config.detection.max_sensitivity}, default: {config.detection.default_sensitivity})'
    )

    parser.add_argument(
        '--camera',
        type=int,
        default=config.camera.default_camera_index,
        help=f'Camera index (default: {config.camera.default_camera_index})'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose output'
    )

    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version information and exit'
    )

    # Parse arguments
    args = parser.parse_args()

    # Handle version request
    if args.version:
        print_version()
        return 0

    # Print startup information
    print("🚀 Starting MLA - Meme Laugh Analyzer")
    print("=" * 50)

    if args.debug:
        print_version()
        print_system_info()
        print("🐛 Debug mode enabled")

    # Validate arguments
    validate_arguments(args)

    # Setup environment
    if not setup_environment():
        return 1

    try:
        # Load custom configuration if provided
        if args.config:
            print(f"📄 Loading configuration from: {args.config}")
            # TODO: Implement configuration file loading
            # config = MLAConfig.load_from_file(args.config)

        print("🎮 Initializing GUI application...")

        # Create and run the main application
        app = MLAMainWindow(
            camera_index=args.camera,
            sensitivity=args.sensitivity
        )

        # Set debug mode on components if requested
        if args.debug:
            app.laugh_detector.debug = True

        print("✅ MLA initialized successfully!")
        print("\n💡 Quick Start Guide:")
        print("   1. Click '▶️ Start Detection' to activate camera")
        print("   2. Click '🔄 Load Memes' to fetch memes")
        print("   3. Look at memes naturally - your reactions are tracked")
        print("   4. Use navigation controls to browse memes")
        print("   5. Check '📊 View Data' to see your laugh analysis")
        print("   6. Export data anytime for external analysis")
        print("\n🎯 Have fun analyzing your sense of humor!")
        print("=" * 50)

        # Run the application
        app.run()

        print("\n👋 Thank you for using MLA!")
        return 0

    except KeyboardInterrupt:
        print("\n⏹️ Application interrupted by user")
        return 0

    except Exception as e:
        print(f"\n❌ Application error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())