import pandas as pd
import numpy as np
from typing import Union, Optional, Tuple, List, Dict


def moving_average(data: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
    """단순 이동평균(Simple Moving Average) 계산
    
    Args:
        data: OHLCV 데이터프레임
        period: 이동평균 기간
        column: 사용할 가격 컬럼 (기본값: 'close')
        
    Returns:
        이동평균 시리즈
    """
    return data[column].rolling(window=period).mean()


def exponential_moving_average(data: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
    """지수 이동평균(Exponential Moving Average) 계산
    
    Args:
        data: OHLCV 데이터프레임
        period: 이동평균 기간
        column: 사용할 가격 컬럼 (기본값: 'close')
        
    Returns:
        지수 이동평균 시리즈
    """
    return data[column].ewm(span=period, adjust=False).mean()


def bollinger_bands(data: pd.DataFrame, period: int = 20, std_dev: float = 2.0, 
                   column: str = 'close') -> Dict[str, pd.Series]:
    """볼린저 밴드(Bollinger Bands) 계산
    
    Args:
        data: OHLCV 데이터프레임
        period: 이동평균 기간
        std_dev: 표준편차 배수
        column: 사용할 가격 컬럼 (기본값: 'close')
        
    Returns:
        {'upper': 상단 밴드, 'middle': 중간 밴드(SMA), 'lower': 하단 밴드} 딕셔너리
    """
    # 중간 밴드 (단순 이동평균)
    middle_band = moving_average(data, period, column)
    
    # 표준편차 계산
    std = data[column].rolling(window=period).std()
    
    # 상단 및 하단 밴드
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    return {
        'upper': upper_band,
        'middle': middle_band,
        'lower': lower_band
    }


def rsi(data: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """RSI(Relative Strength Index) 계산
    
    Args:
        data: OHLCV 데이터프레임
        period: RSI 계산 기간
        column: 사용할 가격 컬럼 (기본값: 'close')
        
    Returns:
        RSI 시리즈 (0-100)
    """
    # 가격 변화량 계산
    delta = data[column].diff()
    
    # 상승/하락 구분
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # 평균 상승/하락 계산
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # 상대적 강도(RS) 계산
    rs = avg_gain / avg_loss
    
    # RSI 계산 (0-100)
    rsi_values = 100 - (100 / (1 + rs))
    
    return rsi_values


def macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9,
        column: str = 'close') -> Dict[str, pd.Series]:
    """MACD(Moving Average Convergence Divergence) 계산
    
    Args:
        data: OHLCV 데이터프레임
        fast: 빠른 이동평균 기간
        slow: 느린 이동평균 기간
        signal: 시그널 이동평균 기간
        column: 사용할 가격 컬럼 (기본값: 'close')
        
    Returns:
        {'macd': MACD 라인, 'signal': 시그널 라인, 'histogram': 히스토그램} 딕셔너리
    """
    # 빠른 EMA와 느린 EMA 계산
    fast_ema = exponential_moving_average(data, fast, column)
    slow_ema = exponential_moving_average(data, slow, column)
    
    # MACD 라인 = 빠른 EMA - 느린 EMA
    macd_line = fast_ema - slow_ema
    
    # 시그널 라인 = MACD의 EMA
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # 히스토그램 = MACD 라인 - 시그널 라인
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def stochastic(data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
    """스토캐스틱 오실레이터(Stochastic Oscillator) 계산
    
    Args:
        data: OHLCV 데이터프레임
        k_period: %K 기간
        d_period: %D 기간
        
    Returns:
        {'k': %K, 'd': %D} 딕셔너리
    """
    # 최근 k_period 기간 중 최고가/최저가 계산
    low_min = data['low'].rolling(window=k_period).min()
    high_max = data['high'].rolling(window=k_period).max()
    
    # %K 계산: (현재가 - 최저가) / (최고가 - 최저가) * 100
    k = 100 * ((data['close'] - low_min) / (high_max - low_min))
    
    # %D 계산: %K의 d_period 이동평균
    d = k.rolling(window=d_period).mean()
    
    return {'k': k, 'd': d}


def atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR(Average True Range) 계산
    
    Args:
        data: OHLCV 데이터프레임
        period: ATR 계산 기간
        
    Returns:
        ATR 시리즈
    """
    # 전일 종가
    prev_close = data['close'].shift(1)
    
    # True Range 계산 = max(고가-저가, abs(고가-전일종가), abs(저가-전일종가))
    tr1 = data['high'] - data['low']
    tr2 = (data['high'] - prev_close).abs()
    tr3 = (data['low'] - prev_close).abs()
    
    # True Range = 세 가지 중 최대값
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR = True Range의 이동평균
    atr_values = tr.rolling(window=period).mean()
    
    return atr_values


def ichimoku(data: pd.DataFrame, tenkan_period: int = 9, kijun_period: int = 26,
            senkou_span_b_period: int = 52, displacement: int = 26) -> Dict[str, pd.Series]:
    """일목균형표(Ichimoku Cloud) 계산
    
    Args:
        data: OHLCV 데이터프레임
        tenkan_period: 전환선 기간
        kijun_period: 기준선 기간
        senkou_span_b_period: 선행스팬 B 기간
        displacement: 선행스팬 이동 기간
        
    Returns:
        {'tenkan': 전환선, 'kijun': 기준선, 'senkou_a': 선행스팬 A, 
         'senkou_b': 선행스팬 B, 'chikou': 후행스팬} 딕셔너리
    """
    # 전환선 (Tenkan-sen) = (최고가 + 최저가) / 2 (for tenkan_period)
    tenkan = (data['high'].rolling(window=tenkan_period).max() + 
              data['low'].rolling(window=tenkan_period).min()) / 2
    
    # 기준선 (Kijun-sen) = (최고가 + 최저가) / 2 (for kijun_period)
    kijun = (data['high'].rolling(window=kijun_period).max() + 
             data['low'].rolling(window=kijun_period).min()) / 2
    
    # 선행스팬 A (Senkou Span A) = (전환선 + 기준선) / 2 (이동: displacement)
    senkou_a = ((tenkan + kijun) / 2).shift(displacement)
    
    # 선행스팬 B (Senkou Span B) = (최고가 + 최저가) / 2 (for senkou_span_b_period) (이동: displacement)
    senkou_b = ((data['high'].rolling(window=senkou_span_b_period).max() + 
                data['low'].rolling(window=senkou_span_b_period).min()) / 2).shift(displacement)
    
    # 후행스팬 (Chikou Span) = 현재 종가 (이동: -displacement)
    chikou = data['close'].shift(-displacement)
    
    return {
        'tenkan': tenkan,
        'kijun': kijun,
        'senkou_a': senkou_a,
        'senkou_b': senkou_b,
        'chikou': chikou
    }


def obv(data: pd.DataFrame) -> pd.Series:
    """OBV(On-Balance Volume) 계산
    
    Args:
        data: OHLCV 데이터프레임 ('close'와 'volume' 컬럼 필요)
        
    Returns:
        OBV 시리즈
    """
    # 종가 변화 방향
    price_change = data['close'].diff()
    
    # 종가 방향에 따른 볼륨 부호 결정
    volume_sign = pd.Series(0, index=data.index)
    volume_sign[price_change > 0] = 1
    volume_sign[price_change < 0] = -1
    
    # 부호가 적용된 볼륨
    signed_volume = volume_sign * data['volume']
    
    # OBV = 부호가 적용된 볼륨의 누적합
    obv_values = signed_volume.cumsum()
    
    return obv_values 