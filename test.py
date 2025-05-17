from coinrich.service.upbit_api import UpbitAPI
from datetime import datetime, timedelta


def test_get_markets():
    """마켓 조회 테스트"""
    print("\n=== 마켓 조회 ===")
    api = UpbitAPI()
    markets = api.get_markets(is_details=True)
    print(f"마켓 수: {len(markets)}")
    print(f"첫 번째 마켓: {markets[0].market}, {markets[0].korean_name}")
    return markets


def test_get_ticker_single():
    """단일 종목 현재가 조회 테스트"""
    print("\n=== 단일 종목 현재가 조회 ===")
    api = UpbitAPI()
    btc_ticker = api.get_ticker("KRW-BTC")
    print(f"비트코인 현재가: {btc_ticker.trade_price:,}원")
    print(f"전일 대비: {btc_ticker.signed_change_rate * 100:.2f}% ({btc_ticker.change})")
    print(f"거래량(24h): {btc_ticker.acc_trade_volume_24h:.4f} BTC")
    print(f"거래대금(24h): {btc_ticker.acc_trade_price_24h / 1000000:.2f}백만원")
    return btc_ticker


def test_get_ticker_multiple():
    """여러 종목 현재가 조회 테스트"""
    print("\n=== 여러 종목 현재가 조회 ===")
    api = UpbitAPI()
    top_coins = api.get_ticker(["KRW-BTC", "KRW-ETH", "KRW-XRP"])
    
    for ticker in top_coins:
        print(f"{ticker.market}: {ticker.trade_price:,}원 ({ticker.signed_change_rate * 100:.2f}%)")
    return top_coins


def test_get_second_candles(market="KRW-BTC", count=5, minutes_ago=5):
    """초봉 조회 테스트
    
    Args:
        market: 마켓 코드 (예: KRW-BTC)
        unit: 초 단위 (1, 10, 60 중 하나)
        count: 조회할 캔들 개수
        minutes_ago: 현재로부터 몇 분 전 데이터부터 조회할지
    """
    print(f"\n=== 초봉 조회 (개수: {count}개) ===")
    api = UpbitAPI()
    
    # 현재 시간으로부터 minutes_ago분 전 시간을 to로 설정
    time_ago = datetime.utcnow() - timedelta(minutes=minutes_ago)
    to_time = time_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    btc_candles = api.get_second_candles(
        market=market,
        to=to_time,
        count=count
    )
    
    if len(btc_candles) > 0:
        for i, candle in enumerate(btc_candles):
            print(f"[{i+1}] {candle.candle_date_time_kst} - 시가: {candle.opening_price:,}원, 종가: {candle.trade_price:,}원")
            delta = candle.trade_price - candle.opening_price
            percent = (delta / candle.opening_price) * 100
            print(f"    변동: {delta:,.0f}원 ({percent:.2f}%), 거래량: {candle.candle_acc_trade_volume:.6f} BTC")
    else:
        print("해당 시간대에 캔들 데이터가 없습니다.")
    
    return btc_candles


def test_get_minute_candles(market="KRW-BTC", unit=1, count=5, hours_ago=1):
    """분봉 조회 테스트
    
    Args:
        market: 마켓 코드 (예: KRW-BTC)
        unit: 분 단위 (1, 3, 5, 10, 15, 30, 60, 240 중 하나)
        count: 조회할 캔들 개수
        hours_ago: 현재로부터 몇 시간 전 데이터부터 조회할지
    """
    print(f"\n=== {unit}분봉 조회 (개수: {count}개) ===")
    api = UpbitAPI()
    
    # 현재 시간으로부터 hours_ago 시간 전 시간을 to로 설정
    time_ago = datetime.utcnow() - timedelta(hours=hours_ago)
    to_time = time_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    candles = api.get_minute_candles(
        market=market,
        unit=unit,
        count=count
    )
    
    if len(candles) > 0:
        for i, candle in enumerate(candles):
            print(f"[{i+1}] {candle.candle_date_time_kst} - 시가: {candle.opening_price:,}원, 종가: {candle.trade_price:,}원")
            delta = candle.trade_price - candle.opening_price
            percent = (delta / candle.opening_price) * 100
            print(f"    변동: {delta:,.0f}원 ({percent:.2f}%), 거래량: {candle.candle_acc_trade_volume:.6f}, 분 단위: {candle.unit}")
    else:
        print("해당 시간대에 캔들 데이터가 없습니다.")
    
    return candles


def run_all_tests():
    """모든 테스트 실행"""
    test_get_markets()
    test_get_ticker_single()
    test_get_ticker_multiple()
    test_get_second_candles(count=5)
    test_get_minute_candles(count=5)


if __name__ == "__main__":
    # 아래에서 원하는 테스트 함수를 주석 해제하여 실행
    
    # 모든 테스트 실행
    # run_all_tests()
    
    # 개별 테스트 실행
    # test_get_markets()
    # test_get_ticker_single()
    # test_get_ticker_multiple()
    # test_get_second_candles(count=5)
    test_get_minute_candles(unit=5, count=5)
    
    # 다양한 초봉 테스트
    # test_get_second_candles(unit=1, count=3)  # 1초 단위 3개
    # test_get_second_candles(unit=60, count=5)  # 60초 단위 5개
    # test_get_second_candles(market="KRW-ETH", unit=10, count=3)  # 이더리움 10초 단위 3개
