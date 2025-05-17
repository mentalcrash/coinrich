import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union


class BacktestResult:
    """백테스트 결과 클래스
    
    백테스트 실행 결과를 저장하고 분석하는 기능을 제공합니다.
    """
    
    def __init__(self, 
                 equity: pd.Series, 
                 positions: pd.Series, 
                 trades: List[Dict[str, Any]]):
        """
        Args:
            equity: 자산 가치 시리즈
            positions: 포지션 보유 여부 시리즈 (0: 미보유, 1: 매수 보유)
            trades: 거래 내역 리스트
        """
        self.equity = equity
        self.positions = positions
        self.trades = trades
        
        # 성과 지표 계산
        self.calculate_metrics()
    
    def calculate_metrics(self):
        """성과 지표 계산"""
        # 시작/종료 자산
        self.initial_equity = self.equity.iloc[0]
        self.final_equity = self.equity.iloc[-1]
        
        # 총 수익률
        self.total_return = (self.final_equity / self.initial_equity) - 1
        
        # 거래 횟수
        self.num_trades = len(self.trades)
        
        # 수익/손실 거래 분석
        if self.num_trades > 0:
            # 승률
            winning_trades = [t for t in self.trades if t['pnl'] > 0]
            self.win_rate = len(winning_trades) / self.num_trades
            
            # 평균 수익률
            self.avg_return = sum(t['pnl_pct'] for t in self.trades) / self.num_trades
            
            # 평균 수익 거래 수익률
            if winning_trades:
                self.avg_win = sum(t['pnl_pct'] for t in winning_trades) / len(winning_trades)
            else:
                self.avg_win = 0
            
            # 평균 손실 거래 손실률
            losing_trades = [t for t in self.trades if t['pnl'] <= 0]
            if losing_trades:
                self.avg_loss = sum(t['pnl_pct'] for t in losing_trades) / len(losing_trades)
            else:
                self.avg_loss = 0
            
            # 손익비
            self.profit_factor = abs(self.avg_win / self.avg_loss) if self.avg_loss != 0 else float('inf')
        else:
            self.win_rate = 0
            self.avg_return = 0
            self.avg_win = 0
            self.avg_loss = 0
            self.profit_factor = 0
        
        # 일일 수익률
        self.daily_returns = self.equity.pct_change().dropna()
        
        # 연율화 수익률 (252 거래일 기준)
        # 분봉/시봉 데이터의 경우 다른 방식으로 연율화 필요
        trading_days_per_year = 252
        self.annual_return = (1 + self.total_return) ** (trading_days_per_year / len(self.equity)) - 1
        
        # 변동성 (일일 수익률의 표준편차)
        self.volatility = self.daily_returns.std()
        self.annualized_volatility = self.volatility * np.sqrt(trading_days_per_year)
        
        # 샤프 비율
        risk_free_rate = 0.02  # 연 2% 가정
        daily_rf = (1 + risk_free_rate) ** (1/trading_days_per_year) - 1
        
        if self.volatility > 0:
            sharpe_ratio = (self.daily_returns.mean() - daily_rf) / self.volatility
            self.sharpe_ratio = sharpe_ratio * np.sqrt(trading_days_per_year)  # 연간화
        else:
            self.sharpe_ratio = 0
        
        # 최대 낙폭 (MDD)
        cumulative = (1 + self.daily_returns).cumprod()
        drawdown = 1 - cumulative / cumulative.cummax()
        self.max_drawdown = drawdown.max()
        
        # 보유 기간 분석
        self.avg_holding_period = 0
        if self.num_trades > 0:
            total_periods = sum(
                (t['exit_date'] - t['entry_date']).total_seconds() / 60 
                for t in self.trades
            )
            self.avg_holding_period = total_periods / self.num_trades  # 분 단위
    
    def summary(self) -> str:
        """백테스트 결과 요약 문자열 반환"""
        summary_text = "=== 백테스트 결과 요약 ===\n"
        summary_text += f"초기 자본: {self.initial_equity:,.0f}\n"
        summary_text += f"최종 자본: {self.final_equity:,.0f}\n"
        summary_text += f"총 수익률: {self.total_return*100:.2f}%\n"
        summary_text += f"연간 수익률: {self.annual_return*100:.2f}%\n"
        summary_text += f"샤프 비율: {self.sharpe_ratio:.2f}\n"
        summary_text += f"최대 낙폭: {self.max_drawdown*100:.2f}%\n"
        summary_text += f"거래 횟수: {self.num_trades}\n"
        summary_text += f"승률: {self.win_rate*100:.2f}%\n"
        summary_text += f"평균 수익률: {self.avg_return*100:.2f}%\n"
        summary_text += f"평균 수익 거래: {self.avg_win*100:.2f}%\n"
        summary_text += f"평균 손실 거래: {self.avg_loss*100:.2f}%\n"
        summary_text += f"손익비: {self.profit_factor:.2f}\n"
        summary_text += f"평균 보유 기간: {self.avg_holding_period:.1f}분\n"
        
        return summary_text
    
    def trade_summary(self) -> str:
        """거래 내역 요약 문자열 반환"""
        if not self.trades:
            return "거래 내역 없음"
        
        summary_text = "=== 거래 내역 요약 ===\n"
        
        for i, trade in enumerate(self.trades, 1):
            entry_time = trade['entry_date'].strftime('%Y-%m-%d %H:%M')
            exit_time = trade['exit_date'].strftime('%Y-%m-%d %H:%M')
            
            market_state = f"{trade['market_state']} → {trade['exit_market_state']}"
            profit_text = f"{trade['pnl_pct']*100:+.2f}%"
            
            summary_text += f"#{i}: {entry_time} 매수 → {exit_time} 매도, "
            summary_text += f"수익률: {profit_text}, 시장: {market_state}\n"
        
        return summary_text
    
    def trade_statistics(self) -> Dict[str, Any]:
        """거래 통계 딕셔너리 반환"""
        stats = {
            'total_trades': self.num_trades,
            'win_rate': self.win_rate,
            'avg_return': self.avg_return,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'avg_holding_period': self.avg_holding_period,
        }
        
        # 추세장/횡보장 거래 분석
        if self.trades:
            trending_trades = [t for t in self.trades if t['market_state'] == 'trending']
            ranging_trades = [t for t in self.trades if t['market_state'] == 'ranging']
            
            # 추세장 거래 승률
            if trending_trades:
                trending_wins = [t for t in trending_trades if t['pnl'] > 0]
                stats['trending_win_rate'] = len(trending_wins) / len(trending_trades)
                stats['trending_avg_return'] = sum(t['pnl_pct'] for t in trending_trades) / len(trending_trades)
            else:
                stats['trending_win_rate'] = 0
                stats['trending_avg_return'] = 0
            
            # 횡보장 거래 승률
            if ranging_trades:
                ranging_wins = [t for t in ranging_trades if t['pnl'] > 0]
                stats['ranging_win_rate'] = len(ranging_wins) / len(ranging_trades)
                stats['ranging_avg_return'] = sum(t['pnl_pct'] for t in ranging_trades) / len(ranging_trades)
            else:
                stats['ranging_win_rate'] = 0
                stats['ranging_avg_return'] = 0
        
        return stats 