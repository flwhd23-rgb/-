#!/usr/bin/env python3
"""Core routines for score calculation and CSV persistence."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

DATE_FMT = "%Y-%m-%d"
DEFAULT_DATA_PATH = Path("data/routines.csv")

CATEGORY_WEIGHTS: dict[str, int] = {
    "생활리듬": 30,
    "명상/일기쓰기": 15,
    "공부시간": 30,
    "운동": 10,
    "핵심키워드": 15,
}

SCORE_TABLES: dict[str, dict[int, float]] = {
    "생활리듬": {7: 30, 6: 27, 5: 25, 4: 15, 3: 10, 2: 5, 1: 3, 0: 0},
    "명상/일기쓰기": {7: 15, 6: 14, 5: 13, 4: 10, 3: 8, 2: 6, 1: 3, 0: 0},
    "운동": {7: 10, 6: 9.5, 5: 9, 4: 8, 3: 7, 2: 4, 1: 2, 0: 0},
    "핵심키워드": {7: 15, 6: 14, 5: 12, 4: 10, 3: 8, 2: 4, 1: 2, 0: 0},
}

GRADE_THRESHOLDS: list[tuple[int, str]] = [
    (95, "SS등급(상위 0.1%)"),
    (90, "S등급(상위 1%)"),
    (85, "A등급(상위 5%)"),
    (75, "B등급(상위 10%)"),
    (65, "C등급(상위 20%)"),
    (55, "D등급(상위 30%)"),
    (0, "주의등급"),
]

CATEGORY_ORDER = [
    "생활리듬",
    "명상/일기쓰기",
    "공부시간",
    "운동",
    "핵심키워드",
]


@dataclass(frozen=True)
class RoutineEntry:
    week_start: date
    category: str
    days: int
    score: float


def parse_date(value: str) -> date:
    return datetime.strptime(value, DATE_FMT).date()


def week_start_for_day(day: date) -> date:
    return day - timedelta(days=day.weekday())


def ensure_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["week_start", "category", "days", "score"])


def calculate_score(category: str, days: int) -> float:
    if category == "공부시간":
        weight = CATEGORY_WEIGHTS[category]
        return round((days / 84) * weight, 2)
    return SCORE_TABLES[category][days]


def validate_days(category: str, days: int) -> None:
    if days < 0:
        raise ValueError("일수는 0 이상이어야 합니다.")
    if category == "공부시간":
        if days > 84:
            raise ValueError("공부시간은 0부터 84 사이여야 합니다.")
        return
    if days > 7:
        raise ValueError("일수는 0부터 7 사이여야 합니다.")


def grade_for_score(score: float) -> str:
    for threshold, label in GRADE_THRESHOLDS:
        if score >= threshold:
            return label
    return "주의등급"


def week_label(week_start: date) -> str:
    year, week, _ = week_start.isocalendar()
    return f"{week_start.strftime(DATE_FMT)} (ISO {year}-W{week:02d})"


def build_entry(week_start: date, category: str, days: int) -> RoutineEntry:
    validate_days(category, days)
    score = calculate_score(category, days)
    return RoutineEntry(week_start=week_start, category=category, days=days, score=score)


def load_entries(path: Path) -> list[RoutineEntry]:
    if not path.exists():
        return []
    entries: list[RoutineEntry] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row:
                continue
            category = row.get("category", "").strip()
            if category not in CATEGORY_WEIGHTS:
                continue
            days = int(row["days"])
            entry = RoutineEntry(
                week_start=parse_date(row["week_start"]),
                category=category,
                days=days,
                score=float(row["score"]),
            )
            entries.append(entry)
    return entries


def save_entries(path: Path, entries: Iterable[RoutineEntry]) -> None:
    ensure_csv(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["week_start", "category", "days", "score"])
        for entry in entries:
            writer.writerow(
                [
                    entry.week_start.strftime(DATE_FMT),
                    entry.category,
                    entry.days,
                    entry.score,
                ]
            )


def upsert_week_entries(path: Path, week_start: date, entries: Iterable[RoutineEntry]) -> None:
    existing = load_entries(path)
    filtered = [entry for entry in existing if entry.week_start != week_start]
    save_entries(path, [*filtered, *entries])


def delete_week_entries(path: Path, week_start: date) -> None:
    existing = load_entries(path)
    filtered = [entry for entry in existing if entry.week_start != week_start]
    save_entries(path, filtered)


def summarize_by_week(entries: Iterable[RoutineEntry]) -> dict[date, float]:
    totals: dict[date, float] = defaultdict(float)
    for entry in entries:
        totals[entry.week_start] += entry.score
    return dict(totals)


def summarize_by_category(
    entries: Iterable[RoutineEntry],
) -> dict[str, dict[date, float]]:
    categories: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for entry in entries:
        categories[entry.category][entry.week_start] += entry.score
    return {category: dict(weeks) for category, weeks in categories.items()}
