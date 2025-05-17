from coinrich.service.candle_service import CandleService
from coinrich.service.upbit_api import UpbitAPI
import os
import time
from datetime import datetime, timedelta


def test_get_minute_candles():
    """캔들 서비스 조회 테스트"""
    print("\n=== 캔들 서비스 테스트 ===")
    
    # 테스트용 DB 파일 (테스트 후 삭제)
    test_db = "test_candle.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # 서비스 초기화
    service = CandleService(db_path=test_db)
    
    # 1. 첫 번째 조회 (API에서 가져오고 DB에 저장)
    print("\n1. 첫 번째 조회 (캐시 없음, API 호출)")
    start_time = time.time()
    candles = service.get_minute_candles("KRW-BTC", unit=1, count=500)
    api_time = time.time() - start_time
    print(f"조회 시간: {api_time:.3f}초")
    print(f"캔들 개수: {len(candles)}")
    
    if len(candles) > 0:
        print("첫 번째 캔들:")
        print(f"  시간: {candles[0].candle_date_time_kst}")
        print(f"  시가: {candles[0].opening_price:,}원")
        print(f"  종가: {candles[0].trade_price:,}원")
    
    # 2. 두 번째 조회 (DB 캐시에서 가져옴)
    print("\n2. 두 번째 조회 (캐시 사용)")
    start_time = time.time()
    cached_candles = service.get_minute_candles("KRW-BTC", unit=1, count=500)
    cache_time = time.time() - start_time
    print(f"조회 시간: {cache_time:.3f}초")
    print(f"캔들 개수: {len(cached_candles)}")
    
    if len(cached_candles) > 0:
        print("첫 번째 캔들 (캐시):")
        print(f"  시간: {cached_candles[0].candle_date_time_kst}")
        print(f"  시가: {cached_candles[0].opening_price:,}원")
        print(f"  종가: {cached_candles[0].trade_price:,}원")
    
    # 3. 캐시 성능 비교
    if api_time > 0 and cache_time > 0:
        speedup = api_time / cache_time
        print(f"\n캐시 성능: API 대비 {speedup:.1f}배 빠름")
    
    # 4. 캐시 무시하고 조회
    print("\n3. 캐시 무시하고 API 재조회")
    fresh_candles = service.get_minute_candles("KRW-BTC", unit=1, count=500, use_cache=False)
    print(f"캔들 개수: {len(fresh_candles)}")
    
    # 5. 캐시 삭제 테스트
    print("\n4. 캐시 삭제 테스트")
    service.clear_cache(market="KRW-BTC", unit=5)
    
    # 삭제 후 다시 조회
    print("캐시 삭제 후 재조회")
    start_time = time.time()
    after_clear = service.get_minute_candles("KRW-BTC", unit=1, count=500)
    after_clear_time = time.time() - start_time
    print(f"조회 시간: {after_clear_time:.3f}초")
    
    # 테스트 DB 파일 삭제
    if os.path.exists(test_db):
        os.remove(test_db)
    
    return candles


def test_different_timeframes():
    """다양한 타임프레임 테스트"""
    print("\n=== 다양한 타임프레임 테스트 ===")
    
    # 테스트용 DB 파일
    test_db = "test_timeframes.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    service = CandleService(db_path=test_db)
    
    # 다양한 타임프레임 테스트
    for unit in [1, 3, 5, 15, 30, 60, 240]:
        print(f"\n{unit}분봉 조회:")
        candles = service.get_minute_candles("KRW-BTC", unit=unit, count=5)
        print(f"캔들 개수: {len(candles)}")
        
        if len(candles) > 0:
            for i, candle in enumerate(candles):
                print(f"[{i+1}] {candle.candle_date_time_kst} - 시가: {candle.opening_price:,}원, 종가: {candle.trade_price:,}원")
    
    # 테스트 DB 파일 삭제
    if os.path.exists(test_db):
        os.remove(test_db)


if __name__ == "__main__":
    # 테스트 실행
    test_get_minute_candles()
    # test_different_timeframes() 