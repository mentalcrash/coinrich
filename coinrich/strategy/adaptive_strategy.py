import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any

from coinrich.utils.indicators import (
    moving_average, bollinger_bands, rsi, adx, is_trending_market
)


class AdaptivePositionStrategy:
    """적응형 포지션 전략
    
    시장 상태(추세장/횡보장)에 따라 다른 전략을 적용하며,
    매수 전략과 매도 전략을 분리하여 구현합니다.
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Args:
            params: 전략 파라미터 딕셔너리
        """
        self.params = params or {}
        
        # 시장 상태 판별 파라미터
        self.adx_threshold = self.params.get('adx_threshold', 25)
        self.bb_width_percentile = self.params.get('bb_width_percentile', 70)
        
        # 이동평균선 파라미터
        self.ma_short_period = self.params.get('ma_short_period', 20)
        self.ma_long_period = self.params.get('ma_long_period', 50)
        
        # 볼린저 밴드 파라미터
        self.bb_period = self.params.get('bb_period', 20)
        self.bb_std_dev = self.params.get('bb_std_dev', 2.0)
        
        # RSI 파라미터
        self.rsi_period = self.params.get('rsi_period', 14)
        self.rsi_oversold = self.params.get('rsi_oversold', 30)
        self.rsi_overbought = self.params.get('rsi_overbought', 70)
        
        # 손익 관리 파라미터
        self.take_profit = self.params.get('take_profit', 0.05)  # 5% 익절
        self.stop_loss = self.params.get('stop_loss', 0.02)  # 2% 손절
        
    def analyze_market(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """시장 상태 분석
        
        Args:
            data: OHLCV 데이터프레임
            
        Returns:
            (trending, adx_values, bb_width): 추세장 여부, ADX 값, BB 폭
        """
        trending, adx_values, bb_width = is_trending_market(
            data, 
            adx_threshold=self.adx_threshold, 
            bb_width_percentile=self.bb_width_percentile
        )
        return trending, adx_values, bb_width
    
    def detect_market_state_change(self, trending: pd.Series, lookback: int = 1) -> pd.Series:
        """시장 상태 변화 감지
        
        Args:
            trending: 추세장 여부 시리즈
            lookback: 몇 기간 전과 비교할지
            
        Returns:
            변화 감지 시리즈 (True/False)
        """
        changes = pd.Series(False, index=trending.index)
        
        for i in range(lookback, len(trending)):
            # 현재와 과거 상태 비교
            if trending.iloc[i] != trending.iloc[i-lookback]:
                changes.loc[changes.index[i]] = True
        
        return changes
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산
        
        Args:
            data: OHLCV 데이터프레임
            
        Returns:
            지표가 추가된 데이터프레임
        """
        df = data.copy()
        
        # 이동평균
        df['ma_short'] = moving_average(df, self.ma_short_period)
        df['ma_long'] = moving_average(df, self.ma_long_period)
        
        # 볼린저 밴드
        bb = bollinger_bands(df, self.bb_period, self.bb_std_dev)
        df['bb_upper'] = bb['upper']
        df['bb_middle'] = bb['middle']
        df['bb_lower'] = bb['lower']
        
        # RSI
        df['rsi'] = rsi(df, self.rsi_period)
        
        # ADX
        adx_result = adx(df)
        df['adx'] = adx_result['adx']
        df['plus_di'] = adx_result['plus_di']
        df['minus_di'] = adx_result['minus_di']
        
        return df
    
    def entry_signals(self, data: pd.DataFrame, trending: pd.Series) -> pd.Series:
        """매수 신호 생성 (포지션 없을 때)
        
        Args:
            data: 지표가 계산된 데이터프레임
            trending: 추세장 여부 시리즈
            
        Returns:
            매수 시그널 시리즈 (True/False)
        """
        buy_signals = pd.Series(False, index=data.index)
        
        for i in range(1, len(data)):
            if trending.iloc[i]:
                # 추세장 매수 전략: 골든 크로스 또는 +DI > -DI
                golden_cross = (data.loc[data.index[i], 'ma_short'] > data.loc[data.index[i], 'ma_long'] and 
                               data.loc[data.index[i-1], 'ma_short'] <= data.loc[data.index[i-1], 'ma_long'])
                
                di_cross = (data.loc[data.index[i], 'plus_di'] > data.loc[data.index[i], 'minus_di'] and
                           data.loc[data.index[i-1], 'plus_di'] <= data.loc[data.index[i-1], 'minus_di'])
                
                if golden_cross or di_cross:
                    buy_signals.loc[data.index[i]] = True
            else:
                # 횡보장 매수 전략: 볼린저 하단 터치 또는 RSI 과매도
                bb_bottom = data.loc[data.index[i], 'close'] <= data.loc[data.index[i], 'bb_lower']
                rsi_oversold = data.loc[data.index[i], 'rsi'] < self.rsi_oversold
                
                if bb_bottom or rsi_oversold:
                    buy_signals.loc[data.index[i]] = True
        
        return buy_signals
    
    def exit_signals(self, data: pd.DataFrame, trending: pd.Series, 
                    position_open_price: Optional[float] = None) -> pd.Series:
        """매도 신호 생성 (포지션 있을 때)
        
        Args:
            data: 지표가 계산된 데이터프레임
            trending: 추세장 여부 시리즈
            position_open_price: 진입 가격 (손익 계산용)
            
        Returns:
            매도 시그널 시리즈 (True/False)
        """
        sell_signals = pd.Series(False, index=data.index)
        
        # 시장 상태 변화 감지
        state_change = self.detect_market_state_change(trending)
        
        for i in range(1, len(data)):
            # 시장 상태 변화 시 매도
            if state_change.iloc[i]:
                sell_signals.loc[data.index[i]] = True
                continue
            
            # 전략별 매도 로직
            if trending.iloc[i]:
                # 추세장 매도 전략: 데드 크로스 또는 +DI < -DI
                dead_cross = (data.loc[data.index[i], 'ma_short'] < data.loc[data.index[i], 'ma_long'] and 
                             data.loc[data.index[i-1], 'ma_short'] >= data.loc[data.index[i-1], 'ma_long'])
                
                di_cross = (data.loc[data.index[i], 'plus_di'] < data.loc[data.index[i], 'minus_di'] and
                           data.loc[data.index[i-1], 'plus_di'] >= data.loc[data.index[i-1], 'minus_di'])
                
                if dead_cross or di_cross:
                    sell_signals.loc[data.index[i]] = True
            else:
                # 횡보장 매도 전략: 볼린저 상단 터치 또는 RSI 과매수
                bb_top = data.loc[data.index[i], 'close'] >= data.loc[data.index[i], 'bb_upper']
                rsi_overbought = data.loc[data.index[i], 'rsi'] > self.rsi_overbought
                
                if bb_top or rsi_overbought:
                    sell_signals.loc[data.index[i]] = True
            
            # 손익 기반 매도 로직
            if position_open_price:
                current_price = data.loc[data.index[i], 'close']
                profit_pct = (current_price - position_open_price) / position_open_price
                
                # 익절
                if profit_pct >= self.take_profit:
                    sell_signals.loc[data.index[i]] = True
                
                # 손절
                if profit_pct <= -self.stop_loss:
                    sell_signals.loc[data.index[i]] = True
        
        return sell_signals
    
    def generate_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """전체 신호 생성 (백테스팅용)
        
        백테스팅에서는 포지션 보유 여부를 모르기 때문에,
        매수/매도 신호를 모두 생성하고 백테스팅 시 적용합니다.
        
        Args:
            data: OHLCV 데이터프레임
            
        Returns:
            (buy_signals, sell_signals, trending): 매수신호, 매도신호, 추세장여부
        """
        # 기술적 지표 계산
        df = self.calculate_indicators(data)
        
        # 시장 상태 분석
        trending, _, _ = self.analyze_market(df)
        
        # 매수/매도 신호 생성
        buy_signals = self.entry_signals(df, trending)
        sell_signals = self.exit_signals(df, trending)
        
        return buy_signals, sell_signals, trending 