# coinrich/models/market.py
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, RootModel

class MarketEvent(BaseModel):
    """시장 경보 정보"""
    warning: Optional[bool] = Field(None, description="유의종목 지정 여부")
    caution: Optional[Dict[str, bool]] = Field(None, description="주의종목 지정 여부")


class Market(BaseModel):
    """종목 정보 모델"""
    market: str = Field(..., description="마켓 코드 (예: KRW-BTC)")
    korean_name: str = Field(..., description="거래 대상 디지털 자산 한글명")
    english_name: str = Field(..., description="거래 대상 디지털 자산 영문명")
    market_event: Optional[MarketEvent] = Field(None, description="시장 경보 상태")


class MarketList(RootModel):
    """종목 리스트 응답 모델"""
    root: List[Market]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]
    
    def __len__(self):
        return len(self.root)
    
    def __contains__(self, item):
        return item in self.root