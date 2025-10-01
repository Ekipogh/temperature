#!/usr/bin/env python3
"""
Database backup utility for temperature monitoring system.
Implements best practices for SQLite database backups.
"""

import gzip
import logging
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Handle database backup operations with best practices."""

    def __init__(self, db_path=None, backup_dir=None):
        self.db_path = (
            Path(db_path) if db_path else Path(__file__).parent / "db.sqlite3"
        )
        self.backup_dir = (
            Path(backup_dir) if backup_dir else Path(__file__).parent / "backups"
        )

        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, compress=True):
        """
        Create a backup of the database using SQLite's backup API.
        This is safer than file copying as it handles locks properly.
        """
        if not self.db_path.exists():
            logger.error(f"Database file not found: {self.db_path}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"temperature_backup_{timestamp}.sqlite3"

        if compress:
            backup_name += ".gz"

        backup_path = self.backup_dir / backup_name

        try:
            # Use SQLite's backup API for safe backup
            with sqlite3.connect(str(self.db_path)) as source:
                if compress:
                    # Create temporary uncompressed backup first
                    temp_backup = self.backup_dir / f"temp_{backup_name[:-3]}"
                    with sqlite3.connect(str(temp_backup)) as backup:
                        source.backup(backup)

                    # Compress the backup
                    with open(temp_backup, "rb") as f_in:
                        with gzip.open(backup_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # Remove temporary file
                    temp_backup.unlink()
                else:
                    with sqlite3.connect(str(backup_path)) as backup:
                        source.backup(backup)

            logger.info(f"✅ Backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return None

    def cleanup_old_backups(self, keep_days=30):
        """Remove backup files older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        removed_count = 0
        for backup_file in self.backup_dir.glob("temperature_backup_*.sqlite3*"):
            try:
                # Extract date from filename
                filename = backup_file.stem
                if filename.endswith(".sqlite3"):
                    date_str = filename.split("_")[-2] + "_" + filename.split("_")[-1]
                else:
                    # Handle .gz files
                    date_str = filename.split("_")[-2] + "_" + filename.split("_")[-1]

                file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")

                if file_date < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup_file.name}")

            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse date from {backup_file.name}: {e}")

        logger.info(f"✅ Cleaned up {removed_count} old backup files")
        return removed_count

    def list_backups(self):
        """List all available backups."""
        backups = []
        for backup_file in sorted(
            self.backup_dir.glob("temperature_backup_*.sqlite3*")
        ):
            try:
                size_mb = backup_file.stat().st_size / (1024 * 1024)
                modified = datetime.fromtimestamp(backup_file.stat().st_mtime)

                backups.append(
                    {
                        "file": backup_file.name,
                        "path": backup_file,
                        "size_mb": size_mb,
                        "modified": modified,
                    }
                )
            except Exception as e:
                logger.warning(f"Error reading backup info for {backup_file}: {e}")

        return backups

    def restore_backup(self, backup_path, confirm=True):
        """
        Restore database from backup.
        ⚠️ This will overwrite the current database!
        """
        backup_path = Path(backup_path)

        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        if confirm:
            response = input(
                "⚠️ This will overwrite the current database. Continue? (yes/no): "
            )
            if response.lower() != "yes":
                logger.info("Restore cancelled")
                return False

        try:
            # Create backup of current database first
            current_backup = self.create_backup(compress=True)
            logger.info(f"Current database backed up to: {current_backup}")

            # Restore from backup
            if backup_path.suffix == ".gz":
                # Decompress first
                with gzip.open(backup_path, "rb") as f_in:
                    with open(self.db_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, self.db_path)

            logger.info(f"✅ Database restored from: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False

    def verify_backup(self, backup_path):
        """Verify that a backup file is a valid SQLite database."""
        backup_path = Path(backup_path)

        if not backup_path.exists():
            return False, "File not found"

        try:
            # Handle compressed backups
            if backup_path.suffix == ".gz":
                with gzip.open(backup_path, "rb") as f:
                    # Read first 16 bytes to check SQLite header
                    header = f.read(16)
                    if not header.startswith(b"SQLite format 3\x00"):
                        return False, "Not a valid SQLite file"
            else:
                with sqlite3.connect(str(backup_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()

                    # Check for expected tables
                    table_names = [table[0] for table in tables]
                    if "homepage_temperature" not in table_names:
                        return False, "Missing expected tables"

            return True, "Valid backup"

        except Exception as e:
            return False, f"Verification failed: {e}"


def main():
    """Command line interface for backup operations."""
    import sys

    backup_manager = DatabaseBackup()

    if len(sys.argv) < 2:
        print(
            "Usage: python backup_utility.py [create|list|cleanup|verify|restore] [options]"
        )
        return

    command = sys.argv[1].lower()

    if command == "create":
        compress = "--no-compress" not in sys.argv
        backup_path = backup_manager.create_backup(compress=compress)
        if backup_path:
            print(f"✅ Backup created: {backup_path}")

    elif command == "list":
        backups = backup_manager.list_backups()
        print(f"Found {len(backups)} backup files:")
        for backup in backups:
            print(
                f"  {backup['file']} - {backup['size_mb']:.1f} MB - {backup['modified']}"
            )

    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        count = backup_manager.cleanup_old_backups(keep_days=days)
        print(f"✅ Cleaned up {count} old backup files")

    elif command == "verify":
        if len(sys.argv) < 3:
            print("Usage: python backup_utility.py verify <backup_file>")
            return

        backup_file = sys.argv[2]
        is_valid, message = backup_manager.verify_backup(backup_file)
        status = "✅" if is_valid else "❌"
        print(f"{status} {backup_file}: {message}")

    elif command == "restore":
        if len(sys.argv) < 3:
            print("Usage: python backup_utility.py restore <backup_file>")
            return

        backup_file = sys.argv[2]
        success = backup_manager.restore_backup(backup_file)
        if success:
            print("✅ Database restored successfully")
        else:
            print("❌ Restore failed")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
