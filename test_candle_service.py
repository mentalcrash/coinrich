from coinrich.service.candle_service import CandleService
from coinrich.service.upbit_api import UpbitAPI
import os
import time
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, MagicMock


def test_candle_service_init():
    """캔들 서비스 초기화 테스트"""
    service = CandleService('test.db')
    assert service.db.conn is not None
    service.db.conn.close()
    # 테스트 DB 삭제
    if os.path.exists('test.db'):
        os.remove('test.db')


def test_get_minute_candles():
    """분 캔들 조회 테스트"""
    service = CandleService()
    
    # 1. 캐시 없이 API 사용
    candles = service.get_minute_candles("KRW-BTC", unit=15, count=10, use_cache=False)
    assert candles is not None
    assert len(candles.root) == 10
    assert candles.root[0].market == "KRW-BTC"
    assert candles.root[0].unit == 15
    
    # 2. 캐시 사용 (이미 저장된 데이터)
    cached_candles = service.get_minute_candles("KRW-BTC", unit=15, count=10)
    assert cached_candles is not None
    assert len(cached_candles.root) == 10
    
    # 3. 특정 시점까지 조회
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%dT%H:%M:%S")
    
    past_candles = service.get_minute_candles("KRW-BTC", unit=15, count=5, to=yesterday_str)
    assert past_candles is not None
    # 시간 검증
    for candle in past_candles.root:
        candle_time = datetime.strptime(candle.candle_date_time_utc, "%Y-%m-%dT%H:%M:%S")
        assert candle_time < yesterday


def test_get_large_candle_data():
    """대량(200개 초과) 캔들 데이터 조회 테스트"""
    service = CandleService()
    
    # 1. 대량 데이터 조회 (캐시 사용 안함)
    with patch('time.sleep') as mock_sleep:  # sleep 함수 모킹하여 테스트 시간 단축
        large_candles = service.get_minute_candles("KRW-BTC", unit=15, count=300, use_cache=False)
        assert large_candles is not None
        assert len(large_candles.root) > 200  # 실제로는 300개에 가깝겠지만, API 상황에 따라 다를 수 있음
        assert mock_sleep.called  # 1초 sleep 호출 확인
    
    # 2. 대량 데이터 조회 (캐시 사용)
    large_cached_candles = service.get_minute_candles("KRW-BTC", unit=15, count=300)
    assert large_cached_candles is not None
    assert len(large_cached_candles.root) >= 200  # 최소한 API 한 번 호출 분량은 있어야 함
    
    # 3. 캐시된 데이터와 API 혼합 사용 시나리오
    # 기존 캐시에서 250개를 요청하고, 300개를 새로 요청하면 캐시 활용 후 추가 데이터만 API 요청
    with patch('coinrich.service.upbit_api.UpbitAPI.get_minute_candles') as mock_api:
        # 목업 반환값 설정
        def mock_return(*args, **kwargs):
            count = kwargs.get('count', args[2] if len(args) > 2 else 200)
            # 요청 개수만큼 더미 캔들 생성
            candles = []
            for i in range(count):
                candle_time = datetime.utcnow() - timedelta(minutes=15*(i+1))
                candle_data = {
                    'market': 'KRW-BTC',
                    'candle_date_time_utc': candle_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    'candle_date_time_kst': (candle_time + timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S"),
                    'opening_price': 50000000 + i*1000,
                    'high_price': 50100000 + i*1000,
                    'low_price': 49900000 + i*1000,
                    'trade_price': 50050000 + i*1000,
                    'timestamp': int(candle_time.timestamp()) * 1000,
                    'candle_acc_trade_price': 1000000.0,
                    'candle_acc_trade_volume': 2.0,
                    'unit': 15
                }
                candles.append(MinuteCandle(**candle_data))
            return MinuteCandleList(root=candles)
        
        mock_api.side_effect = mock_return
        
        # 이미 250개가 캐시되어 있다고 가정하면, 300개 요청 시 50개만 추가로 API 요청해야 함
        extension_candles = service.get_minute_candles("KRW-BTC", unit=15, count=300)
        
        # mock_api가 호출되었는지 확인 (캐시만으로는 부족하여 API 호출이 발생했는지)
        assert mock_api.called
        
        # 결과 확인
        assert extension_candles is not None
        assert len(extension_candles.root) == 300


def test_clear_cache():
    """캐시 삭제 테스트"""
    service = CandleService()
    
    # 캐시 생성을 위한 API 호출
    service.get_minute_candles("KRW-BTC", unit=15, count=10)
    
    # 특정 마켓, 특정 타임프레임 캐시 삭제
    service.clear_cache(market="KRW-BTC", unit=15)
    
    # 캐시가 삭제되었으므로 API를 다시 호출해야 함
    with patch('coinrich.service.upbit_api.UpbitAPI.get_minute_candles') as mock_api:
        mock_api.return_value = MinuteCandleList(root=[])
        service.get_minute_candles("KRW-BTC", unit=15, count=10)
        assert mock_api.called
    
    # 전체 캐시 삭제
    service.clear_cache()


if __name__ == "__main__":
    test_candle_service_init()
    test_get_minute_candles()
    test_get_large_candle_data()
    test_clear_cache()
    print("모든 테스트가 통과되었습니다!") 