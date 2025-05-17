from typing import List, Optional
from pydantic import BaseModel, Field, RootModel
from datetime import datetime


class Candle(BaseModel):
    """캔들 기본 모델 (초/분/일/주/월 공통)"""
    market: str = Field(..., description="종목 코드")
    candle_date_time_utc: str = Field(..., description="캔들 기준 시각(UTC 기준)")
    candle_date_time_kst: str = Field(..., description="캔들 기준 시각(KST 기준)")
    opening_price: float = Field(..., description="시가")
    high_price: float = Field(..., description="고가")
    low_price: float = Field(..., description="저가")
    trade_price: float = Field(..., description="종가")
    timestamp: int = Field(..., description="마지막 틱이 저장된 시각")
    candle_acc_trade_price: float = Field(..., description="누적 거래 금액")
    candle_acc_trade_volume: float = Field(..., description="누적 거래량")
    
    def get_date_time_utc(self) -> datetime:
        """UTC 기준 시각을 datetime 객체로 반환"""
        return datetime.fromisoformat(self.candle_date_time_utc.replace('Z', '+00:00'))
    
    def get_date_time_kst(self) -> datetime:
        """KST 기준 시각을 datetime 객체로 반환"""
        return datetime.fromisoformat(self.candle_date_time_kst.replace('Z', '+09:00'))


class SecondCandle(Candle):
    """초 단위 캔들 모델"""
    pass

class MinuteCandle(Candle):
    """분 단위 캔들 모델"""
    unit: int = Field(..., description="단위(분)")


class DayCandle(Candle):
    """일 단위 캔들 모델"""
    prev_closing_price: float = Field(..., description="전일 종가")
    change_price: float = Field(..., description="변화액")
    change_rate: float = Field(..., description="변화율")
    converted_trade_price: Optional[float] = Field(None, description="종가 환산 화폐 단위로 환산된 가격")


class WeekCandle(Candle):
    """주 단위 캔들 모델"""
    first_day_of_period: str = Field(..., description="캔들 기간의 첫 날")


class MonthCandle(Candle):
    """월 단위 캔들 모델"""
    first_day_of_period: str = Field(..., description="캔들 기간의 첫 날")


class CandleList(RootModel):
    """캔들 목록 모델"""
    root: List[Candle]
    
    def __iter__(self):
        return iter(self.root)
    
    def __getitem__(self, item):
        return self.root[item]
    
    def __len__(self):
        return len(self.root)


class SecondCandleList(RootModel):
    """초 단위 캔들 목록 모델"""
    root: List[SecondCandle]
    
    def __iter__(self):
        return iter(self.root)
    
    def __getitem__(self, item):
        return self.root[item]
    
    def __len__(self):
        return len(self.root)


class MinuteCandleList(RootModel):
    """분 단위 캔들 목록 모델"""
    root: List[MinuteCandle]
    
    def __iter__(self):
        return iter(self.root)
    
    def __getitem__(self, item):
        return self.root[item]
    
    def __len__(self):
        return len(self.root)


class DayCandleList(RootModel):
    """일 단위 캔들 목록 모델"""
    root: List[DayCandle]
    
    def __iter__(self):
        return iter(self.root)
    
    def __getitem__(self, item):
        return self.root[item]
    
    def __len__(self):
        return len(self.root) 