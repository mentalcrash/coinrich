import os
import jwt
import uuid
import hashlib
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from typing import List, Union

from coinrich.models.market import MarketList
from coinrich.models.ticker import Ticker, TickerList

load_dotenv()

class UpbitAPI:
    """Upbit REST API 클라이언트"""
    
    BASE_URL = "https://api.upbit.com/v1"
    
    def __init__(self, access_key=None, secret_key=None):
        """API 키 초기화"""
        self.access_key = access_key or os.getenv('UPBIT_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('UPBIT_SECRET_KEY')
        
    def _create_token(self, query=None) -> str:
        """JWT 토큰 생성"""
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }
        
        if query:
            m = hashlib.sha512()
            m.update(urlencode(query).encode())
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
        
        jwt_token = jwt.encode(payload, self.secret_key)
        authorization_token = 'Bearer {}'.format(jwt_token)
        return authorization_token
    
    def get_markets(self, is_details: bool = False) -> MarketList:
        """마켓 조회"""
        url = f"{self.BASE_URL}/market/all?isDetails={is_details}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return MarketList(root=data)
    
    def get_ticker(self, markets: Union[str, List[str]]) -> Union[Ticker, TickerList]:
        """현재가 조회
        
        Args:
            markets: 단일 마켓 코드 또는 마켓 코드 리스트(예: "KRW-BTC" 또는 ["KRW-BTC", "KRW-ETH"])
            
        Returns:
            단일 종목 조회 시 Ticker 객체, 여러 종목 조회 시 TickerList 객체
        """
        if isinstance(markets, list):
            markets = ','.join(markets)
            
        params = {'markets': markets}
        url = f"{self.BASE_URL}/ticker"
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if len(data) == 1:
            return Ticker(**data[0])
        return TickerList(root=data)
    
    def get_candles(self, market, unit=1, count=200):
        """분 캔들 조회"""
        pass
    
    def get_orderbook(self, markets):
        """호가 정보 조회"""
        pass
    
    def get_accounts(self):
        """계좌 잔고 조회"""
        pass
    
    def place_order(self, market, side, volume, price=None, ord_type='limit'):
        """주문 생성"""
        pass
    
    def cancel_order(self, uuid):
        """주문 취소"""
        pass

# 사용 예시
if __name__ == "__main__":
    api = UpbitAPI()
    # 사용 예시 코드 