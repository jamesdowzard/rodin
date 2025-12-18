"""Transcription statistics and history tracking."""

import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .config import get_config_dir


@dataclass
class TranscriptionRecord:
    """A single transcription record."""

    id: int
    timestamp: datetime
    raw_text: str
    edited_text: str | None
    duration_seconds: float
    word_count: int
    char_count: int
    app_bundle_id: str | None
    app_name: str | None
    preset_used: str | None


@dataclass
class Stats:
    """Aggregated statistics."""

    total_transcriptions: int
    total_words: int
    total_chars: int
    total_duration_seconds: float
    estimated_typing_time_seconds: float  # At 45 WPM
    time_saved_seconds: float
    avg_words_per_transcription: float
    most_active_hour: int | None
    most_active_day: str | None  # Monday, Tuesday, etc.
    top_apps: list[tuple[str, int]]  # (app_name, count)
    top_words: list[tuple[str, int]]  # (word, count)


class TranscriptionDB:
    """SQLite database for transcription history and stats."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS transcriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        edited_text TEXT,
        duration_seconds REAL NOT NULL,
        word_count INTEGER NOT NULL,
        char_count INTEGER NOT NULL,
        app_bundle_id TEXT,
        app_name TEXT,
        preset_used TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_timestamp ON transcriptions(timestamp);
    CREATE INDEX IF NOT EXISTS idx_app_bundle_id ON transcriptions(app_bundle_id);

    CREATE TABLE IF NOT EXISTS word_counts (
        word TEXT PRIMARY KEY,
        count INTEGER NOT NULL DEFAULT 0
    );
    """

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = get_config_dir() / "transcriptions.db"
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.SCHEMA)

    def record(
        self,
        raw_text: str,
        edited_text: str | None,
        duration_seconds: float,
        app_bundle_id: str | None = None,
        app_name: str | None = None,
        preset_used: str | None = None,
    ) -> int:
        """Record a transcription.

        Returns the record ID.
        """
        # Use edited text for counts if available, otherwise raw
        text_for_counts = edited_text or raw_text
        words = text_for_counts.split()
        word_count = len(words)
        char_count = len(text_for_counts)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO transcriptions
                (timestamp, raw_text, edited_text, duration_seconds, word_count, char_count, app_bundle_id, app_name, preset_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    raw_text,
                    edited_text,
                    duration_seconds,
                    word_count,
                    char_count,
                    app_bundle_id,
                    app_name,
                    preset_used,
                ),
            )
            record_id = cursor.lastrowid

            # Update word counts (lowercase, filter short words)
            for word in words:
                word_lower = word.lower().strip(".,!?;:\"'()[]{}").strip()
                if len(word_lower) >= 3:  # Skip very short words
                    conn.execute(
                        """
                        INSERT INTO word_counts (word, count) VALUES (?, 1)
                        ON CONFLICT(word) DO UPDATE SET count = count + 1
                        """,
                        (word_lower,),
                    )

        return record_id

    def get_stats(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Stats:
        """Get aggregated statistics for a time period."""
        with sqlite3.connect(self.db_path) as conn:
            # Build date filter
            where_clause = "1=1"
            params: list = []
            if since:
                where_clause += " AND timestamp >= ?"
                params.append(since.isoformat())
            if until:
                where_clause += " AND timestamp < ?"
                params.append(until.isoformat())

            # Basic aggregates
            row = conn.execute(
                f"""
                SELECT
                    COUNT(*) as total,
                    COALESCE(SUM(word_count), 0) as words,
                    COALESCE(SUM(char_count), 0) as chars,
                    COALESCE(SUM(duration_seconds), 0) as duration
                FROM transcriptions
                WHERE {where_clause}
                """,
                params,
            ).fetchone()

            total_transcriptions = row[0]
            total_words = row[1]
            total_chars = row[2]
            total_duration = row[3]

            # Estimated typing time (45 WPM average)
            estimated_typing_time = (total_words / 45) * 60 if total_words > 0 else 0
            time_saved = max(0, estimated_typing_time - total_duration)

            avg_words = total_words / total_transcriptions if total_transcriptions > 0 else 0

            # Most active hour
            hour_row = conn.execute(
                f"""
                SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as cnt
                FROM transcriptions
                WHERE {where_clause}
                GROUP BY hour
                ORDER BY cnt DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
            most_active_hour = hour_row[0] if hour_row else None

            # Most active day of week
            day_row = conn.execute(
                f"""
                SELECT strftime('%w', timestamp) as dow, COUNT(*) as cnt
                FROM transcriptions
                WHERE {where_clause}
                GROUP BY dow
                ORDER BY cnt DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
            day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            most_active_day = day_names[int(day_row[0])] if day_row else None

            # Top apps
            top_apps = conn.execute(
                f"""
                SELECT COALESCE(app_name, 'Unknown') as app, COUNT(*) as cnt
                FROM transcriptions
                WHERE {where_clause} AND app_name IS NOT NULL
                GROUP BY app_name
                ORDER BY cnt DESC
                LIMIT 10
                """,
                params,
            ).fetchall()

            # Top words (from word_counts table for all-time, or calculate for period)
            if since is None and until is None:
                top_words = conn.execute(
                    "SELECT word, count FROM word_counts ORDER BY count DESC LIMIT 50"
                ).fetchall()
            else:
                # For specific period, we need to recalculate from transcriptions
                texts = conn.execute(
                    f"SELECT COALESCE(edited_text, raw_text) FROM transcriptions WHERE {where_clause}",
                    params,
                ).fetchall()
                word_counter: Counter[str] = Counter()
                for (text,) in texts:
                    for word in text.split():
                        word_lower = word.lower().strip(".,!?;:\"'()[]{}").strip()
                        if len(word_lower) >= 3:
                            word_counter[word_lower] += 1
                top_words = word_counter.most_common(50)

        return Stats(
            total_transcriptions=total_transcriptions,
            total_words=total_words,
            total_chars=total_chars,
            total_duration_seconds=total_duration,
            estimated_typing_time_seconds=estimated_typing_time,
            time_saved_seconds=time_saved,
            avg_words_per_transcription=avg_words,
            most_active_hour=most_active_hour,
            most_active_day=most_active_day,
            top_apps=list(top_apps),
            top_words=list(top_words),
        )

    def get_stats_today(self) -> Stats:
        """Get stats for today."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return self.get_stats(since=today, until=tomorrow)

    def get_stats_this_week(self) -> Stats:
        """Get stats for this week (Monday to Sunday)."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        return self.get_stats(since=start_of_week, until=end_of_week)

    def get_stats_this_month(self) -> Stats:
        """Get stats for this month."""
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if today.month == 12:
            end_of_month = start_of_month.replace(year=today.year + 1, month=1)
        else:
            end_of_month = start_of_month.replace(month=today.month + 1)
        return self.get_stats(since=start_of_month, until=end_of_month)

    def get_stats_this_year(self) -> Stats:
        """Get stats for this year."""
        today = datetime.now()
        start_of_year = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_year = start_of_year.replace(year=today.year + 1)
        return self.get_stats(since=start_of_year, until=end_of_year)

    def get_recent(self, limit: int = 20) -> list[TranscriptionRecord]:
        """Get recent transcriptions."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, raw_text, edited_text, duration_seconds,
                       word_count, char_count, app_bundle_id, app_name, preset_used
                FROM transcriptions
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            TranscriptionRecord(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                raw_text=row[2],
                edited_text=row[3],
                duration_seconds=row[4],
                word_count=row[5],
                char_count=row[6],
                app_bundle_id=row[7],
                app_name=row[8],
                preset_used=row[9],
            )
            for row in rows
        ]

    def get_daily_word_counts(self, days: int = 30) -> list[tuple[str, int]]:
        """Get word counts per day for the last N days."""
        since = datetime.now() - timedelta(days=days)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT date(timestamp) as day, SUM(word_count) as words
                FROM transcriptions
                WHERE timestamp >= ?
                GROUP BY day
                ORDER BY day
                """,
                (since.isoformat(),),
            ).fetchall()
        return list(rows)

    def format_stats(self, stats: Stats) -> str:
        """Format stats as a human-readable string."""
        lines = [
            f"Transcriptions: {stats.total_transcriptions:,}",
            f"Words dictated: {stats.total_words:,}",
            f"Characters: {stats.total_chars:,}",
            f"Recording time: {stats.total_duration_seconds / 60:.1f} min",
            f"Est. typing time: {stats.estimated_typing_time_seconds / 60:.1f} min",
            f"Time saved: {stats.time_saved_seconds / 60:.1f} min",
        ]

        if stats.avg_words_per_transcription > 0:
            lines.append(f"Avg words/transcription: {stats.avg_words_per_transcription:.1f}")

        if stats.most_active_hour is not None:
            hour_12 = stats.most_active_hour % 12 or 12
            am_pm = "AM" if stats.most_active_hour < 12 else "PM"
            lines.append(f"Most active hour: {hour_12} {am_pm}")

        if stats.most_active_day:
            lines.append(f"Most active day: {stats.most_active_day}")

        if stats.top_apps:
            lines.append(f"Top app: {stats.top_apps[0][0]} ({stats.top_apps[0][1]}x)")

        if stats.top_words:
            top_5 = ", ".join(w for w, _ in stats.top_words[:5])
            lines.append(f"Top words: {top_5}")

        return "\n".join(lines)


# Singleton instance
_db: TranscriptionDB | None = None


def get_db() -> TranscriptionDB:
    """Get the transcription database singleton."""
    global _db
    if _db is None:
        _db = TranscriptionDB()
    return _db
