from typing import List, Optional
from pydantic import BaseModel, Field, RootModel
from enum import Enum


class ChangeType(str, Enum):
    """가격 변화 타입"""
    EVEN = "EVEN"  # 보합
    RISE = "RISE"  # 상승
    FALL = "FALL"  # 하락


class Ticker(BaseModel):
    """종목 현재가 정보 모델"""
    market: str = Field(..., description="종목 구분 코드")
    trade_date: str = Field(..., description="최근 거래 일자(UTC) 포맷: yyyyMMdd")
    trade_time: str = Field(..., description="최근 거래 시각(UTC) 포맷: HHmmss")
    trade_date_kst: str = Field(..., description="최근 거래 일자(KST) 포맷: yyyyMMdd")
    trade_time_kst: str = Field(..., description="최근 거래 시각(KST) 포맷: HHmmss")
    trade_timestamp: int = Field(..., description="최근 거래 일시(UTC) 포맷: Unix Timestamp")
    opening_price: float = Field(..., description="시가")
    high_price: float = Field(..., description="고가")
    low_price: float = Field(..., description="저가")
    trade_price: float = Field(..., description="종가(현재가)")
    prev_closing_price: float = Field(..., description="전일 종가(UTC 0시 기준)")
    change: ChangeType = Field(..., description="EVEN: 보합, RISE: 상승, FALL: 하락")
    change_price: float = Field(..., description="변화액의 절대값")
    change_rate: float = Field(..., description="변화율의 절대값")
    signed_change_price: float = Field(..., description="부호가 있는 변화액")
    signed_change_rate: float = Field(..., description="부호가 있는 변화율")
    trade_volume: float = Field(..., description="가장 최근 거래량")
    acc_trade_price: float = Field(..., description="누적 거래대금(UTC 0시 기준)")
    acc_trade_price_24h: float = Field(..., description="24시간 누적 거래대금")
    acc_trade_volume: float = Field(..., description="누적 거래량(UTC 0시 기준)")
    acc_trade_volume_24h: float = Field(..., description="24시간 누적 거래량")
    highest_52_week_price: float = Field(..., description="52주 신고가")
    highest_52_week_date: str = Field(..., description="52주 신고가 달성일 포맷: yyyy-MM-dd")
    lowest_52_week_price: float = Field(..., description="52주 신저가")
    lowest_52_week_date: str = Field(..., description="52주 신저가 달성일 포맷: yyyy-MM-dd")
    timestamp: int = Field(..., description="타임스탬프")


class TickerList(RootModel):
    """여러 종목의 Ticker 정보를 담기 위한 리스트 모델"""
    root: List[Ticker]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]
    
    def __len__(self):
        return len(self.root)
    
    def __contains__(self, item):
        return item in self.root