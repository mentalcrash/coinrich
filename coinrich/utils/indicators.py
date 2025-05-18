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


def bollinger_band_width(data: pd.DataFrame, period: int = 20, std_dev: float = 2.0, 
                        column: str = 'close') -> pd.Series:
    """볼린저 밴드 폭(Bollinger Band Width) 계산
    
    볼린저 밴드의 폭은 시장의 변동성을 나타내며, 
    폭이 좁아지면 횡보장, 폭이 넓어지면 추세장의 신호가 될 수 있음
    
    Args:
        data: OHLCV 데이터프레임
        period: 이동평균 기간
        std_dev: 표준편차 배수
        column: 사용할 가격 컬럼 (기본값: 'close')
        
    Returns:
        볼린저 밴드 폭 시리즈 (상단밴드-하단밴드)/중간밴드
    """
    # 볼린저 밴드 계산
    bb = bollinger_bands(data, period, std_dev, column)
    
    # 밴드 폭 계산 = (상단밴드 - 하단밴드) / 중간밴드
    bb_width = (bb['upper'] - bb['lower']) / bb['middle']
    
    return bb_width


def adx(data: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
    """ADX(Average Directional Index) 계산
    
    ADX는 추세의 강도를 측정하는 지표로, 방향이 아닌 강도만 측정함
    일반적으로 ADX > 25이면 강한 추세, ADX < 20이면 약한 추세(횡보장)로 간주
    
    Args:
        data: OHLCV 데이터프레임 ('high', 'low', 'close' 컬럼 필요)
        period: ADX 계산 기간
        
    Returns:
        {'adx': ADX, 'plus_di': +DI, 'minus_di': -DI} 딕셔너리
    """
    # DM(Directional Movement) 계산
    high_diff = data['high'].diff()
    low_diff = data['low'].diff().mul(-1)  # 음수를 양수로 변환
    
    # +DM과 -DM 계산
    plus_dm = pd.Series(0, index=data.index)
    minus_dm = pd.Series(0, index=data.index)
    
    # +DM: 고가 상승폭 > 저가 하락폭 && 고가 상승폭 > 0
    plus_dm_condition = (high_diff > low_diff) & (high_diff > 0)
    plus_dm.loc[plus_dm_condition] = high_diff.loc[plus_dm_condition]
    
    # -DM: 저가 하락폭 > 고가 상승폭 && 저가 하락폭 > 0
    minus_dm_condition = (low_diff > high_diff) & (low_diff > 0)
    minus_dm.loc[minus_dm_condition] = low_diff.loc[minus_dm_condition]
    
    # TR(True Range) 계산
    tr = atr(data, 1)  # ATR 계산 시 사용한 True Range (EMA 적용 전)
    
    # Smoothed +DM, -DM과 TR 계산
    smoothed_plus_dm = plus_dm.rolling(window=period).sum()
    smoothed_minus_dm = minus_dm.rolling(window=period).sum()
    smoothed_tr = tr.rolling(window=period).sum()
    
    # +DI와 -DI 계산
    plus_di = 100 * (smoothed_plus_dm / smoothed_tr)
    minus_di = 100 * (smoothed_minus_dm / smoothed_tr)
    
    # DX 계산: |+DI - -DI| / (|+DI| + |-DI|) * 100
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).abs())
    
    # ADX 계산: DX의 period 기간 동안의 평균
    adx_value = dx.rolling(window=period).mean()
    
    return {
        'adx': adx_value,
        'plus_di': plus_di,
        'minus_di': minus_di
    }


def is_trending_market(data: pd.DataFrame, 
                       adx_threshold: float = 25.0, 
                       chop_threshold: float = 38.2,
                       adx_period: int = 14,
                       chop_period: int = 14) -> pd.Series:
    """추세장 여부 판단
    
    ADX와 Choppiness Index를 기반으로 추세장 여부를 판단합니다.
    ADX가 높고 Choppiness Index가 낮으면 추세장으로 판단합니다.
    
    Args:
        data: OHLCV 데이터프레임
        adx_threshold: ADX 임계값 (이 값보다 크면 추세장으로 간주)
        chop_threshold: Choppiness Index 임계값 (이 값보다 작으면 추세장으로 간주)
        adx_period: ADX 계산 기간
        chop_period: Choppiness Index 계산 기간
        
    Returns:
        추세장 여부 시리즈 (True/False), ADX 값, Choppiness Index 값
    """
    # ADX 계산 (기간 전달)
    adx_values = adx(data, period=adx_period)['adx']
    
    # Choppiness Index 계산 (기간 전달)
    chop = choppiness_index(data, period=chop_period)
    
    # 추세장 판단 조건
    trending = (adx_values >= adx_threshold) & (chop <= chop_threshold)
    
    return trending, adx_values, chop


def choppiness_index(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Choppiness Index 계산
    
    시장이 추세장인지 횡보장인지 판단하는 지표로,
    0-100 사이의 값을 가지며 값이 높을수록(>60) 횡보장, 낮을수록(<40) 추세장으로 간주함
    
    Args:
        data: OHLCV 데이터프레임
        period: 계산에 사용할 기간
        
    Returns:
        Choppiness Index 시리즈
    """
    high = data['high']
    low = data['low']
    close = data['close']

    # True Range 계산
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    # ATR = TR의 n기간 이동합
    atr_sum = tr.rolling(window=period).sum()

    # n기간 동안의 최고가, 최저가
    high_max = high.rolling(window=period).max()
    low_min = low.rolling(window=period).min()
    price_range = high_max - low_min

    # Chop 계산
    chop = 100 * np.log10(atr_sum / price_range) / np.log10(period)
    
    return chop 