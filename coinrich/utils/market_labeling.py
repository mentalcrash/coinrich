import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional, Union

def label_trending_market(data: pd.DataFrame, 
                         window: int = 20, 
                         directional_threshold: float = 0.15,
                         volatility_ratio_threshold: float = 2.0) -> Dict[str, pd.Series]:
    """추세장/횡보장 객관적 라벨링
    
    추세장과 횡보장을 객관적인 가격 행동 기반으로 라벨링합니다.
    
    Args:
        data: OHLCV 데이터프레임
        window: 판단 기간
        directional_threshold: 방향성 임계값 (절대 수익률)
        volatility_ratio_threshold: 방향성 대비 변동성 임계값
        
    Returns:
        딕셔너리: {
            'trending': 추세장 여부 시리즈 (True=추세장, False=횡보장),
            'abs_return': 절대 수익률,
            'volatility': 변동성,
            'efficiency_ratio': 방향성 대비 변동성 비율
        }
    """
    # 방향성 계산: N기간 절대 수익률
    abs_return = abs(data['close'].pct_change(window))
    
    # 변동성 계산: N기간 동안의 일별 변동폭 합
    volatility = (data['high'] - data['low']).rolling(window=window).sum() / data['close'].shift(window)
    
    # 방향성 대비 변동성 비율
    efficiency_ratio = abs_return / volatility
    
    # 추세장 판단:
    # 1. 절대 수익률이 임계값 이상
    # 2. 방향성 대비 변동성 비율이 임계값 이상 (효율적 움직임)
    is_trending = (abs_return > directional_threshold) & (efficiency_ratio > volatility_ratio_threshold)
    
    return {
        'trending': is_trending,
        'abs_return': abs_return,
        'volatility': volatility,
        'efficiency_ratio': efficiency_ratio
    }


def evaluate_trend_detection(actual_trend: pd.Series, 
                            predicted_trend: pd.Series) -> Dict[str, float]:
    """추세 감지 성능 평가
    
    객관적 라벨링(실제)과 지표 기반 예측 간의 성능을 평가합니다.
    
    Args:
        actual_trend: 객관적 라벨링 기반 추세장 여부 (True/False)
        predicted_trend: 지표 기반 예측 추세장 여부 (True/False)
        
    Returns:
        성능 지표 딕셔너리 (정확도, 정밀도, 재현율, F1 점수)
    """
    # 결측치 제거
    valid_indices = actual_trend.notna() & predicted_trend.notna()
    actual = actual_trend[valid_indices]
    predicted = predicted_trend[valid_indices]
    
    # 혼동 행렬 계산
    true_positive = ((actual == True) & (predicted == True)).sum()
    false_positive = ((actual == False) & (predicted == True)).sum()
    true_negative = ((actual == False) & (predicted == False)).sum()
    false_negative = ((actual == True) & (predicted == False)).sum()
    
    # 성능 지표 계산
    accuracy = (true_positive + true_negative) / len(actual) if len(actual) > 0 else 0
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'accuracy': accuracy,
        'precision': precision, 
        'recall': recall,
        'f1_score': f1,
        'true_positive': true_positive,
        'false_positive': false_positive,
        'true_negative': true_negative,
        'false_negative': false_negative
    }


def optimize_trend_parameters(data: pd.DataFrame,
                             adx_range: List[float] = [20, 25, 30],
                             chop_range: List[float] = [35, 38.2, 40, 45],
                             use_ma_alignment: bool = False) -> Dict[str, Union[float, Dict]]:
    """추세 감지 파라미터 최적화
    
    가장 좋은 성능의 ADX 및 Choppiness Index 임계값을 찾습니다.
    
    Args:
        data: OHLCV 데이터프레임
        adx_range: 테스트할 ADX 임계값 목록
        chop_range: 테스트할 Choppiness 임계값 목록
        use_ma_alignment: 이동평균선 정렬 조건 사용 여부
        
    Returns:
        최적 파라미터 및 성능 딕셔너리
    """
    from coinrich.utils.indicators import is_trending_market, adx, choppiness_index
    
    # 객관적 라벨링
    actual_result = label_trending_market(data)
    actual_trend = actual_result['trending']
    
    best_metrics = {'f1_score': 0}
    best_params = {}
    results = []
    
    # 그리드 서치
    for adx_threshold in adx_range:
        for chop_threshold in chop_range:
            # 지표 기반 추세 예측
            predicted_trend, _, _ = is_trending_market(
                data, 
                adx_threshold=adx_threshold,
                chop_threshold=chop_threshold,
                use_ma_alignment=use_ma_alignment
            )
            
            # 성능 평가
            metrics = evaluate_trend_detection(actual_trend, predicted_trend)
            
            # 결과 저장
            result = {
                'adx_threshold': adx_threshold,
                'chop_threshold': chop_threshold,
                'accuracy': metrics['accuracy'],
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1_score': metrics['f1_score']
            }
            results.append(result)
            
            # 최고 성능 업데이트
            if metrics['f1_score'] > best_metrics['f1_score']:
                best_metrics = metrics
                best_params = {
                    'adx_threshold': adx_threshold,
                    'chop_threshold': chop_threshold
                }
    
    return {
        'best_params': best_params,
        'best_metrics': best_metrics,
        'all_results': results
    } 