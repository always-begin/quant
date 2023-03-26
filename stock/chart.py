import finterstellar as fs
import matplotlib.pyplot as plt


def draw_chart(dataframe, left=None, right='Close'):
  fs.draw_chart(dataframe, left, right)


def draw_trade_results(dataframe):
  fs.draw_trade_results(dataframe)


def draw_band_chart(dataframe, band=['lb', 'center', 'ub'], log=False):
  fs.draw_band_chart(dataframe, band=['lb', 'center', 'ub'], log=False)
