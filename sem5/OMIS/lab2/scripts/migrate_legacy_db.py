"""Rename the legacy SQLite schema and enum values without changing record IDs."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from scripts.legacy_name_map import COLUMN_NAMES, TABLE_NAMES


ENUM_VALUES = {
    "Article": {"publication_status": {
        "Черновик": "draft", "На модерации": "in_moderation",
        "Требует правок": "needs_revision", "Опубликовано": "published",
        "Архив": "archived", "Снято": "unpublished",
    }},
    "Comment": {"status": {"Виден": "visible", "Скрыт": "hidden", "Удалён": "deleted"}},
    "Complaint": {"status": {"Новая": "new", "Подтверждена": "confirmed", "Отклонена": "dismissed"}},
    "Reaction": {"reaction_type": {"Нравится": "like", "Полезно": "helpful"}},
    "EditorRemark": {"severity": {"Низкая": "low", "Средняя": "medium", "Высокая": "high"}},
    "PublicationRecord": {"result": {"Одобрено": "approved"}},
}


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def migrate(database_path: str | Path, backup_dir: str | Path | None = None) -> Path | None:
    path = Path(database_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not names.intersection(TABLE_NAMES):
        connection.close()
        return None
    if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        connection.close()
        raise RuntimeError("The legacy database failed its integrity check")
    old_counts = {name: connection.execute(f"SELECT COUNT(*) FROM {quote_identifier(name)}").fetchone()[0]
                  for name in names if name in TABLE_NAMES}
    old_accounts = {row[0]: row[1] for row in connection.execute(
        'SELECT "идАккаунта", "пароль" FROM "УчетнаяЗапись"')} if "УчетнаяЗапись" in names else {}
    target_dir = Path(backup_dir) if backup_dir else path.parent / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = target_dir / f"{path.stem}-before-english-{stamp}.sqlite"
    with sqlite3.connect(backup_path) as backup:
        connection.backup(backup)
    try:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("BEGIN IMMEDIATE")
        for old_table, new_table in TABLE_NAMES.items():
            if old_table not in names:
                continue
            connection.execute(f"ALTER TABLE {quote_identifier(old_table)} RENAME TO {quote_identifier(new_table)}")
            old_columns = [row[1] for row in connection.execute(f"PRAGMA table_info({quote_identifier(new_table)})")]
            for old_column in old_columns:
                new_column = COLUMN_NAMES.get(old_column)
                if new_column and new_column != old_column:
                    connection.execute(
                        f"ALTER TABLE {quote_identifier(new_table)} RENAME COLUMN "
                        f"{quote_identifier(old_column)} TO {quote_identifier(new_column)}")
        for table, columns in ENUM_VALUES.items():
            if table not in {TABLE_NAMES[name] for name in old_counts}:
                continue
            for column, values in columns.items():
                for old_value, new_value in values.items():
                    connection.execute(
                        f"UPDATE {quote_identifier(table)} SET {quote_identifier(column)}=? "
                        f"WHERE {quote_identifier(column)}=?", (new_value, old_value))
        for old_table, count in old_counts.items():
            new_table = TABLE_NAMES[old_table]
            current = connection.execute(f"SELECT COUNT(*) FROM {quote_identifier(new_table)}").fetchone()[0]
            if current != count:
                raise RuntimeError(f"Record count changed in {new_table}")
        if old_accounts:
            current_accounts = {row[0]: row[1] for row in connection.execute(
                'SELECT account_id, password_hash FROM UserAccount')}
            if current_accounts != old_accounts:
                raise RuntimeError("Account IDs or password hashes changed")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Foreign keys failed after migration")
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Database integrity failed after migration")
        remaining = [name for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','index')") if not name.isascii()]
        if remaining:
            raise RuntimeError(f"Non-English schema names remain: {remaining}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.close()
    return backup_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate an existing OMIS SQLite database")
    parser.add_argument("--db", default="blog.sqlite", help="SQLite database path")
    parser.add_argument("--backup-dir", help="Directory for a timestamped pre-migration backup")
    args = parser.parse_args()
    backup = migrate(args.db, args.backup_dir)
    print(f"Migrated {args.db}; backup: {backup}" if backup else f"No legacy schema in {args.db}")
