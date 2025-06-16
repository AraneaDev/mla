"""
Dialogs Module - FIXED
Handles user dialogs and interactions
"""

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import time
import threading
from typing import Optional, Callable, Dict, Any

from config import config


class DialogManager:
    """Manages application dialogs and user interactions"""

    def __init__(self, parent: tk.Tk):
        self.parent = parent

    def show_calibration_dialog(self, calibration_callback: Callable[[], bool]) -> bool:
        """Show calibration dialog and handle the process"""
        result = messagebox.askyesno(
            "Calibration",
            "Start calibration?\n\n"
            "Keep a NEUTRAL expression for 3 seconds.\n"
            "Don't smile or talk during calibration."
        )

        if not result:
            return False

        # Create progress dialog
        progress_dialog = CalibrationProgressDialog(self.parent, calibration_callback)
        return progress_dialog.run()

    def show_reset_confirmation(self) -> bool:
        """Show data reset confirmation dialog"""
        return messagebox.askyesno(
            "Reset Data",
            "Are you sure you want to reset ALL data?\n\n"
            "This will delete:\n"
            "• All meme responses\n"
            "• Calibration data\n"
            "• Settings\n\n"
            "This action cannot be undone!"
        )

    def show_export_dialog(self) -> Optional[str]:
        """Show export file dialog"""
        return filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export MLA Data",
            initialdir=config.export.default_export_dir
        )

    def show_import_dialog(self) -> Optional[str]:
        """Show import file dialog"""
        return filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Import MLA Data"
        )

    def show_success_message(self, title: str, message: str):
        """Show success message"""
        messagebox.showinfo(title, message)

    def show_error_message(self, title: str, message: str):
        """Show error message"""
        messagebox.showerror(title, message)

    def show_warning_message(self, title: str, message: str):
        """Show warning message"""
        messagebox.showwarning(title, message)

    def get_sensitivity_input(self, current_value: float) -> Optional[float]:
        """Get sensitivity input from user"""
        result = simpledialog.askfloat(
            "Set Sensitivity",
            f"Enter sensitivity value ({config.detection.min_sensitivity}-{config.detection.max_sensitivity}):",
            initialvalue=current_value,
            minvalue=config.detection.min_sensitivity,
            maxvalue=config.detection.max_sensitivity
        )
        return result

    def show_about_dialog(self):
        """Show about dialog"""
        about_text = f"""
MLA - Meme Laugh Analyzer v1.0.0

An advanced system for analyzing human responses to memes using
computer vision and machine learning techniques.

Features:
• Real-time laugh detection using MediaPipe
• Multi-source meme scraping
• Comprehensive data analysis and export
• Customizable sensitivity settings

© 2024 MLA Development Team
        """
        messagebox.showinfo("About MLA", about_text.strip())

    def show_help_dialog(self):
        """Show help dialog"""
        help_text = """
Quick Start Guide:

1. 📹 Click 'Start Detection' to activate camera
2. 🔄 Click 'Load Memes' to fetch memes  
3. 😊 Look at memes naturally - reactions are tracked
4. ⬅️➡️ Use navigation to browse memes
5. 📊 Check 'View Data' for analysis
6. 💾 Export data for external analysis

Tips:
• Adjust sensitivity if detection is too sensitive/insensitive
• Use calibration for better accuracy
• Auto-advance automatically shows next meme after 10 seconds
• All data is saved automatically
        """
        messagebox.showinfo("Help - How to Use MLA", help_text.strip())

    def show_camera_error_dialog(self, error_msg: str):
        """Show camera error dialog"""
        messagebox.showerror(
            "Camera Error",
            f"Failed to initialize camera:\n{error_msg}\n\n"
            "Please check:\n"
            "• Camera is connected\n"
            "• No other applications are using the camera\n"
            "• Camera drivers are installed"
        )

    def show_detection_not_active_dialog(self):
        """Show detection not active dialog"""
        messagebox.showerror(
            "Detection Not Active",
            "Please start detection first before calibrating.\n\n"
            "Click 'Start Detection' to activate the camera."
        )

    def show_no_memes_dialog(self):
        """Show no memes available dialog"""
        messagebox.showwarning(
            "No Memes Available",
            "No memes are currently loaded.\n\n"
            "Click 'Load Memes' to fetch memes from online sources."
        )

    def show_export_success_dialog(self, count: int, filename: str):
        """Show export success dialog"""
        messagebox.showinfo(
            "Export Successful",
            f"Successfully exported {count} meme responses to:\n{filename}"
        )

    def show_import_success_dialog(self, count: int, filename: str):
        """Show import success dialog"""
        messagebox.showinfo(
            "Import Successful",
            f"Successfully imported {count} meme responses from:\n{filename}"
        )

    def show_reset_success_dialog(self):
        """Show reset success dialog"""
        messagebox.showinfo("Reset Complete", "All data has been reset successfully.")


class CalibrationProgressDialog:
    """Custom dialog for calibration progress - FIXED"""

    def __init__(self, parent: tk.Tk, calibration_callback: Callable[[], bool]):
        self.parent = parent
        self.calibration_callback = calibration_callback
        self.dialog = None
        self.progress_label = None
        self.result = False
        self.cancelled = False

    def run(self) -> bool:
        """Run the calibration dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Calibration Progress")
        self.dialog.geometry("400x200")
        self.dialog.configure(bg=config.gui.theme_colors['bg_primary'])
        self.dialog.resizable(False, False)

        # Center the dialog
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Create UI
        self._create_ui()

        # Start calibration process in separate thread - FIXED
        self.parent.after(500, self._start_calibration_thread)

        # Wait for dialog to close
        self.dialog.wait_window()

        return self.result

    def _create_ui(self):
        """Create calibration dialog UI"""
        # Main frame
        main_frame = tk.Frame(
            self.dialog,
            bg=config.gui.theme_colors['bg_primary'],
            padx=20,
            pady=20
        )
        main_frame.pack(fill='both', expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="🎯 Calibration in Progress",
            font=('Arial', 16, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_primary']
        )
        title_label.pack(pady=(0, 20))

        # Instructions
        instructions = tk.Label(
            main_frame,
            text="Keep a NEUTRAL expression\nDon't smile or talk",
            font=('Arial', 12),
            fg=config.gui.theme_colors['text_secondary'],
            bg=config.gui.theme_colors['bg_primary'],
            justify='center'
        )
        instructions.pack(pady=(0, 20))

        # Progress label
        self.progress_label = tk.Label(
            main_frame,
            text="Preparing...",
            font=('Arial', 14, 'bold'),
            fg=config.gui.theme_colors['accent_blue'],
            bg=config.gui.theme_colors['bg_primary']
        )
        self.progress_label.pack(pady=10)

        # Cancel button
        cancel_btn = tk.Button(
            main_frame,
            text="Cancel",
            command=self._cancel,
            font=('Arial', 10),
            bg=config.gui.theme_colors['accent_red'],
            fg='white',
            width=10
        )
        cancel_btn.pack(pady=10)

    def _start_calibration_thread(self):
        """Start calibration in separate thread - FIXED"""
        def calibration_thread():
            try:
                self._run_calibration()
            except Exception as e:
                print(f"Calibration thread error: {e}")
                self.parent.after(0, lambda: self._show_error(str(e)))

        thread = threading.Thread(target=calibration_thread, daemon=True)
        thread.start()

    def _run_calibration(self):
        """Run the calibration process with countdown - FIXED"""
        if self.cancelled:
            return

        # Countdown
        for i in range(3, 0, -1):
            if self.cancelled:
                return
            self.parent.after(0, lambda count=i: self._update_progress(f"Starting in {count}..."))
            time.sleep(1)

        if self.cancelled:
            return

        self.parent.after(0, lambda: self._update_progress("🎯 Keep neutral expression..."))

        # Run actual calibration
        try:
            self.result = self.calibration_callback()

            if self.cancelled:
                return

            if self.result:
                self.parent.after(0, lambda: self._update_progress(
                    "✅ Calibration Complete!",
                    config.gui.theme_colors['accent_green']
                ))
            else:
                self.parent.after(0, lambda: self._update_progress(
                    "❌ Calibration Failed",
                    config.gui.theme_colors['accent_red']
                ))

            time.sleep(2)

        except Exception as e:
            if self.cancelled:
                return
            self.parent.after(0, lambda: self._update_progress(
                f"❌ Error: {str(e)[:30]}...",
                config.gui.theme_colors['accent_red']
            ))
            time.sleep(2)

        finally:
            if not self.cancelled:
                self.parent.after(0, self._close_dialog)

    def _update_progress(self, text: str, color: str = None):
        """Update progress text - FIXED"""
        if self.progress_label and not self.cancelled:
            self.progress_label.config(text=text)
            if color:
                self.progress_label.config(fg=color)

    def _show_error(self, error_msg: str):
        """Show error message - FIXED"""
        if not self.cancelled:
            self._update_progress(f"❌ Error: {error_msg[:30]}...",
                                config.gui.theme_colors['accent_red'])
            self.parent.after(2000, self._close_dialog)

    def _close_dialog(self):
        """Close dialog safely - FIXED"""
        if self.dialog:
            try:
                self.dialog.destroy()
            except tk.TclError:
                pass  # Dialog already destroyed

    def _cancel(self):
        """Cancel calibration - FIXED"""
        self.cancelled = True
        self.result = False
        self._close_dialog()


class SettingsDialog:
    """Settings configuration dialog - FIXED"""

    def __init__(self, parent: tk.Tk, current_settings: Dict[str, Any]):
        self.parent = parent
        self.current_settings = current_settings.copy()
        self.dialog = None
        self.widgets = {}
        self.result = None

    def show(self) -> Optional[Dict[str, Any]]:
        """Show settings dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("MLA Settings")
        self.dialog.geometry("500x400")
        self.dialog.configure(bg=config.gui.theme_colors['bg_primary'])
        self.dialog.resizable(False, False)

        # Center and make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        self._create_ui()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")

        self.dialog.wait_window()

        return self.result

    def _create_ui(self):
        """Create settings dialog UI"""
        # Main frame with scrollable content
        main_frame = tk.Frame(
            self.dialog,
            bg=config.gui.theme_colors['bg_primary'],
            padx=20,
            pady=20
        )
        main_frame.pack(fill='both', expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="⚙️ MLA Settings",
            font=('Arial', 16, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_primary']
        )
        title_label.pack(pady=(0, 20))

        # Settings sections
        self._create_detection_settings(main_frame)
        self._create_display_settings(main_frame)
        self._create_data_settings(main_frame)

        # Buttons
        self._create_buttons(main_frame)

    def _create_detection_settings(self, parent):
        """Create detection settings section"""
        detection_frame = tk.LabelFrame(
            parent,
            text="Detection Settings",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        )
        detection_frame.pack(fill='x', pady=(0, 10))

        # Sensitivity setting
        sens_frame = tk.Frame(detection_frame, bg=config.gui.theme_colors['bg_secondary'])
        sens_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(
            sens_frame,
            text="Default Sensitivity:",
            bg=config.gui.theme_colors['bg_secondary'],
            fg=config.gui.theme_colors['text_primary']
        ).pack(side='left')

        self.widgets['sensitivity'] = tk.Scale(
            sens_frame,
            from_=config.detection.min_sensitivity,
            to=config.detection.max_sensitivity,
            resolution=config.detection.sensitivity_step,
            orient='horizontal',
            bg=config.gui.theme_colors['bg_secondary'],
            fg=config.gui.theme_colors['text_primary']
        )
        self.widgets['sensitivity'].set(self.current_settings.get('sensitivity', 1.3))
        self.widgets['sensitivity'].pack(side='right')

    def _create_display_settings(self, parent):
        """Create display settings section"""
        display_frame = tk.LabelFrame(
            parent,
            text="Display Settings",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        )
        display_frame.pack(fill='x', pady=(0, 10))

        # Auto-advance setting
        self.widgets['auto_advance'] = tk.BooleanVar(
            value=self.current_settings.get('auto_advance', False)
        )
        auto_check = tk.Checkbutton(
            display_frame,
            text="Auto-advance memes (10 seconds)",
            variable=self.widgets['auto_advance'],
            bg=config.gui.theme_colors['bg_secondary'],
            fg=config.gui.theme_colors['text_primary'],
            selectcolor=config.gui.theme_colors['bg_secondary']
        )
        auto_check.pack(anchor='w', padx=10, pady=5)

        # Show landmarks setting
        self.widgets['show_landmarks'] = tk.BooleanVar(
            value=self.current_settings.get('show_landmarks', True)
        )
        landmarks_check = tk.Checkbutton(
            display_frame,
            text="Show facial landmarks",
            variable=self.widgets['show_landmarks'],
            bg=config.gui.theme_colors['bg_secondary'],
            fg=config.gui.theme_colors['text_primary'],
            selectcolor=config.gui.theme_colors['bg_secondary']
        )
        landmarks_check.pack(anchor='w', padx=10, pady=5)

    def _create_data_settings(self, parent):
        """Create data settings section"""
        data_frame = tk.LabelFrame(
            parent,
            text="Data Settings",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        )
        data_frame.pack(fill='x', pady=(0, 10))

        # Auto-backup setting
        self.widgets['auto_backup'] = tk.BooleanVar(
            value=self.current_settings.get('auto_backup', True)
        )
        backup_check = tk.Checkbutton(
            data_frame,
            text="Auto-backup database on reset",
            variable=self.widgets['auto_backup'],
            bg=config.gui.theme_colors['bg_secondary'],
            fg=config.gui.theme_colors['text_primary'],
            selectcolor=config.gui.theme_colors['bg_secondary']
        )
        backup_check.pack(anchor='w', padx=10, pady=5)

    def _create_buttons(self, parent):
        """Create dialog buttons"""
        button_frame = tk.Frame(parent, bg=config.gui.theme_colors['bg_primary'])
        button_frame.pack(fill='x', pady=10)

        # OK button
        ok_btn = tk.Button(
            button_frame,
            text="OK",
            command=self._save_settings,
            bg=config.gui.theme_colors['accent_green'],
            fg='white',
            width=10
        )
        ok_btn.pack(side='right', padx=(5, 0))

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            bg=config.gui.theme_colors['accent_red'],
            fg='white',
            width=10
        )
        cancel_btn.pack(side='right')

        # Reset to defaults button
        reset_btn = tk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
            bg=config.gui.theme_colors['accent_orange'],
            fg='white',
            width=15
        )
        reset_btn.pack(side='left')

    def _save_settings(self):
        """Save settings and close dialog"""
        self.result = {
            'sensitivity': self.widgets['sensitivity'].get(),
            'auto_advance': self.widgets['auto_advance'].get(),
            'show_landmarks': self.widgets['show_landmarks'].get(),
            'auto_backup': self.widgets['auto_backup'].get()
        }
        self.dialog.destroy()

    def _cancel(self):
        """Cancel and close dialog"""
        self.result = None
        self.dialog.destroy()

    def _reset_defaults(self):
        """Reset all settings to defaults"""
        self.widgets['sensitivity'].set(config.detection.default_sensitivity)
        self.widgets['auto_advance'].set(False)
        self.widgets['show_landmarks'].set(True)
        self.widgets['auto_backup'].set(True)