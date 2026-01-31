# 예시 실행 로그

아래는 기본 데이터 경로(`data/routines.csv`)로 실행한 예시입니다.

## 초기화

```bash
python3 routine_tracker.py init
```

```
초기화 완료: data/routines.csv
```

## 2024-01-01 주차 입력

```bash
python3 routine_tracker.py add 2024-01-01 "생활리듬" 6
```

```
추가 완료: 2024-01-01 생활리듬 6일 27점
주간 합계: 2024-01-01 (ISO 2024-W01) 27.0점 주의등급
```

```bash
python3 routine_tracker.py add 2024-01-01 "명상/일기쓰기" 5
```

```
추가 완료: 2024-01-01 명상/일기쓰기 5일 13점
주간 합계: 2024-01-01 (ISO 2024-W01) 40.0점 주의등급
```

```bash
python3 routine_tracker.py add 2024-01-01 "공부시간" 4
```

```
추가 완료: 2024-01-01 공부시간 4일 1.43점
주간 합계: 2024-01-01 (ISO 2024-W01) 41.4점 주의등급
```

```bash
python3 routine_tracker.py add 2024-01-01 "운동" 3
```

```
추가 완료: 2024-01-01 운동 3일 7점
주간 합계: 2024-01-01 (ISO 2024-W01) 48.4점 주의등급
```

```bash
python3 routine_tracker.py add 2024-01-01 "핵심키워드" 7
```

```
추가 완료: 2024-01-01 핵심키워드 7일 15점
주간 합계: 2024-01-01 (ISO 2024-W01) 63.4점 D등급(상위 30%)
```

## 주간 총점/등급 요약

```bash
python3 routine_tracker.py summary
```

```
2024-01-01 (ISO 2024-W01)	63.4점	D등급(상위 30%)
```

## 그래프 생성

```bash
python3 routine_tracker.py plot
```

```
matplotlib이 없어 SVG로 저장했습니다: plots/score_trend.svg
```

## 리포트 생성

```bash
python3 routine_tracker.py report
```

```
리포트 저장 완료: reports/weekly_report.html
```
