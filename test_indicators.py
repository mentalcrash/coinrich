import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta

from coinrich.service.candle_service import CandleService
from coinrich.utils.indicators import (
    bollinger_bands, bollinger_band_width, 
    adx, is_trending_market, rsi, macd
)


def test_bollinger_band_width():
    """볼린저 밴드 폭 테스트"""
    print("\n=== 볼린저 밴드 폭 테스트 ===")
    
    # 데이터 가져오기
    service = CandleService()
    candles = service.get_minute_candles("KRW-BTC", unit=30, count=200)
    
    # DataFrame으로 변환
    candle_data = []
    for candle in candles:
        candle_data.append({
            'datetime': pd.to_datetime(candle.candle_date_time_utc),
            'open': candle.opening_price,
            'high': candle.high_price,
            'low': candle.low_price,
            'close': candle.trade_price,
            'volume': candle.candle_acc_trade_volume
        })
    
    df = pd.DataFrame(candle_data)
    df.set_index('datetime', inplace=True)
    df.sort_index(inplace=True)
    
    # 볼린저 밴드 및 밴드 폭 계산
    bb = bollinger_bands(df, period=20, std_dev=2.0)
    bb_width = bollinger_band_width(df, period=20, std_dev=2.0)
    
    print(f"데이터 샘플 수: {len(df)}")
    print(f"볼린저 밴드 폭 평균: {bb_width.mean():.4f}")
    print(f"볼린저 밴드 폭 최소: {bb_width.min():.4f}")
    print(f"볼린저 밴드 폭 최대: {bb_width.max():.4f}")
    
    # 차트 저장 디렉토리 생성
    os.makedirs('charts', exist_ok=True)
    
    # 볼린저 밴드 및 밴드 폭 시각화
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # 상단 차트 - 가격 및 볼린저 밴드
    ax1.plot(df.index, df['close'], label='Price', color='#333333')
    ax1.plot(df.index, bb['upper'], label='Upper Band', color='red', linestyle='--')
    ax1.plot(df.index, bb['middle'], label='Middle Band', color='blue')
    ax1.plot(df.index, bb['lower'], label='Lower Band', color='green', linestyle='--')
    ax1.set_title('BTC/KRW Price with Bollinger Bands')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 하단 차트 - 볼린저 밴드 폭
    ax2.plot(df.index, bb_width, label='BB Width', color='purple')
    ax2.set_title('Bollinger Band Width')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=bb_width.mean(), color='black', linestyle='--', label='Average')
    ax2.legend()
    
    plt.tight_layout()
    filepath = os.path.join('charts', 'bollinger_band_width.png')
    plt.savefig(filepath, dpi=300)
    print(f"차트 저장 완료: {filepath}")
    
    plt.show()
    plt.close()


def test_adx():
    """ADX 지표 테스트"""
    print("\n=== ADX 지표 테스트 ===")
    
    # 데이터 가져오기
    service = CandleService()
    candles = service.get_minute_candles("KRW-BTC", unit=30, count=200)
    
    # DataFrame으로 변환
    candle_data = []
    for candle in candles:
        candle_data.append({
            'datetime': pd.to_datetime(candle.candle_date_time_utc),
            'open': candle.opening_price,
            'high': candle.high_price,
            'low': candle.low_price,
            'close': candle.trade_price,
            'volume': candle.candle_acc_trade_volume
        })
    
    df = pd.DataFrame(candle_data)
    df.set_index('datetime', inplace=True)
    df.sort_index(inplace=True)
    
    # ADX 계산
    adx_result = adx(df, period=14)
    
    print(f"데이터 샘플 수: {len(df)}")
    print(f"ADX 평균: {adx_result['adx'].mean():.2f}")
    print(f"ADX 최소: {adx_result['adx'].min():.2f}")
    print(f"ADX 최대: {adx_result['adx'].max():.2f}")
    
    # 차트 저장 디렉토리 생성
    os.makedirs('charts', exist_ok=True)
    
    # ADX 시각화
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 2]})
    
    # 상단 차트 - 가격
    ax1.plot(df.index, df['close'], label='BTC Price', color='#333333')
    ax1.set_title('BTC/KRW Price')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 하단 차트 - ADX, +DI, -DI
    ax2.plot(df.index, adx_result['adx'], label='ADX', color='purple', linewidth=2)
    ax2.plot(df.index, adx_result['plus_di'], label='+DI', color='green')
    ax2.plot(df.index, adx_result['minus_di'], label='-DI', color='red')
    ax2.axhline(y=25, color='black', linestyle='--', label='Threshold (25)')
    ax2.set_title('ADX Indicator')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    filepath = os.path.join('charts', 'adx_indicator.png')
    plt.savefig(filepath, dpi=300)
    print(f"차트 저장 완료: {filepath}")
    
    plt.show()
    plt.close()


def test_trending_market():
    """추세장 판별 테스트"""
    print("\n=== 추세장 판별 테스트 ===")
    
    # 데이터 가져오기
    service = CandleService()
    candles = service.get_minute_candles("KRW-BTC", unit=30, count=200)
    
    # DataFrame으로 변환
    candle_data = []
    for candle in candles:
        candle_data.append({
            'datetime': pd.to_datetime(candle.candle_date_time_utc),
            'open': candle.opening_price,
            'high': candle.high_price,
            'low': candle.low_price,
            'close': candle.trade_price,
            'volume': candle.candle_acc_trade_volume
        })
    
    df = pd.DataFrame(candle_data)
    df.set_index('datetime', inplace=True)
    df.sort_index(inplace=True)
    
    # 추세장 판별
    trending, adx_values, bb_width = is_trending_market(df, adx_threshold=25, bb_width_percentile=70)
    
    # 추세장 및 횡보장 통계
    trend_count = trending.sum()
    total_count = len(trending)
    trend_percent = (trend_count / total_count) * 100
    
    print(f"데이터 샘플 수: {total_count}")
    print(f"추세장 구간 수: {trend_count} ({trend_percent:.1f}%)")
    print(f"횡보장 구간 수: {total_count - trend_count} ({100 - trend_percent:.1f}%)")
    
    # 차트 저장 디렉토리 생성
    os.makedirs('charts', exist_ok=True)
    
    # 시각화
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), gridspec_kw={'height_ratios': [3, 1, 1]})
    
    # 상단 차트 - 가격 및 추세장 배경 표시
    ax1.plot(df.index, df['close'], label='BTC Price', color='#333333')
    
    # 추세장 배경색 표시
    for i in range(len(trending)):
        if i > 0 and trending.iloc[i]:
            ax1.axvspan(trending.index[i-1], trending.index[i], alpha=0.2, color='green')
    
    ax1.set_title('BTC/KRW Price with Trend Highlighting')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 중간 차트 - ADX
    ax2.plot(adx_values.index, adx_values, label='ADX', color='purple')
    ax2.axhline(y=25, color='black', linestyle='--', label='ADX Threshold (25)')
    ax2.set_title('ADX Indicator')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 하단 차트 - 볼린저 밴드 폭
    ax3.plot(bb_width.index, bb_width, label='BB Width', color='blue')
    ax3.set_title('Bollinger Band Width')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    filepath = os.path.join('charts', 'trend_identification.png')
    plt.savefig(filepath, dpi=300)
    print(f"차트 저장 완료: {filepath}")
    
    plt.show()
    plt.close()


if __name__ == "__main__":
    # 테스트할 함수 선택하여 실행
    test_bollinger_band_width()
    test_adx()
    test_trending_market() 