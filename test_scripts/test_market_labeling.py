#!/usr/bin/env python
import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse
from datetime import datetime

from coinrich.service.candle_service import CandleService
from coinrich.utils.market_labeling import label_trending_market


def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(description='추세장 라벨링 테스트')
    parser.add_argument('--market', type=str, default='KRW-BTC',
                        help='분석할 마켓 심볼 (예: KRW-BTC)')
    parser.add_argument('--unit', type=int, default=15,
                        help='캔들 시간 단위(분) (1, 3, 5, 15, 30, 60, 240)')
    parser.add_argument('--count', type=int, default=400,
                        help='분석할 캔들 개수')
    parser.add_argument('--window', type=int, default=20,
                        help='라벨링 기준 윈도우 크기')
    parser.add_argument('--direction-threshold', type=float, default=0.15,
                        help='방향성 임계값 (절대 수익률)')
    parser.add_argument('--vol-ratio-threshold', type=float, default=2.0,
                        help='방향성 대비 변동성 비율 임계값')
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


def test_trending_market_labeling(df, params):
    """추세장 라벨링 테스트"""
    print(f"\n=== 추세장 라벨링 테스트 ===")
    print(f"윈도우 크기: {params['window']}")
    print(f"방향성 임계값: {params['direction_threshold']}")
    print(f"방향성/변동성 비율 임계값: {params['vol_ratio_threshold']}")
    
    # 객관적 라벨링 수행
    labeling_result = label_trending_market(
        df, 
        window=params['window'],
        directional_threshold=params['direction_threshold'],
        volatility_ratio_threshold=params['vol_ratio_threshold']
    )
    
    # 결과에서 필요한 시리즈 추출
    trending = labeling_result['trending']
    abs_return = labeling_result['abs_return']
    volatility = labeling_result['volatility']
    efficiency_ratio = labeling_result['efficiency_ratio']
    
    # 추세장 통계
    trend_count = trending.sum()
    total_count = len(trending.dropna())
    trend_percent = (trend_count / total_count) * 100
    
    print(f"유효 데이터 수: {total_count}")
    print(f"추세장 구간 수: {trend_count} ({trend_percent:.1f}%)")
    print(f"횡보장 구간 수: {total_count - trend_count} ({100 - trend_percent:.1f}%)")
    
    return labeling_result, trend_percent


def visualize_results(df, labeling_result, params):
    """시각화 및 저장"""
    print("\n=== 결과 시각화 ===")
    
    # 라벨링 결과에서 시리즈 추출
    trending = labeling_result['trending']
    abs_return = labeling_result['abs_return']
    volatility = labeling_result['volatility']
    efficiency_ratio = labeling_result['efficiency_ratio']
    
    # 차트 저장 디렉토리 생성
    os.makedirs(params['output_dir'], exist_ok=True)
    
    # 시각화
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), 
                                  gridspec_kw={'height_ratios': [3, 1]})
    
    # 상단 차트 - 가격 및 추세장 배경 표시
    ax1.plot(df.index, df['close'], label=f"{params['market']} Price", color='#333333')
    
    # 추세장 구간 표시
    for i in range(1, len(trending)):
        if trending.iloc[i] and not trending.iloc[i-1]:
            # 추세장 시작
            start_idx = trending.index[i]
            
            # 끝점 찾기 (다음 False 또는 끝까지)
            end_idx = None
            for j in range(i+1, len(trending)):
                if not trending.iloc[j]:
                    end_idx = trending.index[j]
                    break
            
            if end_idx is None:
                end_idx = trending.index[-1]
            
            # 추세장 구간 배경색
            ax1.axvspan(start_idx, end_idx, alpha=0.2, color='green')
    
    # 하단 차트 - 방향성/변동성 비율 (라벨링 함수에서 계산된 값 사용)
    ax2.plot(efficiency_ratio.index, efficiency_ratio, label='Direction/Volatility Ratio', color='blue')
    ax2.axhline(y=params['vol_ratio_threshold'], color='red', linestyle='--', 
               label=f"Threshold ({params['vol_ratio_threshold']})")
    
    # 방향성 임계값 시각화 (보조 Y축)
    ax2_twin = ax2.twinx()
    ax2_twin.plot(abs_return.index, abs_return, label='Absolute Return', color='purple', alpha=0.5)
    ax2_twin.axhline(y=params['direction_threshold'], color='black', linestyle=':', 
                    label=f"Threshold ({params['direction_threshold']})")
    
    # 범례 및 제목
    trend_percent = trending.sum() / len(trending.dropna()) * 100
    ax1.set_title(f"{params['market']} Price with Trend Labeling - {trend_percent:.1f}% Trending")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2.set_title('Direction/Volatility Ratio and Absolute Return')
    ax2.set_ylabel('Direction/Volatility Ratio')
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    ax2_twin.set_ylabel('Absolute Return')
    ax2_twin.legend(loc='upper right')
    
    # 파라미터 정보 추가
    parameter_text = (
        f"Parameters:\n"
        f"Market: {params['market']}\n"
        f"Timeframe: {params['unit']}min\n"
        f"Window: {params['window']}\n"
        f"Direction Threshold: {params['direction_threshold']}\n"
        f"Volatility Ratio Threshold: {params['vol_ratio_threshold']}\n"
        f"Data Period: {df.index[0].strftime('%Y-%m-%d %H:%M')} ~ {df.index[-1].strftime('%Y-%m-%d %H:%M')}"
    )
    
    plt.figtext(0.01, 0.01, parameter_text, fontsize=10,
                bbox=dict(facecolor='white', alpha=0.8))
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])  # 하단 여백 확보
    
    # 파일명
    filename = f"trend_labeling_{params['market'].replace('-', '_')}_{params['unit']}min_w{params['window']}_d{params['direction_threshold']}_v{params['vol_ratio_threshold']}.png"
    filepath = os.path.join(params['output_dir'], filename)
    
    plt.savefig(filepath, dpi=300)
    print(f"차트 저장 완료: {filepath}")
    
    return fig


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
        'direction_threshold': args.direction_threshold,
        'vol_ratio_threshold': args.vol_ratio_threshold,
        'output_dir': args.output_dir
    }
    
    # 데이터 가져오기
    df = fetch_data(params['market'], params['unit'], params['count'])
    
    # 추세장 라벨링 테스트
    labeling_result, trend_percent = test_trending_market_labeling(df, params)
    
    # 결과 시각화
    fig = visualize_results(df, labeling_result, params)
    
    # 결과 출력
    print("\n=== 분석 결과 요약 ===")
    trending = labeling_result['trending']
    print(f"총 유효 샘플 수: {len(trending.dropna())}")
    print(f"추세장 비율: {trend_percent:.1f}% ({trending.sum()} 샘플)")
    print(f"횡보장 비율: {100-trend_percent:.1f}% ({len(trending.dropna()) - trending.sum()} 샘플)")
    
    # 차트 표시
    plt.show()
    plt.close()


if __name__ == "__main__":
    main() 