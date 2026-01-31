#!/usr/bin/env python3
"""Weekly routine tracker CLI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import routine_core as rc

DEFAULT_PLOT_PATH = Path("plots/score_trend.png")
DEFAULT_REPORT_PATH = Path("reports/weekly_report.html")


def parse_date(value: str) -> rc.date:
    try:
        return rc.parse_date(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"날짜는 {rc.DATE_FMT} 형식이어야 합니다. (예: 2024-01-15)"
        ) from exc


def parse_days(value: str) -> int:
    try:
        days = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("일수는 정수여야 합니다.") from exc

    return days


def validate_days(category: str, days: int) -> None:
    try:
        rc.validate_days(category, days)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def append_entry(path: Path, entry: rc.RoutineEntry) -> None:
    entries = rc.load_entries(path)
    entries.append(entry)
    rc.save_entries(path, entries)


def plot_scores_matplotlib(
    totals: dict[rc.date, float],
    category_data: dict[str, dict[rc.date, float]],
    output_path: Path,
) -> None:
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if totals:
        weeks = sorted(totals.keys())
        scores = [totals[week] for week in weeks]
        plt.plot(weeks, scores, marker="o", label="총합")
        plt.ylabel("점수")

    for category, week_scores in sorted(category_data.items()):
        weeks = sorted(week_scores.keys())
        scores = [week_scores[week] for week in weeks]
        plt.plot(weeks, scores, marker="o", label=category)

    if totals or category_data:
        plt.legend()

    plt.title("루틴 점수 추이")
    plt.xlabel("주 시작일")
    plt.ylim(0, 100)
    plt.grid(True, axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_scores_svg(
    totals: dict[rc.date, float],
    category_data: dict[str, dict[rc.date, float]],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_dates = sorted({*totals.keys(), *{d for data in category_data.values() for d in data}})
    if not all_dates:
        raise ValueError("시각화할 데이터가 없습니다.")

    width, height, padding = 800, 400, 50
    x_step = (width - 2 * padding) / max(len(all_dates) - 1, 1)

    def x_pos(index: int) -> float:
        return padding + index * x_step

    def y_pos(score: float) -> float:
        return height - padding - (score / 100) * (height - 2 * padding)

    lines = []
    labels = []

    def add_series(label: str, series: dict[rc.date, float], color: str) -> None:
        points = []
        for idx, day in enumerate(all_dates):
            score = series.get(day)
            if score is None:
                continue
            points.append((x_pos(idx), y_pos(score)))
        if not points:
            return
        path = " ".join(
            [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
            + [f"L {x:.1f} {y:.1f}" for x, y in points[1:]]
        )
        lines.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" />')
        labels.append((label, color))

    add_series("총합", totals, "#1f77b4")
    palette = ["#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    for color, (category, series) in zip(palette, sorted(category_data.items())):
        add_series(category, series, color)

    x_labels = []
    for idx, day in enumerate(all_dates):
        x_labels.append(
            f'<text x="{x_pos(idx):.1f}" y="{height - padding + 20}" '
            f'font-size="10" text-anchor="middle">{day.strftime("%m-%d")}</text>'
        )

    y_labels = []
    for score in range(0, 101, 20):
        y = y_pos(score)
        y_labels.append(
            f'<text x="{padding - 10}" y="{y:.1f}" font-size="10" '
            f'text-anchor="end">{score}</text>'
        )

    legend_items = []
    legend_y = padding / 2
    legend_x = padding
    for idx, (label, color) in enumerate(labels):
        x = legend_x + idx * 120
        legend_items.append(
            f'<rect x="{x}" y="{legend_y}" width="10" height="10" fill="{color}" />'
            f'<text x="{x + 14}" y="{legend_y + 9}" font-size="10">{label}</text>'
        )

    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\">
  <rect width=\"100%\" height=\"100%\" fill=\"white\" />
  <text x=\"{width/2:.1f}\" y=\"20\" text-anchor=\"middle\" font-size=\"14\">루틴 점수 추이</text>
  <line x1=\"{padding}\" y1=\"{padding}\" x2=\"{padding}\" y2=\"{height - padding}\" stroke=\"#ccc\" />
  <line x1=\"{padding}\" y1=\"{height - padding}\" x2=\"{width - padding}\" y2=\"{height - padding}\" stroke=\"#ccc\" />
  {''.join(y_labels)}
  {''.join(x_labels)}
  {''.join(lines)}
  {''.join(legend_items)}
</svg>
"""
    output_path.write_text(svg, encoding="utf-8")
    return output_path


def generate_plot(
    entries: list[rc.RoutineEntry],
    output_path: Path,
    per_category: bool,
    total_only: bool,
) -> tuple[Path, bool]:
    totals = rc.summarize_by_week(entries)
    if not totals:
        raise ValueError("시각화할 데이터가 없습니다.")

    if per_category:
        category_data = rc.summarize_by_category(entries)
        totals = {}
    elif total_only:
        category_data = {}
    else:
        category_data = rc.summarize_by_category(entries)

    try:
        import matplotlib.pyplot as plt  # noqa: F401
    except ModuleNotFoundError:
        svg_path = output_path if output_path.suffix == ".svg" else output_path.with_suffix(".svg")
        plot_scores_svg(totals, category_data, svg_path)
        return svg_path, False

    plot_scores_matplotlib(totals, category_data, output_path)
    return output_path, True


def init_command(args: argparse.Namespace) -> None:
    rc.ensure_csv(args.data)
    print(f"초기화 완료: {args.data}")


def add_command(args: argparse.Namespace) -> None:
    validate_days(args.category, args.days)
    entry = rc.build_entry(args.week_start, args.category, args.days)
    append_entry(args.data, entry)
    print(f"추가 완료: {entry.week_start} {entry.category} {entry.days}일 {entry.score}점")

    entries = rc.load_entries(args.data)
    totals = rc.summarize_by_week(entries)
    total_score = totals.get(entry.week_start, 0.0)
    grade = rc.grade_for_score(total_score)
    print(f"주간 합계: {rc.week_label(entry.week_start)} {total_score:.1f}점 {grade}")


def list_command(args: argparse.Namespace) -> None:
    entries = rc.load_entries(args.data)
    if not entries:
        print("등록된 루틴 점수가 없습니다.")
        return

    entries.sort(key=lambda item: (item.week_start, item.category))
    for entry in entries:
        print(
            f"{entry.week_start.strftime(rc.DATE_FMT)}\t{entry.category}\t"
            f"{entry.days}일\t{entry.score}점"
        )


def plot_command(args: argparse.Namespace) -> None:
    entries = rc.load_entries(args.data)
    output_path, used_matplotlib = generate_plot(
        entries, args.output, args.per_category, args.total_only
    )
    if used_matplotlib:
        print(f"그래프 저장 완료: {output_path}")
    else:
        print(f"matplotlib이 없어 SVG로 저장했습니다: {output_path}")


def summary_command(args: argparse.Namespace) -> None:
    entries = rc.load_entries(args.data)
    totals = rc.summarize_by_week(entries)
    if not totals:
        print("등록된 루틴 점수가 없습니다.")
        return

    for week_start in sorted(totals.keys()):
        total_score = totals[week_start]
        grade = rc.grade_for_score(total_score)
        print(f"{rc.week_label(week_start)}\t{total_score:.1f}점\t{grade}")


def report_command(args: argparse.Namespace) -> None:
    entries = rc.load_entries(args.data)
    totals = rc.summarize_by_week(entries)
    if not totals:
        print("등록된 루틴 점수가 없습니다.")
        return

    plot_path, used_matplotlib = generate_plot(
        entries, args.plot, per_category=False, total_only=False
    )

    report_path = args.output
    report_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for week_start in sorted(totals.keys()):
        total_score = totals[week_start]
        grade = rc.grade_for_score(total_score)
        rows.append(
            f"<tr><td>{rc.week_label(week_start)}</td><td>{total_score:.1f}점</td>"
            f"<td>{grade}</td></tr>"
        )

    plot_note = "" if used_matplotlib else "<p>matplotlib 미설치로 SVG 그래프를 사용했습니다.</p>"
    relative_plot_path = Path(os.path.relpath(plot_path, report_path.parent))
    html = f"""<!doctype html>
<html lang=\"ko\">
<head>
  <meta charset=\"utf-8\" />
  <title>루틴 주간 리포트</title>
  <style>
    body {{ font-family: sans-serif; margin: 24px; }}
    .tabs {{ display: flex; gap: 8px; margin-bottom: 16px; }}
    .tab-button {{ padding: 8px 12px; border: 1px solid #ccc; cursor: pointer; }}
    .tab-button.active {{ background: #f0f0f0; font-weight: bold; }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
  </style>
  <script>
    function showTab(id) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-button').forEach(el => el.classList.remove('active'));
      document.getElementById(id).classList.add('active');
      document.querySelector(`[data-tab=\"${id}\"]`).classList.add('active');
    }}
    window.addEventListener('DOMContentLoaded', () => showTab('summary'));
  </script>
</head>
<body>
  <h1>루틴 주간 리포트</h1>
  <div class=\"tabs\">
    <button class=\"tab-button\" data-tab=\"summary\" onclick=\"showTab('summary')\">총합/등급</button>
    <button class=\"tab-button\" data-tab=\"trend\" onclick=\"showTab('trend')\">그래프 추이</button>
  </div>
  <div id=\"summary\" class=\"tab-content\">
    <h2>주간 총합 및 등급</h2>
    <table>
      <thead>
        <tr><th>주차</th><th>총점</th><th>등급</th></tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
  <div id=\"trend\" class=\"tab-content\">
    <h2>그래프 추이</h2>
    {plot_note}
    <img src=\"{relative_plot_path.as_posix()}\" alt=\"루틴 점수 추이 그래프\" style=\"max-width: 100%;\" />
  </div>
</body>
</html>
"""
    report_path.write_text(html, encoding="utf-8")
    print(f"리포트 저장 완료: {report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="주간 루틴 점수를 기록하고 날짜별로 시각화합니다."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=rc.DEFAULT_DATA_PATH,
        help="CSV 데이터 파일 경로 (기본값: data/routines.csv)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="CSV 파일을 초기화합니다.")
    init_parser.set_defaults(func=init_command)

    add_parser = subparsers.add_parser("add", help="주간 루틴 점수를 추가합니다.")
    add_parser.add_argument("week_start", type=parse_date, help="주 시작일 (YYYY-MM-DD)")
    add_parser.add_argument(
        "category",
        type=str,
        choices=sorted(rc.CATEGORY_WEIGHTS.keys()),
        help="루틴 카테고리",
    )
    add_parser.add_argument(
        "days", type=parse_days, help="수행 일수 또는 시간 (0-7, 공부시간은 0-84)"
    )
    add_parser.set_defaults(func=add_command)

    list_parser = subparsers.add_parser("list", help="등록된 점수를 표시합니다.")
    list_parser.set_defaults(func=list_command)

    plot_parser = subparsers.add_parser("plot", help="그래프를 생성합니다.")
    plot_parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PLOT_PATH,
        help="출력 이미지 경로 (기본값: plots/score_trend.png)",
    )
    plot_group = plot_parser.add_mutually_exclusive_group()
    plot_group.add_argument(
        "--per-category",
        action="store_true",
        help="카테고리별 라인만 표시합니다.",
    )
    plot_group.add_argument(
        "--total-only",
        action="store_true",
        help="총합 라인만 표시합니다.",
    )
    plot_parser.set_defaults(func=plot_command)

    summary_parser = subparsers.add_parser("summary", help="주간 총점과 등급을 표시합니다.")
    summary_parser.set_defaults(func=summary_command)

    report_parser = subparsers.add_parser("report", help="탭 포함 리포트를 생성합니다.")
    report_parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="출력 HTML 경로 (기본값: reports/weekly_report.html)",
    )
    report_parser.add_argument(
        "--plot",
        type=Path,
        default=DEFAULT_PLOT_PATH,
        help="리포트에 포함할 그래프 이미지 경로",
    )
    report_parser.set_defaults(func=report_command)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
