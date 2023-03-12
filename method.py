# %%
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import finterstellar as fs
import matplotlib.pyplot as plt

# download stock dataframe


def get_yf_df(name, startDt, endDt):
  ticker = yf.Ticker(name)
  print(f"start : {startDt},end: {endDt}")
  stockDf = ticker.history(start=startDt, end=endDt)
  print(f"yahoo finance df's columns : {stockDf.columns}")
  return stockDf

# %% set strategy


def get_trend_of_macd_df(input_df, short=12, long=26, signal=9, factor='Close'):

  output_df = input_df.copy()
  output_df['ema_short'] = input_df[factor].ewm(span=short).mean()
  output_df['ema_long'] = input_df[factor].ewm(span=long).mean()
  output_df['macd'] = (output_df['ema_short']-output_df['ema_long']).round(2)
  output_df['macd_signal'] = output_df['macd'].ewm(span=signal).mean().round(2)
  output_df['macd_oscillator'] = (output_df['macd']-output_df['macd_signal']).round(2)
  ret = output_df[[factor, 'macd', 'macd_signal', 'macd_oscillator']]
  print(f"macd output_df : {ret.columns}")
  return ret


def get_trend_of_rsi(input_df, window=14, factor='Close'):

  output_df = input_df.copy()
  output_df.fillna(method='ffill', inplace=True)
  if len(output_df) > window:
    output_df['diff'] = output_df.loc[:, factor].diff()
    output_df['au'] = output_df['diff'].where(output_df['diff'] > 0, 0).rolling(window).mean()
    output_df['ad'] = output_df['diff'].where(output_df['diff'] < 0, 0).rolling(window).mean().abs()
    for r in range(window+1, len(output_df)):
      output_df['au'][r] = (output_df['au'][r-1]*(window-1) + output_df['diff'].where(output_df['diff'] > 0, 0)[r]) / window
      output_df['ad'][r] = (output_df['ad'][r-1]*(window-1) + output_df['diff'].where(output_df['diff'] < 0, 0).abs()[r]) / window
    output_df['rsi'] = (output_df['au'] / (output_df['au'] + output_df['ad']) * 100).round(2)
    ret = output_df[[factor, 'rsi']]
    print(f"rsi output_df : {ret.columns}")
    return ret
  else:
    print("it cant create rsi dataframe")
    return None
  

def get_trend_of_envelope(input_df, window=20, spread = .05, factor='Close'):

  output_df = input_df.copy()
  output_df['center'] = output_df[factor].rolling(window).mean()
  output_df['ub'] = output_df['center']*(1+spread)
  output_df['lb'] = output_df['center']*(1-spread)
  return output_df[[factor, 'center', 'ub', 'lb']]


def get_trend_of_bollinger(input_df, w=20, k=2, factor='Close'):
  output_df = input_df.copy()
  output_df['center'] = output_df[factor].rolling(w).mean()
  output_df['sigma'] = output_df[factor].rolling(w).std()
  output_df['ub'] = output_df['center'] + k * output_df['sigma']
  output_df['lb'] = output_df['center'] - k * output_df['sigma']
  return output_df[[factor, 'center','ub','lb']]


# %% set position


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
  add_position_df(df)
  print(f"signal columns : {df.columns}")
  return df

def add_band_to_signal(df, factor, buy, sell):

    df['trade'] = np.nan
    # buy
    if buy == 'A':
        df['trade'].mask(df[factor]>df['ub'], 'have', inplace=True)
    elif buy == 'B':
        df['trade'].mask((df['ub']>df[factor]) & (df[factor]>df['center']), 'have', inplace=True)
    elif buy == 'C':
        df['trade'].mask((df['center']>df[factor]) & (df[factor]>df['lb']), 'have', inplace=True)
    elif buy == 'D':
        df['trade'].mask((df['lb']>df[factor]), 'have', inplace=True)
    # zero
    if sell == 'A':
        df['trade'].mask(df[factor]>df['ub'], 'zero', inplace=True)
    elif sell == 'B':
        df['trade'].mask((df['ub']>df[factor]) & (df[factor]>df['center']), 'zero', inplace=True)
    elif sell == 'C':
        df['trade'].mask((df['center']>df[factor]) & (df[factor]>df['lb']), 'zero', inplace=True)
    elif sell == 'D':
        df['trade'].mask((df['lb']>df[factor]), 'zero', inplace=True)
    df['trade'].fillna(method='ffill', inplace=True)
    df['trade'].fillna('zero', inplace=True)
    return df['trade']

def add_combine_signal_and(df, conditions):
    '''
    Combine signals as intersection
    :param df: Dataframe containing historical prices
    :param cond: Columns to be combined
    :return: Dataframe of selected signals
    '''
    for c in conditions:
        df['trade'].mask((df['trade'] == 'have') & (df[c] == 'have'), 'have', inplace=True)
        df['trade'].mask((df['trade'] == 'zero') | (df[c] == 'zero'), 'zero', inplace=True)
    return df


def add_combine_signal_or(df, conditions):
    '''
    Combine signals as union
    :param df: Dataframe containing historical prices
    :param cond: Columns to be combined
    :return: Dataframe of selected signals
    '''
    for c in conditions:
        df['trade'].mask((df['trade'] == 'have') | (df[c] == 'have'), 'have', inplace=True)
        df['trade'].mask((df['trade'] == 'zero') & (df[c] == 'zero'), 'zero', inplace=True)
    return df


def add_position_df(df):
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

# %% to evaluate a strategy


def get_evaluate_column(df, factor='Close', cost=.001, rf_rate=.01,isPrint=True):
  '''
  Calculate daily returns and MDDs of portfolio
  :param df: The dataframe containing trading position
  :param cost: Transaction cost when sell
  :return: Returns, MDD
  '''
  df = df.copy()
  df['signal_price'] = np.nan
  df['signal_price'].mask(df['position'] == 'buy', df.loc[:, factor], inplace=True)
  df['signal_price'].mask(df['position'] == 'sell', df.loc[:, factor], inplace=True)

  record = df[['position', 'signal_price']].dropna()
  record['rtn'] = 1
  record['rtn'].mask(record['position'] == 'sell', (record['signal_price'] * (1-cost))/record['signal_price'].shift(1), inplace=True)
  record['acc_rtn'] = record['rtn'].cumprod()

  df['signal_price'].mask(df['position'] == 'have_wait', df.loc[:, factor], inplace=True)
  df['rtn'] = record['rtn']
  df['rtn'].fillna(1, inplace=True)

  df['daily_rtn'] = 1
  df['daily_rtn'].mask(df['position'] == 'have_wait', df['signal_price'] / df['signal_price'].shift(1), inplace=True)
  df['daily_rtn'].mask(df['position'] == 'sell', (df['signal_price'] * (1-cost)) / df['signal_price'].shift(1), inplace=True)
  df['daily_rtn'].fillna(1, inplace=True)

  df['acc_rtn'] = df['daily_rtn'].cumprod()
  df['acc_rtn_dp'] = ((df['acc_rtn']-1)*100).round(2)
  df['mdd'] = (df['acc_rtn'] / df['acc_rtn'].cummax()).round(4)
  df['bm_mdd'] = (df.iloc[:, 0] / df.iloc[:, 0].cummax()).round(4)
  df.drop(columns='signal_price', inplace=True)
  ret = calcualte_performance(df, rf_rate, isPrint)

  return df, ret


def calcualte_performance(df, rf_rate=.01, isPrint=True):
  '''
  Calculate additional information of portfolio
  :param df: The dataframe with daily returns
  :param rf_rate: Risk free interest rate
  :return: Number of trades, Number of wins, Hit ratio, Sharpe ratio, ...
  '''
  rst = {}
  rst['no_trades'] = (df['position'] == 'buy').sum()
  rst['no_win'] = (df['rtn'] > 1).sum()
  rst['acc_rtn'] = df['acc_rtn'][-1].round(4)
  rst['hit_ratio'] = round((df['rtn'] > 1).sum() / rst['no_trades'], 4) if rst['no_trades'] > 0 else 0
  rst['avg_rtn'] = round(df[df['rtn'] != 1]['rtn'].mean(), 4)
  rst['period'] = __get_period(df)
  rst['annual_rtn'] = __annualize(rst['acc_rtn'], rst['period'])
  rst['bm_rtn'] = round(df.iloc[-1, 0]/df.iloc[0, 0], 4)
  rst['sharpe_ratio'] = __get_sharpe_ratio(df, rf_rate)
  rst['mdd'] = df['mdd'].min()
  rst['bm_mdd'] = df['bm_mdd'].min()

  if isPrint :
    print('CAGR: {:.2%}'.format(rst['annual_rtn'] - 1))
    print('Accumulated return: {:.2%}'.format(rst['acc_rtn'] - 1))
    print('Average return: {:.2%}'.format(rst['avg_rtn'] - 1))
    print('Benchmark return : {:.2%}'.format(rst['bm_rtn']-1))
    print('Number of trades: {}'.format(rst['no_trades']))
    print('Number of win: {}'.format(rst['no_win']))
    print('Hit ratio: {:.2%}'.format(rst['hit_ratio']))
    print('Investment period: {:.1f}yrs'.format(rst['period']/365))
    print('Sharpe ratio: {:.2f}'.format(rst['sharpe_ratio']))
    print('MDD: {:.2%}'.format(rst['mdd']-1))
    print('Benchmark MDD: {:.2%}'.format(rst['bm_mdd']-1))
    print("\n\n\n")
  ret ={}

  ret['CAGR'] = float(round((rst['annual_rtn'] - 1)*100, 3))
  ret['Accumulated'] = float(round((rst['acc_rtn'] - 1)*100, 3))
  ret['Average'] =round( (rst['avg_rtn'] - 1)*100, 3)
  ret['Benchmark'] =float(round( (rst['bm_rtn']-1)*100, 3))
  ret['Trade'] = int(rst['no_trades'])
  ret['Win'] = int(rst['no_win'])
  ret['Hit ratio'] = float(round(rst['hit_ratio']*100))
  ret['Investment period'] = int(rst['period'])
  ret['Sharpe'] = float(round(rst['sharpe_ratio']*100,3))
  ret['MDD'] = round((rst['mdd']-1)*100, 3)
  ret['Benchmark MDD'] =round( (rst['bm_mdd']-1)*100, 3)
  return ret


def __get_period(df):
  df.dropna(inplace=True)
  end_date = df.index[-1]
  start_date = df.index[0]
  days_between = (end_date - start_date).days
  return abs(days_between)


def __annualize(rate, period):
  if period < 360:
    rate = ((rate-1) / period * 365) + 1
  elif period > 365:
    rate = rate ** (365 / period)
  else:
    rate = rate
  return round(rate, 4)


def __get_sharpe_ratio(df, rf_rate):
  '''
  Calculate sharpe ratio
  :param df:
  :param rf_rate:
  :return: Sharpe ratio
  '''
  period = __get_period(df)
  rf_rate_daily = rf_rate / 365 + 1
  df['exs_rtn_daily'] = df['daily_rtn'] - rf_rate_daily
  exs_rtn_annual = (__annualize(df['acc_rtn'][-1], period) - 1) - rf_rate
  exs_rtn_vol_annual = df['exs_rtn_daily'].std() * np.sqrt(365)
  sharpe_ratio = exs_rtn_annual / exs_rtn_vol_annual if exs_rtn_vol_annual > 0 else 0
  return round(sharpe_ratio, 4)

# %% just show


def draw_chart(dataframe, left=None, right='Close'):
  fs.draw_chart(dataframe, left, right)


def draw_trade_results(dataframe):
  fs.draw_trade_results(dataframe)

def draw_band_chart(dataframe, band=['lb','center','ub'], log=False):
  fs.draw_band_chart(dataframe, band=['lb','center','ub'], log=False)


# %%
