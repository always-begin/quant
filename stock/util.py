import pandas as pd


def str_to_list(s):
  if type(s) == list:
    cds = s
  else:
    cds = []
    cds.append(s)
  return cds


def months_before(date, n):
  d = pd.to_datetime(date) - pd.DateOffset(months=n)
  if d.weekday() > 4:
    adj = d.weekday() - 4
    d += pd.DateOffset(days=adj)
  else:
    d = d
  return d.date()


headers = {
    'User-Agent': 'Mozilla',
    'X-Requested-With': 'XMLHttpRequest',
}


def __decimal_formatter(duex):
  if duex:
    pd.options.display.float_format = '{:,.2f}'.format
  else:
    pd.options.display.float_format = '{:,.6f}'.format


def _get_factor(input_df, factor):
  if factor == '-':
    factor = input_df.columns[0]
    print(f'factor : {factor}')
  return factor
