import numpy as np
import pandas as pd
import util as ut


def get_macd(input_df, short=12, long=26, signal=9, factor='-'):
  factor = ut._get_factor(input_df, factor)
  output_df = input_df.copy()
  output_df['ema_short'] = input_df[factor].ewm(span=short).mean()
  output_df['ema_long'] = input_df[factor].ewm(span=long).mean()
  output_df['macd'] = (output_df['ema_short'] - output_df['ema_long']).round(2)
  output_df['macd_signal'] = output_df['macd'].ewm(span=signal).mean().round(2)
  output_df['macd_oscillator'] = (output_df['macd'] - output_df['macd_signal']).round(2)
  ret = output_df[[factor, 'macd', 'macd_signal', 'macd_oscillator']]
  print(f"macd output_df : {ret.columns}")
  return ret


def get_rsi(input_df, window=14, factor='-'):
  factor = ut._get_factor(input_df, factor)
  output_df = input_df.copy()
  output_df.fillna(method='ffill', inplace=True)
  if len(output_df) > window:
    output_df['diff'] = output_df.loc[:, factor].diff()
    output_df['au'] = output_df['diff'].where(output_df['diff'] > 0, 0).rolling(window).mean()
    output_df['ad'] = output_df['diff'].where(output_df['diff'] < 0, 0).rolling(window).mean().abs()
    for r in range(window + 1, len(output_df)):
      output_df['au'][r] = (output_df['au'][r - 1] * (window - 1) + output_df['diff'].where(output_df['diff'] > 0, 0)[r]) / window
      output_df['ad'][r] = (output_df['ad'][r - 1] * (window - 1) + output_df['diff'].where(output_df['diff'] < 0, 0).abs()[r]) / window
    output_df['rsi'] = (output_df['au'] / (output_df['au'] + output_df['ad']) * 100).round(2)
    ret = output_df[[factor, 'rsi']]
    print(f"rsi output_df : {ret.columns}")
    return ret
  else:
    print("it cant create rsi dataframe")
    return None


def get_envelope(input_df, window=20, spread=.05, factor='-'):
  factor = ut._get_factor(input_df, factor)
  output_df = input_df.copy()
  output_df['center'] = output_df[factor].rolling(window).mean()
  output_df['ub'] = output_df['center'] * (1 + spread)
  output_df['lb'] = output_df['center'] * (1 - spread)
  ret = output_df[[factor, 'center', 'ub', 'lb']]
  print(f"envelope output_df : {ret.columns}")
  return ret


def get_bollinger(input_df, w=20, k=2, factor='-'):
  factor = ut._get_factor(input_df, factor)
  output_df = input_df.copy()
  output_df['center'] = output_df[factor].rolling(w).mean()
  output_df['sigma'] = output_df[factor].rolling(w).std()
  output_df['ub'] = output_df['center'] + k * output_df['sigma']
  output_df['lb'] = output_df['center'] - k * output_df['sigma']
  ret = output_df[[factor, 'center', 'ub', 'lb']]
  print(f"bollinger output_df : {ret.columns}")
  return ret


def get_stochastic(input_df, day_fast_k=14, day_slow_k=3, day_slow_d=3, factor='-'):
  factor = ut._get_factor(input_df, factor)
  output_df = input_df.copy()
  try:
    output_df['fast_k'] = ((output_df['Close'] - output_df['Low'].rolling(day_fast_k).min())
                           / (output_df['High'].rolling(day_fast_k).max() - output_df['Low'].rolling(day_fast_k).min())
                           ).round(4) * 100
    output_df['slow_k'] = output_df['fast_k'].rolling(day_slow_k).mean().round(2)
    output_df['slow_d'] = output_df['slow_k'].rolling(day_slow_d).mean().round(2)
    ret = output_df[[factor, 'slow_k', 'slow_d']]
    print(f"stochastic output_df : {ret.columns}")
    return ret
  except:
    return 'Error. The stochastic indicator requires OHLC data and symbol. Try get_ohlc() to retrieve price data.'
