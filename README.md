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
- 백테스팅 시스템 및 성과 분석
- 적응형 트레이딩 전략 구현
- 추세장/횡보장 파라미터 최적화 도구

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

# 대량 데이터 요청 (200개 초과도 자동 처리)
large_data = service.get_minute_candles("KRW-BTC", unit=15, count=1000)
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

# 외부 축(axes)을 사용한 차트 생성
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(12, 8))
chart = CandleChart(title="BTC/KRW - 커스텀 차트", style="korean", ax=ax, fig=fig)
chart.plot(candles)
chart.add_moving_average([10, 30])
plt.show()
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

### 추세장/횡보장 분석 도구 사용

추세장/횡보장 판별을 위한 ADX 임계값, 볼린저 밴드 폭 백분위수 등 최적의 파라미터를 찾기 위한 도구입니다.

```bash
# 기본 분석 (BTC, 15분봉, 파라미터 기본값)
python trend_analyzer.py

# 파라미터 변경하여 분석
python trend_analyzer.py --market KRW-BTC --unit 30 --count 800 --adx-threshold 20 --bb-percentile 65

# 여러 종목 분석
python trend_analyzer.py --market KRW-ETH --unit 60
python trend_analyzer.py --market KRW-XRP --adx-threshold 30
```

결과는 `charts` 디렉토리에 자동 저장되며, 파라미터 정보와 분석 결과를 포함한 차트가 생성됩니다. 이를 통해 다양한 파라미터로 시험하며 최적의 추세장/횡보장 판별 파라미터를 찾을 수 있습니다.

### 백테스팅 시스템 사용

```python
from coinrich.service.candle_service import CandleService
from coinrich.strategy.adaptive_strategy import AdaptivePositionStrategy
from coinrich.backtest.backtest import Backtest
import pandas as pd

# 데이터 준비
service = CandleService()
candles = service.get_minute_candles("KRW-BTC", unit=60, count=200)

# 데이터프레임 변환
candle_data = []
for candle in candles:
    candle_data.append({
        'datetime': pd.to_datetime(candle.candle_date_time_utc),
        'open': candle.opening_price,
        'high': candle.high_price,
        'low': candle.low_price,
        'close': candle.trade_price,
        'volume': candle.candle_acc_trade_volume
    })

df = pd.DataFrame(candle_data)
df = df.set_index('datetime')
df = df.sort_index()

# 전략 파라미터 설정
strategy_params = {
    'adx_threshold': 25,           # ADX 임계값
    'bb_width_percentile': 70,     # 볼린저 밴드 폭 백분위수
    'ma_short_period': 20,         # 단기 이동평균
    'ma_long_period': 50,          # 장기 이동평균
    'rsi_period': 14,              # RSI 기간
    'take_profit': 0.05,           # 5% 익절
    'stop_loss': 0.02              # 2% 손절
}

# 백테스트 실행
strategy = AdaptivePositionStrategy(strategy_params)
backtest = Backtest(df, strategy, initial_capital=1000000, position_size=0.5)
result, df_result = backtest.run()

# 백테스트 결과 확인
print(result.summary())
print(result.trade_summary())

# 결과 시각화 및 차트 저장
fig = backtest.visualize(result, df_result)
plt.show()
```

## 테스트 실행

```
python test.py                   # 기본 API 테스트
python test_candle_service.py    # 캔들 서비스 및 캐싱 테스트
python test_chart.py             # 차트 시각화 테스트
python test_indicators.py        # 기술적 지표 테스트
python test_backtest.py          # 백테스팅 및 전략 테스트
python trend_analyzer.py         # 추세장/횡보장 분석 도구
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
├── utils/
│   └── indicators.py     # 기술적 지표 계산 함수
├── strategy/
│   └── adaptive_strategy.py # 적응형 트레이딩 전략
└── backtest/
    ├── backtest.py       # 백테스팅 엔진
    └── backtest_result.py # 백테스트 결과 분석
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

## 구현된 백테스팅 및 시각화 기능

- 백테스팅 엔진 및 성과 분석
- 시장 상태별 성과 분석 (추세장/횡보장)
- 메인 차트와 Equity 차트 동기화 (matplotlib sharex 활용)
- 매수/매도 포인트 시각화
- 수익률 및 성과 지표 계산
- 시장 상태 시각화 (배경색 구분)
- 추세장/횡보장 파라미터 최적화 도구

## 추가 예정 기능

- 최적화된 파라미터 탐색 기능
- 실시간 거래 알고리즘
- 리스크 관리 시스템
- 웹 대시보드

## 라이센스

MIT