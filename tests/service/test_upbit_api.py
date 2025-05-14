import pytest
import jwt
import re
import responses
from unittest.mock import patch
from coinrich.service.upbit_api import UpbitAPI
from coinrich.models.market import MarketList
from coinrich.models.ticker import Ticker, TickerList, ChangeType
from coinrich.models.candle import SecondCandle, SecondCandleList
import requests
import json
class TestUpbitAPI:
    
    def setup_method(self):
        """각 테스트 실행 전 설정"""
        self.api = UpbitAPI(access_key="test_access", secret_key="test_secret")
        self.base_url = self.api.BASE_URL
        
    @responses.activate
    def test_get_markets_basic(self):
        """기본 마켓 조회 테스트"""
        # 목 응답 데이터 설정
        mock_response = [
            {
                "market": "KRW-BTC",
                "korean_name": "비트코인",
                "english_name": "Bitcoin"
            },
            {
                "market": "KRW-ETH",
                "korean_name": "이더리움", 
                "english_name": "Ethereum"
            }
        ]
        
        # API 응답 모킹
        responses.add(
            responses.GET,
            f"{self.base_url}/market/all?isDetails=False",
            json=mock_response,
            status=200
        )
        
        # 메소드 호출
        result = self.api.get_markets()
        
        assert isinstance(result, MarketList)
        assert len(result) == 2
        assert result[0].market == "KRW-BTC"
        assert result[0].korean_name == "비트코인"
        assert result[1].market == "KRW-ETH"
        
    @responses.activate
    def test_get_ticker_single(self):
        """단일 종목 현재가 조회 테스트"""
        mock_response = [
            {
                "market": "KRW-BTC",
                "trade_date": "20230601",
                "trade_time": "102030",
                "trade_date_kst": "20230601",
                "trade_time_kst": "192030",
                "trade_timestamp": 1685614230000,
                "opening_price": 50000000.0,
                "high_price": 51000000.0,
                "low_price": 49000000.0,
                "trade_price": 50500000.0,
                "prev_closing_price": 49500000.0,
                "change": "RISE",
                "change_price": 1000000.0,
                "change_rate": 0.0202,
                "signed_change_price": 1000000.0,
                "signed_change_rate": 0.0202,
                "trade_volume": 0.1,
                "acc_trade_price": 500000000.0,
                "acc_trade_price_24h": 1000000000.0,
                "acc_trade_volume": 10.0,
                "acc_trade_volume_24h": 20.0,
                "highest_52_week_price": 52000000.0,
                "highest_52_week_date": "2023-05-01",
                "lowest_52_week_price": 30000000.0,
                "lowest_52_week_date": "2022-06-15",
                "timestamp": 1685614235000
            }
        ]
        
        responses.add(
            responses.GET,
            f"{self.base_url}/ticker?markets=KRW-BTC",
            json=mock_response,
            status=200
        )
        
        result = self.api.get_ticker("KRW-BTC")
        
        assert isinstance(result, Ticker)
        assert result.market == "KRW-BTC"
        assert result.trade_price == 50500000.0
        assert result.change == ChangeType.RISE
        assert result.signed_change_rate == 0.0202
        
    @responses.activate
    def test_get_ticker_multiple(self):
        """복수 종목 현재가 조회 테스트"""
        mock_response = [
            {
                "market": "KRW-BTC",
                "trade_date": "20230601",
                "trade_time": "102030",
                "trade_date_kst": "20230601",
                "trade_time_kst": "192030",
                "trade_timestamp": 1685614230000,
                "opening_price": 50000000.0,
                "high_price": 51000000.0,
                "low_price": 49000000.0,
                "trade_price": 50500000.0,
                "prev_closing_price": 49500000.0,
                "change": "RISE",
                "change_price": 1000000.0,
                "change_rate": 0.0202,
                "signed_change_price": 1000000.0,
                "signed_change_rate": 0.0202,
                "trade_volume": 0.1,
                "acc_trade_price": 500000000.0,
                "acc_trade_price_24h": 1000000000.0,
                "acc_trade_volume": 10.0,
                "acc_trade_volume_24h": 20.0,
                "highest_52_week_price": 52000000.0,
                "highest_52_week_date": "2023-05-01",
                "lowest_52_week_price": 30000000.0,
                "lowest_52_week_date": "2022-06-15",
                "timestamp": 1685614235000
            },
            {
                "market": "KRW-ETH",
                "trade_date": "20230601",
                "trade_time": "102030",
                "trade_date_kst": "20230601",
                "trade_time_kst": "192030",
                "trade_timestamp": 1685614230000,
                "opening_price": 2000000.0,
                "high_price": 2100000.0,
                "low_price": 1900000.0,
                "trade_price": 2050000.0,
                "prev_closing_price": 1950000.0,
                "change": "RISE",
                "change_price": 100000.0,
                "change_rate": 0.0513,
                "signed_change_price": 100000.0,
                "signed_change_rate": 0.0513,
                "trade_volume": 0.5,
                "acc_trade_price": 100000000.0,
                "acc_trade_price_24h": 200000000.0,
                "acc_trade_volume": 50.0,
                "acc_trade_volume_24h": 100.0,
                "highest_52_week_price": 2200000.0,
                "highest_52_week_date": "2023-05-10",
                "lowest_52_week_price": 1000000.0,
                "lowest_52_week_date": "2022-06-20",
                "timestamp": 1685614235000
            }
        ]
        
        responses.add(
            responses.GET,
            f"{self.base_url}/ticker?markets=KRW-BTC,KRW-ETH",
            json=mock_response,
            status=200
        )
        
        result = self.api.get_ticker(["KRW-BTC", "KRW-ETH"])
        
        assert isinstance(result, TickerList)
        assert len(result) == 2
        assert result[0].market == "KRW-BTC"
        assert result[1].market == "KRW-ETH"
        assert result[0].change == ChangeType.RISE
        assert result[1].trade_price == 2050000.0
        
    @responses.activate
    def test_get_markets_with_details(self):
        """상세 정보 포함 마켓 조회 테스트"""
        # 목 응답 데이터 설정
        mock_response = [
            {
                "market": "KRW-BTC",
                "korean_name": "비트코인",
                "english_name": "Bitcoin",
                "market_event": {
                    "warning": False,
                    "caution": {"PRICE_FLUCTUATIONS": False}
                }
            }
        ]
        
        # API 응답 모킹
        responses.add(
            responses.GET,
            f"{self.base_url}/market/all?isDetails=True",
            json=mock_response,
            status=200
        )
        
        # 메소드 호출
        result = self.api.get_markets(is_details=True)
        
        # 결과 검증
        assert isinstance(result, MarketList)
        assert len(result) == 1
        assert result[0].market == "KRW-BTC"
        assert result[0].market_event is not None
        assert result[0].market_event.warning is False
        assert "PRICE_FLUCTUATIONS" in result[0].market_event.caution
        
    @responses.activate
    def test_get_markets_empty_response(self):
        """빈 응답 처리 테스트"""
        # 빈 목 응답 설정
        responses.add(
            responses.GET,
            f"{self.base_url}/market/all?isDetails=False",
            json=[],
            status=200
        )
        
        # 메소드 호출
        result = self.api.get_markets()
        
        # 결과 검증
        assert isinstance(result, MarketList)
        assert len(result) == 0
        
    @responses.activate
    def test_get_markets_error_response(self):
        """에러 응답 처리 테스트"""
        # 에러 응답 설정
        responses.add(
            responses.GET,
            f"{self.base_url}/market/all?isDetails=False",
            json={"error": "Invalid request"},
            status=400
        )
        
        # 에러 발생 검증
        with pytest.raises(Exception):
            self.api.get_markets()

    @responses.activate
    def test_get_second_candles_basic(self):
        """기본 초봉 조회 테스트"""
        # 목 응답 데이터 설정
        mock_response = [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": "2023-01-01T00:00:00",
                "candle_date_time_kst": "2023-01-01T09:00:00",
                "opening_price": 20000000.0,
                "high_price": 20100000.0,
                "low_price": 19900000.0,
                "trade_price": 20050000.0,
                "timestamp": 1672531200000,
                "candle_acc_trade_price": 5000000.0,
                "candle_acc_trade_volume": 0.25
            },
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": "2023-01-01T00:00:01",
                "candle_date_time_kst": "2023-01-01T09:00:01",
                "opening_price": 20050000.0,
                "high_price": 20150000.0,
                "low_price": 20000000.0,
                "trade_price": 20100000.0,
                "timestamp": 1672531201000,
                "candle_acc_trade_price": 6000000.0,
                "candle_acc_trade_volume": 0.3
            }
        ]
        
        # Mock API 응답 설정
        responses.add(
            responses.GET,
            f"{self.base_url}/candles/seconds",
            json=mock_response,
            status=200
        )
        
        # API 호출
        candles = self.api.get_second_candles("KRW-BTC")
        
        # 결과 검증
        assert isinstance(candles, SecondCandleList)
        assert len(candles) == 2
        assert candles[0].market == "KRW-BTC"
        assert candles[0].opening_price == 20000000.0
        assert candles[0].trade_price == 20050000.0
        assert candles[1].high_price == 20150000.0
        
    @responses.activate
    def test_get_second_candles_with_params(self):
        """파라미터를 사용한 초봉 조회 테스트"""
        # 목 응답 데이터 설정
        mock_response = [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": "2023-01-01T00:00:00",
                "candle_date_time_kst": "2023-01-01T09:00:00",
                "opening_price": 20000000.0,
                "high_price": 20100000.0,
                "low_price": 19900000.0,
                "trade_price": 20050000.0,
                "timestamp": 1672531200000,
                "candle_acc_trade_price": 5000000.0,
                "candle_acc_trade_volume": 0.25
            }
        ]
        
        # 파라미터 검증을 위한 함수
        def request_callback(request):
            params = request.params
            assert params.get('market') == 'KRW-BTC'
            assert params.get('to') == '2023-01-01T00:00:00Z'
            assert params.get('count') == '1'
            return (200, {}, json.dumps(mock_response))
        
        # Mock API 응답 설정
        responses.add_callback(
            responses.GET,
            f"{self.base_url}/candles/seconds",
            callback=request_callback,
            content_type='application/json',
        )
        
        # API 호출
        candles = self.api.get_second_candles(
            market="KRW-BTC",
            to="2023-01-01T00:00:00Z",
            count=1
        )
        
        # 결과 검증
        assert isinstance(candles, SecondCandleList)
        assert len(candles) == 1
        
    @responses.activate
    def test_get_second_candles_error(self):
        """초봉 조회 에러 테스트"""
        # Mock API 오류 응답 설정
        responses.add(
            responses.GET,
            f"{self.base_url}/candles/seconds",
            json={"error": {"message": "Invalid market", "name": "invalid_request"}},
            status=400
        )
        
        # API 호출 시 예외 발생 확인
        with pytest.raises(requests.exceptions.HTTPError):
            self.api.get_second_candles("INVALID-MARKET") 