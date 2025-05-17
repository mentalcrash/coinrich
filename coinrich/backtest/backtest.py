import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from coinrich.strategy.adaptive_strategy import AdaptivePositionStrategy
from coinrich.backtest.backtest_result import BacktestResult
from coinrich.chart.candle_chart import CandleChart


class Backtest:
    """백테스트 클래스
    
    트레이딩 전략의 과거 성과를 테스트하고 분석합니다.
    """
    
    def __init__(self, 
                 data: pd.DataFrame, 
                 strategy: AdaptivePositionStrategy,
                 initial_capital: float = 1000000,
                 position_size: float = 1.0,
                 commission: float = 0.0005):  # 0.05% 수수료
        """
        Args:
            data: OHLCV 데이터프레임
            strategy: 트레이딩 전략 (AdaptivePositionStrategy)
            initial_capital: 초기 자본
            position_size: 자본 대비 포지션 크기 비율 (0~1)
            commission: 거래 수수료 (ex: 0.0005 = 0.05%)
        """
        self.data = data.copy()
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.commission = commission
    
    def run(self) -> Tuple[BacktestResult, pd.DataFrame]:
        """백테스트 실행
        
        Returns:
            (result, results_df): 백테스트 결과와 백테스트 데이터프레임
        """
        # 기술적 지표 계산
        df = self.strategy.calculate_indicators(self.data)
        
        # 시장 상태 분석
        trending, adx_values, bb_width = self.strategy.analyze_market(df)
        
        # 시장 상태 추가
        df['trending'] = trending
        df['market_state'] = trending.apply(lambda x: 'trending' if x else 'ranging')
        
        # 결과 저장용 컬럼 추가
        df['position'] = 0  # 0: 미보유, 1: 매수 포지션
        df['capital'] = self.initial_capital  # 보유 현금
        df['coin_value'] = 0  # 코인 가치
        df['equity'] = self.initial_capital  # 총 자산 가치
        
        # 거래 기록
        trades = []
        current_position = None
        
        # 백테스팅 루프
        for i in range(1, len(df)):
            # 이전 상태 복사
            df['position'].iloc[i] = df['position'].iloc[i-1]
            df['capital'].iloc[i] = df['capital'].iloc[i-1]
            df['coin_value'].iloc[i] = df['coin_value'].iloc[i-1]
            
            current_price = df['close'].iloc[i]
            
            # 포지션이 없는 경우: 매수 신호 확인
            if df['position'].iloc[i-1] == 0:
                # 매수 전략 적용 (entry_signals)
                entry_df = df.iloc[:i+1].copy()
                buy_signal = self.strategy.entry_signals(entry_df, trending.iloc[:i+1]).iloc[-1]
                
                if buy_signal:
                    # 매수 실행
                    # 자본의 position_size 비율만큼 사용
                    investment = df['capital'].iloc[i] * self.position_size
                    
                    # 수수료 계산
                    fee = investment * self.commission
                    actual_investment = investment - fee
                    
                    # 구매 수량
                    quantity = actual_investment / current_price
                    
                    # 자본 차감 및 코인 가치 증가
                    df['capital'].iloc[i] -= investment
                    df['coin_value'].iloc[i] = quantity * current_price
                    df['position'].iloc[i] = 1
                    
                    # 거래 기록 시작
                    current_position = {
                        'entry_date': df.index[i],
                        'entry_price': current_price,
                        'quantity': quantity,
                        'investment': investment,
                        'fee_paid': fee,
                        'market_state': df['market_state'].iloc[i]
                    }
            
            # 포지션이 있는 경우: 매도 신호 확인
            elif df['position'].iloc[i-1] == 1 and current_position is not None:
                # 포지션 가치 업데이트
                df['coin_value'].iloc[i] = current_position['quantity'] * current_price
                
                # 매도 전략 적용 (exit_signals)
                exit_df = df.iloc[:i+1].copy()
                sell_signal = self.strategy.exit_signals(
                    exit_df, 
                    trending.iloc[:i+1],
                    current_position['entry_price']
                ).iloc[-1]
                
                if sell_signal:
                    # 매도 실행
                    sell_value = df['coin_value'].iloc[i]
                    
                    # 수수료 계산
                    fee = sell_value * self.commission
                    actual_sell_value = sell_value - fee
                    
                    # 자본 증가 및 코인 가치 제거
                    df['capital'].iloc[i] += actual_sell_value
                    df['coin_value'].iloc[i] = 0
                    df['position'].iloc[i] = 0
                    
                    # 거래 완료 기록
                    pnl = actual_sell_value - current_position['investment']
                    pnl_pct = pnl / current_position['investment']
                    
                    current_position.update({
                        'exit_date': df.index[i],
                        'exit_price': current_price,
                        'exit_value': sell_value,
                        'exit_fee': fee,
                        'total_fee': fee + current_position['fee_paid'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_market_state': df['market_state'].iloc[i]
                    })
                    
                    trades.append(current_position)
                    current_position = None
            
            # 자산 가치 계산
            df['equity'].iloc[i] = df['capital'].iloc[i] + df['coin_value'].iloc[i]
        
        # 백테스트 결과 반환
        result = BacktestResult(df['equity'], df['position'], trades)
        
        return result, df
    
    def visualize(self, result: BacktestResult, data: pd.DataFrame) -> CandleChart:
        """백테스트 결과 시각화
        
        Args:
            result: 백테스트 결과
            data: 백테스트 데이터프레임
            
        Returns:
            chart: 생성된 차트 객체
        """
        # 캔들 차트 생성 - 더 큰 사이즈로 설정
        chart = CandleChart(title="Adaptive Strategy Backtest", style="korean", 
                          width=1500, height=1000)
        
        # 데이터 필터링 - 마지막 50개 캔들만 표시하여 캔들이 더 넓게 보이도록 함
        display_data = self.data.iloc[-50:].copy()
        
        # 필터링된 데이터로 차트 생성
        chart.plot(display_data)
        
        # 이동평균선 추가
        chart.add_moving_average([self.strategy.ma_short_period, self.strategy.ma_long_period])
        
        # 볼린저 밴드 추가
        chart.add_bollinger_bands(period=self.strategy.bb_period, std_dev=self.strategy.bb_std_dev)
        
        # 필터링된 데이터에 해당하는 인덱스만 표시
        filtered_idx = display_data.index
        filtered_data = data[data.index.isin(filtered_idx)]
        
        # 시장 상태 배경색 표시
        for i in range(1, len(filtered_data)):
            idx = filtered_data.index[i-1]
            next_idx = filtered_data.index[i]
            
            if idx in filtered_idx and next_idx in filtered_idx:
                if filtered_data['trending'].iloc[i]:
                    chart.axes[0].axvspan(idx, next_idx, 
                                        alpha=0.2, color='green')
                else:
                    chart.axes[0].axvspan(idx, next_idx, 
                                        alpha=0.1, color='gray')
        
        # 매수/매도 포인트 표시 - 필터링된 기간 내 거래만 표시
        for trade in result.trades:
            entry_date = trade['entry_date']
            exit_date = trade['exit_date']
            
            # 표시 기간 내 거래만 필터링
            if entry_date in filtered_idx or exit_date in filtered_idx:
                # 매수 지점이 표시 범위 내에 있는 경우
                if entry_date in filtered_idx:
                    # 매수 지점 - 더 크고 뚜렷하게 표시
                    chart.annotate("BUY", 
                                (entry_date, display_data.loc[entry_date, 'low'] * 0.995), 
                                color='green', arrow=True)
                
                # 매도 지점이 표시 범위 내에 있는 경우
                if exit_date in filtered_idx:
                    # 매도 지점 - 더 크고 뚜렷하게 표시
                    chart.annotate("SELL", 
                                (exit_date, display_data.loc[exit_date, 'high'] * 1.005), 
                                color='red', arrow=True)
                    
                    # 수익률 표시
                    pnl_text = f"{trade['pnl_pct']*100:.1f}%"
                    color = 'green' if trade['pnl'] > 0 else 'red'
                    chart.annotate(pnl_text, 
                                (exit_date, display_data.loc[exit_date, 'high'] * 1.01), 
                                color=color, arrow=False)
        
        # 백테스트 정보 텍스트 추가
        info_text = (
            f"Total Return: {result.total_return*100:.1f}%\n"
            f"Max Drawdown: {result.max_drawdown*100:.1f}%\n"
            f"Trades: {result.num_trades}\n"
            f"Win Rate: {result.win_rate*100:.1f}%"
        )
        chart.axes[0].text(0.02, 0.05, info_text, transform=chart.axes[0].transAxes, 
                          fontsize=12, bbox=dict(facecolor='white', alpha=0.7))
        
        # 자산 가치 패널 추가
        equity_ax = chart.fig.add_axes([0.1, 0.05, 0.8, 0.15])
        
        # 자산 가치는 전체 기간 표시 (필터링 안함)
        equity_ax.plot(result.equity.loc[filtered_idx], color='blue', linewidth=1.5)
        equity_ax.set_title('Equity Curve')
        equity_ax.grid(True, alpha=0.3)
        
        # 차트 저장
        chart.save("adaptive_strategy_backtest.png")
        
        return chart 