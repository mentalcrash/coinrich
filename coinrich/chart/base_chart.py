import os
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple, Union


class BaseChart(ABC):
    """차트 기본 추상 클래스
    
    다양한 차트 타입의 기본 인터페이스를 정의하는 추상 클래스입니다.
    matplotlib, mplfinance, plotly 등 다양한 라이브러리를 지원할 수 있도록 설계되었습니다.
    """
    
    def __init__(self, 
                 title: Optional[str] = None, 
                 width: int = 800, 
                 height: int = 600,
                 style: str = 'default',
                 save_dir: str = 'charts'):
        """
        Args:
            title: 차트 제목
            width: 차트 너비 (픽셀)
            height: 차트 높이 (픽셀)
            style: 차트 스타일 ('default', 'binance', 'yahoo', 'classic', 등)
            save_dir: 차트 저장 디렉토리
        """
        self.title = title
        self.width = width
        self.height = height
        self.style = style
        self.save_dir = save_dir
        self.fig = None
        self.axes = None
        self.data = None
    
    @abstractmethod
    def create_figure(self) -> Tuple:
        """차트 기본 프레임 생성 (추상 메소드)
        
        Returns:
            fig, axes: matplotlib 또는 plotly의 figure 객체와 axes 객체
        """
        pass
    
    @abstractmethod
    def plot(self, data: Any) -> None:
        """데이터를 사용하여 차트 그리기 (추상 메소드)
        
        Args:
            data: 차트에 표시할 데이터
        """
        pass
    
    def show(self) -> None:
        """차트 표시"""
        if self.fig is None:
            raise ValueError("차트가 아직 생성되지 않았습니다. plot() 메소드를 먼저 호출하세요.")
        plt.show()
    
    def save(self, filename: str, dpi: int = 300) -> str:
        """차트 저장
        
        Args:
            filename: 저장할 파일 이름 (확장자 포함)
            dpi: 해상도 (dots per inch)
            
        Returns:
            저장된 파일 경로
        """
        if self.fig is None:
            raise ValueError("차트가 아직 생성되지 않았습니다. plot() 메소드를 먼저 호출하세요.")
        
        # 저장 디렉토리가 없으면 생성
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        # 파일 경로 생성
        filepath = os.path.join(self.save_dir, filename)
        
        # 저장 (plotly는 별도 처리 필요)
        if hasattr(self.fig, 'write_image'):
            # plotly 차트
            self.fig.write_image(filepath)
        else:
            # matplotlib 차트
            self.fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
        
        return filepath
    
    def set_title(self, title: str) -> None:
        """차트 제목 설정
        
        Args:
            title: 차트 제목
        """
        self.title = title
        if self.fig is not None:
            if hasattr(self.fig, 'update_layout'):
                # plotly 차트
                self.fig.update_layout(title=title)
            else:
                # matplotlib 차트
                self.fig.suptitle(title)
    
    def set_size(self, width: int, height: int) -> None:
        """차트 크기 설정
        
        Args:
            width: 차트 너비 (픽셀)
            height: 차트 높이 (픽셀)
        """
        self.width = width
        self.height = height
        if self.fig is not None:
            if hasattr(self.fig, 'update_layout'):
                # plotly 차트
                self.fig.update_layout(width=width, height=height)
            else:
                # matplotlib 차트
                self.fig.set_size_inches(width/100, height/100)
                plt.tight_layout()
    
    def _prepare_data(self, data: Any) -> Any:
        """데이터 전처리 (상속받은 클래스에서 구현)
        
        Args:
            data: 원본 데이터

        Returns:
            전처리된 데이터
        """
        return data
    
    def close(self) -> None:
        """차트 리소스 정리"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.axes = None 