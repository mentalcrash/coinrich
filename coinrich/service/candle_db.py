import sqlite3
import os
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

from coinrich.models.candle import MinuteCandle, MinuteCandleList


class CandleDB:
    """캔들 데이터 DB 저장 및 조회 클래스"""
    
    def __init__(self, db_path='coinrich.db'):
        """
        Args:
            db_path: SQLite DB 파일 경로
        """
        self.db_path = db_path
        self._create_tables_if_not_exists()
    
    def _create_tables_if_not_exists(self):
        """필요한 테이블과 인덱스 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 캔들 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS candles (
            id INTEGER PRIMARY KEY,
            market TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL, 
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            volume REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(market, timeframe, timestamp)
        )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_tf_ts ON candles(market, timeframe, timestamp)')
        
        conn.commit()
        conn.close()
    
    def save_minute_candles(self, candles: MinuteCandleList, market: str, unit: int):
        """분 캔들 데이터 저장 (중복 방지)
        
        Args:
            candles: 저장할 캔들 데이터 목록
            market: 마켓 코드 (예: KRW-BTC)
            unit: 분 단위 (1, 3, 5, 10, 15, 30, 60, 240)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timeframe = f"{unit}m"
        
        for candle in candles:
            cursor.execute('''
            INSERT OR IGNORE INTO candles 
            (market, timeframe, timestamp, open_price, high_price, low_price, close_price, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                market,
                timeframe,
                int(candle.timestamp / 1000),  # 밀리초 → 초 변환
                candle.opening_price,
                candle.high_price,
                candle.low_price,
                candle.trade_price,
                candle.candle_acc_trade_volume
            ))
        
        conn.commit()
        conn.close()
    
    def get_minute_candles(self, market: str, unit: int, 
                          start_time: Optional[int] = None, 
                          end_time: Optional[int] = None, 
                          limit: int = 200) -> List[Dict[str, Any]]:
        """저장된 분 캔들 데이터 조회
        
        Args:
            market: 마켓 코드 (예: KRW-BTC)
            unit: 분 단위 (1, 3, 5, 10, 15, 30, 60, 240)
            start_time: 시작 타임스탬프 (초 단위, 포함)
            end_time: 종료 타임스탬프 (초 단위, 포함)
            limit: 최대 조회 개수
            
        Returns:
            캔들 데이터 목록 (딕셔너리 형태)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 컬럼명으로 접근 가능하도록 설정
        cursor = conn.cursor()
        
        timeframe = f"{unit}m"
        
        query = "SELECT * FROM candles WHERE market=? AND timeframe=?"
        params = [market, timeframe]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # sqlite3.Row 객체를 딕셔너리로 변환
        result = [dict(row) for row in rows]
        
        conn.close()
        return result
    
    def has_cached_candles(self, market: str, unit: int, 
                           start_time: Optional[int] = None, 
                           end_time: Optional[int] = None,
                           min_count: int = 1) -> bool:
        """해당 기간의 캔들 데이터가 캐시되어 있는지 확인
        
        Args:
            market: 마켓 코드 (예: KRW-BTC)
            unit: 분 단위 (1, 3, 5, 10, 15, 30, 60, 240)
            start_time: 시작 타임스탬프 (초 단위)
            end_time: 종료 타임스탬프 (초 단위)
            min_count: 최소한 이 개수 이상의 캔들이 있어야 True 반환
            
        Returns:
            캐시 데이터 존재 여부
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timeframe = f"{unit}m"
        
        query = "SELECT COUNT(*) FROM candles WHERE market=? AND timeframe=?"
        params = [market, timeframe]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        
        conn.close()
        return count >= min_count
    
    def clear_cache(self, market: Optional[str] = None, timeframe: Optional[str] = None):
        """캐시 데이터 삭제
        
        Args:
            market: 마켓 코드 (None일 경우 모든 마켓)
            timeframe: 타임프레임 (None일 경우 모든 타임프레임)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if market and timeframe:
            query = "DELETE FROM candles WHERE market=? AND timeframe=?"
            params = (market, timeframe)
        elif market:
            query = "DELETE FROM candles WHERE market=?"
            params = (market,)
        elif timeframe:
            query = "DELETE FROM candles WHERE timeframe=?"
            params = (timeframe,)
        else:
            query = "DELETE FROM candles"
            params = ()
        
        cursor.execute(query, params)
        conn.commit()
        conn.close() 