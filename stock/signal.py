
import numpy as np


def add_signal_df(df, factor, buy, sell):
  df['trade'] = np.nan
  if buy >= sell:
    df['trade'] = df['trade'].mask(df[factor] > buy, 'have')
    df['trade'] = df['trade'].mask(df[factor] < sell, 'zero')
  else:
    df['trade'] = df['trade'].mask(df[factor] < buy, 'have')
    df['trade'] = df['trade'].mask(df[factor] > sell, 'zero')
  df['trade'].fillna(method='ffill', inplace=True)
  df['trade'].fillna('zero', inplace=True)
  _add_position_df(df)
  print(f"signal columns : {df.columns}")
  return df


def add_band_to_signal(df, factor, buy, sell):

  df['trade'] = np.nan
  # buy
  if buy == 'A':
    df['trade'].mask(df[factor] > df['ub'], 'have', inplace=True)
  elif buy == 'B':
    df['trade'].mask((df['ub'] > df[factor]) & (df[factor] > df['center']), 'have', inplace=True)
  elif buy == 'C':
    df['trade'].mask((df['center'] > df[factor]) & (df[factor] > df['lb']), 'have', inplace=True)
  elif buy == 'D':
    df['trade'].mask((df['lb'] > df[factor]), 'have', inplace=True)
  # zero
  if sell == 'A':
    df['trade'].mask(df[factor] > df['ub'], 'zero', inplace=True)
  elif sell == 'B':
    df['trade'].mask((df['ub'] > df[factor]) & (df[factor] > df['center']), 'zero', inplace=True)
  elif sell == 'C':
    df['trade'].mask((df['center'] > df[factor]) & (df[factor] > df['lb']), 'zero', inplace=True)
  elif sell == 'D':
    df['trade'].mask((df['lb'] > df[factor]), 'zero', inplace=True)
  df['trade'].fillna(method='ffill', inplace=True)
  df['trade'].fillna('zero', inplace=True)
  _add_position_df(df)
  return df


def add_combine_signal_and(df, conditions):
  for c in conditions:
    df['trade'].mask((df['trade'] == 'have') & (df[c] == 'have'), 'have', inplace=True)
    df['trade'].mask((df['trade'] == 'zero') | (df[c] == 'zero'), 'zero', inplace=True)
  _add_position_df(df)
  return df


def add_combine_signal_or(df, conditions):
  for c in conditions:
    df['trade'].mask((df['trade'] == 'have') | (df[c] == 'have'), 'have', inplace=True)
    df['trade'].mask((df['trade'] == 'zero') & (df[c] == 'zero'), 'zero', inplace=True)
  _add_position_df(df)
  return df


def _add_position_df(df):
  pos = 'position'
  trade = 'trade'
  pos_chart = 'position_chart'

  df[pos] = ''
  df[pos].mask((df[trade].shift(1) == 'zero') & (df[trade] == 'zero'), 'zero_wait', inplace=True)
  df[pos].mask((df[trade].shift(1) == 'zero') & (df[trade] == 'have'), 'buy', inplace=True)
  df[pos].mask((df[trade].shift(1) == 'have') & (df[trade] == 'zero'), 'sell', inplace=True)
  df[pos].mask((df[trade].shift(1) == 'have') & (df[trade] == 'have'), 'have_wait', inplace=True)

  df[pos_chart] = 0
  df[pos_chart].mask(df[trade] == 'have', 1, inplace=True)
