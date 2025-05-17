#!/usr/bin/env python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse
from datetime import datetime

from coinrich.service.candle_service import CandleService
from coinrich.utils.indicators import (
    bollinger_bands, bollinger_band_width, 
    adx, is_trending_market
)


def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(description='추세장/횡보장 분석 도구')
    parser.add_argument('--market', type=str, default='KRW-BTC',
                        help='분석할 마켓 심볼 (예: KRW-BTC)')
    parser.add_argument('--unit', type=int, default=15,
                        help='캔들 시간 단위(분) (1, 3, 5, 15, 30, 60, 240)')
    parser.add_argument('--count', type=int, default=600,
                        help='분석할 캔들 개수')
    parser.add_argument('--adx-threshold', type=float, default=25,
                        help='ADX 임계값 (추세 강도 판단 기준)')
    parser.add_argument('--bb-percentile', type=float, default=60,
                        help='볼린저 밴드 폭 백분위수 (횡보장 판단 기준)')
    parser.add_argument('--output-dir', type=str, default='charts',
                        help='차트 저장 디렉토리')
    
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


def analyze_trend(df, adx_threshold, bb_percentile):
    """추세장 판별 분석"""
    print(f"\n=== 추세장 판별 분석 (ADX 임계값: {adx_threshold}, BB 폭 백분위수: {bb_percentile}) ===")
    
    # 추세장 판별
    trending, adx_values, bb_width = is_trending_market(
        df, 
        adx_threshold=adx_threshold, 
        bb_width_percentile=bb_percentile
    )
    
    # 추세장 및 횡보장 통계
    trend_count = trending.sum()
    total_count = len(trending)
    trend_percent = (trend_count / total_count) * 100
    
    print(f"데이터 샘플 수: {total_count}")
    print(f"추세장 구간 수: {trend_count} ({trend_percent:.1f}%)")
    print(f"횡보장 구간 수: {total_count - trend_count} ({100 - trend_percent:.1f}%)")
    
    return trending, adx_values, bb_width, trend_percent


def visualize_results(df, trending, adx_values, bb_width, params):
    """결과 시각화 및 저장"""
    print("\n=== 결과 시각화 및 저장 ===")
    
    # 차트 저장 디렉토리 생성
    os.makedirs(params['output_dir'], exist_ok=True)
    
    # 시각화
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), 
                                       gridspec_kw={'height_ratios': [3, 1, 1]})
    
    # 상단 차트 - 가격 및 추세장 배경 표시
    ax1.plot(df.index, df['close'], label=f"{params['market']} Price", color='#333333')
    
    # 연속된 추세 구간 최적화하여 표시
    trend_blocks = []  # (시작 인덱스, 종료 인덱스, 추세 여부)
    
    current_trend = trending.iloc[0]
    start_idx = trending.index[0]
    
    for i in range(1, len(trending)):
        # 추세 상태가 변경되거나 마지막 데이터
        if trending.iloc[i] != current_trend or i == len(trending) - 1:
            end_idx = trending.index[i]
            trend_blocks.append((start_idx, end_idx, current_trend))
            
            # 다음 블록 준비
            current_trend = trending.iloc[i]
            start_idx = trending.index[i]
    
    # 추세 블록 표시
    for start, end, is_trend in trend_blocks:
        if is_trend:
            ax1.axvspan(start, end, alpha=0.2, color='green')
        else:
            ax1.axvspan(start, end, alpha=0.1, color='gray')
    
    # 추세장 비율 포함한 제목
    trend_percent = trending.sum() / len(trending) * 100
    ax1.set_title(f"{params['market']} Price with Trend Analysis - {trend_percent:.1f}% Trending")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 중간 차트 - ADX
    ax2.plot(adx_values.index, adx_values, label='ADX', color='purple')
    ax2.axhline(y=params['adx_threshold'], color='black', linestyle='--', 
               label=f"ADX Threshold ({params['adx_threshold']})")
    ax2.set_title('ADX Indicator')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 하단 차트 - 볼린저 밴드 폭
    # BB 폭 백분위수 계산
    bb_percentile_value = np.percentile(bb_width.dropna(), params['bb_percentile'])
    
    ax3.plot(bb_width.index, bb_width, label='BB Width', color='blue')
    ax3.axhline(y=bb_percentile_value, color='red', linestyle='--', 
               label=f"BB Width {params['bb_percentile']}th Percentile")
    ax3.set_title('Bollinger Band Width')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 파라미터 정보 추가
    parameter_text = (
        f"Parameters:\n"
        f"Market: {params['market']}\n"
        f"Timeframe: {params['unit']}min\n"
        f"ADX Threshold: {params['adx_threshold']}\n"
        f"BB Width Percentile: {params['bb_percentile']}\n"
        f"Data Period: {df.index[0].strftime('%Y-%m-%d %H:%M')} ~ {df.index[-1].strftime('%Y-%m-%d %H:%M')}"
    )
    
    # 텍스트 표시
    plt.figtext(0.01, 0.01, parameter_text, fontsize=10,
                bbox=dict(facecolor='white', alpha=0.8))
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])  # 하단 여백 확보
    
    # 파일명에 파라미터 포함
    filename = f"trend_analysis_{params['market'].replace('-', '_')}_{params['unit']}min_ADX{params['adx_threshold']}_BB{params['bb_percentile']}.png"
    filepath = os.path.join(params['output_dir'], filename)
    
    plt.savefig(filepath, dpi=300)
    print(f"차트 저장 완료: {filepath}")
    
    # 결과 반환 (차트와 통계)
    results = {
        'trend_percent': trend_percent,
        'trend_count': trending.sum(),
        'ranging_count': len(trending) - trending.sum(),
        'total_samples': len(trending),
        'chart_path': filepath
    }
    
    return fig, results


def main():
    """메인 함수"""
    # 명령줄 인자 파싱
    args = parse_arguments()
    
    # 파라미터 정보
    params = {
        'market': args.market,
        'unit': args.unit,
        'count': args.count, 
        'adx_threshold': args.adx_threshold,
        'bb_percentile': args.bb_percentile,
        'output_dir': args.output_dir
    }
    
    # 데이터 가져오기
    df = fetch_data(params['market'], params['unit'], params['count'])
    
    # 추세장 분석
    trending, adx_values, bb_width, trend_percent = analyze_trend(
        df, params['adx_threshold'], params['bb_percentile']
    )
    
    # 결과 시각화
    fig, results = visualize_results(df, trending, adx_values, bb_width, params)
    
    # 결과 출력
    print("\n=== 분석 결과 요약 ===")
    print(f"총 샘플 수: {results['total_samples']}")
    print(f"추세장 비율: {results['trend_percent']:.1f}% ({results['trend_count']} 샘플)")
    print(f"횡보장 비율: {100-results['trend_percent']:.1f}% ({results['ranging_count']} 샘플)")
    print(f"차트 저장 경로: {results['chart_path']}")
    
    # 차트 표시
    plt.show()
    plt.close()


if __name__ == "__main__":
    main() 