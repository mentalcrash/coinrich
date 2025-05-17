from typing import Optional
from datetime import datetime
from operator import attrgetter
import time

from coinrich.service.upbit_api import UpbitAPI
from coinrich.service.candle_db import CandleDB
from coinrich.models.candle import MinuteCandle, MinuteCandleList


class CandleService:
    """캔들 데이터 서비스 클래스 - API와 DB 연동"""
    
    def __init__(self, db_path='coinrich.db'):
        """
        Args:
            db_path: SQLite DB 파일 경로
        """
        self.db = CandleDB(db_path)
        self.api = UpbitAPI()
    
    def get_minute_candles(self, market: str, unit: int = 1, count: int = 200, 
                           to: Optional[str] = None, use_cache: bool = True):
        """분 캔들 데이터 조회 (DB 캐시 우선)
        
        Args:
            market: 마켓 코드 (예: KRW-BTC)
            unit: 분 단위 (1, 3, 5, 10, 15, 30, 60, 240)
            count: 조회할 캔들 개수 (200 초과 요청 가능, 캐시 활용 또는 자동 분할 호출)
            to: 마지막 캔들 시각 (exclusive). 형식: yyyy-MM-dd'T'HH:mm:ss'Z' or yyyy-MM-dd HH:mm:ss
            use_cache: 캐시 사용 여부
            
        Returns:
            분 캔들 목록 (시간 오름차순 정렬)
        """
        # 기본 API 호출 제한
        MAX_API_COUNT = 200
        
        # 1. 캐시 미사용 또는 요청 개수가 200 이하인 경우 기존 로직 활용
        if not use_cache and count <= MAX_API_COUNT:
            candles = self.api.get_minute_candles(market, unit, count, to)
            # API 응답 정렬 (업비트는 일반적으로 최신 데이터 먼저 반환)
            candles_sorted = self._ensure_ascending_order(candles)
            self.db.save_minute_candles(candles_sorted, market, unit)
            return candles_sorted
        
        # 2. 캐시 미사용 + 200개 초과 요청: 분할 API 호출
        if not use_cache and count > MAX_API_COUNT:
            all_candles = []
            remaining = count
            current_to = to
            
            while remaining > 0:
                # 이번 호출에서 가져올 개수 결정
                batch_count = min(remaining, MAX_API_COUNT)
                
                # API 호출
                batch_candles = self.api.get_minute_candles(market, unit, batch_count, current_to)
                if not batch_candles or len(batch_candles.root) == 0:
                    break  # 더 이상 데이터가 없으면 종료
                
                # 정렬
                batch_sorted = self._ensure_ascending_order(batch_candles)
                
                # 결과 추가
                if not all_candles:
                    all_candles = batch_sorted
                else:
                    # 첫 번째 배치가 아니라면 목록에 추가
                    all_candles.root = batch_sorted.root + all_candles.root
                
                # 다음 호출을 위한 to 값 업데이트 (가장 오래된 캔들 시간)
                oldest_candle = batch_sorted.root[0]
                current_to = oldest_candle.candle_date_time_utc
                
                # 가져온 개수만큼 차감
                remaining -= len(batch_sorted.root)
                
                # API 호출 제한 준수: 1초 대기
                if remaining > 0:
                    time.sleep(1)
            
            # 모든 데이터 정렬 및 캐시에 저장
            all_candles_sorted = self._ensure_ascending_order(all_candles)
            self.db.save_minute_candles(all_candles_sorted, market, unit)
            return all_candles_sorted
        
        # 3. 시간 범위를 타임스탬프로 변환 (필요 시)
        end_time = None
        if to:
            # ISO 형식 시간을 타임스탬프로 변환
            if 'T' in to:
                dt_format = "%Y-%m-%dT%H:%M:%S" if to.endswith('Z') else "%Y-%m-%dT%H:%M:%S%z"
                to = to.rstrip('Z')  # 'Z' 제거
                end_time = int(datetime.strptime(to, dt_format).timestamp())
            else:
                dt_format = "%Y-%m-%d %H:%M:%S"
                end_time = int(datetime.strptime(to, dt_format).timestamp())
        
        # 4. DB에서 캐시된 데이터 확인
        cached_data = self.db.get_minute_candles(market, unit, end_time=end_time, limit=count)
        
        # 5. 충분한 캐시 데이터가 있으면 반환
        if cached_data and len(cached_data) >= count:
            # count 만큼만 반환
            return self._convert_db_to_model(cached_data[:count], unit)
        
        # 6. 캐시 부족 또는 없음: 부족한 만큼 API 호출
        if cached_data:
            cached_count = len(cached_data)
            needed_count = count - cached_count
            
            # 가장 오래된 캐시 데이터의 시간
            oldest_cached = cached_data[0]
            to_time = datetime.utcfromtimestamp(oldest_cached['timestamp']).strftime("%Y-%m-%dT%H:%M:%S")
            
            # 필요한 만큼만 API 호출 (분할 호출)
            remaining = needed_count
            all_new_candles = []
            current_to = to_time
            
            while remaining > 0:
                batch_count = min(remaining, MAX_API_COUNT)
                
                # API 호출
                batch_candles = self.api.get_minute_candles(market, unit, batch_count, current_to)
                if not batch_candles or len(batch_candles.root) == 0:
                    break
                
                batch_sorted = self._ensure_ascending_order(batch_candles)
                
                # 결과 추가
                if not all_new_candles:
                    all_new_candles = batch_sorted.root
                else:
                    all_new_candles = batch_sorted.root + all_new_candles
                
                # 다음 호출을 위한 to 값 업데이트
                if len(batch_sorted.root) > 0:
                    oldest_candle = batch_sorted.root[0]
                    current_to = oldest_candle.candle_date_time_utc
                    
                    # 가져온 개수만큼 차감
                    remaining -= len(batch_sorted.root)
                    
                    # API 호출 제한 준수: 1초 대기
                    if remaining > 0:
                        time.sleep(1)
                else:
                    break  # 더 이상 데이터가 없음
            
            # 새로운 데이터를 DB에 저장
            if all_new_candles:
                new_candles = MinuteCandleList(root=all_new_candles)
                self.db.save_minute_candles(new_candles, market, unit)
            
            # 캐시와 새 데이터를 합쳐서 반환
            all_cached_data = self.db.get_minute_candles(market, unit, end_time=end_time, limit=count)
            return self._convert_db_to_model(all_cached_data[:count], unit)
        
        # 7. 캐시가 전혀 없는 경우: 분할 API 호출로 필요한 만큼 데이터 수집
        return self.get_minute_candles(market, unit, count, to, use_cache=False)
    
    def _ensure_ascending_order(self, candles):
        """캔들 데이터를 시간 오름차순으로 정렬
        
        Args:
            candles: 정렬할 캔들 목록
            
        Returns:
            시간 오름차순으로 정렬된 캔들 목록
        """
        # timestamp 기준으로 정렬 (작은 값부터)
        if hasattr(candles, 'root'):
            sorted_candles = sorted(candles.root, key=lambda x: x.timestamp)
            return MinuteCandleList(root=sorted_candles)
        return candles  # 정렬할 수 없는 경우
    
    def _convert_db_to_model(self, db_data, unit):
        """DB 데이터를 캔들 모델로 변환
        
        Args:
            db_data: DB에서 조회한 캔들 데이터 (딕셔너리 리스트)
            unit: 분 단위
            
        Returns:
            MinuteCandleList 객체
        """
        # DB 데이터를 모델 형식에 맞게 변환
        candles = []
        for row in db_data:
            # UTC 시간과 KST 시간 생성
            ts = row['timestamp']
            dt_utc = datetime.utcfromtimestamp(ts)
            dt_kst = datetime.utcfromtimestamp(ts + 9 * 3600)  # KST = UTC + 9h
            
            utc_str = dt_utc.strftime("%Y-%m-%dT%H:%M:%S")
            kst_str = dt_kst.strftime("%Y-%m-%dT%H:%M:%S")
            
            candle_data = {
                'market': row['market'],
                'candle_date_time_utc': utc_str,
                'candle_date_time_kst': kst_str,
                'opening_price': row['open_price'],
                'high_price': row['high_price'],
                'low_price': row['low_price'],
                'trade_price': row['close_price'],
                'timestamp': row['timestamp'] * 1000,  # 초 → 밀리초 변환
                'candle_acc_trade_price': 0.0,  # 임시값, DB에 없는 필드
                'candle_acc_trade_volume': row['volume'],
                'unit': unit
            }
            candles.append(MinuteCandle(**candle_data))
        
        return MinuteCandleList(root=candles)
    
    def clear_cache(self, market=None, unit=None):
        """캐시 데이터 삭제
        
        Args:
            market: 마켓 코드 (None일 경우 모든 마켓)
            unit: 분 단위 (None일 경우 모든 타임프레임)
        """
        timeframe = f"{unit}m" if unit else None
        self.db.clear_cache(market, timeframe) 