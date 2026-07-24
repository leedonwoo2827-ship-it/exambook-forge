# SQLD 개념 풀 (원본 01회 50문항에서 추출)

자사 회차 재집필의 **개념 근거**. 각 항목은 원본 문항(`derived_from`)·전형 난이도·키워드를 담는다.
회차마다 이 풀에서 개념을 뽑아 **표면을 새로 써** 문항을 만든다(같은 개념, 다른 문제).
과목 비율은 1과목 10 : 2과목 40 유지.

---

## 1과목. 데이터 모델링의 이해 (10문항)

| # | 개념 | derived_from | 전형 난이도 | 키워드(tags) |
|---|---|---|---|---|
| M1 | 분산 데이터베이스 장단점(가용성·관리·보안·비용) | 01-01 | 중 | 분산 데이터베이스, 가용성, 투명성 |
| M2 | 데이터 모델링 3관점 + CRUD 매트릭스 | 01-02 | 하 | 데이터 모델링 관점, CRUD 매트릭스 |
| M3 | 속성의 종류(단일·복합·다중값) | 01-04 | 하 | 속성, 복합 속성, 다중값 속성 |
| M4 | 3층 스키마(외부·개념·내부) | 01-05 | 하 | 3층 스키마, ANSI/SPARC, 논리적/물리적 독립성 |
| M5 | 정규화/반정규화 목적·기법 | 01-06 | 중 | 반정규화, 정규화, 성능, 중복 |
| M6 | 슈퍼타입/서브타입 변환(OneToOne·Plus·Single) | 01-07 | 중 | 슈퍼타입, 서브타입, 트랜잭션 |
| M7 | 카디널리티·선택도(선택도×전체레코드수) | 01-08 | 중 | 카디널리티, 선택도, 통계정보 |
| M8 | 정규화 단계(1~4NF, 이행함수종속=3NF) | 01-09 | 하 | 정규화, 제3정규형, 이행함수종속 |
| M9 | ERD 관계 해석(식별·비식별, Optional/Mandatory, 카디널리티) | 01-10 | 중 | ERD, 관계, 식별자관계, 선택참여 |
| M10 | 키의 종류(기본·후보·슈퍼·외래키) / 식별자(내부·외부·주·보조·인조·본질) | 01-45, 01-49 | 하~중 | 후보키, 슈퍼키, 외래키, 식별자 |

> 1과목 보충 개념(회차 변주용): 엔터티/속성/관계 정의, 도메인, 관계차수, 식별자 분류, 정규화 이상현상(삽입/갱신/삭제 이상).

---

## 2과목. SQL 기본 및 활용 (40문항)

### (A) SQL 기본 · DDL/DCL/TCL

| # | 개념 | derived_from | 난이도 | tags |
|---|---|---|---|---|
| S1 | SQL 분류(DDL/DML/DCL/TCL) 정의 | 01-26 | 하 | SQL 분류, DDL, DML, DCL, TCL |
| S2 | DDL 아닌 것(COMMIT=TCL) | 01-12 | 하 | DDL, TCL, COMMIT |
| S3 | ALTER MODIFY(칼럼 속성 변경) | 01-11 | 중 | ALTER, MODIFY, 제약조건 |
| S4 | ALTER ADD(칼럼 추가) | 01-13 | 중 | ALTER, ADD COLUMN |
| S5 | DROP TABLE CASCADE CONSTRAINT(DBMS별 차이) | 01-25 | 상 | DROP, CASCADE CONSTRAINT, 참조무결성 |
| S6 | DELETE vs TRUNCATE vs DROP(COMMIT 여부) | 01-03 | 중 | DELETE, TRUNCATE, DROP, DDL |
| S7 | GRANT/REVOKE, WITH GRANT OPTION 연쇄 취소 | 01-23 | 상 | DCL, GRANT, REVOKE, WITH GRANT OPTION |
| S8 | TCL: COMMIT/ROLLBACK/SAVEPOINT(ROLLBACK TO) | 01-14 | 상 | TCL, SAVEPOINT, ROLLBACK TO |
| S9 | INSERT 데이터타입/형변환 에러(TO_DATE) | 01-35 | 중 | INSERT, 데이터타입, TO_DATE, 형변환 |

### (B) 함수 · NULL · 정렬

| # | 개념 | derived_from | 난이도 | tags |
|---|---|---|---|---|
| S10 | 단일행 함수(ROUND 등) | 01-47 | 하 | 단일행 함수, ROUND, 반올림 |
| S11 | NULL 처리 NVL/DECODE/CASE, `=null` vs IS NULL | 01-33 | 상 | NULL, NVL, DECODE, CASE, IS NULL |
| S12 | 집계함수와 NULL(COUNT 칼럼 NULL 제외) | 01-46 | 중 | COUNT, SUM, NULL, 집계함수 |
| S13 | 집계함수 조합(MAX/MIN/SUM 빈칸) | 01-37 | 중 | MAX, MIN, SUM, 집계 |
| S14 | 정규표현식 시작/끝(^ $) | 01-24 | 하 | 정규표현식, 앵커 |
| S15 | ORDER BY 다중정렬·NULL 정렬 | 01-34, 01-36 | 중~상 | ORDER BY, DESC, NULL 정렬 |
| S16 | SQL 논리적 실행순서(FROM→WHERE→GROUP BY→HAVING→SELECT→ORDER BY) | 01-21 | 중 | 실행순서, HAVING |

### (C) GROUP BY · 집계 확장

| # | 개념 | derived_from | 난이도 | tags |
|---|---|---|---|---|
| S17 | GROUP BY + COUNT(DISTINCT) | 01-28 | 중 | GROUP BY, COUNT DISTINCT |
| S18 | ROLLUP(계층적 소계) | 01-38 | 중 | ROLLUP, 소계, GROUP BY 확장 |
| S19 | CUBE(모든 결합 집계) | 01-41 | 중 | CUBE, 다차원 집계 |
| S20 | CUBE=GROUPING SETS 동치 변환 | 01-15 | 중 | GROUPING SETS, CUBE |

### (D) WINDOW 함수

| # | 개념 | derived_from | 난이도 | tags |
|---|---|---|---|---|
| S21 | 순위 함수 RANK/DENSE_RANK/ROW_NUMBER 구분 | 01-29 | 중 | WINDOW, DENSE_RANK, 순위함수 |
| S22 | 윈도우 프레임 ROWS/RANGE BETWEEN 유효성 | 01-30 | 상 | 윈도우 프레임, RANGE, UNBOUNDED PRECEDING |
| S23 | PARTITION/프레임 해석 | 01-31 | 상 | PARTITION BY, 프레임, RANGE |
| S24 | RANGE 값 기준 범위 카운트 | 01-48 | 상 | RANGE BETWEEN, COUNT OVER |

### (E) 계층형 쿼리

| # | 개념 | derived_from | 난이도 | tags |
|---|---|---|---|---|
| S25 | 계층 쿼리 설명(PRIOR 순/역방향, CONNECT BY) | 01-17 | 중 | 계층형 쿼리, CONNECT BY, PRIOR |
| S26 | START WITH / CONNECT BY PRIOR 빈칸 | 01-18 | 상 | START WITH, CONNECT BY PRIOR, 순방향 |
| S27 | 상위(부모) 탐색 계층 쿼리 | 01-19 | 상 | 역방향 전개, WHERE 후필터 |
| S28 | 계층 쿼리 내장함수(LEVEL/SYS_CONNECT_BY_PATH/CONNECT_BY_ROOT/ISLEAF) | 01-20 | 중 | LEVEL, SYS_CONNECT_BY_PATH, CONNECT_BY_ROOT |

### (F) 집합 연산 · 조인 · 서브쿼리

| # | 개념 | derived_from | 난이도 | tags |
|---|---|---|---|---|
| S29 | 집합연산 UNION/UNION ALL/MINUS/INTERSECT 결과 행 수 | 01-16 | 중 | 집합 연산자, UNION, MINUS |
| S30 | 집합연산 + GROUP BY 조합 동치 | 01-32 | 상 | UNION, GROUP BY, MAX/MIN |
| S31 | 조인 종류별 결과 건수(INNER/LEFT/RIGHT/FULL/CROSS) | 01-40 | 상 | 조인, OUTER JOIN, CROSS JOIN, 건수 |
| S32 | CROSS JOIN(카티션 곱) | 01-42 | 중 | CROSS JOIN, 카티션곱 |
| S33 | Oracle(+) ↔ ANSI OUTER JOIN 변환(RIGHT) | 01-43 | 중 | Oracle 조인, ANSI, RIGHT OUTER JOIN |
| S34 | Oracle(+) ↔ ANSI OUTER JOIN 변환(LEFT) | 01-44 | 중 | Oracle 조인, ANSI, LEFT OUTER JOIN |
| S35 | 등가조인 → ANSI INNER JOIN 변환 | 01-39 | 중 | INNER JOIN, ANSI 표준, 등가조인 |
| S36 | 다중컬럼 IN 조건 등가/비등가 | 01-22 | 상 | 다중컬럼 IN, WHERE 조건 |
| S37 | IN ↔ EXISTS 상관 서브쿼리 변환 | 01-50 | 상 | 서브쿼리, EXISTS, 상관 서브쿼리 |
| S38 | 집계함수 NVL 조합 결과 비교 | 01-27 | 상 | AVG, SUM, COUNT, NVL |

> 2과목 보충 개념(회차 변주용): DML(INSERT/UPDATE/DELETE/MERGE), 뷰, 인덱스 기초, 문자/숫자/날짜 함수(SUBSTR/INSTR/CONCAT/CASE/COALESCE), TOP-N/ROWNUM, 스칼라 서브쿼리, HAVING, DISTINCT.

---

## 회차 배치 가이드(순서 변경)
- 원본은 M1..M10 → S(11..50) 순서이지만, 자사 회차는 개념 순서를 **섞어** 배치한다.
  예) m01 2과목은 [조인→WINDOW→계층→집합→NULL→DDL...] 처럼 원본과 다른 흐름.
- 단, **과목 경계는 유지**: 1~10번 = 1과목, 11~50번 = 2과목 (실전 시험 구성).
- 3회차가 서로 다르게 느껴지도록, 같은 개념이라도 회차마다 다른 하위주제/데이터/보기로 변주.
