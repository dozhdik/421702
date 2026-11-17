"""Convert legacy sample identifiers without discarding records."""
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .database import get_connection


def migrate_legacy_samples():
    conn = get_connection()
    try:
        changes = []
        for table in ("Contract", "IndividualContract"):
            for row in conn.execute(f"SELECT id, contract_number FROM {table}"):
                value = row["contract_number"]
                match = re.fullmatch(r"(?:DEMO|КД)-(\d{3})", value)
                group = re.fullmatch(r"DEMO-GROUP-(\d{3})", value)
                individual = re.fullmatch(r"DEMO-IND-(\d{3})", value)
                if match and table == "Contract" and 1 <= int(match[1]) <= 5:
                    new = f"КД-{int(match[1]):04d}"
                elif group and table == "Contract" and 1 <= int(group[1]) <= 95:
                    new = f"КД-{int(group[1])+1000:04d}"
                elif individual and table == "IndividualContract" and 1 <= int(individual[1]) <= 40:
                    new = f"ИД-{int(individual[1]):04d}"
                else:
                    continue
                occupied = any(conn.execute(f"SELECT 1 FROM {other} WHERE contract_number=?", (new,)).fetchone()
                               for other in ("Contract", "IndividualContract"))
                if not occupied:
                    changes.append((table, "contract_number", row["id"], new))
        for row in conn.execute("SELECT id, passport_details, phone_number FROM Agent"):
            value = row["passport_details"]
            base = re.fullmatch(r"DEMO-PASS-(\d{3})", value)
            agent = re.fullmatch(r"DEMO-AGENT-(\d{3})", value)
            marked = re.fullmatch(r"(MP\d{7}) \(учебный\)", value)
            new = (f"MP9{int(base[1]):06d}" if base and 1 <= int(base[1]) <= 2 else
                   f"MP{int(agent[1]):07d}" if agent and 1 <= int(agent[1]) <= 38 else
                   marked[1] if marked else None)
            if new and not conn.execute("SELECT 1 FROM Agent WHERE passport_details=?", (new,)).fetchone():
                changes.append(("Agent", "passport_details", row["id"], new))
            digits = re.sub(r"\D", "", row["phone_number"])
            if len(digits) == 12 and digits.startswith("375") and row["phone_number"] != "+" + digits:
                changes.append(("Agent", "phone_number", row["id"], "+" + digits))
        for row in conn.execute("SELECT id, bank_details FROM Organization"):
            if re.fullmatch(r"BY00 DEMO \d{4}", row["bank_details"]):
                changes.append(("Organization", "bank_details", row["id"],
                                "BY00 TEST 0000 0000 " + row["bank_details"][-4:] + " 0000"))
        if not changes:
            return None
        path = conn.execute("PRAGMA database_list").fetchone()["file"]
        backup_path = None
        if path:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            source = Path(path)
            backup_path = str(source.with_name(source.stem + ".before-format-" + stamp + ".db"))
            fd = os.open(backup_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
            backup = sqlite3.connect(backup_path)
            try:
                conn.backup(backup)
            finally:
                backup.close()
        try:
            conn.execute("BEGIN IMMEDIATE")
            for table, column, row_id, value in changes:
                conn.execute(f"UPDATE {table} SET {column}=? WHERE id=?", (value, row_id))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return backup_path
    finally:
        conn.close()
