#!/usr/bin/env python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import argparse
from datetime import datetime

from coinrich.service.candle_service import CandleService
from coinrich.utils.indicators import is_trending_market
from coinrich.utils.market_labeling import label_trending_market, evaluate_trend_detection, optimize_trend_parameters


def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(description='추세장 파라미터 최적화 도구')
    parser.add_argument('--market', type=str, default='KRW-BTC',
                        help='분석할 마켓 심볼 (예: KRW-BTC)')
    parser.add_argument('--unit', type=int, default=15,
                        help='캔들 시간 단위(분) (1, 3, 5, 15, 30, 60, 240)')
    parser.add_argument('--count', type=int, default=600,
                        help='분석할 캔들 개수')
    parser.add_argument('--window', type=int, default=20,
                        help='라벨링 기준 윈도우 크기')
    parser.add_argument('--use-ma-alignment', action='store_true',
                        help='이동평균선 정렬 조건 사용 여부')
    parser.add_argument('--output-dir', type=str, default='results',
                        help='결과 저장 디렉토리')
    
    return parser.parse_args()


def fetch_data(market, unit, count):
    """캔들 데이터 가져오기"""
    print(f"\n=== {market} {unit}분봉 {count}개 데이터 가져오기 ===")
    
    service = CandleService()
    candles = service.get_minute_candles(market, unit=unit, count=count)
    
    # DataFrame으로 변환
    candle_data = []
    for candle in candles.root:
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
    
    print(f"가져온 데이터: {len(df)}개 ({df.index[0]} ~ {df.index[-1]})")
    return df


def compare_trend_detection(df, window, adx_threshold, chop_threshold, use_ma_alignment):
    """객관적 라벨링과 지표 기반 추세 감지 비교"""
    print(f"\n=== 추세장 감지 비교 분석 ===")
    print(f"라벨링 윈도우: {window}")
    print(f"ADX 임계값: {adx_threshold}, Choppiness 임계값: {chop_threshold}")
    
    if use_ma_alignment:
        print("이동평균선 정렬 조건 사용")
    
    # 객관적 라벨링
    actual_trend = label_trending_market(df, window=window)
    
    # 지표 기반 추세 예측
    predicted_trend, adx_values, chop_values = is_trending_market(
        df, 
        adx_threshold=adx_threshold,
        chop_threshold=chop_threshold,
        use_ma_alignment=use_ma_alignment
    )
    
    # 성능 평가
    metrics = evaluate_trend_detection(actual_trend, predicted_trend)
    
    # 결과 출력
    print("\n=== 성능 평가 결과 ===")
    print(f"정확도: {metrics['accuracy']:.4f}")
    print(f"정밀도: {metrics['precision']:.4f}")
    print(f"재현율: {metrics['recall']:.4f}")
    print(f"F1 점수: {metrics['f1_score']:.4f}")
    print(f"혼동 행렬:")
    print(f"  참 양성: {metrics['true_positive']}")
    print(f"  거짓 양성: {metrics['false_positive']}")
    print(f"  참 음성: {metrics['true_negative']}")
    print(f"  거짓 음성: {metrics['false_negative']}")
    
    return actual_trend, predicted_trend, adx_values, chop_values, metrics


def visualize_comparison(df, actual_trend, predicted_trend, adx_values, chop_values, params):
    """비교 결과 시각화"""
    print("\n=== 결과 시각화 ===")
    
    # 차트 저장 디렉토리 생성
    os.makedirs(params['output_dir'], exist_ok=True)
    
    # 시각화
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), 
                                       gridspec_kw={'height_ratios': [3, 1, 1]})
    
    # 상단 차트 - 가격 및 라벨링 표시
    ax1.plot(df.index, df['close'], label=f"{params['market']} Price", color='#333333')
    
    # 객관적 라벨링 배경 표시
    for i in range(1, len(actual_trend)):
        if actual_trend.iloc[i] and not actual_trend.iloc[i-1]:
            start_idx = actual_trend.index[i]
            
            # 다음 False 또는 끝까지 찾기
            end_idx = None
            for j in range(i+1, len(actual_trend)):
                if not actual_trend.iloc[j]:
                    end_idx = actual_trend.index[j]
                    break
            
            if end_idx is None:
                end_idx = actual_trend.index[-1]
                
            ax1.axvspan(start_idx, end_idx, alpha=0.2, color='green', label='Actual Trend' if i == 1 else "")
    
    # 지표 기반 예측 배경 표시
    for i in range(1, len(predicted_trend)):
        if predicted_trend.iloc[i] and not predicted_trend.iloc[i-1]:
            start_idx = predicted_trend.index[i]
            
            # 다음 False 또는 끝까지 찾기
            end_idx = None
            for j in range(i+1, len(predicted_trend)):
                if not predicted_trend.iloc[j]:
                    end_idx = predicted_trend.index[j]
                    break
            
            if end_idx is None:
                end_idx = predicted_trend.index[-1]
                
            # 예측 테두리 표시 (점선 테두리)
            ax1.axvspan(start_idx, end_idx, alpha=0, edgecolor='red', linestyle='--', 
                       linewidth=2, label='Predicted Trend' if i == 1 else "")
    
    # 제목 및 범례
    ax1.set_title(f"{params['market']} Price with Trend Detection Comparison")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 중간 차트 - ADX
    ax2.plot(adx_values.index, adx_values, label='ADX', color='purple')
    ax2.axhline(y=params['adx_threshold'], color='black', linestyle='--', 
               label=f"ADX Threshold ({params['adx_threshold']})")
    ax2.set_title('ADX Indicator')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 하단 차트 - Choppiness Index
    ax3.plot(chop_values.index, chop_values, label='Choppiness Index', color='blue')
    ax3.axhline(y=params['chop_threshold'], color='red', linestyle='--', 
               label=f"Chop Threshold ({params['chop_threshold']})")
    ax3.set_title('Choppiness Index (Low = Trending, High = Ranging)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 파라미터 정보 추가
    parameter_text = (
        f"Parameters:\n"
        f"Market: {params['market']}\n"
        f"Timeframe: {params['unit']}min\n"
        f"Window: {params['window']}\n"
        f"ADX Threshold: {params['adx_threshold']}\n"
        f"Choppiness Threshold: {params['chop_threshold']}\n"
    )
    
    plt.figtext(0.01, 0.01, parameter_text, fontsize=10,
                bbox=dict(facecolor='white', alpha=0.8))
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])  # 하단 여백 확보
    
    # 파일명
    filename = f"trend_comparison_{params['market'].replace('-', '_')}_{params['unit']}min.png"
    filepath = os.path.join(params['output_dir'], filename)
    
    plt.savefig(filepath, dpi=300)
    print(f"차트 저장 완료: {filepath}")
    
    return fig


def run_optimization(df, window, use_ma_alignment, output_dir):
    """파라미터 최적화 실행"""
    print("\n=== 파라미터 최적화 실행 ===")
    
    # ADX 및 Choppiness 임계값 범위
    adx_range = [20, 22, 25, 28, 30]
    chop_range = [30, 35, 38.2, 40, 45, 50]
    
    # 최적화 실행
    results = optimize_trend_parameters(
        df,
        adx_range=adx_range,
        chop_range=chop_range,
        use_ma_alignment=use_ma_alignment
    )
    
    # 결과 출력
    print("\n=== 최적화 결과 ===")
    print(f"최적 ADX 임계값: {results['best_params']['adx_threshold']}")
    print(f"최적 Choppiness 임계값: {results['best_params']['chop_threshold']}")
    print(f"최고 F1 점수: {results['best_metrics']['f1_score']:.4f}")
    print(f"정확도: {results['best_metrics']['accuracy']:.4f}")
    print(f"정밀도: {results['best_metrics']['precision']:.4f}")
    print(f"재현율: {results['best_metrics']['recall']:.4f}")
    
    # 결과 저장 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 결과를 데이터프레임으로 변환
    results_df = pd.DataFrame(results['all_results'])
    
    # 엑셀 파일로 저장
    excel_path = os.path.join(output_dir, 'trend_parameter_optimization.xlsx')
    results_df.to_excel(excel_path, index=False)
    print(f"최적화 결과 저장 완료: {excel_path}")
    
    # 히트맵 시각화
    plt.figure(figsize=(10, 8))
    
    # 데이터 피벗
    pivot_df = results_df.pivot(index='adx_threshold', columns='chop_threshold', values='f1_score')
    
    # 히트맵 생성
    sns.heatmap(pivot_df, annot=True, cmap='viridis', fmt='.3f')
    plt.title('F1 Score by ADX and Choppiness Thresholds')
    plt.xlabel('Choppiness Threshold')
    plt.ylabel('ADX Threshold')
    
    # 저장
    heatmap_path = os.path.join(output_dir, 'trend_parameter_heatmap.png')
    plt.savefig(heatmap_path, dpi=300)
    print(f"히트맵 저장 완료: {heatmap_path}")
    
    return results


def main():
    """메인 함수"""
    # 명령줄 인자 파싱
    args = parse_arguments()
    
    # 파라미터 정보
    params = {
        'market': args.market,
        'unit': args.unit,
        'count': args.count,
        'window': args.window,
        'adx_threshold': 25,  # 기본값
        'chop_threshold': 38.2,  # 기본값
        'use_ma_alignment': args.use_ma_alignment,
        'output_dir': args.output_dir
    }
    
    # 데이터 가져오기
    df = fetch_data(params['market'], params['unit'], params['count'])
    
    # 파라미터 최적화
    optimization_results = run_optimization(
        df, 
        params['window'], 
        params['use_ma_alignment'], 
        params['output_dir']
    )
    
    # 최적 파라미터 적용
    params['adx_threshold'] = optimization_results['best_params']['adx_threshold']
    params['chop_threshold'] = optimization_results['best_params']['chop_threshold']
    
    # 최적 파라미터로 비교 분석
    actual_trend, predicted_trend, adx_values, chop_values, metrics = compare_trend_detection(
        df, 
        params['window'], 
        params['adx_threshold'], 
        params['chop_threshold'], 
        params['use_ma_alignment']
    )
    
    # 결과 시각화
    fig = visualize_comparison(
        df, 
        actual_trend, 
        predicted_trend, 
        adx_values, 
        chop_values, 
        params
    )
    
    plt.show()
    plt.close()


if __name__ == "__main__":
    main() 