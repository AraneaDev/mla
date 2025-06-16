"""
Data Viewer Module
Provides detailed views of meme response data
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
from typing import Optional
from datetime import datetime

from config import config
from src.core.database import MLADatabase


class MemeDataViewer:
    """Window for viewing and analyzing meme response data"""

    def __init__(self, parent: tk.Tk, database: MLADatabase):
        self.parent = parent
        self.database = database
        self.window = None

    def show(self):
        """Show the data viewer window"""
        if self.window is not None:
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("MLA - Meme Response Data")
        self.window.geometry("1400x900")
        self.window.configure(bg=config.gui.theme_colors['bg_primary'])
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_data_viewer()

    def setup_data_viewer(self):
        """Setup the data viewer interface"""
        # Main frame
        main_frame = tk.Frame(self.window, bg=config.gui.theme_colors['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Title
        title_label = tk.Label(
            main_frame,
            text="📊 Meme Response Data Analysis",
            font=('Arial', 18, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_primary']
        )
        title_label.pack(pady=(0, 10))

        # Statistics summary
        self.setup_statistics_frame(main_frame)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True, pady=10)

        # Setup tabs
        self.setup_all_memes_tab()
        self.setup_laughed_memes_tab()
        self.setup_sources_tab()

    def setup_statistics_frame(self, parent):
        """Setup statistics summary frame"""
        stats_frame = tk.LabelFrame(
            parent,
            text="📈 Quick Statistics",
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary'],
            bd=2
        )
        stats_frame.pack(fill='x', pady=(0, 10))

        # Get statistics
        stats = self.database.get_statistics()

        # Create statistics display
        stats_inner = tk.Frame(stats_frame, bg=config.gui.theme_colors['bg_secondary'])
        stats_inner.pack(fill='x', padx=10, pady=5)

        # Row 1: Basic counts
        row1 = tk.Frame(stats_inner, bg=config.gui.theme_colors['bg_secondary'])
        row1.pack(fill='x', pady=2)

        self.create_stat_label(row1, "Total Memes:", str(stats['total_memes']))
        self.create_stat_label(row1, "Laughed At:", str(stats['memes_laughed_at']))
        self.create_stat_label(row1, "Laugh Rate:", f"{stats['laugh_rate']:.1f}%")

        # Row 2: Averages
        row2 = tk.Frame(stats_inner, bg=config.gui.theme_colors['bg_secondary'])
        row2.pack(fill='x', pady=2)

        self.create_stat_label(row2, "Avg Intensity:", f"{stats['avg_laugh_intensity']:.2f}")
        self.create_stat_label(row2, "Avg Confidence:", f"{stats['avg_laugh_confidence']:.2f}")
        self.create_stat_label(row2, "Avg Score:", f"{stats['avg_laugh_score']:.1f}")

    def create_stat_label(self, parent, label_text, value_text):
        """Create a statistics label pair"""
        container = tk.Frame(parent, bg=config.gui.theme_colors['bg_secondary'])
        container.pack(side='left', padx=20)

        tk.Label(
            container,
            text=label_text,
            font=('Arial', 10),
            fg=config.gui.theme_colors['text_secondary'],
            bg=config.gui.theme_colors['bg_secondary']
        ).pack()

        tk.Label(
            container,
            text=value_text,
            font=('Arial', 12, 'bold'),
            fg=config.gui.theme_colors['text_primary'],
            bg=config.gui.theme_colors['bg_secondary']
        ).pack()

    def setup_all_memes_tab(self):
        """Setup tab showing all memes"""
        all_frame = tk.Frame(self.notebook, bg=config.gui.theme_colors['bg_tertiary'])
        self.notebook.add(all_frame, text="All Memes")

        self.create_meme_data_display(
            all_frame,
            "All Memes Viewed",
            laughed_only=False
        )

    def setup_laughed_memes_tab(self):
        """Setup tab showing only memes that made user laugh"""
        laugh_frame = tk.Frame(self.notebook, bg=config.gui.theme_colors['bg_tertiary'])
        self.notebook.add(laugh_frame, text="Made Me Laugh")

        self.create_meme_data_display(
            laugh_frame,
            "Memes That Made Me Laugh",
            laughed_only=True
        )

    def setup_sources_tab(self):
        """Setup tab showing source analysis"""
        sources_frame = tk.Frame(self.notebook, bg=config.gui.theme_colors['bg_tertiary'])
        self.notebook.add(sources_frame, text="Source Analysis")

        self.create_source_analysis(sources_frame)

    def create_meme_data_display(self, parent, title, laughed_only=False):
        """Create a meme data display with treeview"""
        # Title
        title_label = tk.Label(
            parent,
            text=title,
            font=('Arial', 16, 'bold'),
            bg=config.gui.theme_colors['bg_tertiary'],
            fg=config.gui.theme_colors['bg_primary']
        )
        title_label.pack(pady=10)

        # Create frame for treeview and scrollbars
        tree_frame = tk.Frame(parent, bg=config.gui.theme_colors['bg_tertiary'])
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Define columns
        columns = (
            'Score', 'Title', 'Source', 'Date', 'Duration',
            'Laughs', 'Intensity', 'Confidence', 'URL'
        )

        # Create treeview
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=20
        )

        # Configure column headings and widths
        column_config = {
            'Score': 70,
            'Title': 350,
            'Source': 120,
            'Date': 100,
            'Duration': 80,
            'Laughs': 60,
            'Intensity': 80,
            'Confidence': 80,
            'URL': 250
        }

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_config.get(col, 100), minwidth=50)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Load data
        responses = self.database.get_meme_responses(laughed_only=laughed_only)

        for response in responses:
            (meme_id, meme_url, meme_title, meme_source, timestamp,
             laugh_detected, laugh_intensity, laugh_confidence, laugh_count,
             laugh_score, viewed_duration, meme_tags) = response

            # Format data for display
            date_str = timestamp[:10] if timestamp else "N/A"
            duration_str = f"{viewed_duration:.1f}s" if viewed_duration else "N/A"
            score_str = f"{laugh_score:.0f}" if laugh_score else "0"
            intensity_str = f"{laugh_intensity:.2f}" if laugh_intensity else "0.00"
            confidence_str = f"{laugh_confidence:.2f}" if laugh_confidence else "0.00"

            # Insert data
            item = tree.insert('', 'end', values=(
                score_str, meme_title[:50] + "..." if len(meme_title) > 50 else meme_title,
                meme_source, date_str, duration_str, laugh_count,
                intensity_str, confidence_str, meme_url
            ))

            # Color code by laugh score
            if laugh_score >= 80:
                tree.item(item, tags=('high_score',))
            elif laugh_score >= 60:
                tree.item(item, tags=('medium_score',))
            elif laugh_score >= 40:
                tree.item(item, tags=('low_score',))

        # Configure tags for color coding
        tree.tag_configure('high_score', background='#d5f4e6')  # Light green
        tree.tag_configure('medium_score', background='#fff3cd')  # Light yellow
        tree.tag_configure('low_score', background='#f8d7da')  # Light red

        # Bind double-click to open URL
        def on_double_click(event):
            item = tree.selection()[0]
            url = tree.item(item, "values")[8]  # URL is the 9th column
            webbrowser.open(url)

        tree.bind('<Double-1>', on_double_click)

        # Add info label
        info_text = f"Total: {len(responses)} memes | Double-click row to open URL in browser"
        if laughed_only:
            info_text += f" | Showing only memes that made you laugh"

        info_label = tk.Label(
            parent,
            text=info_text,
            font=('Arial', 10),
            bg=config.gui.theme_colors['bg_tertiary'],
            fg=config.gui.theme_colors['text_secondary']
        )
        info_label.pack(pady=5)

    def create_source_analysis(self, parent):
        """Create source analysis display"""
        # Title
        title_label = tk.Label(
            parent,
            text="Source Performance Analysis",
            font=('Arial', 16, 'bold'),
            bg=config.gui.theme_colors['bg_tertiary'],
            fg=config.gui.theme_colors['bg_primary']
        )
        title_label.pack(pady=10)

        # Get statistics
        stats = self.database.get_statistics()
        sources_data = stats.get('sources', [])

        if not sources_data:
            no_data_label = tk.Label(
                parent,
                text="No source data available yet.\nView some memes first!",
                font=('Arial', 14),
                bg=config.gui.theme_colors['bg_tertiary'],
                fg=config.gui.theme_colors['text_secondary']
            )
            no_data_label.pack(expand=True)
            return

        # Create frame for source analysis
        analysis_frame = tk.Frame(parent, bg=config.gui.theme_colors['bg_tertiary'])
        analysis_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Create treeview for source stats
        columns = ('Source', 'Total Memes', 'Laughs', 'Laugh Rate', 'Performance')

        tree = ttk.Treeview(
            analysis_frame,
            columns=columns,
            show='headings',
            height=15
        )

        # Configure columns
        tree.heading('Source', text='Source')
        tree.heading('Total Memes', text='Total Memes')
        tree.heading('Laughs', text='Laughs')
        tree.heading('Laugh Rate', text='Laugh Rate')
        tree.heading('Performance', text='Performance Rating')

        tree.column('Source', width=150)
        tree.column('Total Memes', width=100)
        tree.column('Laughs', width=80)
        tree.column('Laugh Rate', width=100)
        tree.column('Performance', width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(analysis_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Sort sources by laugh rate
        sources_data.sort(key=lambda x: x['laugh_rate'], reverse=True)

        # Add source data
        for source_info in sources_data:
            source = source_info['source']
            count = source_info['count']
            laughs = source_info['laughs']
            rate = source_info['laugh_rate']

            # Determine performance rating
            if rate >= 40:
                performance = "🔥 Excellent"
                tag = 'excellent'
            elif rate >= 30:
                performance = "👍 Good"
                tag = 'good'
            elif rate >= 20:
                performance = "👌 Average"
                tag = 'average'
            else:
                performance = "👎 Below Average"
                tag = 'below_average'

            item = tree.insert('', 'end', values=(
                source, count, laughs, f"{rate:.1f}%", performance
            ), tags=(tag,))

        # Configure tags
        tree.tag_configure('excellent', background='#d4edda')
        tree.tag_configure('good', background='#d1ecf1')
        tree.tag_configure('average', background='#fff3cd')
        tree.tag_configure('below_average', background='#f8d7da')

        # Add summary
        summary_frame = tk.Frame(parent, bg=config.gui.theme_colors['bg_tertiary'])
        summary_frame.pack(fill='x', padx=20, pady=10)

        if sources_data:
            best_source = sources_data[0]
            total_sources = len(sources_data)

            summary_text = (
                f"📊 Analysis Summary:\n"
                f"• Best performing source: {best_source['source']} "
                f"({best_source['laugh_rate']:.1f}% laugh rate)\n"
                f"• Total sources analyzed: {total_sources}\n"
                f"• Recommendation: Focus on sources with >30% laugh rate for better content"
            )

            summary_label = tk.Label(
                summary_frame,
                text=summary_text,
                font=('Arial', 11),
                bg=config.gui.theme_colors['bg_tertiary'],
                fg=config.gui.theme_colors['bg_primary'],
                justify='left'
            )
            summary_label.pack(anchor='w')

    def on_closing(self):
        """Handle window closing"""
        self.window.destroy()
        self.window = None