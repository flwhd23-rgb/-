#!/usr/bin/env python3
"""Streamlit app for routine tracking."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st

import routine_core as rc

DATA_PATH = rc.DEFAULT_DATA_PATH
PLOT_PATH = Path("plots/score_trend.png")
REPORT_PATH = Path("reports/weekly_report.html")

CATEGORY_KEY_MAP = {
    "생활리듬": "생활리듬",
    "명상/일기쓰기": "명상",
    "공부시간": "공부시간",
    "운동": "운동",
    "핵심키워드": "핵심키워드",
}


def entries_to_dataframe(entries: list[rc.RoutineEntry]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "week_start": entry.week_start.strftime(rc.DATE_FMT),
                "category": entry.category,
                "days": entry.days,
                "score": entry.score,
            }
            for entry in entries
        ]
    )


def compute_totals(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["week_start", "total_score", "grade"])
    totals = (
        df.groupby("week_start", as_index=False)["score"]
        .sum()
        .rename(columns={"score": "total_score"})
    )
    totals["grade"] = totals["total_score"].apply(rc.grade_for_score)
    totals = totals.sort_values("week_start")
    return totals


def safe_rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


# 기록/관리 탭 개선: 주차별 요약 테이블 및 필터링용 데이터 생성
def build_weekly_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "week_start",
                "total_score",
                "grade",
                *rc.CATEGORY_ORDER,
            ]
        )

    df = df.copy()
    df["week_start_dt"] = pd.to_datetime(df["week_start"], format=rc.DATE_FMT)
    pivot = (
        df.pivot_table(
            index=["week_start", "week_start_dt"],
            columns="category",
            values="score",
            aggfunc="sum",
        )
        .reindex(columns=rc.CATEGORY_ORDER)
        .fillna(0)
    )
    totals = (
        df.groupby(["week_start", "week_start_dt"], as_index=False)["score"]
        .sum()
        .rename(columns={"score": "total_score"})
    )
    summary = totals.merge(
        pivot.reset_index(), on=["week_start", "week_start_dt"], how="left"
    )
    summary["grade"] = summary["total_score"].apply(rc.grade_for_score)
    summary = summary.sort_values("week_start_dt", ascending=False)
    return summary[
        ["week_start", "total_score", "grade", *rc.CATEGORY_ORDER, "week_start_dt"]
    ]


# 기록/관리 + 그래프 탭 공통: 주차/기간 필터 적용
def apply_week_filters(df: pd.DataFrame, label_prefix: str) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["week_start_dt"] = pd.to_datetime(df["week_start"], format=rc.DATE_FMT)
    week_options = (
        df.sort_values("week_start_dt", ascending=False)["week_start"].unique().tolist()
    )

    st.markdown("#### 필터")
    col_week, col_period = st.columns([2, 3])
    with col_week:
        selected_week = st.selectbox(
            "주차 선택",
            options=["(전체)"] + week_options,
            key=f"{label_prefix}_week_filter",
        )
    with col_period:
        period_mode = st.radio(
            "기간 선택",
            ["최근 4주", "최근 8주", "최근 12주", "주차 범위"],
            horizontal=True,
            key=f"{label_prefix}_period_mode",
        )

    filtered = df
    if selected_week != "(전체)":
        filtered = filtered[filtered["week_start"] == selected_week]

    if period_mode.startswith("최근"):
        weeks = int(period_mode.replace("최근 ", "").replace("주", ""))
        cutoff = df["week_start_dt"].max() - pd.Timedelta(weeks=weeks - 1)
        filtered = filtered[filtered["week_start_dt"] >= cutoff]
    else:
        range_options = df.sort_values("week_start_dt")["week_start"].unique().tolist()
        if range_options:
            default_range = (range_options[0], range_options[-1])
            start_week, end_week = st.select_slider(
                "주차 범위",
                options=range_options,
                value=default_range,
                key=f"{label_prefix}_range_slider",
            )
            start_dt = pd.to_datetime(start_week, format=rc.DATE_FMT)
            end_dt = pd.to_datetime(end_week, format=rc.DATE_FMT)
            if start_dt > end_dt:
                start_dt, end_dt = end_dt, start_dt
            filtered = filtered[
                (filtered["week_start_dt"] >= start_dt)
                & (filtered["week_start_dt"] <= end_dt)
            ]

    return filtered.drop(columns=["week_start_dt"])


# 기록/관리 탭 개선: 주차별 수정/삭제 입력값 동기화
def sync_edit_inputs(df: pd.DataFrame) -> None:
    selected_week = st.session_state.get("edit_week_select")
    if not selected_week or df.empty:
        return
    week_df = df[df["week_start"] == selected_week]
    for category in rc.CATEGORY_ORDER:
        key_suffix = CATEGORY_KEY_MAP[category]
        key = f"edit_days_{key_suffix}"
        row = week_df[week_df["category"] == category]
        current = int(row["days"].iloc[0]) if not row.empty else 0
        st.session_state[key] = current


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


def generate_plot(entries: list[rc.RoutineEntry], output_path: Path) -> tuple[Path, bool]:
    totals = rc.summarize_by_week(entries)
    category_data = rc.summarize_by_category(entries)
    if not totals and not category_data:
        raise ValueError("시각화할 데이터가 없습니다.")

    try:
        import matplotlib.pyplot as plt  # noqa: F401
    except ModuleNotFoundError:
        svg_path = output_path if output_path.suffix == ".svg" else output_path.with_suffix(".svg")
        plot_scores_svg(totals, category_data, svg_path)
        return svg_path, False

    plot_scores_matplotlib(totals, category_data, output_path)
    return output_path, True


def generate_report(path: Path, plot_path: Path) -> Path:
    entries = rc.load_entries(DATA_PATH)
    totals = rc.summarize_by_week(entries)
    if not totals:
        raise ValueError("등록된 루틴 점수가 없습니다.")

    plot_path, used_matplotlib = generate_plot(entries, plot_path)

    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for week_start in sorted(totals.keys()):
        total_score = totals[week_start]
        grade = rc.grade_for_score(total_score)
        rows.append(
            f"<tr><td>{rc.week_label(week_start)}</td><td>{total_score:.1f}점</td>"
            f"<td>{grade}</td></tr>"
        )

    plot_note = "" if used_matplotlib else "<p>matplotlib 미설치로 SVG 그래프를 사용했습니다.</p>"
    relative_plot_path = Path(os.path.relpath(plot_path, path.parent))
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
    path.write_text(html, encoding="utf-8")
    return path


def main() -> None:
    st.set_page_config(page_title="루틴 점수 트래커", layout="wide")
    st.title("루틴 점수 트래커")
    st.caption("클릭만으로 주간 루틴 점수를 입력하고 추이를 확인하세요.")

    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = date.today()

    tabs = st.tabs(["주간 입력", "기록/관리", "그래프"])

    with tabs[0]:
        st.subheader("주간 점수 입력")
        col_date, col_auto = st.columns([2, 1])
        with col_date:
            selected_date = st.date_input(
                "날짜 선택",
                value=st.session_state["selected_date"],
                key="input_date",
            )
        with col_auto:
            if st.button("이번 주 자동 선택", key="input_auto_this_week"):
                st.session_state["selected_date"] = date.today()
                safe_rerun()

        week_start = rc.week_start_for_day(selected_date)
        st.info(f"선택된 주차 시작일: {week_start.strftime(rc.DATE_FMT)} (월요일 기준)")

        input_cols = st.columns(5)
        inputs: Dict[str, int] = {}
        for idx, category in enumerate(rc.CATEGORY_ORDER):
            with input_cols[idx]:
                if category == "공부시간":
                    inputs[category] = st.number_input(
                        f"{category} (0~84)",
                        min_value=0,
                        max_value=84,
                        value=0,
                        step=1,
                        key=f"input_{category}",
                    )
                else:
                    inputs[category] = st.slider(
                        f"{category} (0~7)",
                        min_value=0,
                        max_value=7,
                        value=0,
                        step=1,
                        key=f"input_{category}",
                    )

        scores = {cat: rc.calculate_score(cat, value) for cat, value in inputs.items()}
        total_score = sum(scores.values())
        grade = rc.grade_for_score(total_score)

        score_cols = st.columns(3)
        with score_cols[0]:
            st.metric("총점", f"{total_score:.1f}점")
        with score_cols[1]:
            st.metric("등급", grade)
        with score_cols[2]:
            st.metric("주차", rc.week_label(week_start))

        st.markdown("#### 카테고리별 점수")
        for category in rc.CATEGORY_ORDER:
            st.write(f"- {category}: {scores[category]:.1f}점")

        if st.button("저장", key="input_save_week"):
            entries = [rc.build_entry(week_start, category, days) for category, days in inputs.items()]
            rc.upsert_week_entries(DATA_PATH, week_start, entries)
            st.success("저장 완료! 주간 점수가 기록되었습니다.")

    with tabs[1]:
        st.subheader("기록 관리")
        entries = rc.load_entries(DATA_PATH)
        df = entries_to_dataframe(entries)
        if df.empty:
            st.info("아직 저장된 데이터가 없습니다.")
        else:
            # edit 탭 키 네임스페이스: edit_week_select, edit_auto_this_week,
            # edit_days_생활리듬/명상/공부시간/운동/핵심키워드, edit_save_week, edit_delete_week
            # 기록/관리 탭 개선: 주차별 요약 + 필터
            filtered_df = apply_week_filters(df, "records")
            weekly_summary = build_weekly_summary(filtered_df)
            if weekly_summary.empty:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
            else:
                summary_view = weekly_summary.drop(columns=["week_start_dt"])
                st.dataframe(summary_view, use_container_width=True)

            st.markdown("#### 주차별 수정/삭제")
            weekly_summary_all = build_weekly_summary(df)
            week_options = (
                weekly_summary_all.sort_values("week_start_dt", ascending=False)[
                    "week_start"
                ]
                .unique()
                .tolist()
            )
            if not week_options:
                st.info("수정/삭제할 주차가 없습니다.")
                st.stop()

            default_week = week_options[0]
            if "edit_week_select" not in st.session_state:
                st.session_state["edit_week_select"] = default_week
                sync_edit_inputs(df)

            col_week, col_auto = st.columns([3, 1])
            with col_week:
                selected_week = st.selectbox(
                    "주차 선택",
                    options=week_options,
                    key="edit_week_select",
                    on_change=sync_edit_inputs,
                    args=(df,),
                )
            with col_auto:
                if st.button("이번 주 자동 선택", key="edit_auto_this_week"):
                    st.session_state["edit_week_select"] = rc.week_start_for_day(
                        date.today()
                    ).strftime(rc.DATE_FMT)
                    sync_edit_inputs(df)
                    safe_rerun()

            edit_cols = st.columns(5)
            updated_values: Dict[str, int] = {}
            for idx, category in enumerate(rc.CATEGORY_ORDER):
                with edit_cols[idx]:
                    key_suffix = CATEGORY_KEY_MAP[category]
                    if category == "공부시간":
                        updated_values[category] = st.number_input(
                            f"{category} 수정",
                            min_value=0,
                            max_value=84,
                            step=1,
                            key=f"edit_days_{key_suffix}",
                        )
                    else:
                        updated_values[category] = st.slider(
                            f"{category} 수정",
                            min_value=0,
                            max_value=7,
                            step=1,
                            key=f"edit_days_{key_suffix}",
                        )

            if st.button("수정 저장", key="edit_save_week"):
                week_start = rc.parse_date(selected_week)
                entries = [
                    rc.build_entry(week_start, category, days)
                    for category, days in updated_values.items()
                ]
                rc.upsert_week_entries(DATA_PATH, week_start, entries)
                st.success("수정 완료! 데이터를 갱신했습니다.")
                safe_rerun()

            if st.button("주차 삭제", key="edit_delete_week"):
                week_start = rc.parse_date(selected_week)
                rc.delete_week_entries(DATA_PATH, week_start)
                st.success("삭제 완료! 선택한 주차 데이터를 제거했습니다.")
                safe_rerun()

    with tabs[2]:
        st.subheader("점수 추이")
        entries = rc.load_entries(DATA_PATH)
        df = entries_to_dataframe(entries)
        if df.empty:
            st.info("그래프를 표시할 데이터가 없습니다.")
        else:
            # graph 탭 키 네임스페이스: charts_week_filter, charts_period_mode, charts_range_slider, graph_report
            # 그래프 탭 개선: 주차 단위 필터 + 개별 카테고리 그래프
            filtered_df = apply_week_filters(df, "charts")
            if filtered_df.empty:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
            else:
                totals = compute_totals(filtered_df)
                st.markdown("#### 총점 추이")
                totals_chart = totals.set_index("week_start")["total_score"]
                totals_chart.index = pd.to_datetime(totals_chart.index, format=rc.DATE_FMT)
                totals_chart = totals_chart.sort_index()
                st.line_chart(totals_chart, height=300)

                st.markdown("#### 카테고리별 추이")
                for category in rc.CATEGORY_ORDER:
                    st.markdown(f"**{category}**")
                    category_df = filtered_df[filtered_df["category"] == category].copy()
                    category_df["week_start_dt"] = pd.to_datetime(
                        category_df["week_start"], format=rc.DATE_FMT
                    )
                    category_df = category_df.sort_values("week_start_dt")
                    series = category_df.set_index("week_start_dt")["score"]
                    st.line_chart(series, height=200)

            st.markdown("#### 리포트 생성")
            if st.button("리포트 생성", key="graph_report"):
                try:
                    report_path = generate_report(REPORT_PATH, PLOT_PATH)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.success(f"리포트를 생성했습니다: {report_path}")


if __name__ == "__main__":
    main()
