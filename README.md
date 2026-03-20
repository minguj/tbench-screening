# log-incident-reconciliation

## 개요 (Overview)

이 저장소는 **T-bench 스크리닝 과제**로, AI 에이전트의 **다중 로그 파싱, 정규화, 그리고 결정적 집계 능력**을 평가하기 위해 설계되었습니다.

이 과제는 단순한 로그 파싱을 넘어 다음과 같은 능력을 요구합니다:

- 서로 다른 로그 포맷 처리
- 여러 소스 간 incident 병합
- 시간 정보의 UTC 정규화
- 항상 동일한 결과를 보장하는 deterministic 처리

---

## 과제 목표 (Task Objective)

에이전트는 여러 서비스에서 생성된 로그 파일을 분석하여, incident 단위로 정리된 **결정적(JSON) 리포트**를 생성해야 합니다.

### 주요 요구사항

- 여러 로그 파일 읽기
- 서로 다른 로그 포맷 파싱
- `ERROR`, `WARN` 로그만 추출
- 잘못된 형식의 로그는 무시
- `incident_id`가 없는 로그는 무시
- 모든 시간은 **UTC ISO 8601 형식으로 변환**
- 동일한 `incident_id`를 하나로 병합
- 항상 동일한 결과 생성 (deterministic)

---

## 입력 데이터 (Input Data)

컨테이너 내부 경로:

/app/app.log  
/app/worker.log  
/app/gateway.log  

각 로그 파일은 서로 다른 형식을 가지고 있으며, 이를 모두 처리해야 합니다.

---

## 출력 결과 (Output Specification)

결과는 아래 경로에 생성되어야 합니다:

/app/report.json  

### 출력 구조 예시

{
  "total_incidents": 0,
  "by_service": {
    "service_name": 0
  },
  "incidents": [
    {
      "incident_id": "INC001",
      "services": ["auth", "billing"],
      "count": 3,
      "severity": "ERROR",
      "first_seen": "2026-03-15T01:16:01Z",
      "last_seen": "2026-03-15T01:18:20Z",
      "duration_seconds": 139
    }
  ]
}

---

## 결정성 규칙 (Deterministic Rules)

동일한 입력은 항상 동일한 출력이 생성되어야 합니다.

### 필수 규칙

- `ERROR`, `WARN` 로그만 포함
- 파싱 불가능한 로그는 제외
- `incident_id`가 없거나 유효하지 않으면 제외
- 모든 소스에서 동일 incident 병합

### 집계 규칙

- severity: `ERROR > WARN`
- count: 전체 발생 횟수
- first_seen: 가장 빠른 시간
- last_seen: 가장 늦은 시간
- duration_seconds: last - first

### 정렬 규칙

- services: 중복 제거 후 알파벳 정렬
- incidents: incident_id 기준 오름차순
- by_service: 서비스명 기준 정렬

---

## Edge Case (중요)

이 과제는 다음과 같은 edge case를 포함합니다:

- 동일 incident에 대한 중복 로그
- 서로 다른 로그 포맷 혼합
- 잘못된 incident_id
- 파싱 불가능한 로그 라인
- 시간대 정규화 오류 가능성
- 여러 서비스에 걸친 incident

---

## 검증 (Verification)

테스트는 다음을 검증합니다:

- expected 결과와 완전 일치
- JSON 구조 정확성
- deterministic 정렬
- cross-source 병합 정확성
- UTC 시간 정규화
- severity 집계 정확성
- 중복 카운트 정확성
- 잘못된 로그 제외 여부

---

## 프로젝트 구조 (Project Structure)

log-incident-reconciliation/
├── instruction.md
├── task.toml
├── environment/
│   ├── Dockerfile
│   ├── app.log
│   ├── worker.log
│   ├── gateway.log
│   └── solution_impl.py
├── solution/
│   └── solve.sh
└── tests/
    ├── test.sh
    └── test_outputs.py

---

## 실행 방법 (How to Run)

harbor run -a oracle -p log-incident-reconciliation

---

## 참고 사항 (Notes)

- 결과는 반드시 `/app/report.json`에 생성되어야 합니다
- 평가는 오직 출력 결과로만 진행됩니다
- 외부 API 또는 네트워크 사용 불가
- 단순 파싱이 아닌 **데이터 정규화 및 추론 능력**을 평가합니다

---

## 핵심 난이도 (Key Challenge)

이 과제는 단순해 보이지만 다음 요소 때문에 난이도가 존재합니다:

- 다양한 로그 포맷 처리
- 여러 파일 간 데이터 병합
- 시간대 정규화
- 엄격한 deterministic 요구사항

부분적으로 맞는 구현은 테스트를 통과하지 못합니다.

---

## 목적 (Purpose)

이 과제는 AI가 다음 능력을 갖추었는지 평가합니다:

- 여러 데이터 소스를 종합적으로 처리하는 능력
- 정규화 및 집계 로직 구현 능력
- 재현 가능한 deterministic 결과 생성 능력

---

## 라이선스 (License)

본 저장소는 T-bench 스크리닝 용도로 제공됩니다.
