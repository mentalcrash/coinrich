#!/usr/bin/env python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import argparse

from coinrich.service.candle_service import CandleService
from coinrich.utils.indicators import (
    is_trending_market
)

from mplfinance.original_flavor import candlestick_ohlc


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
    parser.add_argument('--chop-threshold', type=float, default=38.2,
                        help='Choppiness Index 임계값 (이 값보다 작으면 추세장으로 간주)')
    parser.add_argument('--adx-period', type=int, default=14,
                        help='ADX 계산 기간')
    parser.add_argument('--chop-period', type=int, default=14,
                        help='Choppiness Index 계산 기간')
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


def analyze_trend(df, adx_threshold, chop_threshold, adx_period, chop_period):
    """추세장 판별 분석"""
    print(f"\n=== 추세장 판별 분석 ===")
    print(f"ADX 임계값: {adx_threshold}, Choppiness Index 임계값: {chop_threshold}")
    print(f"ADX 계산 기간: {adx_period}, Choppiness Index 계산 기간: {chop_period}")
    
    # 추세장 판별
    trending, adx_values, chop_values, trend_direction = is_trending_market(
        df, 
        adx_threshold=adx_threshold, 
        chop_threshold=chop_threshold,
        adx_period=adx_period,
        chop_period=chop_period
    )
    
    # 추세장 및 횡보장 통계
    trend_count = trending.sum()
    total_count = len(trending)
    trend_percent = (trend_count / total_count) * 100
    
    # 상승/하락 추세 통계
    uptrend_count = (trend_direction == 1).sum()
    downtrend_count = (trend_direction == -1).sum()
    uptrend_percent = (uptrend_count / trend_count * 100) if trend_count > 0 else 0
    downtrend_percent = (downtrend_count / trend_count * 100) if trend_count > 0 else 0
    
    print(f"데이터 샘플 수: {total_count}")
    print(f"추세장 구간 수: {trend_count} ({trend_percent:.1f}%)")
    print(f"  - 상승 추세: {uptrend_count} ({uptrend_percent:.1f}%)")
    print(f"  - 하락 추세: {downtrend_count} ({downtrend_percent:.1f}%)")
    print(f"횡보장 구간 수: {total_count - trend_count} ({100 - trend_percent:.1f}%)")
    
    return trending, adx_values, chop_values, trend_direction, trend_percent


def visualize_results(df, trending, adx_values, chop_values, trend_direction, params):
    """결과 시각화 및 저장"""
    print("\n=== 결과 시각화 및 저장 ===")
    
    # 차트 저장 디렉토리 생성
    os.makedirs(params['output_dir'], exist_ok=True)
    
    # 시각화 - X축 공유 설정
    fig, axs = plt.subplots(3, 1, figsize=(15, 12), 
                            gridspec_kw={'height_ratios': [3, 1, 1]},
                            sharex=True)  # sharex=True로 X축 공유
    
    ax1, ax2, ax3 = axs
    
    # 상단 차트 - 캔들스틱 차트로 변경
    # 데이터 준비 - OHLC 포맷으로 변환
    ohlc = []
    for date, row in df.iterrows():
        date_num = mdates.date2num(date)
        ohlc.append([date_num, row['open'], row['high'], row['low'], row['close']])
    
    # 캔들스틱 차트 그리기
    candlestick_ohlc(ax1, ohlc, width=0.6/(24*60/params['unit']), colorup='green', colordown='red')
    
    # 연속된 추세 구간 최적화하여 표시
    trend_blocks = []  # (시작 인덱스, 종료 인덱스, 추세 여부, 방향)
    
    current_trend = trending.iloc[0]
    current_direction = trend_direction.iloc[0]
    start_idx = trending.index[0]
    
    for i in range(1, len(trending)):
        # 추세 상태나 방향이 변경되거나 마지막 데이터
        if trending.iloc[i] != current_trend or trend_direction.iloc[i] != current_direction or i == len(trending) - 1:
            end_idx = trending.index[i]
            trend_blocks.append((start_idx, end_idx, current_trend, current_direction))
            
            # 다음 블록 준비
            current_trend = trending.iloc[i]
            current_direction = trend_direction.iloc[i]
            start_idx = trending.index[i]
    
    # 추세 블록 표시 (색상 구분)
    for start, end, is_trend, direction in trend_blocks:
        start_num = mdates.date2num(start)
        end_num = mdates.date2num(end)
        if is_trend:
            if direction == 1:  # 상승 추세
                ax1.axvspan(start_num, end_num, alpha=0.2, color='green', label='Uptrend')
            else:  # 하락 추세
                ax1.axvspan(start_num, end_num, alpha=0.2, color='red', label='Downtrend')
        else:
            ax1.axvspan(start_num, end_num, alpha=0.1, color='gray', label='Ranging')
    
    # 범례에 중복 제거
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax1.legend(by_label.values(), by_label.keys(), loc='upper left')
    
    # 추세장 비율 포함한 제목
    trend_percent = trending.sum() / len(trending) * 100
    uptrend_count = (trend_direction == 1).sum()
    downtrend_count = (trend_direction == -1).sum()
    ax1.set_title(f"{params['market']} Price - Trending: {trend_percent:.1f}% (Up: {uptrend_count}, Down: {downtrend_count})")
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
    
    # X축 날짜 포맷 설정 - 맨 아래 차트에만 표시
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
    
    # 상단 두 차트의 X축 레이블 숨기기
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.setp(ax2.get_xticklabels(), visible=False)
    
    # 파라미터 정보 추가
    parameter_text = (
        f"Parameters:\n"
        f"Market: {params['market']}\n"
        f"Timeframe: {params['unit']}min\n"
        f"ADX Threshold: {params['adx_threshold']}\n"
        f"Choppiness Threshold: {params['chop_threshold']}\n"
        f"ADX Period: {params['adx_period']}\n"
        f"Choppiness Period: {params['chop_period']}\n"
    )
    
    parameter_text += f"Data Period: {df.index[0].strftime('%Y-%m-%d %H:%M')} ~ {df.index[-1].strftime('%Y-%m-%d %H:%M')}"
    
    # 텍스트 표시
    plt.figtext(0.01, 0.01, parameter_text, fontsize=10,
                bbox=dict(facecolor='white', alpha=0.8))
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])  # 하단 여백 확보
    
    # 파일명에 파라미터 포함
    filename = f"trend_analysis_{params['market'].replace('-', '_')}_{params['unit']}min_ADX{params['adx_threshold']}_CHOP{params['chop_threshold']}"
    
    filename += f"_ADXp{params['adx_period']}_CHOPp{params['chop_period']}.png"
    filepath = os.path.join(params['output_dir'], filename)
    
    plt.savefig(filepath, dpi=300)
    print(f"차트 저장 완료: {filepath}")
    
    # 결과 반환 (차트와 통계)
    results = {
        'trend_percent': trend_percent,
        'trend_count': trending.sum(),
        'uptrend_count': uptrend_count, 
        'downtrend_count': downtrend_count,
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
        'chop_threshold': args.chop_threshold,
        'adx_period': args.adx_period,
        'chop_period': args.chop_period,
        'output_dir': args.output_dir
    }
    
    # 데이터 가져오기
    df = fetch_data(params['market'], params['unit'], params['count'])
    
    # 추세장 분석
    trending, adx_values, chop_values, trend_direction, trend_percent = analyze_trend(
        df, 
        params['adx_threshold'], 
        params['chop_threshold'],
        params['adx_period'],
        params['chop_period']
    )
    
    # 결과 시각화
    fig, results = visualize_results(df, trending, adx_values, chop_values, trend_direction, params)
    
    # 결과 출력
    print("\n=== 분석 결과 요약 ===")
    print(f"총 샘플 수: {results['total_samples']}")
    print(f"추세장 비율: {results['trend_percent']:.1f}% ({results['trend_count']} 샘플)")
    print(f"  - 상승 추세: {results['uptrend_count']} 샘플")
    print(f"  - 하락 추세: {results['downtrend_count']} 샘플")
    print(f"횡보장 비율: {100-results['trend_percent']:.1f}% ({results['ranging_count']} 샘플)")
    print(f"차트 저장 경로: {results['chart_path']}")
    
    # 차트 표시
    plt.show()
    plt.close()


if __name__ == "__main__":
    main() 