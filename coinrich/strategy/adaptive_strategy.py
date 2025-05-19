import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any

from coinrich.utils.indicators import (
    moving_average, bollinger_bands, rsi, adx, is_trending_market, macd, atr
)
from coinrich.utils.signals import (
    rsi_bollinger_buy_signal,
    macd_histogram_volume_buy_signal,
    bullish_engulfing_ema_buy_signal,
    fixed_risk_exit_signal,
    macd_histogram_exit_signal,
    rsi_overbought_reversal_exit_signal,
    trailing_stop_exit_signal,
    strong_macd_volume_signal,
    atr_risk_exit_signal,
    ema_pullback_buy_signal
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
        self.chop_threshold = self.params.get('chop_threshold', 38.2)
        self.adx_period = self.params.get('adx_period', 14)
        self.chop_period = self.params.get('chop_period', 14)
        
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
        
    def analyze_market(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """시장 상태 분석
        
        Args:
            data: OHLCV 데이터프레임
            
        Returns:
            (trending, adx_values, chop_values, trend_direction): 추세장 여부, ADX 값, Choppiness Index 값, 추세 방향
        """
        trending, adx_values, chop_values, trend_direction = is_trending_market(
            data, 
            adx_threshold=self.adx_threshold, 
            chop_threshold=self.chop_threshold,
            adx_period=self.adx_period,
            chop_period=self.chop_period
        )
        return trending, adx_values, chop_values, trend_direction
    
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
        
        # MACD
        macd_result = macd(df)
        df['macd'] = macd_result['macd']
        df['signal'] = macd_result['signal']
        df['histogram'] = macd_result['histogram']

        df['atr'] = atr(df)
        
        return df
    
    def entry_signals(self, data: pd.DataFrame) -> pd.Series:
        """매수 신호 생성 (포지션 없을 때)"""
        # 보편적 매수 조건 (추세/횡보 무관)
        signal_rsi_bb = rsi_bollinger_buy_signal(data, self.rsi_oversold)
        signal_macd_vol = macd_histogram_volume_buy_signal(data)
        signal_candle_ema = bullish_engulfing_ema_buy_signal(data, ema_period=self.ma_short_period)
        signal_pullback = ema_pullback_buy_signal(data, ema_period=20)

        # Strong signal: MACD-volume + 강한 거래량
        
        strong_signal = strong_macd_volume_signal(data, volume_multiplier=1.2)

        # Base entry: 2개 이상 신호
        combined_hits = (
            1*signal_rsi_bb.astype(int) +
            2*signal_macd_vol.astype(int) +
            1*signal_candle_ema.astype(int) +
            1*signal_pullback.astype(int)
        )
        base_entry = combined_hits >= 2
        buy_signals = base_entry | strong_signal

        return buy_signals
    
    def exit_signals(self, data: pd.DataFrame, position_open_price: Optional[float] = None) -> pd.Series:
        """매도 신호 생성 (포지션 있을 때)"""
        sell_signals = pd.Series(False, index=data.index)

        if position_open_price is None:
            return sell_signals

        current_price = data['close']

        condition_risk = atr_risk_exit_signal(
            current_price=current_price,
            entry_price=position_open_price,
            atr_series=data['atr'],
            stop_mult=0.8,
            tp_mult=2.2
        )

        # 조건 B: MACD 히스토그램 음전환
        condition_macd = macd_histogram_exit_signal(data)

        # 조건 C: RSI 과매수 후 하락 반전
        condition_rsi = rsi_overbought_reversal_exit_signal(data, self.rsi_overbought)

        # 조건 D: 트레일링 스탑
        condition_trailing = trailing_stop_exit_signal(
            entry_price=position_open_price,
            current_price=current_price,
            fallback=0.013
        )

        for i in range(1, len(data)):
            if condition_risk.iloc[i]:
                sell_signals.iloc[i] = True
                continue
            if condition_macd.iloc[i] or condition_rsi.iloc[i] or condition_trailing.iloc[i]:
                sell_signals.iloc[i] = True

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
        trending, _, _, trend_direction = self.analyze_market(df)
        
        # 매수/매도 신호 생성
        buy_signals = self.entry_signals(df, trending, trend_direction)
        sell_signals = self.exit_signals(df, trending, trend_direction)
        
        return buy_signals, sell_signals, trending