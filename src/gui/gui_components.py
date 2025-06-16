"""
GUI Components Module
Handles GUI setup and layout creation with ALL buttons and controls
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Optional

from config import config


class GUIComponentManager:
    """Manages GUI component creation and layout"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.widgets = {}

        # Configure root window
        self.root.title(config.gui.window_title)
        self.root.geometry(config.gui.window_size)
        self.root.configure(bg=config.gui.theme_colors['bg_primary'])
        self.root.minsize(1200, 800)

    def setup_main_layout(self) -> Dict[str, tk.Widget]:
        """Setup the main application layout with ALL components"""
        # Configure main window grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Main container
        main_frame = tk.Frame(self.root, bg=config.gui.theme_colors['bg_primary'])
        main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # Configure layout
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Create sections
        self.widgets.update({
            'main_frame': main_frame,
            'title_label': self._create_title(main_frame),
            'display_container': self._create_display_section(main_frame),
            'control_container': self._create_control_section(main_frame)
        })

        return self.widgets

    def _create_title(self, parent):
        """Create title label"""
        title_label = tk.Label(
            parent,
            text=config.gui.window_title,
            font=('Arial', 20, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_primary']
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky='ew')
        return title_label

    def _create_display_section(self, parent):
        """Create display section for camera and memes"""
        display_container = tk.Frame(parent, bg=config.gui.theme_colors['bg_primary'])
        display_container.grid(row=1, column=0, sticky='nsew', pady=(0, 10))

        # Camera frame (left side)
        camera_frame = tk.LabelFrame(
            display_container,
            text="📹 Camera Feed",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            bd=2
        )
        camera_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        camera_label = tk.Label(
            camera_frame,
            text="Camera stopped",
            bg='black',
            fg='white'
        )
        camera_label.pack(fill='both', expand=True, padx=5, pady=5)

        # Meme frame (right side)
        meme_frame = tk.LabelFrame(
            display_container,
            text="🎭 Current Meme",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            bd=2
        )
        meme_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Configure meme frame grid
        meme_frame.grid_rowconfigure(1, weight=1)
        meme_frame.grid_columnconfigure(0, weight=1)

        # Meme title
        meme_title = tk.Label(
            meme_frame,
            text="No meme loaded",
            font=('Arial', 12, 'bold'),
            bg=config.gui.theme_colors['bg_secondary'],
            fg=config.gui.theme_colors['text_primary'],
            wraplength=800
        )
        meme_title.grid(row=0, column=0, pady=5, sticky='ew')

        # Meme image container
        meme_label = tk.Label(
            meme_frame,
            text="Click 'Load Memes' to start",
            bg=config.gui.theme_colors['bg_tertiary'],
            compound='center'
        )
        meme_label.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

        # Store widgets
        self.widgets.update({
            'camera_label': camera_label,
            'meme_title': meme_title,
            'meme_label': meme_label
        })

        return display_container

    def _create_control_section(self, parent):
        """Create control section with ALL controls"""
        control_container = tk.Frame(parent, bg=config.gui.theme_colors['bg_primary'])
        control_container.grid(row=2, column=0, sticky='ew')

        # Configure grid
        control_container.grid_rowconfigure(0, weight=0)  # Status frame
        control_container.grid_rowconfigure(1, weight=0)  # Controls frame
        control_container.grid_columnconfigure(0, weight=1)

        # Status frame
        status_frame = self._create_status_frame(control_container)

        # Controls frame with ALL buttons
        controls_frame = self._create_controls_frame(control_container)

        self.widgets.update({
            'status_frame': status_frame,
            'controls_frame': controls_frame
        })

        return control_container

    def _create_status_frame(self, parent):
        """Create status display frame"""
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

        # Status labels
        laugh_status = tk.Label(
            status_inner,
            text="😐 Not Laughing",
            font=('Arial', 16, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        )
        laugh_status.pack()

        detection_info = tk.Label(
            status_inner,
            text="Intensity: 0.00 | Confidence: 0.00 | Sensitivity: 1.3",
            font=('Arial', 12),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        )
        detection_info.pack()

        meme_info = tk.Label(
            status_inner,
            text="Memes viewed: 0 | Current laugh count: 0",
            font=('Arial', 12),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        )
        meme_info.pack()

        # Store widgets
        self.widgets.update({
            'laugh_status': laugh_status,
            'detection_info': detection_info,
            'meme_info': meme_info
        })

        return status_frame

    def _create_controls_frame(self, parent):
        """Create control buttons frame with ALL functionality"""
        controls_frame = tk.LabelFrame(
            parent,
            text="🎮 Controls",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            bd=2
        )
        controls_frame.grid(row=1, column=0, sticky='ew')

        # Create all control sections
        self._create_detection_controls(controls_frame)
        self._create_system_controls(controls_frame)
        self._create_options_controls(controls_frame)

        return controls_frame

    def _create_detection_controls(self, parent):
        """Create detection and navigation controls"""
        btn_frame1 = tk.Frame(parent, bg=config.gui.theme_colors['bg_secondary'])
        btn_frame1.pack(pady=5)

        # Detection controls
        start_btn = self.create_button(
            btn_frame1,
            text="▶️ Start Detection",
            bg_color=config.gui.theme_colors['accent_green'],
            width=15
        )
        start_btn.pack(side='left', padx=2)

        stop_btn = self.create_button(
            btn_frame1,
            text="⏸️ Stop Detection",
            bg_color=config.gui.theme_colors['accent_red'],
            width=15,
            state='disabled'
        )
        stop_btn.pack(side='left', padx=2)

        # Meme controls
        load_btn = self.create_button(
            btn_frame1,
            text="🔄 Load Memes",
            bg_color=config.gui.theme_colors['accent_blue'],
            width=12
        )
        load_btn.pack(side='left', padx=2)

        prev_btn = self.create_button(
            btn_frame1,
            text="⬅️ Previous",
            bg_color=config.gui.theme_colors['accent_orange'],
            width=10
        )
        prev_btn.pack(side='left', padx=2)

        next_btn = self.create_button(
            btn_frame1,
            text="➡️ Next",
            bg_color=config.gui.theme_colors['accent_green'],
            width=10
        )
        next_btn.pack(side='left', padx=2)

        # Store button references
        self.widgets.update({
            'start_btn': start_btn,
            'stop_btn': stop_btn,
            'load_btn': load_btn,
            'prev_btn': prev_btn,
            'next_btn': next_btn
        })

    def _create_system_controls(self, parent):
        """Create system management controls"""
        btn_frame2 = tk.Frame(parent, bg=config.gui.theme_colors['bg_secondary'])
        btn_frame2.pack(pady=5)

        # Data and analysis buttons
        data_btn = self.create_button(
            btn_frame2,
            text="📊 View Data",
            bg_color=config.gui.theme_colors['accent_purple'],
            width=12
        )
        data_btn.pack(side='left', padx=2)

        calibrate_btn = self.create_button(
            btn_frame2,
            text="🎯 Calibrate",
            bg_color=config.gui.theme_colors['accent_purple'],
            width=12
        )
        calibrate_btn.pack(side='left', padx=2)

        reset_btn = self.create_button(
            btn_frame2,
            text="🗑️ Reset Data",
            bg_color=config.gui.theme_colors['accent_orange'],
            width=12
        )
        reset_btn.pack(side='left', padx=2)

        # Import/Export buttons
        export_btn = self.create_button(
            btn_frame2,
            text="💾 Export",
            bg_color='#1abc9c',
            width=10
        )
        export_btn.pack(side='left', padx=2)

        import_btn = self.create_button(
            btn_frame2,
            text="📁 Import",
            bg_color='#95a5a6',
            width=10
        )
        import_btn.pack(side='left', padx=2)

        # Store button references
        self.widgets.update({
            'data_btn': data_btn,
            'calibrate_btn': calibrate_btn,
            'reset_btn': reset_btn,
            'export_btn': export_btn,
            'import_btn': import_btn
        })

    def _create_options_controls(self, parent):
        """Create options and settings controls"""
        opts_frame = tk.Frame(parent, bg=config.gui.theme_colors['bg_secondary'])
        opts_frame.pack(pady=5)

        # Sensitivity control
        sensitivity_frame = tk.Frame(opts_frame, bg=config.gui.theme_colors['bg_secondary'])
        sensitivity_frame.pack(side='left', padx=5)

        tk.Label(
            sensitivity_frame,
            text="Sensitivity:",
            font=('Arial', 10),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        ).pack(side='left', padx=(0, 5))

        sens_var = tk.DoubleVar(value=config.detection.default_sensitivity)
        sens_scale = tk.Scale(
            sensitivity_frame,
            from_=config.detection.min_sensitivity,
            to=config.detection.max_sensitivity,
            resolution=config.detection.sensitivity_step,
            orient='horizontal',
            variable=sens_var,
            bg=config.gui.theme_colors['bg_secondary'],
            fg=config.gui.theme_colors['text_primary'],
            highlightthickness=0,
            width=15,
            length=120
        )
        sens_scale.pack(side='left')

        # Checkboxes frame
        checkbox_frame = tk.Frame(opts_frame, bg=config.gui.theme_colors['bg_secondary'])
        checkbox_frame.pack(side='left', padx=20)

        # Auto-advance option
        auto_advance = tk.BooleanVar(value=False)
        auto_check = tk.Checkbutton(
            checkbox_frame,
            text="Auto-advance (10s)",
            variable=auto_advance,
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            selectcolor=config.gui.theme_colors['bg_secondary']
        )
        auto_check.pack(side='left', padx=10)

        # Show landmarks option
        show_landmarks = tk.BooleanVar(value=True)
        landmarks_check = tk.Checkbutton(
            checkbox_frame,
            text="Show landmarks",
            variable=show_landmarks,
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            selectcolor=config.gui.theme_colors['bg_secondary']
        )
        landmarks_check.pack(side='left', padx=10)

        # Store widget references
        self.widgets.update({
            'sens_var': sens_var,
            'sens_scale': sens_scale,
            'auto_advance': auto_advance,
            'auto_check': auto_check,
            'show_landmarks': show_landmarks,
            'landmarks_check': landmarks_check
        })

    def create_button(self, parent, text, bg_color, **kwargs):
        """Helper method to create consistent buttons"""
        button = tk.Button(
            parent,
            text=text,
            bg=bg_color,
            fg='white',
            font=('Arial', 10),
            **kwargs
        )
        return button

    def set_button_command(self, button_name: str, command: Callable):
        """Set command for a button by name"""
        if button_name in self.widgets:
            self.widgets[button_name].config(command=command)

    def set_scale_command(self, scale_name: str, command: Callable):
        """Set command for a scale by name"""
        if scale_name in self.widgets:
            self.widgets[scale_name].config(command=command)

    def set_checkbox_command(self, checkbox_name: str, command: Callable):
        """Set command for a checkbox by name"""
        if checkbox_name in self.widgets:
            self.widgets[checkbox_name].config(command=command)

    def enable_button(self, button_name: str):
        """Enable a button"""
        if button_name in self.widgets:
            self.widgets[button_name].config(state='normal')

    def disable_button(self, button_name: str):
        """Disable a button"""
        if button_name in self.widgets:
            self.widgets[button_name].config(state='disabled')

    def set_button_text(self, button_name: str, text: str):
        """Set button text"""
        if button_name in self.widgets:
            self.widgets[button_name].config(text=text)

    def get_variable_value(self, var_name: str):
        """Get value of a tkinter variable"""
        if var_name in self.widgets:
            return self.widgets[var_name].get()
        return None

    def set_variable_value(self, var_name: str, value):
        """Set value of a tkinter variable"""
        if var_name in self.widgets:
            self.widgets[var_name].set(value)

    def reset_button_text_after_delay(self, button_name: str, original_text: str, delay: int = 2000):
        """Reset button text after a delay"""
        if button_name in self.widgets:
            self.root.after(delay, lambda: self.set_button_text(button_name, original_text))