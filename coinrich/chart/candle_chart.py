import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from typing import Optional, List, Dict, Any, Tuple, Union

from coinrich.chart.base_chart import BaseChart
from coinrich.models.candle import MinuteCandle, MinuteCandleList


class CandleChart(BaseChart):
    """캔들스틱 차트 클래스
    
    mplfinance 라이브러리를 사용한 캔들스틱 차트를 제공합니다.
    이동평균선, 거래량, 기술적 지표 등을 추가할 수 있습니다.
    """
    
    def __init__(self, 
                 title: Optional[str] = None,
                 width: int = 1200,
                 height: int = 800,
                 style: str = 'yahoo',
                 save_dir: str = 'charts',
                 volume: bool = True,
                 ax: Optional[plt.Axes] = None,
                 fig: Optional[plt.Figure] = None,
                 **kwargs):
        """
        Args:
            title: 차트 제목
            width: 차트 너비 (픽셀)
            height: 차트 높이 (픽셀)
            style: 차트 스타일 ('default', 'binance', 'yahoo', 'classic', 등)
            save_dir: 차트 저장 디렉토리
            volume: 거래량 표시 여부
            ax: 외부에서 제공된 matplotlib Axes 객체
            fig: 외부에서 제공된 matplotlib Figure 객체
            **kwargs: 추가 매개변수
        """
        super().__init__(title, width, height, style, save_dir)
        self.volume = volume
        self.panel_ratios = kwargs.get('panel_ratios', (4, 1))  # 기본 비율: 캔들 4, 거래량 1
        self.ma_periods = []  # 이동평균선 기간 리스트
        self.ma_colors = []   # 이동평균선 색상 리스트
        
        # 외부 axes와 figure 저장
        self.external_ax = ax
        self.external_fig = fig
        
        # mplfinance 스타일 설정
        self.mpf_style = self._get_mpf_style(style)
        
        # 추가 플롯 목록
        self.additional_plots = []
    
    def _get_mpf_style(self, style_name: str) -> dict:
        """mplfinance 스타일 설정 가져오기
        
        Args:
            style_name: 스타일 이름
            
        Returns:
            스타일 설정 딕셔너리
        """
        if style_name == 'korean':
            # 한국식 캔들 색상 (상승: 빨간색, 하락: 파란색)
            mc = mpf.make_marketcolors(
                up='#FF3232',         # 상승봉 색상 (빨간색)
                down='#0066FF',       # 하락봉 색상 (파란색)
                edge='inherit',       # 캔들 테두리는 몸통 색상과 동일
                wick='inherit',       # 심지 색상은 몸통 색상과 동일
                volume='inherit',     # 거래량은 캔들 색상과 동일
            )
            
            return mpf.make_mpf_style(
                base_mpf_style='yahoo',
                marketcolors=mc
            )
        # mplfinance 기본 스타일 사용
        elif style_name in ['binance', 'upbit']:
            # 커스텀 스타일이 호환성 문제로 직접 구현하지 않고 기본 스타일 사용
            if style_name == 'binance':
                return 'yahoo'
            else:
                return 'classic'
        
        # 기본 스타일은 그대로 반환
        return style_name
    
    def create_figure(self) -> Tuple:
        """차트 기본 프레임 생성
        
        Returns:
            fig, axes: matplotlib figure와 axes 객체
        """
        if self.data is None:
            raise ValueError("데이터가 없습니다. plot() 메소드를 먼저 호출하세요.")
        
        # 외부에서 제공된 axes 사용
        if self.external_ax is not None:
            self.fig = self.external_fig if self.external_fig is not None else self.external_ax.figure
            self.axes = [self.external_ax]
            
            # 제목 설정
            if self.title:
                self.external_ax.set_title(self.title)
            
            # 캔들차트 그리기
            mpf.plot(
                self.data,
                ax=self.external_ax,
                style=self.mpf_style,
                type='candle',
                volume=False,  # 별도의 볼륨 패널을 사용하지 않음
                returnfig=False
            )
            
            # 추가 플롯이 있으면 설정
            if self.additional_plots:
                for ap in self.additional_plots:
                    mpf.plot(
                        self.data,
                        ax=self.external_ax,
                        style=self.mpf_style,
                        type='candle',
                        volume=False,
                        addplot=ap,
                        returnfig=False
                    )
                    
            return self.fig, self.axes
        
        # 기존 로직: 자체적으로 figure와 axes 생성
        # 레이아웃 설정
        kwargs = {
            'figsize': (self.width / 100, self.height / 100),
            'style': self.mpf_style,
            'title': self.title,
            'type': 'candle',
            'volume': self.volume,
            'panel_ratios': self.panel_ratios if self.volume else None,
            'returnfig': True
        }
        
        # 추가 플롯이 있으면 설정
        if self.additional_plots:
            kwargs['addplot'] = self.additional_plots
        
        # 차트 생성
        self.fig, self.axes = mpf.plot(self.data, **kwargs)
        
        return self.fig, self.axes
    
    def plot(self, data: Union[pd.DataFrame, MinuteCandleList]) -> None:
        """캔들스틱 차트 그리기
        
        Args:
            data: 캔들 데이터 (pandas DataFrame 또는 MinuteCandleList)
                - DataFrame의 경우 'open', 'high', 'low', 'close' 컬럼 필요
                - DataFrame의 index는 datetime 타입이어야 함
        """
        # 데이터 전처리
        self.data = self._prepare_data(data)
        
        # 외부 axes 사용 시 직접 그리기
        if self.external_ax is not None:
            # 캔들차트 그리기 (mpf.plot)
            mpf.plot(
                self.data,
                ax=self.external_ax,
                style=self.mpf_style,
                type='candle',
                volume=False,
                returnfig=False
            )
            
            if self.title:
                self.external_ax.set_title(self.title)
                
            return
        
        # 자체적으로 axes를 생성하는 경우
        self.create_figure()
    
    def _prepare_data(self, data: Union[pd.DataFrame, MinuteCandleList]) -> pd.DataFrame:
        """캔들 데이터 전처리
        
        Args:
            data: 원본 캔들 데이터
            
        Returns:
            mplfinance 형식에 맞게 변환된 DataFrame
        """
        if isinstance(data, pd.DataFrame):
            # 이미 DataFrame인 경우 컬럼 이름만 확인
            required_cols = ['open', 'high', 'low', 'close']
            
            # 소문자로 변환 (대소문자 구분 없이 처리)
            data.columns = [col.lower() for col in data.columns]
            
            # 컬럼 매핑 (다른 이름으로 되어있는 경우)
            col_map = {
                'opening_price': 'open',
                'high_price': 'high', 
                'low_price': 'low',
                'trade_price': 'close',
                'candle_acc_trade_volume': 'volume'
            }
            
            for src, dst in col_map.items():
                if src in data.columns and dst not in data.columns:
                    data[dst] = data[src]
            
            # 필수 컬럼 확인
            missing = [col for col in required_cols if col not in data.columns]
            if missing:
                raise ValueError(f"DataFrame에 필요한 컬럼이 없습니다: {missing}")
            
            # 인덱스가 datetime 타입인지 확인
            if not isinstance(data.index, pd.DatetimeIndex):
                raise ValueError("DataFrame의 인덱스는 DatetimeIndex 타입이어야 합니다.")
            
            return data
        
        elif isinstance(data, MinuteCandleList):
            # MinuteCandleList를 DataFrame으로 변환
            candle_data = []
            for candle in data:
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
            df.sort_index(inplace=True)  # 시간순 정렬
            
            return df
        
        else:
            raise ValueError("지원하지 않는 데이터 타입입니다. DataFrame 또는 MinuteCandleList만 지원합니다.")
    
    def add_moving_average(self, periods: List[int], colors: Optional[List[str]] = None) -> None:
        """이동평균선 추가
        
        Args:
            periods: 이동평균 기간 리스트 (예: [5, 20, 60])
            colors: 색상 리스트 (periods와 같은 길이), None이면 자동 설정
        """
        if self.data is None:
            raise ValueError("데이터가 없습니다. plot() 메소드를 먼저 호출하세요.")
        
        # 색상 기본값 설정
        default_colors = ['#1976D2', '#FB8C00', '#7CB342', '#E53935', '#5E35B1']
        
        if colors is None:
            colors = default_colors[:len(periods)]
        
        if len(colors) < len(periods):
            # 색상이 부족하면 기본 색상으로 채움
            colors.extend(default_colors[len(colors):len(periods)])
        
        # 이동평균 계산 및 추가
        for i, period in enumerate(periods):
            ma = self.data['close'].rolling(window=period).mean()
            self.additional_plots.append(
                mpf.make_addplot(ma, color=colors[i], width=1, label=f'MA{period}')
            )
        
        # 기간과 색상 저장
        self.ma_periods = periods
        self.ma_colors = colors
        
        # 외부 axes 사용 시 직접 그리기
        if self.external_ax is not None:
            for i, period in enumerate(periods):
                ma = self.data['close'].rolling(window=period).mean()
                self.external_ax.plot(range(len(ma)), ma, color=colors[i], linewidth=1, label=f'MA{period}')
            
            # 범례 추가
            self.external_ax.legend(loc='upper left')
            return
        
        # 차트 다시 그리기 (외부 axes가 없을 경우만)
        self.create_figure()
    
    def add_bollinger_bands(self, period: int = 20, std_dev: float = 2.0, color: str = '#9C27B0') -> None:
        """볼린저 밴드 추가
        
        Args:
            period: 이동평균 기간
            std_dev: 표준편차 배수
            color: 밴드 색상
        """
        if self.data is None:
            raise ValueError("데이터가 없습니다. plot() 메소드를 먼저 호출하세요.")
        
        # 이동평균 및 표준편차 계산
        ma = self.data['close'].rolling(window=period).mean()
        std = self.data['close'].rolling(window=period).std()
        
        # 상단 및 하단 밴드
        upper_band = ma + (std * std_dev)
        lower_band = ma - (std * std_dev)
        
        # 추가 플롯에 추가
        self.additional_plots.extend([
            mpf.make_addplot(upper_band, color=color, linestyle='--', width=0.8, label=f'Upper BB({period})'),
            mpf.make_addplot(ma, color=color, linestyle='-', width=1.0, label=f'MA({period})'),
            mpf.make_addplot(lower_band, color=color, linestyle='--', width=0.8, label=f'Lower BB({period})')
        ])
        
        # 외부 axes 사용 시 직접 그리기
        if self.external_ax is not None:
            x = range(len(ma))
            self.external_ax.plot(x, upper_band, color=color, linestyle='--', linewidth=0.8, label=f'Upper BB({period})')
            self.external_ax.plot(x, ma, color=color, linestyle='-', linewidth=1.0, label=f'MA({period})')
            self.external_ax.plot(x, lower_band, color=color, linestyle='--', linewidth=0.8, label=f'Lower BB({period})')
            
            # 범례 추가
            self.external_ax.legend(loc='upper left')
            return
        
        # 차트 다시 그리기
        self.create_figure()
    
    def add_rsi(self, period: int = 14, color: str = '#E91E63', panel_ratio: float = 1.0) -> None:
        """RSI(Relative Strength Index) 지표 추가
        
        Args:
            period: RSI 계산 기간
            color: 선 색상
            panel_ratio: 패널 비율 (메인 차트 대비)
        """
        if self.data is None:
            raise ValueError("데이터가 없습니다. plot() 메소드를 먼저 호출하세요.")
        
        # RSI 계산
        delta = self.data['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 오버솔드/오버바웃 라인
        overbought = pd.Series(70, index=self.data.index)
        oversold = pd.Series(30, index=self.data.index)
        
        # 추가 플롯에 추가 (별도 패널)
        self.additional_plots.extend([
            mpf.make_addplot(rsi, color=color, panel=1, ylabel=f'RSI({period})'),
            mpf.make_addplot(overbought, color='gray', linestyle='--', panel=1, secondary_y=False),
            mpf.make_addplot(oversold, color='gray', linestyle='--', panel=1, secondary_y=False)
        ])
        
        # 패널 비율 업데이트
        self.panel_ratios = (4, panel_ratio)
        
        # 차트 다시 그리기
        self.create_figure()
    
    def add_macd(self, fast: int = 12, slow: int = 26, signal: int = 9, 
                 panel_ratio: float = 1.0) -> None:
        """MACD(Moving Average Convergence Divergence) 지표 추가
        
        Args:
            fast: 빠른 이동평균 기간
            slow: 느린 이동평균 기간
            signal: 시그널 이동평균 기간
            panel_ratio: 패널 비율 (메인 차트 대비)
        """
        if self.data is None:
            raise ValueError("데이터가 없습니다. plot() 메소드를 먼저 호출하세요.")
        
        # MACD 계산
        fast_ema = self.data['close'].ewm(span=fast, adjust=False).mean()
        slow_ema = self.data['close'].ewm(span=slow, adjust=False).mean()
        macd = fast_ema - slow_ema
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        # 추가 플롯에 추가 (별도 패널)
        self.additional_plots.extend([
            mpf.make_addplot(macd, color='#2196F3', panel=2, ylabel=f'MACD({fast},{slow},{signal})'),
            mpf.make_addplot(signal_line, color='#FF9800', panel=2),
            mpf.make_addplot(histogram, type='bar', color='#9E9E9E', panel=2)
        ])
        
        # 패널 비율 업데이트 (캔들:4, 지표1:1, 지표2:1)
        if self.volume:
            self.panel_ratios = (4, 1, panel_ratio)
        else:
            self.panel_ratios = (4, panel_ratio)
        
        # 차트 다시 그리기
        self.create_figure()
    
    def annotate(self, text: str, xy: Tuple[Any, float], color: str = 'black', 
                 arrow: bool = True) -> None:
        """차트에 주석 추가
        
        Args:
            text: 주석 텍스트
            xy: (x, y) 좌표 (x는 인덱스 또는 날짜, y는 가격)
            color: 주석 색상
            arrow: 화살표 표시 여부
        """
        if self.fig is None or self.axes is None:
            raise ValueError("차트가 아직 생성되지 않았습니다.")
        
        # x 좌표가 datetime인 경우 처리
        x, y = xy
        if isinstance(x, (pd.Timestamp, str)):
            if isinstance(x, str):
                x = pd.to_datetime(x)
            # 인덱스에서 위치 찾기
            x_idx = self.data.index.get_indexer([x], method='nearest')[0]
            x = x_idx
        
        # 주석 추가
        arrowprops = {'arrowstyle': '->', 'color': color} if arrow else None
        self.axes[0].annotate(text, xy=(x, y), xytext=(x+5, y+5),
                             arrowprops=arrowprops, color=color) 