# CoinRich: 코인 자동 매매 프로그램

## 🧠 프로젝트 개요

**CoinRich**는 업비트(Upbit) 거래소를 대상으로, 고빈도 스캘핑(Scalping) 전략을 자동으로 수행하는 암호화폐 트레이딩 봇입니다.
실시간 마켓 데이터를 결합하여, 빠르고 정밀한 진입/청산을 목표로 합니다. (AI 판단 로직은 현재 제외)
프로젝트는 **TDD(Test-Driven Development)** 방식으로 설계와 검증을 병행하며 개발됩니다.

**Upbit API 문서**: [https://docs.upbit.com/kr/reference](https://docs.upbit.com/kr/reference)

---

## 📋 현재 개발 진행 상황

### 업비트 API 연동 기능 구현 (TDD 방식)

- ✅ **프로젝트 기본 구조 설정**: TDD 방식의 폴더 구조 및 환경 구성
- ✅ **API 인증 구현**: JWT 토큰 기반 인증 처리 모듈 개발 및 테스트
- ✅ **마켓 정보 조회 API**: 거래 가능한 종목 목록 조회 기능 구현
- ✅ **현재가(Ticker) 조회 API**: 단일/복수 종목 현재가 조회 기능 구현
- ✅ **초봉(Second Candle) 조회 API**: 초 단위 캔들 데이터 조회 기능 구현
- ✅ **분봉(Minute Candle) 조회 API**: 분 단위 캔들 데이터 조회 기능 구현
- ✅ **데이터 모델링**: Pydantic을 활용한 응답 데이터 모델 구현
  - 마켓(Market) 모델
  - 현재가(Ticker) 모델
  - 캔들(Candle) 모델 - 초봉, 분봉 등 다양한 시간 단위 구현
- ✅ **단위 테스트**: 각 API 기능에 대한 테스트 코드 작성 및 검증
- ✅ **테스트 유틸리티**: 실행 가능한 테스트 스크립트 구현

### 개발 환경 구성

- ✅ **의존성 관리**: requirements.txt 작성
- ✅ **환경 변수 설정**: .env 파일을 통한 API 키 관리
- ✅ **테스트 프레임워크**: pytest, responses를 활용한 테스트 환경 구성
- ✅ **IDE 통합**: VSCode 디버깅 설정 (launch.json)

### 다음 개발 예정 항목

- [ ] 일/주/월 캔들 데이터 조회 API 구현
- [ ] 호가창(Orderbook) 조회 API 구현
- [ ] WebSocket 연결을 통한 실시간 데이터 수신 구현
- [ ] 주문 생성/조회/취소 API 구현
- [ ] 계좌 잔고 조회 API 구현
- [ ] 종목 선정 및 스크리닝 알고리즘 개발
- [ ] 거래 전략 구현 및 백테스트 프레임워크 구축

---

## 🚀 주요 목표

- **스캘핑 전략**에 최적화된 거래 시그널 생성
- 실시간 **업비트 API 연동** (호가창, 체결 정보 등)
- **로컬 NoSQL DB (TinyDB)**를 이용한 빠른 상태 저장 및 로깅
- 거래 **백테스트 모듈** 구축
- **테스트 주도 개발**을 통한 안정성 확보
- Discord Webhook을 통한 실시간 알림
- 백테스트 → 모의투자 → 실계좌 순의 안전한 전환 흐름
- 추후 **웹 대시보드** 및 모니터링 기능 확장 가능성 고려

---

## 📈 핵심 전략 및 실행 계획

### 1. 권장 핵심 전략: 적응형 변동성 돌파 + RSI 필터 + 트레일링 스탑

| 요소             | 목적                     | 요약 로직                                                                 |
| ---------------- | ------------------------ | ------------------------------------------------------------------------- |
| **변동성 돌파**  | 강한 시세 분출 초입 포착 | 전일 고가‑저가 범위를 K계수로 스케일 → 가격이 목표가(Target) 상향 돌파 시 매수 |
| **RSI 필터**     | 거짓 돌파 및 과열 회피   | 3 분봉 RSI < 65(과열 아님) 조건에서만 진입                                  |
| **트레일링 스탑** | 이익 보호·손실 제한    | 진입 후 +0.6 % 이상 시 손절선을 진입가 + 0.2 %로 상승                        |
| **데일리 손실 한도** | 계좌 보호                | 하루 누적 손실 ‑1 % 도달 시 당일 거래 중단                                  |

### 2. 위험 관리

- **API Rate Limit 초과**: 30 초 쿨다운 후 재시도(최대 3회), 이후 전략 중단
- **주문 실패 누적**: 1시간 내 주문 실패 5회 이상 시 모든 포지션 강제 청산 및 전략 중단
- **최근 승률 저하**: 최근 100 트레이드 승률 ≤ 45%일 경우 파라미터 자동 재최적화 또는 전략 일시 중단
- **API 키 보안**: 고정 IP + 환경변수로 관리
- **일일 손실 한도**: -1.0% 초과 시 시스템 중단 (다음날 자정 또는 수동 재활성화)
- **이상 거래 패턴 감지 (옵션)**:
    - 시세 급변: 1분 내 ±5% 이상 변동 시 전략 중단
    - WebSocket 장애: 재연결 시도 및 중단 알림
    - 슬리피지: 진입가 ↔ 체결가 차이 ±1% 초과 시 경고

#### 리스크 상태 구조 예시 (JSON)
```json
{
  "daily_loss_percent": -0.83,
  "total_loss_limit_hit": false,
  "rate_limit_cooldown": false,
  "consecutive_failures": 2,
  "win_rate_100": 48.5,
  "strategy_disabled": false
}
```

### 3. 단계별 실행 로드맵

1.  **백테스트 & 파라미터 튜닝**: 2023‑01 ~ 2025‑04 1분봉 데이터 Walk‑Forward Analysis
2.  **모의투자(Paper Trading)**: 2주간, 하루 수익 0.3% 이상 달성 시 실계좌 전환
3.  **소액 실계좌**: 손실 ‑1% 도달 시 즉시 모드 전환, 4주 수익 ≥ 5% 달성 시 규모 확대
4.  **전략 다변화**: 횡보장에는 Grid Bot, 급등장에는 EMA Cross 자동 전환
5.  **머신러닝 보조(옵션, 현재 제외)**: LSTM + LightGBM 예측 확률 55% 이상일 때 포지션 가중치 조절

### 4. 시장 상태 판단 (15분봉 기반)

- **판단 기준**: 15분봉 EMA(9), EMA(21), RSI(14) 지표 사용
- **판단 주기**: 1분마다 최신 캔들과 실시간 가격을 반영하여 재평가
- **시장 구분 로직**:
    - `상승장 (Bull)`: EMA(9) > EMA(21) && RSI(14) > 60
    - `하락장 (Bear)`: EMA(9) < EMA(21) && RSI(14) < 40
    - `횡보장 (Sideway)`: 그 외 조건
- **활용 방식**: 상승장일 경우에만 변동성 돌파 전략 활성화
- **보완 필터 (정밀도 향상)**:
    - ADX(14) < 20 (추세 없음) 시 전략 발동 억제
    - RSI(5)와 RSI(14) 병렬 확인
    - 최근 3봉 중 고점 갱신, 볼린저 밴드 폭 확대 등 캔들 패턴 보조 활용
    - 시장 상태 연속 3회 동일 시에만 전략 발동 (잦은 상태 변경으로 인한 오진 방지)

### 5. 진입/청산 로직

#### 가. 진입 판단 (멀티 타임프레임 활용)

| 기능                 | 봉 기준        | 사용 예                                  |
| -------------------- | -------------- | ---------------------------------------- |
| **돌파 조건 판단**   | 1분봉          | 현재가가 전일 고점 + α 돌파 확인         |
| **RSI 필터링**       | 3분봉 또는 5분봉 | 과열 여부 판단 (예: RSI < 65)            |
| **거래량 급등 탐지** | 1분봉          | 직전 평균 대비 2배 이상 거래량 증가        |
| **ADX 보조 지표**    | 5분봉          | 추세 강도 판단 (ADX > 20)                |
| **시장 추세 판단**   | 15분봉         | 상승/하락/횡보장 구분 (시장 상태 판단과 연동) |

- 주로 **1분봉**으로 시세 추적, **3/5분봉**은 보조 필터로 사용.

#### 나. 매수 실행

- **주문 방식**: 시장가 주문
- **수량 계산**: 초기 고정 금액 (예: 50,000원) → 향후 잔액 비율(예: 20%)로 전환 검토
- **주문 조건**: 업비트 최소 주문 금액 충족, 주문 실패 시 최대 3회 재시도 (1초 간격)
- **중복 방지**: 동일 종목 포지션 보유 시 진입 차단
- **기록**: 로컬 DB 및 Discord 알림

#### 다. 청산 조건 (1분마다 평가)

| 조건 유형         | 설명                                                               | 우선순위 |
| ----------------- | ------------------------------------------------------------------ | -------- |
| ✅ 트레일링 스탑  | +0.6% 수익 도달 후, 가격이 진입가 +0.2% 이하로 하락 시 청산          | 1        |
| ✅ 익절 조건 (TP) | 수익률 +0.6% 이상 도달 시 익절                                       | 2        |
| ✅ 손절 조건 (SL) | 수익률 -0.4% 이하 도달 시 손절                                       | 3        |

- **평가 주기**: 진입 후 1초 또는 3초 (스캘핑 특성상 빠른 반응, API Rate Limit 고려)
- **사용 데이터**: 실시간 가격 기반 (캔들/지표 미사용)

#### 라. 포지션 상태 구조 예시 (Python Dict)
```python
{
  "symbol": "KRW-BTC",
  "entry_price": 97300000,
  "max_price": 97900000, # 진입 후 최고가 (트레일링 스탑용)
  "entry_time": "2025-05-09T12:22:11",
  "strategy": "BreakoutRSI",
  "stop_loss": 96900000, # 동적 손절 기준 가격
  "trailing_active": True # 익절 조건 만족 후 트레일링 활성화 여부
}
```

#### 마. 매도 실행

- **주문 방식**: 시장가 매도 (보유 포지션 전량)
- **실패 처리**: 주문 실패 시 최대 3회 재시도 (1초 간격)
- **기록**: `TradeLog` DB 저장, Discord 알림 (체결가, 수익률, 사유 등)
- **포지션 정리**: 매도 완료 후 메모리 및 DB에서 해당 포지션 제거

#### 매도 기록 예시 (JSON)
```json
{
  "symbol": "KRW-BTC",
  "entry_price": 97300000,
  "exit_price": 97800000,
  "entry_time": "2025-05-09T12:22:11",
  "exit_time": "2025-05-09T12:34:02",
  "strategy": "BreakoutRSI",
  "pnl_percent": 0.51,
  "reason": "TRAILING_STOP", # 또는 "TAKE_PROFIT", "STOP_LOSS"
  "order_id": "upbit:O987654321"
}
```

#### Discord 알림 예시 (매도)
```
[매도 완료] KRW-BTC | 전략: BreakoutRSI | +0.51% | 진입가 97,300,000 → 청산가 97,800,000 | 사유: TRAILING_STOP | 12:34:02
```

### 6. 코인 선정 전략

- **초기 대상**: BTC (비트코인) 단일 종목으로 안정화 우선
- **향후 확장**:
    - 업비트 KRW 마켓 거래대금 상위 10종 후보군
    - 자동 스크리닝 기준 (매일 오전):
        - 거래대금 ≥ 100억 원
        - 24시간 변동률 ≥ ±3%
        - 평균 호가 스프레드 < 0.2%
    - 상위 3개 종목 자동 선택하여 동일 전략 병렬 적용
- **수동 지정**: 옵션 지원

---

## 🛠️ 시스템 아키텍처

### 1. 기술 스택

| 항목         | 내용                                       |
| -------------- | ------------------------------------------ |
| 언어         | Python 3.10+                               |
| 거래소 API   | 업비트 REST + WebSocket                    |
| DB           | TinyDB (로컬 JSON 기반 키-값 저장)         |
| 로깅/알림    | 콘솔 + 텍스트 파일 + Discord Webhook        |
| 테스트       | pytest, coverage, mocker, faker            |
| 코드 스타일  | Black, isort, flake8                       |
| 실행 환경    | 로컬 Python 환경                           |

### 2. 시스템 구성도 (High-Level Architecture)

CoinRich 시스템은 다음과 같은 주요 컴포넌트들로 구성되며, 각 컴포넌트는 유기적으로 상호작용하여 자동 매매 로직을 수행합니다.

1.  **실행 엔진 (Main Engine - `core/main.py`)**
    *   **역할**: 전체 시스템의 실행 흐름을 제어하고, 설정 파일을 로드하며, 각 모듈의 초기화 및 주기적인 작업 실행을 담당합니다. 1분 주기의 메인 루프를 관리합니다.
    *   **상호작용**: `Configuration Manager`, `Upbit Service`, `Strategy Evaluator`, `Order Executor`, `Position Manager`, `Risk Manager`, `Database Handler`, `Logging & Notification Service`.

2.  **설정 관리자 (Configuration Manager - `config.yaml` 또는 유사 파일, `.env`)**
    *   **역할**: 시스템 운영에 필요한 모든 설정값(API 키, 전략 파라미터, DB 경로, 로그 레벨 등)을 관리합니다.
    *   **상호작용**: `Main Engine`에 의해 로드되어 전체 모듈에서 참조됩니다.

3.  **업비트 연동 서비스 (Upbit Service - `service/`)**
    *   **역할**: 업비트 API(REST, WebSocket)와의 모든 통신을 담당합니다. 실시간 시세 수신, 과거 데이터 조회(캔들), 주문 실행(매수/매도), 주문 상태 확인 등의 기능을 수행합니다.
    *   **상호작용**: `Main Engine`, `Strategy Evaluator`, `Order Executor`.

4.  **전략 평가기 (Strategy Evaluator - `strategy/`)**
    *   **역할**: 정의된 매매 전략(예: 변동성 돌파 + RSI + 트레일링 스탑)에 따라 시장 데이터를 분석하여 진입 및 청산 시그널을 생성합니다.
    *   **상호작용**: `Upbit Service` (시장 데이터 획득), `Position Manager` (현재 포지션 상태 참조), `Configuration Manager` (전략 파라미터 로드).

5.  **주문 실행기 (Order Executor - `core/` 또는 `service/` 내 통합)**
    *   **역할**: `Strategy Evaluator`로부터 매수/매도 시그널을 받아 실제 주문을 업비트에 전송하고, 체결 결과를 확인하며, 주문 실패 시 재시도 로직을 수행합니다.
    *   **상호작용**: `Upbit Service`, `Position Manager`, `Database Handler` (거래 기록), `Logging & Notification Service`.

6.  **포지션 관리자 (Position Manager - `core/` 내 통합)**
    *   **역할**: 현재 보유 중인 포지션의 상태(진입 가격, 수량, 현재가, 평가손익, 트레일링 스탑 상태 등)를 실시간으로 추적하고 관리합니다.
    *   **상호작용**: `Order Executor` (포지션 생성/종료), `Strategy Evaluator` (청산 조건 판단), `Database Handler` (상태 지속성).

7.  **리스크 관리자 (Risk Manager - `core/` 및 `strategy/` 내 통합)**
    *   **역할**: 일일 손실 한도, API Rate Limit, 연속 주문 실패 등 사전에 정의된 위험 관리 규칙을 모니터링하고, 조건 충족 시 거래 중단 등의 조치를 수행합니다.
    *   **상호작용**: `Main Engine`, `Order Executor`.

8.  **데이터베이스 핸들러 (Database Handler - `db/` with TinyDB)**
    *   **역할**: 매매 기록(`TradeLog`), (필요시) 시장 스냅샷(`MarketSnapshot`), (필요시) 시스템 설정(`Settings`), 포지션 상태 등을 로컬 DB에 저장하고 조회합니다.
    *   **상호작용**: `Main Engine`, `Order Executor`, `Position Manager`.

9.  **로깅 및 알림 서비스 (Logging & Notification Service - `utils/` 또는 통합)**
    *   **역할**: 시스템의 주요 동작 및 오류 상황을 콘솔과 파일에 기록하고, 중요한 이벤트(매매 체결, 오류 발생, 시스템 중단 등)를 Discord를 통해 사용자에게 알립니다.
    *   **상호작용**: 시스템 전반의 모든 주요 모듈.

**간략한 시스템 흐름:**
```text
[스케줄러/사용자 실행]
       |
       V
[Main Engine (`main.py`, `core/`)] ---------------------> [Configuration Manager (`config.yaml`, `.env`)]
   |   A
   |   | (주기적 실행)
   |   V
   | [Upbit Service (`service/`)] <----------------------> [업비트 API (시세, 주문)]
   |   | (시장 데이터)
   |   V
   | [Strategy Evaluator (`strategy/`)] ---- (포지션 정보) ---> [Position Manager (`core/`)]
   |   | (매매 신호)                                          A         | (DB RW)
   |   V                                                      |         V
   | [Order Executor (`core/` 또는 `service/`)] --------------+------> [Database Handler (`db/`)]
   |   | (주문 결과, 상태 변경)                                          (거래/상태 기록)
   |   V
   | [Risk Manager (`core/`, `strategy/`)]
   |   (위험 감지 시 제어)
   V
[Logging & Notification Service (`utils/`)] <---------------- (시스템 전반의 이벤트)
   (로그 파일, Discord 알림)
```

### 3. 디렉토리 구조 (예정)

```
coinrich/
├── core/               # 전략 실행 엔진, 메인 루프, 주문 실행기, 포지션/리스크 관리자
├── data/               # 시세, 캔들, 백테스트/매매 기록 저장
├── db/                 # TinyDB 핸들러 및 데이터 파일 (.json)
├── service/            # 업비트 API 연동 모듈 (REST, WebSocket)
├── strategy/           # 각종 매매 전략 클래스 구현 (전략 평가기)
├── utils/              # 공통 유틸리티 (계산, 포맷팅, 로깅, 알림 서비스 등)
├── tests/              # pytest 단위/통합 테스트
├── main.py             # 프로그램 실행 진입점 (실행 엔진의 일부)
├── requirements.txt    # 프로젝트 의존성 명세
├── config.yaml         # 시스템 및 전략 설정 파일 (설정 관리자)
├── .env                # 환경변수 (API 키 등)
└── README.md
```

### 4. 메인 루프 실행 구조 (1분 주기)

1.  **[Init]** `Main Engine`이 `Configuration Manager`를 통해 환경 초기화 (API 키, 전략 설정, DB, Webhook 로드)
2.  **[시장 상태 판단]** `Main Engine`이 `Upbit Service`로부터 데이터를 받아 BTC 15분봉 EMA, RSI 등으로 상승/하락/횡보 판단
3.  **[종목 선정]** `Main Engine`이 대상 종목 선정 (초기 BTC → 향후 자동 스크리닝)
4.  **[진입 판단]** `Strategy Evaluator`가 `evaluate_entry()` 호출 → 조건 충족 시 매수 신호 반환
5.  **[매수 실행]** `Order Executor`가 주문 실행 → `Position Manager`에 포지션 기록 → `Logging & Notification Service`로 알림
6.  **[청산 조건 평가]** `Strategy Evaluator`가 `evaluate_exit()` 호출 (현재 `Position Manager` 상태 참조) → 익절/손절/트레일링 조건 확인 후 신호 반환
7.  **[매도 실행]** `Order Executor`가 주문 실행 → `Database Handler`에 거래 로그 저장 → `Position Manager`에서 포지션 정리 → `Logging & Notification Service`로 알림
8.  **[리스크 관리 점검]** `Risk Manager`가 일일 손실, Rate Limit 등 위험 조건 확인 후 필요시 `Main Engine`에 제어 신호
9.  **[대기]** `Main Engine`이 60초 후 루프 재시작

### 5. 상태 저장 및 알림

#### 가. 로깅 시스템 (`Logging & Notification Service`의 일부)
- **콘솔 출력**: 실시간 주요 정보
- **파일 저장**: `logs/` 폴더에 일자별 `.log` 파일 자동 생성

#### 나. 알림 시스템 (`Logging & Notification Service`의 일부)
- **Discord Webhook**: 주요 이벤트(`매수/매도`, `에러`, `전략 상태 변경`) 실시간 알림

#### 다. 로컬 DB (TinyDB) - `Database Handler`가 관리
- **저장 위치**: `db/` 디렉토리에 `.json` 파일로 저장
- **주요 테이블**:
    - `TradeLog`: 매매 상세 기록 (종목, 진입/청산가, 수익률, 전략, 시간, 사유 등)
    - `MarketSnapshot`: (필요시) 시장 상태 판단용 시점별 지표 데이터
    - `CurrentPositions`: 현재 보유 중인 포지션 상세 정보 (실시간 업데이트)
    - `Settings`: (필요시) `config.yaml` 외 DB에 저장할 설정 (예: 동적 파라미터)

---

## 🧪 개발 원칙

### 1. TDD (Test-Driven Development)
- 모든 로직은 **테스트 코드 우선 작성** 후 구현
- 명확한 입출력 정의, 예외 처리 포함
- 매 전략마다 **최소 3개 이상의 테스트 케이스** 작성 (성공/실패/엣지 케이스)
- `pytest`를 중심으로 `mocker`, `faker`, `pytest-cov` 등 활용

### 2. 결정이 필요한 주요 항목 (문서화 및 설계 반영 예정)

| 분류         | 결정할 질문                                           |
| ------------ | ----------------------------------------------------- |
| 시장 판단    | EMA 외 보조지표 추가 여부 / 하락장 전략 적용 여부       |
| 종목 선정    | BTC 외 자동 선정 시 병렬 실행 구조 구체화             |
| 진입 조건    | 전략 클래스 내부 판단 vs. 외부 전달 구조              |
| 주문 방식    | 시장가 외 지정가 옵션 / 수량 계산 방식 고도화         |
| 포지션 구조  | `dict` vs. `dataclass` vs. `Pydantic` 모델 사용 여부  |
| 리스크 제어  | 일 손실 한도 기준 세분화 / RateLimit 대처 방식 구체화 |
| 예외 처리    | API 실패 재시도 로직 / WebSocket 재연결 상세 처리     |
| 설정 관리    | `config.yaml` 구조 및 업데이트 방식 상세화 (`Configuration Manager`)
| 백테스팅     | 슬리피지/수수료 반영 모델, 결과 지표 상세화           |

---

## 📅 향후 계획

### 1. 주요 기능 TODO

- [ ] 업비트 실시간 시세 WebSocket 구독 모듈 구현 (`Upbit Service`)
- [ ] 스캘핑 전략 클래스(`SignalStrategy` 기반) 상세 설계 및 구현 (`Strategy Evaluator`)
    - [ ] 적응형 변동성 돌파 + RSI 필터 + 트레일링 스탑 전략
- [ ] 거래 실행/취소 관리 모듈 (`Order Executor`) 개발
- [ ] 로컬 DB 저장 로직 (`Database Handler`: `TradeLog`, `MarketSnapshot`, `CurrentPositions`) 구체화
- [ ] 설정 파일(`config.yaml`) 로드 및 파싱 로직 구현 (`Configuration Manager`)
- [ ] 단위 테스트 및 통합 테스트 커버리지 확대
- [ ] 백테스트 시뮬레이터 기본 기능 구축
- [ ] 데일리 손실 한도 및 트레일링 스탑 로직 정교화 (`Risk Manager`)
- [ ] 위험 관리 체크리스트 항목 자동 모니터링 기능 (`Risk Manager`)
- [ ] 단계별 실행 로드맵(백테스트 → 모의투자 → 실계좌) 전환 로직 일부 자동화

### 2. 확장 아이디어

- 다양한 전략 추가 지원 (예: Swing, RSI 역추세, Grid, News-based 등)
- Telegram/Slack 등 추가 알림 채널 연동 (`Logging & Notification Service`)
- 성능 최적화 (예: Cython, WASM 모듈 일부 적용 검토)
- 모바일 푸시 알림 연동
- 웹 기반 대시보드 개발 (FastAPI + React/Vue 등)

---

## 👨‍💻 개발자 노트

- 전략 설계 시 **손익비 1:1.5 이상**을 목표로 함.
- 과도한 거래 빈도나 리스크를 방지하기 위한 필터링 조건 강화.
- **로컬 환경**에서의 단독 실행을 전제로 초기 시스템 설계.