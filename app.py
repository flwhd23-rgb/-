#!/usr/bin/env python3
"""Streamlit app for routine tracking."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st

import routine_tracker as rt

DATA_PATH = rt.DEFAULT_DATA_PATH


CATEGORY_ORDER = [
    "생활리듬",
    "명상/일기쓰기",
    "공부시간",
    "운동",
    "핵심키워드",
]


def week_start_for_day(day: date) -> date:
    return day - timedelta(days=day.weekday())


def load_dataframe(path: Path) -> pd.DataFrame:
    rt.ensure_csv(path)
    df = pd.read_csv(path)
    if df.empty:
        return pd.DataFrame(columns=["week_start", "category", "days", "score"])
    return df


def save_dataframe(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def build_entry(week_start: date, category: str, days: int) -> Dict[str, object]:
    score = rt.calculate_score(category, days)
    return {
        "week_start": week_start.strftime(rt.DATE_FMT),
        "category": category,
        "days": days,
        "score": score,
    }


def compute_totals(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["week_start", "total_score", "grade"])
    totals = (
        df.groupby("week_start", as_index=False)["score"]
        .sum()
        .rename(columns={"score": "total_score"})
    )
    totals["grade"] = totals["total_score"].apply(rt.grade_for_score)
    totals = totals.sort_values("week_start")
    return totals


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
                key="date_input",
            )
        with col_auto:
            if st.button("이번 주 자동 선택"):
                st.session_state["selected_date"] = date.today()
                st.experimental_rerun()

        week_start = week_start_for_day(selected_date)
        st.info(f"선택된 주차 시작일: {week_start.strftime(rt.DATE_FMT)} (월요일 기준)")

        input_cols = st.columns(5)
        inputs: Dict[str, int] = {}
        for idx, category in enumerate(CATEGORY_ORDER):
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

        scores = {cat: rt.calculate_score(cat, value) for cat, value in inputs.items()}
        total_score = sum(scores.values())
        grade = rt.grade_for_score(total_score)

        st.markdown("### 이번 주 점수 미리보기")
        preview_cols = st.columns(3)
        with preview_cols[0]:
            st.metric("총점", f"{total_score:.1f}점")
        with preview_cols[1]:
            st.metric("등급", grade)
        with preview_cols[2]:
            st.metric("주차", rt.week_label(week_start))

        score_table = pd.DataFrame(
            {
                "카테고리": CATEGORY_ORDER,
                "입력값": [inputs[cat] for cat in CATEGORY_ORDER],
                "점수": [scores[cat] for cat in CATEGORY_ORDER],
            }
        )
        st.dataframe(score_table, use_container_width=True, hide_index=True)

        if st.button("이번 주 기록 저장", type="primary"):
            df = load_dataframe(DATA_PATH)
            week_str = week_start.strftime(rt.DATE_FMT)
            df = df[~((df["week_start"] == week_str) & (df["category"].isin(CATEGORY_ORDER)))]
            new_rows = [build_entry(week_start, cat, inputs[cat]) for cat in CATEGORY_ORDER]
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            save_dataframe(DATA_PATH, df)
            st.success("저장 완료! 기록이 업데이트되었습니다.")

    with tabs[1]:
        st.subheader("주차별 기록 관리")
        df = load_dataframe(DATA_PATH)
        if df.empty:
            st.info("아직 저장된 기록이 없습니다.")
        else:
            df_sorted = df.sort_values(["week_start", "category"])
            st.dataframe(df_sorted, use_container_width=True)

            totals = compute_totals(df_sorted)
            st.markdown("#### 주간 총점/등급")
            st.dataframe(totals, use_container_width=True, hide_index=True)

            week_options = sorted(df_sorted["week_start"].unique())
            selected_week = st.selectbox("수정/삭제할 주차 선택", week_options)
            week_rows = df_sorted[df_sorted["week_start"] == selected_week]

            st.markdown("#### 개별 카테고리 수정")
            edit_col1, edit_col2, edit_col3 = st.columns(3)
            with edit_col1:
                edit_category = st.selectbox("카테고리", CATEGORY_ORDER)
            with edit_col2:
                current_days = week_rows.loc[
                    week_rows["category"] == edit_category, "days"
                ]
                current_value = int(current_days.iloc[0]) if not current_days.empty else 0
                if edit_category == "공부시간":
                    new_days = st.number_input(
                        "새 입력값 (0~84)",
                        min_value=0,
                        max_value=84,
                        value=current_value,
                        step=1,
                        key="edit_days_number",
                    )
                else:
                    new_days = st.slider(
                        "새 입력값 (0~7)",
                        min_value=0,
                        max_value=7,
                        value=current_value,
                        step=1,
                        key="edit_days_slider",
                    )
            with edit_col3:
                st.metric("예상 점수", f"{rt.calculate_score(edit_category, new_days):.1f}점")

            if st.button("선택 항목 수정"):
                mask = (df_sorted["week_start"] == selected_week) & (
                    df_sorted["category"] == edit_category
                )
                df_sorted.loc[mask, "days"] = new_days
                df_sorted.loc[mask, "score"] = rt.calculate_score(edit_category, new_days)
                save_dataframe(DATA_PATH, df_sorted)
                st.success("수정 완료!")
                st.experimental_rerun()

            st.markdown("#### 기록 삭제")
            delete_col1, delete_col2 = st.columns(2)
            with delete_col1:
                delete_category = st.selectbox(
                    "삭제할 카테고리", CATEGORY_ORDER, key="delete_category"
                )
                if st.button("카테고리 삭제"):
                    mask = (df_sorted["week_start"] == selected_week) & (
                        df_sorted["category"] == delete_category
                    )
                    df_sorted = df_sorted[~mask]
                    save_dataframe(DATA_PATH, df_sorted)
                    st.success("선택한 카테고리를 삭제했습니다.")
                    st.experimental_rerun()
            with delete_col2:
                if st.button("주차 전체 삭제", type="secondary"):
                    df_sorted = df_sorted[df_sorted["week_start"] != selected_week]
                    save_dataframe(DATA_PATH, df_sorted)
                    st.success("주차 전체 기록을 삭제했습니다.")
                    st.experimental_rerun()

    with tabs[2]:
        st.subheader("점수 추이")
        df = load_dataframe(DATA_PATH)
        if df.empty:
            st.info("그래프를 표시하려면 먼저 기록을 추가하세요.")
        else:
            totals = compute_totals(df)
            totals["week_start"] = pd.to_datetime(totals["week_start"])
            totals = totals.sort_values("week_start")
            st.markdown("#### 총점 추이")
            st.line_chart(totals.set_index("week_start")["total_score"], height=300)

            st.markdown("#### 카테고리별 추이")
            pivot = df.pivot_table(
                index="week_start", columns="category", values="score", aggfunc="sum"
            ).reindex(columns=CATEGORY_ORDER)
            pivot.index = pd.to_datetime(pivot.index)
            pivot = pivot.sort_index()
            st.line_chart(pivot, height=300)

            st.markdown("#### 리포트 생성")
            if st.button("리포트 생성"):
                args = type(
                    "Args",
                    (),
                    {
                        "data": DATA_PATH,
                        "plot": rt.DEFAULT_PLOT_PATH,
                        "output": rt.DEFAULT_REPORT_PATH,
                    },
                )()
                rt.report_command(args)
                st.success("리포트를 생성했습니다: reports/weekly_report.html")


if __name__ == "__main__":
    main()
