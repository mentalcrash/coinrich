import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates

from coinrich.service.candle_service import CandleService
from coinrich.strategy.adaptive_strategy import AdaptivePositionStrategy
from coinrich.backtest.backtest import Backtest


def test_adaptive_strategy():
    """적응형 포지션 전략 백테스팅 테스트"""
    print("\n=== Adaptive Position Strategy Backtest ===")
    
    # 데이터 가져오기
    service = CandleService()
    candles = service.get_minute_candles("KRW-BTC", unit=60, count=200)
    
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
    # inplace=True 제거하고 새 DataFrame에 할당
    df = df.set_index('datetime')
    df = df.sort_index()
    
    # 전략 파라미터
    strategy_params = {
        'adx_threshold': 25,           # ADX 임계값
        'bb_width_percentile': 70,     # 볼린저 밴드 폭 백분위수
        'ma_short_period': 20,         # 단기 이동평균
        'ma_long_period': 50,          # 장기 이동평균
        'bb_period': 20,               # 볼린저 밴드 기간
        'bb_std_dev': 2.0,             # 볼린저 밴드 표준편차
        'rsi_period': 14,              # RSI 기간
        'rsi_oversold': 30,            # RSI 과매도 기준
        'rsi_overbought': 70,          # RSI 과매수 기준
        'take_profit': 0.05,           # 5% 익절
        'stop_loss': 0.02              # 2% 손절
    }
    
    # 백테스트 파라미터
    backtest_params = {
        'initial_capital': 1000000,    # 초기 자본 (100만원)
        'position_size': 0.5,          # 자본의 50%만 사용
        'commission': 0.0005           # 0.05% 수수료
    }
    
    # 전략 및 백테스트 객체 생성
    strategy = AdaptivePositionStrategy(strategy_params)
    backtest = Backtest(
        df, 
        strategy, 
        initial_capital=backtest_params['initial_capital'],
        position_size=backtest_params['position_size'],
        commission=backtest_params['commission']
    )
    
    # 백테스트 실행
    result, df_result = backtest.run()
    
    # 백테스트 결과 출력
    print(result.summary())
    print()
    print(result.trade_summary())
    
    # 시장 유형별 성과 분석
    trade_stats = result.trade_statistics()
    print("\n=== Performance by Market Type ===")
    print(f"Total trades: {trade_stats['total_trades']}")
    print(f"Overall win rate: {trade_stats['win_rate']*100:.1f}%")
    
    if 'trending_win_rate' in trade_stats:
        print(f"Trending market win rate: {trade_stats['trending_win_rate']*100:.1f}%")
        print(f"Trending market avg return: {trade_stats['trending_avg_return']*100:.2f}%")
    
    if 'ranging_win_rate' in trade_stats:
        print(f"Ranging market win rate: {trade_stats['ranging_win_rate']*100:.1f}%")
        print(f"Ranging market avg return: {trade_stats['ranging_avg_return']*100:.2f}%")
    
    # 결과 시각화
    chart = backtest.visualize(result, df_result)
    
    # X축 정보 출력
    print("\n=== X-Axis Information ===")
    print(f"X-axis type: {type(chart.axes[0].xaxis)}")
    print(f"X-axis limits: {chart.axes[0].get_xlim()}")
    print(f"X-axis ticks: {chart.axes[0].get_xticks()}")
    print(f"X-axis formatter: {chart.axes[0].xaxis.get_major_formatter()}")
    
    # X축 데이터와 인덱스 매핑 확인
    x_min, x_max = chart.axes[0].get_xlim()
    print(f"X-axis min date: {mdates.num2date(x_min)}")
    print(f"X-axis max date: {mdates.num2date(x_max)}")
    
    # 데이터 인덱스 확인
    print("\n=== DataFrame Index ===")
    print(f"First date: {df_result.index[0]}")
    print(f"Last date: {df_result.index[-1]}")
    print(f"Total dates: {len(df_result.index)}")
    
    # 차트 표시
    chart.show()
    
    return result, df_result, chart


if __name__ == "__main__":
    test_adaptive_strategy() 