"""
Database Module
Handles all data storage and retrieval for MLA
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import os
import shutil

from config import config


@dataclass
class MemeResponse:
    """Data class for meme response records"""
    meme_id: str
    meme_url: str
    meme_title: str
    meme_source: str
    timestamp: datetime
    viewed_duration: float
    laugh_detected: bool
    laugh_intensity: float
    laugh_confidence: float
    laugh_count: int
    max_intensity: float
    meme_tags: List[str]
    laugh_score: float = 0.0

    def __post_init__(self):
        """Calculate laugh score if not provided"""
        if self.laugh_score == 0.0 and self.laugh_detected:
            self.laugh_score = self.calculate_laugh_score()

    def calculate_laugh_score(self) -> float:
        """Calculate composite laugh score (0-100)"""
        if not self.laugh_detected:
            return 0.0

        # Weighted scoring algorithm
        intensity_score = self.laugh_intensity * 50  # 0-50 points
        confidence_score = self.laugh_confidence * 30  # 0-30 points
        frequency_score = min(self.laugh_count, 5) * 4  # 0-20 points

        return min(intensity_score + confidence_score + frequency_score, 100.0)


class MLADatabase:
    """Main database class for MLA data management"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.database.default_db_path
        self.ensure_directory_exists()
        self.init_database()
        print(f"📊 Database initialized: {self.db_path}")

    def ensure_directory_exists(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def init_database(self):
        """Initialize database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # Main meme responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meme_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meme_id TEXT NOT NULL,
                meme_url TEXT NOT NULL,
                meme_title TEXT,
                meme_source TEXT,
                timestamp TEXT NOT NULL,
                viewed_duration REAL DEFAULT 0,
                laugh_detected BOOLEAN DEFAULT FALSE,
                laugh_intensity REAL DEFAULT 0,
                laugh_confidence REAL DEFAULT 0,
                laugh_count INTEGER DEFAULT 0,
                max_intensity REAL DEFAULT 0,
                meme_tags TEXT DEFAULT '[]',
                laugh_score REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(meme_id, timestamp)
            )
        """)

        # Calibration data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                baseline_data TEXT,
                sensitivity REAL,
                detector_config TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # System settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sessions table for tracking usage sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                start_time TEXT,
                end_time TEXT,
                memes_viewed INTEGER DEFAULT 0,
                total_laughs INTEGER DEFAULT 0,
                avg_laugh_intensity REAL DEFAULT 0,
                session_notes TEXT
            )
        """)

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meme_responses_timestamp ON meme_responses(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meme_responses_laugh_score ON meme_responses(laugh_score DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meme_responses_source ON meme_responses(meme_source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meme_responses_laugh_detected ON meme_responses(laugh_detected)")

        conn.commit()
        conn.close()

    def save_meme_response(self, response: MemeResponse) -> bool:
        """Save a meme response to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO meme_responses 
                (meme_id, meme_url, meme_title, meme_source, timestamp, viewed_duration,
                 laugh_detected, laugh_intensity, laugh_confidence, laugh_count, 
                 max_intensity, meme_tags, laugh_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                response.meme_id,
                response.meme_url,
                response.meme_title,
                response.meme_source,
                response.timestamp.isoformat(),
                response.viewed_duration,
                response.laugh_detected,
                response.laugh_intensity,
                response.laugh_confidence,
                response.laugh_count,
                response.max_intensity,
                json.dumps(response.meme_tags),
                response.laugh_score
            ))

            conn.commit()
            conn.close()
            return True

        except sqlite3.Error as e:
            print(f"❌ Error saving meme response: {e}")
            return False

    def get_meme_responses(self,
                           limit: Optional[int] = None,
                           laughed_only: bool = False,
                           source_filter: Optional[str] = None,
                           date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None) -> List[Tuple]:
        """Get meme responses with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT meme_id, meme_url, meme_title, meme_source, timestamp, 
                   laugh_detected, laugh_intensity, laugh_confidence, laugh_count,
                   laugh_score, viewed_duration, meme_tags
            FROM meme_responses 
            WHERE 1=1
        """
        params = []

        if laughed_only:
            query += " AND laugh_detected = 1"

        if source_filter:
            query += " AND meme_source = ?"
            params.append(source_filter)

        if date_from:
            query += " AND timestamp >= ?"
            params.append(date_from.isoformat())

        if date_to:
            query += " AND timestamp <= ?"
            params.append(date_to.isoformat())

        query += " ORDER BY laugh_score DESC, timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM meme_responses")
        stats['total_memes'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM meme_responses WHERE laugh_detected = 1")
        stats['memes_laughed_at'] = cursor.fetchone()[0]

        # Laugh rate
        if stats['total_memes'] > 0:
            stats['laugh_rate'] = (stats['memes_laughed_at'] / stats['total_memes']) * 100
        else:
            stats['laugh_rate'] = 0.0

        # Average scores
        cursor.execute(
            "SELECT AVG(laugh_intensity), AVG(laugh_confidence), AVG(laugh_score) FROM meme_responses WHERE laugh_detected = 1")
        avg_result = cursor.fetchone()
        stats['avg_laugh_intensity'] = avg_result[0] or 0.0
        stats['avg_laugh_confidence'] = avg_result[1] or 0.0
        stats['avg_laugh_score'] = avg_result[2] or 0.0

        # Top sources
        cursor.execute("""
            SELECT meme_source, COUNT(*) as count, 
                   SUM(CASE WHEN laugh_detected THEN 1 ELSE 0 END) as laughs
            FROM meme_responses 
            GROUP BY meme_source 
            ORDER BY count DESC
        """)
        stats['sources'] = [
            {'source': row[0], 'count': row[1], 'laughs': row[2],
             'laugh_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0}
            for row in cursor.fetchall()
        ]

        # Recent activity (last 7 days)
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count,
                   SUM(CASE WHEN laugh_detected THEN 1 ELSE 0 END) as laughs
            FROM meme_responses 
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """)
        stats['recent_activity'] = [
            {'date': row[0], 'memes': row[1], 'laughs': row[2]}
            for row in cursor.fetchall()
        ]

        conn.close()
        return stats

    def export_to_csv(self, filename: str, include_tags: bool = True) -> int:
        """Export all meme data to CSV"""
        try:
            conn = sqlite3.connect(self.db_path)

            query = """
                SELECT meme_id, meme_url, meme_title, meme_source, timestamp, 
                       viewed_duration, laugh_detected, laugh_intensity, 
                       laugh_confidence, laugh_count, max_intensity, 
                       meme_tags, laugh_score
                FROM meme_responses 
                ORDER BY laugh_score DESC, timestamp DESC
            """

            df = pd.read_sql_query(query, conn)
            conn.close()

            # Process tags if needed
            if include_tags and not df.empty:
                df['meme_tags'] = df['meme_tags'].apply(
                    lambda x: ', '.join(json.loads(x)) if x else ''
                )

            # Ensure export directory exists
            export_dir = os.path.dirname(filename)
            if export_dir and not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)

            df.to_csv(filename, index=False)
            return len(df)

        except Exception as e:
            print(f"❌ Export error: {e}")
            return 0

    def import_from_csv(self, filename: str) -> int:
        """Import meme data from CSV"""
        try:
            if not os.path.exists(filename):
                raise FileNotFoundError(f"File not found: {filename}")

            df = pd.read_csv(filename)

            # Validate required columns
            required_cols = ['meme_id', 'meme_url', 'meme_title', 'meme_source', 'timestamp']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            conn = sqlite3.connect(self.db_path)
            imported_count = 0

            for _, row in df.iterrows():
                try:
                    cursor = conn.cursor()

                    # Process meme_tags back to JSON
                    tags = row.get('meme_tags', '')
                    if isinstance(tags, str) and tags:
                        if tags.startswith('['):
                            # Already JSON
                            tags_json = tags
                        else:
                            # Comma-separated string
                            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                            tags_json = json.dumps(tag_list)
                    else:
                        tags_json = '[]'

                    cursor.execute("""
                        INSERT OR IGNORE INTO meme_responses 
                        (meme_id, meme_url, meme_title, meme_source, timestamp, 
                         viewed_duration, laugh_detected, laugh_intensity, 
                         laugh_confidence, laugh_count, max_intensity, 
                         meme_tags, laugh_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('meme_id', ''),
                        row.get('meme_url', ''),
                        row.get('meme_title', ''),
                        row.get('meme_source', ''),
                        row.get('timestamp', ''),
                        float(row.get('viewed_duration', 0)),
                        bool(row.get('laugh_detected', False)),
                        float(row.get('laugh_intensity', 0)),
                        float(row.get('laugh_confidence', 0)),
                        int(row.get('laugh_count', 0)),
                        float(row.get('max_intensity', 0)),
                        tags_json,
                        float(row.get('laugh_score', 0))
                    ))
                    imported_count += 1

                except Exception as row_error:
                    print(f"Warning: Failed to import row {imported_count + 1}: {row_error}")
                    continue

            conn.commit()
            conn.close()
            return imported_count

        except Exception as e:
            print(f"❌ Import error: {e}")
            return 0

    def backup_database(self, backup_path: str = None) -> bool:
        """Create a backup of the database"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.db_path}.backup_{timestamp}"

            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Database backed up to: {backup_path}")
            return True

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def reset_all_data(self, create_backup: bool = None) -> bool:
        """Reset all data in database with optional backup"""
        try:
            if create_backup is None:
                create_backup = config.database.backup_on_reset

            if create_backup:
                self.backup_database()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Clear all tables
            cursor.execute("DELETE FROM meme_responses")
            cursor.execute("DELETE FROM calibration_data")
            cursor.execute("DELETE FROM settings")
            cursor.execute("DELETE FROM sessions")

            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence")

            conn.commit()
            conn.close()

            print("✅ All data has been reset")
            return True

        except Exception as e:
            print(f"❌ Reset failed: {e}")
            return False

    def save_calibration(self, baseline_data: Any, sensitivity: float,
                         detector_config: Dict[str, Any] = None) -> bool:
        """Save calibration data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO calibration_data 
                (timestamp, baseline_data, sensitivity, detector_config)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                json.dumps(baseline_data) if baseline_data is not None else None,
                sensitivity,
                json.dumps(detector_config or {})
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ Error saving calibration: {e}")
            return False

    def get_latest_calibration(self) -> Optional[Tuple]:
        """Get the most recent calibration data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT baseline_data, sensitivity, detector_config, timestamp
                FROM calibration_data 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)

            result = cursor.fetchone()
            conn.close()
            return result

        except Exception as e:
            print(f"❌ Error retrieving calibration: {e}")
            return None

    def save_setting(self, key: str, value: str) -> bool:
        """Save a system setting"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.now().isoformat()))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ Error saving setting: {e}")
            return False

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a system setting"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            conn.close()

            return result[0] if result else default

        except Exception as e:
            print(f"❌ Error retrieving setting: {e}")
            return default

    def get_database_info(self) -> Dict[str, Any]:
        """Get database file information"""
        try:
            info = {
                'path': self.db_path,
                'exists': os.path.exists(self.db_path),
                'size_bytes': 0,
                'size_mb': 0,
                'created': None,
                'modified': None
            }

            if info['exists']:
                stat = os.stat(self.db_path)
                info['size_bytes'] = stat.st_size
                info['size_mb'] = stat.st_size / (1024 * 1024)
                info['created'] = datetime.fromtimestamp(stat.st_ctime).isoformat()
                info['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()

            return info

        except Exception as e:
            print(f"❌ Error getting database info: {e}")
            return {'error': str(e)}