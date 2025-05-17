# CoinRich

Upbit API를 활용한 암호화폐 트레이딩 봇 프로젝트

## 주요 기능

- Upbit API 연동
- 마켓, 현재가, 캔들 데이터 조회
- 주문 생성 및 취소
- 계좌 조회
- SQLite 데이터베이스를 사용한 캔들 데이터 캐싱

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

## 테스트 실행

```
python test.py                 # 기본 API 테스트
python test_candle_service.py  # 캔들 서비스 및 캐싱 테스트
```

## 프로젝트 구조

```
coinrich/
├── service/
│   ├── upbit_api.py     # Upbit API 클라이언트
│   ├── candle_db.py     # 캔들 데이터 DB 관리
│   └── candle_service.py # API와 DB 연동 서비스
├── models/
│   ├── market.py        # 마켓 데이터 모델
│   ├── ticker.py        # 현재가 데이터 모델
│   └── candle.py        # 캔들 데이터 모델
└── chart/               # (개발 예정) 차트 시각화
```

## 추가 예정 기능

- 캔들 데이터 차트 시각화
- 기술적 지표 계산 (이동평균선, MACD, RSI 등)
- 백테스팅 시스템
- 실시간 거래 알고리즘
- 웹 대시보드

## 라이센스

MIT