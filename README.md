# Routine Score Tracker

일주일 단위로 루틴 수행 일수를 기록하고, 100점 만점의 점수 추이를
그래프로 확인하는 CLI 도구입니다.

## 점수 기준

| 항목 | 만점 |
| --- | --- |
| 생활리듬 | 30점 |
| 명상/일기쓰기 | 15점 |
| 공부시간 | 30점 |
| 운동 | 10점 |
| 핵심키워드 | 15점 |
| **총합** | **100점** |

입력한 수행 일수를 기반으로 점수를 환산합니다. `공부시간`은 0~84 범위를 사용하며,
나머지는 0~7 범위를 사용합니다.

- 공부시간: `입력값 / 84 * 30점`
- 생활리듬: 7→30, 6→27, 5→25, 4→15, 3→10, 2→5, 1→3, 0→0
- 명상/일기쓰기: 7→15, 6→14, 5→13, 4→10, 3→8, 2→6, 1→3, 0→0
- 운동: 7→10, 6→9.5, 5→9, 4→8, 3→7, 2→4, 1→2, 0→0
- 핵심키워드: 7→15, 6→14, 5→12, 4→10, 3→8, 2→4, 1→2, 0→0

## 등급 기준

- 95점 이상: SS등급(상위 0.1%)
- 90~94점: S등급(상위 1%)
- 85~89점: A등급(상위 5%)
- 75~84점: B등급(상위 10%)
- 65~74점: C등급(상위 20%)
- 55~64점: D등급(상위 30%)
- 0~54점: 주의등급

## 빠른 시작

```bash
python routine_tracker.py init
python routine_tracker.py add 2024-01-01 생활리듬 6
python routine_tracker.py add 2024-01-01 명상/일기쓰기 5
python routine_tracker.py add 2024-01-01 공부시간 4
python routine_tracker.py add 2024-01-01 운동 3
python routine_tracker.py add 2024-01-01 핵심키워드 7
python routine_tracker.py list
python routine_tracker.py summary
python routine_tracker.py report
python routine_tracker.py plot
```

`plots/score_trend.png` 파일이 생성됩니다.

## GUI 앱 (Streamlit)

코딩을 모르는 사용자도 클릭만으로 입력할 수 있는 시각적 앱이 포함되어 있습니다.

```bash
python3 -m streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 확인할 수 있습니다. macOS에서
더블클릭 실행 방법은 `INSTALL_MAC.md`를 참고하세요.

## 주요 개념

- **입력 범위:** 0 ~ 7일 (공부시간은 0 ~ 84)
- **기본 데이터 위치:** `data/routines.csv`
- **그래프 출력 위치:** `plots/score_trend.png` (matplotlib 미설치 시 `.svg`로 저장)
- **리포트 출력 위치:** `reports/weekly_report.html`

## 명령어 요약

| 명령어 | 설명 |
| --- | --- |
| `init` | CSV 파일을 초기화합니다. |
| `add` | 주간 루틴 점수를 추가합니다. |
| `list` | 저장된 점수를 확인합니다. |
| `summary` | 주간 총점과 등급을 표시합니다. |
| `plot` | 총합/카테고리 점수 그래프를 생성합니다. (matplotlib 없으면 SVG 생성) |
| `report` | 총합/등급과 그래프 추이를 탭으로 보여주는 HTML을 생성합니다. |

## 카테고리별 추이 확인 (총합 제외)

```bash
python routine_tracker.py plot --per-category
```

## 총합만 추이 확인

```bash
python routine_tracker.py plot --total-only
```

## 총합/카테고리 전체 추이 + 리포트

```bash
python routine_tracker.py plot
python routine_tracker.py report
```

리포트 HTML을 열면 `총합/등급` 탭에서 주간 점수를 확인하고, `그래프 추이` 탭을
눌러 언제든지 추이 그래프로 이동할 수 있습니다.

## 데이터 포맷

CSV는 다음 헤더를 사용합니다.

```
week_start,category,days,score
```
