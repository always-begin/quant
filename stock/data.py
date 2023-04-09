

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import finterstellar as fs
import matplotlib.pyplot as plt
import requests as req
import json
from . import util as ut


def get_ohlc(symbol, start_date=None, end_date=None, decimal_duex=True):
  if isinstance(symbol, list):
    symbol = symbol[0]
  end_date = pd.to_datetime(end_date).date() if end_date else pd.Timestamp.today().date()
  start_date = pd.to_datetime(start_date).date() if start_date else ut.months_before(end_date, 12)
  df = _get_daily_price(symbol, start=start_date, end=end_date)
  ut.__decimal_formatter(decimal_duex)
  return df


def get_price(symbol, start_date=None, end_date=None, decimal_duex=True):
  df = get_ohlc(symbol, start_date=start_date, end_date=end_date, decimal_duex=decimal_duex)
  df.rename(columns={'Close': symbol}, inplace=True)
  return df[[symbol]]


def get_finter_single(symbol='', window='T'):
  file = open("../token", 'r')
  otp = file.readline()
  url = 'https://api.finterstellar.com/api/single?otp={}&symbol={}&window={}'.format(otp, symbol, window)
  r = req.get(url)
  try:
    df = pd.read_json(r.text, orient='index')
    if 'Current Debt' in df.columns:
      df['Current Debt'].fillna(0, inplace=True)
    else:
      df['Current Debt'] = 0
    df = df[~(pd.isna(df['Revenue']) | pd.isna(df['Price']))].fillna(0).copy()
    return df
  except:
    print(r.text)


def _get_daily_price(symbol, interval='1d', range=None, start=None, end=None):
  symbol = symbol.replace('.', '-')
  params = {
      'region': 'US',
      'interval': interval,
      'corsDomain': 'finance.yahoo.com',
      '.tsrc': 'finance',
      'range': range if range else None,
      'period1': (pd.Timestamp(start) - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s') if start else 946688460,
      'period2': (pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
      if end else (pd.Timestamp.today() + pd.Timedelta(days=1) - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s'),
  }
  url = 'https://query1.finance.yahoo.com/v8/finance/chart/{}'.format(symbol)
  r = req.get(url, headers=ut.headers, params=params)
  raw = json.loads(r.text)
  rst = _make_ohlc(raw)
  return rst


def _make_ohlc(raw):
  time_offset = raw['chart']['result'][0]['meta']['gmtoffset']
  times = pd.to_datetime([x + time_offset for x in raw['chart']['result'][0]['timestamp']], unit='s').date
  open = raw['chart']['result'][0]['indicators']['quote'][0]['open']
  high = raw['chart']['result'][0]['indicators']['quote'][0]['high']
  low = raw['chart']['result'][0]['indicators']['quote'][0]['low']
  close = raw['chart']['result'][0]['indicators']['quote'][0]['close']
  adj_close = raw['chart']['result'][0]['indicators']['adjclose'][0]['adjclose']
  volume = raw['chart']['result'][0]['indicators']['quote'][0]['volume']
  d = {
      'Open': open,
      'High': high,
      'Low': low,
      'Close': close,
      'Volume': volume,
      'Adj Close': adj_close,
  }
  data = pd.DataFrame(d, index=times)
  data.index = pd.to_datetime(data.index)
  data = data.round(2)
  return data


def _get_multiple_prices(symbols, dates):
  prices = pd.DataFrame()
  for s in symbols:
    tmp = _get_daily_price(s, start=dates[0], end=dates[-1])['Close']
    tmp.rename(s, inplace=True)
    prices = pd.concat([prices, tmp], axis=1)
    prices.index = pd.to_datetime(prices.index)
  return prices.loc[dates]


def __get_month_ends(start_date=None, end_date=None):
  checker = _get_daily_price('SPY', start=start_date, end=end_date)['Close']
  month_ends = checker[checker.groupby([checker.index.year, checker.index.month]).apply(lambda s: np.max(s.index))].index
  return month_ends


def __get_month_end_prices(symbols, start_date=None, end_date=None):
  checker = _get_daily_price('SPY', start=start_date, end=end_date)['Close']
  month_ends = checker[checker.groupby([checker.index.year, checker.index.month]).apply(lambda s: np.max(s.index))].index
  prices = pd.DataFrame()
  for s in symbols:
    tmp = _get_daily_price(s, start=month_ends.min(), end=month_ends.max())['Close']
    tmp.rename(s, inplace=True)
    prices = pd.concat([prices, tmp], axis=1)
    prices.index = pd.to_datetime(prices.index)
  return prices.loc[month_ends]


if __name__ == '__main__':
  df = get_price('MSFT')
