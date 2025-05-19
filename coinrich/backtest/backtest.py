import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

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
        trending, adx_values, bb_width, trend_direction = self.strategy.analyze_market(df)
        
        # 시장 상태 추가
        df['trending'] = trending
        df['market_state'] = trending.apply(lambda x: 'trending' if x else 'ranging')
        df['trend_direction'] = trend_direction  # 추세 방향성 컬럼 추가
        
        # 결과 저장용 컬럼 추가 - 데이터 타입 명시
        df['position'] = 0  # 0: 미보유, 1: 매수 포지션
        df['capital'] = float(self.initial_capital)  # 보유 현금
        df['coin_value'] = 0.0  # 코인 가치
        df['equity'] = float(self.initial_capital)  # 총 자산 가치
        
        # 거래 기록
        trades = []
        current_position = None
        
        # 백테스팅 루프
        for i in range(1, len(df)):
            # 이전 상태 복사 - .loc 사용하여 할당
            df.loc[df.index[i], 'position'] = df.loc[df.index[i-1], 'position']
            df.loc[df.index[i], 'capital'] = float(df.loc[df.index[i-1], 'capital'])
            df.loc[df.index[i], 'coin_value'] = float(df.loc[df.index[i-1], 'coin_value'])
            
            current_price = df.loc[df.index[i], 'close']
            
            # 포지션이 없는 경우: 매수 신호 확인
            if df.loc[df.index[i-1], 'position'] == 0:
                # 매수 전략 적용 (entry_signals)
                entry_df = df.iloc[:i+1].copy()
                buy_signal = self.strategy.entry_signals(entry_df).iloc[-1]
                
                if buy_signal:
                    # 매수 실행
                    # 자본의 position_size 비율만큼 사용
                    investment = float(df.loc[df.index[i], 'capital']) * self.position_size
                    
                    # 수수료 계산
                    fee = investment * self.commission
                    actual_investment = investment - fee
                    
                    # 구매 수량
                    quantity = actual_investment / current_price
                    
                    # 자본 차감 및 코인 가치 증가
                    df.loc[df.index[i], 'capital'] = float(df.loc[df.index[i], 'capital']) - investment
                    df.loc[df.index[i], 'coin_value'] = float(quantity * current_price)
                    df.loc[df.index[i], 'position'] = 1
                    
                    # 거래 기록 시작
                    current_position = {
                        'entry_date': df.index[i],
                        'entry_price': current_price,
                        'quantity': quantity,
                        'investment': investment,
                        'fee_paid': fee,
                        'market_state': df.loc[df.index[i], 'market_state']
                    }
            
            # 포지션이 있는 경우: 매도 신호 확인
            elif df.loc[df.index[i-1], 'position'] == 1 and current_position is not None:
                # 포지션 가치 업데이트
                df.loc[df.index[i], 'coin_value'] = float(current_position['quantity'] * current_price)
                
                # 매도 전략 적용 (exit_signals)
                exit_df = df.iloc[:i+1].copy()
                sell_signal = self.strategy.exit_signals(
                    exit_df, 
                    current_position['entry_price']
                ).iloc[-1]
                
                if sell_signal:
                    # 매도 실행
                    sell_value = float(df.loc[df.index[i], 'coin_value'])
                    
                    # 수수료 계산
                    fee = sell_value * self.commission
                    actual_sell_value = sell_value - fee
                    
                    # 자본 증가 및 코인 가치 제거
                    df.loc[df.index[i], 'capital'] = float(df.loc[df.index[i], 'capital']) + actual_sell_value
                    df.loc[df.index[i], 'coin_value'] = 0.0
                    df.loc[df.index[i], 'position'] = 0
                    
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
                        'exit_market_state': df.loc[df.index[i], 'market_state']
                    })
                    
                    trades.append(current_position)
                    current_position = None
            
            # 자산 가치 계산
            df.loc[df.index[i], 'equity'] = float(df.loc[df.index[i], 'capital']) + float(df.loc[df.index[i], 'coin_value'])
        
        # 백테스트 결과 반환
        result = BacktestResult(df['equity'], df['position'], trades)
        
        return result, df
    
    def visualize(self, result: BacktestResult, data: pd.DataFrame) -> plt.Figure:
        """백테스트 결과 시각화
        
        Args:
            result: 백테스트 결과
            data: 백테스트 데이터프레임
            
        Returns:
            chart: 생성된 차트 객체
        """
        # 데이터 일관성을 위해 동일한 데이터프레임 사용
        # 필요한 OHLC 컬럼이 있는지 확인
        chart_data = data.copy()
        
        # 서브플롯 생성 (메인 차트와 equity 차트)
        fig, (ax_main, ax_equity) = plt.subplots(
            nrows=2, ncols=1,
            sharex=True,
            gridspec_kw={'height_ratios': [4, 1]},
            figsize=(12, 8),
            constrained_layout=True
        )
        
        # 캔들 차트 생성 (외부 axes 사용)
        chart = CandleChart(title="Adaptive Strategy Backtest", style="korean", ax=ax_main, fig=fig)
        chart.plot(chart_data)
        
        # 이동평균선 추가
        chart.add_moving_average([self.strategy.ma_short_period, self.strategy.ma_long_period])
        
        # 볼린저 밴드 추가
        chart.add_bollinger_bands(period=self.strategy.bb_period, std_dev=self.strategy.bb_std_dev)
        
        # 차트 내부적으로 데이터는 0부터 시작하는 인덱스로 표시됩니다
        # 시장 상태 배경색 표시 - 최적화된 방식
        prev_trending = data['trending'].iloc[0]
        start_idx = 0
        
        for i in range(1, len(data)):
            # 추세 상태가 변하거나 마지막 데이터에 도달한 경우
            if data['trending'].iloc[i] != prev_trending or i == len(data) - 1:
                end_idx = i
                
                # 현재 추세에 맞는 색상 선택
                color = 'green' if prev_trending else 'gray'
                alpha = 0.2 if prev_trending else 0.1
                
                # 구간 채우기 - chart.axes 대신 ax_main 직접 사용
                ax_main.axvspan(start_idx, end_idx, alpha=alpha, color=color)
                
                # 다음 구간 시작
                prev_trending = data['trending'].iloc[i]
                start_idx = i
        
        # 매수/매도 포인트 표시를 위한 인덱스 위치 찾기
        date_to_idx = {date: idx for idx, date in enumerate(data.index)}
        
        # 매수/매도 포인트 표시
        for trade in result.trades:
            # 날짜를 정수 위치로 변환
            entry_idx = date_to_idx.get(trade['entry_date'])
            exit_idx = date_to_idx.get(trade['exit_date'])
            
            # 실제 거래가(종가) 기준으로 표시
            if entry_idx is not None:
                # 매수 지점 - 실제 거래가 표시
                buy_price = chart_data.loc[trade['entry_date'], 'close']
                buy_annotation = f"B ({buy_price:,.0f})"
                
                # chart.annotate 대신 직접 주석 추가
                ax_main.annotate(buy_annotation, 
                             (entry_idx, buy_price), 
                             color='green', arrowprops=dict(color='green'))
            
            if exit_idx is not None:
                # 매도 지점 - 실제 거래가와 수익률 표시
                sell_price = chart_data.loc[trade['exit_date'], 'close']
                pnl_text = f"{trade['pnl_pct']*100:.1f}%"
                sell_annotation = f"S ({sell_price:,.0f}, {pnl_text})"
                
                # chart.annotate 대신 직접 주석 추가
                ax_main.annotate(sell_annotation, 
                             (exit_idx, sell_price), 
                             color='red', arrowprops=dict(color='red'))
        
        # 백테스트 정보 텍스트 추가
        info_text = (
            f"Total Return: {result.total_return*100:.1f}%\n"
            f"Max Drawdown: {result.max_drawdown*100:.1f}%\n"
            f"Trades: {result.num_trades}\n"
            f"Win Rate: {result.win_rate*100:.1f}%\n"
            f"Commission: {self.commission*100:.3f}%"  # 수수료율 표시 추가
        )
        ax_main.text(0.02, 0.05, info_text, transform=ax_main.transAxes, 
                   fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
        
        # 자산 가치 패널 추가 - sharex를 통해 x축 공유
        x_range = range(len(result.equity))
        ax_equity.plot(x_range, result.equity, color='blue', linewidth=1.5)
        ax_equity.set_title('Equity Curve')
        ax_equity.grid(True, alpha=0.3)
        ax_equity.set_ylabel('Capital')
        
        # 차트 저장
        fig.savefig("charts/adaptive_strategy_backtest.png", dpi=150)
        
        return fig 