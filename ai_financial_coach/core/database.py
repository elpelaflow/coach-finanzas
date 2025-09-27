from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd
import sqlite3

PACKAGE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_DIR.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "database.db"


def resolve_db_path(db_path: Optional[Path] = None) -> Path:
    return Path(db_path) if db_path else DEFAULT_DB_PATH


def init_db(db_path: Optional[Path] = None) -> None:
    path = resolve_db_path(db_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                type TEXT,
                category TEXT,
                amount REAL,
                comment TEXT
            )
            """
        )
        conn.commit()


def save_movements_to_db(
    movements: Iterable[Dict[str, Any]], db_path: Optional[Path] = None
) -> None:
    path = resolve_db_path(db_path)
    with sqlite3.connect(path) as conn:
        conn.executemany(
            """
            INSERT INTO movements (timestamp, type, category, amount, comment)
            VALUES (:timestamp, :type, :category, :amount, :comment)
            """,
            list(movements),
        )
        conn.commit()


def clear_db(db_path: Optional[Path] = None) -> None:
    """Eliminar todos los movimientos almacenados en la base de datos."""
    path = resolve_db_path(db_path)
    init_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM movements")
        conn.commit()


def fetch_data_from_db(
    start_date: date, end_date: Optional[date] = None, db_path: Optional[Path] = None
) -> pd.DataFrame:
    path = resolve_db_path(db_path)
    end = end_date or start_date
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    query = (
        "SELECT * FROM movements WHERE DATE(timestamp) BETWEEN ? AND ?"
    )
    with sqlite3.connect(path) as conn:
        df = pd.read_sql_query(query, conn, params=(start_str, end_str))
    return df
