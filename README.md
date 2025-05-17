# CoinRich

Upbit API를 활용한 암호화폐 트레이딩 봇 프로젝트

## 주요 기능

- Upbit API 연동
- 마켓, 현재가, 캔들 데이터 조회
- 주문 생성 및 취소
- 계좌 조회
- SQLite 데이터베이스를 사용한 캔들 데이터 캐싱
- 캔들 차트 시각화 (한국식 캔들 색상 지원)
- 다양한 기술적 지표 계산 및 시각화
- 추세장/횡보장 판별 기능

## 설치 방법

1. 저장소 클론
   ```
   git clone https://github.com/yourusername/coinrich.git
   cd coinrich
   ```

2. 가상환경 생성 및 활성화
   ```
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 의존성 설치
   ```
   pip install -r requirements.txt
   ```

4. 환경변수 설정 (.env 파일 생성)
   ```
   UPBIT_ACCESS_KEY=your_access_key
   UPBIT_SECRET_KEY=your_secret_key
   ```

## 사용 예시

### API 기본 사용

```python
from coinrich.service.upbit_api import UpbitAPI

# API 클라이언트 초기화
api = UpbitAPI()

# 마켓 정보 조회
markets = api.get_markets()
print(f"마켓 수: {len(markets)}")

# 현재가 조회
btc_ticker = api.get_ticker("KRW-BTC")
print(f"비트코인 현재가: {btc_ticker.trade_price:,}원")

# 분 캔들 조회
btc_candles = api.get_minute_candles("KRW-BTC", unit=5, count=10)
```

### 캔들 데이터 캐싱 사용

```python
from coinrich.service.candle_service import CandleService

# 캔들 서비스 초기화
service = CandleService()

# 캐시를 활용한 분 캔들 조회 (DB에 없으면 API 호출)
candles = service.get_minute_candles("KRW-BTC", unit=5, count=10)

# 캐시 무시하고 API에서 최신 데이터 가져오기
fresh_candles = service.get_minute_candles("KRW-BTC", unit=5, count=10, use_cache=False)

# 캐시 삭제
service.clear_cache(market="KRW-BTC", unit=5)
```

### 차트 시각화

```python
from coinrich.chart.candle_chart import CandleChart

# 캔들 서비스 초기화
service = CandleService()
candles = service.get_minute_candles("KRW-BTC", unit=15, count=100)

# 기본 캔들 차트 생성
chart = CandleChart(title="BTC/KRW - 15분봉", style="yahoo")
chart.plot(candles)

# 이동평균선 추가
chart.add_moving_average([5, 20, 60])

# 볼린저 밴드 추가
chart.add_bollinger_bands(period=20)

# RSI 지표 추가
chart.add_rsi(period=14)

# MACD 지표 추가
chart.add_macd()

# 한국식 캔들 차트 생성 (상승: 빨간색, 하락: 파란색)
korean_chart = CandleChart(title="BTC/KRW - 한국식 캔들", style="korean")
korean_chart.plot(candles)

# 차트 저장 및 표시
chart.save("btc_chart.png")
chart.show()
```

### 기술적 지표 사용

```python
import pandas as pd
from coinrich.utils.indicators import bollinger_bands, rsi, macd, adx, is_trending_market

# 데이터 준비
df = pd.DataFrame(...)  # OHLCV 데이터

# 볼린저 밴드
bb = bollinger_bands(df, period=20, std_dev=2.0)
print(f"상단 밴드: {bb['upper'].iloc[-1]:.2f}")
print(f"중간 밴드: {bb['middle'].iloc[-1]:.2f}")
print(f"하단 밴드: {bb['lower'].iloc[-1]:.2f}")

# RSI
rsi_values = rsi(df, period=14)
print(f"RSI: {rsi_values.iloc[-1]:.2f}")

# MACD
macd_result = macd(df, fast=12, slow=26, signal=9)
print(f"MACD: {macd_result['macd'].iloc[-1]:.2f}")
print(f"시그널: {macd_result['signal'].iloc[-1]:.2f}")
print(f"히스토그램: {macd_result['histogram'].iloc[-1]:.2f}")

# ADX (추세 강도)
adx_result = adx(df, period=14)
print(f"ADX: {adx_result['adx'].iloc[-1]:.2f}")
print(f"+DI: {adx_result['plus_di'].iloc[-1]:.2f}")
print(f"-DI: {adx_result['minus_di'].iloc[-1]:.2f}")

# 추세장/횡보장 판별
trending, _, _ = is_trending_market(df, adx_threshold=25, bb_width_percentile=70)
print(f"현재 추세장 여부: {trending.iloc[-1]}")
```

## 테스트 실행

```
python test.py                   # 기본 API 테스트
python test_candle_service.py    # 캔들 서비스 및 캐싱 테스트
python test_chart.py             # 차트 시각화 테스트
python test_indicators.py        # 기술적 지표 테스트
```

## 프로젝트 구조

```
coinrich/
├── service/
│   ├── upbit_api.py      # Upbit API 클라이언트
│   ├── candle_db.py      # 캔들 데이터 DB 관리
│   └── candle_service.py # API와 DB 연동 서비스
├── models/
│   ├── market.py         # 마켓 데이터 모델
│   ├── ticker.py         # 현재가 데이터 모델
│   └── candle.py         # 캔들 데이터 모델
├── chart/
│   ├── base_chart.py     # 차트 기본 추상 클래스
│   └── candle_chart.py   # 캔들 차트 구현
└── utils/
    └── indicators.py     # 기술적 지표 계산 함수
```

## 구현된 기술적 지표

- 이동평균선 (SMA, EMA)
- 볼린저 밴드 및 밴드 폭
- RSI (상대강도지수)
- MACD (이동평균수렴발산)
- 스토캐스틱 오실레이터
- ATR (평균진폭)
- 일목균형표
- OBV (온밸런스볼륨)
- ADX (평균방향지수)
- 추세장/횡보장 판별 알고리즘

## 추가 예정 기능

- 백테스팅 시스템
- 트레이딩 전략 구현
- 리스크 관리 시스템
- 실시간 거래 알고리즘
- 웹 대시보드

## 라이센스

MIT