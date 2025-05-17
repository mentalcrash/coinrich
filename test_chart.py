import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pandas as pd

from coinrich.service.candle_service import CandleService
from coinrich.chart.candle_chart import CandleChart
from coinrich.utils.indicators import bollinger_bands, rsi, macd, stochastic


def test_basic_candle_chart():
    """기본 캔들 차트 테스트"""
    print("\n=== 기본 캔들 차트 테스트 ===")
    
    # 데이터 가져오기 (캐시 활용)
    service = CandleService()
    candles = service.get_minute_candles("KRW-BTC", unit=15, count=100)
    
    # 차트 생성
    chart = CandleChart(title="BTC/KRW - 15분봉", style="binance")
    chart.plot(candles)
    
    # 차트 저장
    filepath = chart.save("btc_basic.png")
    print(f"차트 저장 완료: {filepath}")
    
    # 차트 표시
    chart.show()
    chart.close()
    
    return chart


def test_indicator_chart():
    """지표가 포함된 차트 테스트"""
    print("\n=== 지표가 포함된 차트 테스트 ===")
    
    # 데이터 가져오기 (캐시 활용)
    service = CandleService()
    candles = service.get_minute_candles("KRW-BTC", unit=30, count=100)
    
    # 차트 생성
    chart = CandleChart(title="BTC/KRW - 30분봉 (지표 포함)", style="upbit")
    chart.plot(candles)
    
    # 이동평균선 추가
    chart.add_moving_average([5, 20, 60])
    
    # 차트 저장
    filepath = chart.save("btc_with_ma.png")
    print(f"차트 저장 완료: {filepath}")
    
    # 차트 표시
    chart.show()
    chart.close()
    
    return chart


def test_multi_panel_chart():
    """멀티패널 차트 테스트 (여러 지표)"""
    print("\n=== 멀티패널 차트 테스트 ===")
    
    # 데이터 가져오기 (캐시 활용)
    service = CandleService()
    candles = service.get_minute_candles("KRW-BTC", unit=60, count=100)
    
    # 차트 생성
    chart = CandleChart(title="BTC/KRW - 60분봉 (멀티패널)", style="binance")
    chart.plot(candles)
    
    # 이동평균선 추가
    chart.add_moving_average([5, 20, 60])
    
    # 볼린저 밴드 추가
    chart.add_bollinger_bands(period=20)
    
    # RSI 패널 추가
    chart.add_rsi(period=14)
    
    # MACD 패널 추가
    chart.add_macd()
    
    # 차트 저장
    filepath = chart.save("btc_multi_panel.png")
    print(f"차트 저장 완료: {filepath}")
    
    # 차트 표시
    chart.show()
    chart.close()
    
    return chart


def test_multiple_coins():
    """여러 코인 비교 테스트"""
    print("\n=== 여러 코인 비교 테스트 ===")
    
    # 데이터 가져오기 (캐시 활용)
    service = CandleService()
    btc_candles = service.get_minute_candles("KRW-BTC", unit=60, count=30)
    eth_candles = service.get_minute_candles("KRW-ETH", unit=60, count=30)
    
    # 데이터프레임으로 변환
    btc_df = pd.DataFrame([{
        'datetime': pd.to_datetime(candle.candle_date_time_utc),
        'open': candle.opening_price,
        'high': candle.high_price,
        'low': candle.low_price,
        'close': candle.trade_price,
        'volume': candle.candle_acc_trade_volume
    } for candle in btc_candles])
    btc_df.set_index('datetime', inplace=True)
    
    eth_df = pd.DataFrame([{
        'datetime': pd.to_datetime(candle.candle_date_time_utc),
        'open': candle.opening_price,
        'high': candle.high_price,
        'low': candle.low_price,
        'close': candle.trade_price,
        'volume': candle.candle_acc_trade_volume
    } for candle in eth_candles])
    eth_df.set_index('datetime', inplace=True)
    
    # 종가를 사용해 동일한 시간대 데이터 비교를 위한 정규화
    btc_normalized = btc_df['close'] / btc_df['close'].iloc[0] * 100
    eth_normalized = eth_df['close'] / eth_df['close'].iloc[0] * 100
    
    # 비교 차트 생성
    plt.figure(figsize=(12, 6))
    plt.plot(btc_normalized.index, btc_normalized, label='BTC', linewidth=2)
    plt.plot(eth_normalized.index, eth_normalized, label='ETH', linewidth=2)
    plt.title('BTC vs ETH 가격 변동 비교 (60분봉, 정규화)')
    plt.ylabel('상대 가격 (시작=100)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # 차트 저장
    comparison_path = os.path.join('charts', 'coin_comparison.png')
    os.makedirs('charts', exist_ok=True)
    plt.savefig(comparison_path)
    print(f"비교 차트 저장 완료: {comparison_path}")
    
    plt.show()
    plt.close()


if __name__ == "__main__":
    # 테스트할 함수 선택하여 실행
    # test_basic_candle_chart()
    # test_indicator_chart()
    test_multi_panel_chart()
    # test_multiple_coins() 