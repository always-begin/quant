# %%
import yfinance as yf
import pandas as pd
import numpy as np
import util as ut
from datetime import datetime


def get_evaluate_column(df, cost=.001, rf_rate=.01, isPrint=True, factor='-'):
  factor = ut._get_factor(df, factor)
  df = df.copy()
  df['signal_price'] = np.nan
  df['signal_price'].mask(df['position'] == 'buy', df.loc[:, factor], inplace=True)
  df['signal_price'].mask(df['position'] == 'sell', df.loc[:, factor], inplace=True)

  record = df[['position', 'signal_price']].dropna()
  record['rtn'] = 1
  record['rtn'].mask(record['position'] == 'sell', (record['signal_price'] * (1 - cost)) / record['signal_price'].shift(1), inplace=True)
  record['acc_rtn'] = record['rtn'].cumprod()

  df['signal_price'].mask(df['position'] == 'have_wait', df.loc[:, factor], inplace=True)
  df['rtn'] = record['rtn']
  df['rtn'].fillna(1, inplace=True)

  df['daily_rtn'] = 1
  df['daily_rtn'].mask(df['position'] == 'have_wait', df['signal_price'] / df['signal_price'].shift(1), inplace=True)
  df['daily_rtn'].mask(df['position'] == 'sell', (df['signal_price'] * (1 - cost)) / df['signal_price'].shift(1), inplace=True)
  df['daily_rtn'].fillna(1, inplace=True)

  df['acc_rtn'] = df['daily_rtn'].cumprod()
  df['acc_rtn_dp'] = ((df['acc_rtn'] - 1) * 100).round(2)
  df['mdd'] = (df['acc_rtn'] / df['acc_rtn'].cummax()).round(4)
  df['bm_mdd'] = (df.iloc[:, 0] / df.iloc[:, 0].cummax()).round(4)
  df.drop(columns='signal_price', inplace=True)
  ret = calculate_performance(df, rf_rate, isPrint)

  return df, ret


def calculate_performance(df, rf_rate=.01, isPrint=True):
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
  rst['period'] = _get_period(df)
  rst['annual_rtn'] = _annualize(rst['acc_rtn'], rst['period'])
  rst['bm_rtn'] = round(df.iloc[-1, 0] / df.iloc[0, 0], 4)
  rst['sharpe_ratio'] = _get_sharpe_ratio(df, rf_rate)
  rst['mdd'] = df['mdd'].min()
  rst['bm_mdd'] = df['bm_mdd'].min()

  if isPrint:
    print('CAGR: {:.2%}'.format(rst['annual_rtn'] - 1))
    print('Accumulated return: {:.2%}'.format(rst['acc_rtn'] - 1))
    print('Average return: {:.2%}'.format(rst['avg_rtn'] - 1))
    print('Benchmark return : {:.2%}'.format(rst['bm_rtn'] - 1))
    print('Number of trades: {}'.format(rst['no_trades']))
    print('Number of win: {}'.format(rst['no_win']))
    print('Hit ratio: {:.2%}'.format(rst['hit_ratio']))
    print('Investment period: {:.1f}yrs'.format(rst['period'] / 365))
    print('Sharpe ratio: {:.2f}'.format(rst['sharpe_ratio']))
    print('MDD: {:.2%}'.format(rst['mdd'] - 1))
    print('Benchmark MDD: {:.2%}'.format(rst['bm_mdd'] - 1))
    print("\n\n\n")
  ret = {}

  ret['CAGR'] = float(round((rst['annual_rtn'] - 1) * 100, 3))
  ret['Accumulated'] = float(round((rst['acc_rtn'] - 1) * 100, 3))
  ret['Average'] = round((rst['avg_rtn'] - 1) * 100, 3)
  ret['Benchmark'] = float(round((rst['bm_rtn'] - 1) * 100, 3))
  ret['Trade'] = int(rst['no_trades'])
  ret['Win'] = int(rst['no_win'])
  ret['Hit ratio'] = float(round(rst['hit_ratio'] * 100))
  ret['Investment period'] = int(rst['period'])
  ret['Sharpe'] = float(round(rst['sharpe_ratio'] * 100, 3))
  ret['MDD'] = round((rst['mdd'] - 1) * 100, 3)
  ret['Benchmark MDD'] = round((rst['bm_mdd'] - 1) * 100, 3)
  return ret


def _get_period(df):
  df.dropna(inplace=True)
  end_date = df.index[-1]
  start_date = df.index[0]
  days_between = (end_date - start_date).days
  return abs(days_between)


def _annualize(rate, period):
  if period < 360:
    rate = ((rate - 1) / period * 365) + 1
  elif period > 365:
    rate = rate ** (365 / period)
  else:
    rate = rate
  return round(rate, 4)


def _get_sharpe_ratio(df, rf_rate):
  period = _get_period(df)
  rf_rate_daily = rf_rate / 365 + 1
  df['exs_rtn_daily'] = df['daily_rtn'] - rf_rate_daily
  exs_rtn_annual = (_annualize(df['acc_rtn'][-1], period) - 1) - rf_rate
  exs_rtn_vol_annual = df['exs_rtn_daily'].std() * np.sqrt(365)
  sharpe_ratio = exs_rtn_annual / exs_rtn_vol_annual if exs_rtn_vol_annual > 0 else 0
  return round(sharpe_ratio, 4)
