import matplotlib.font_manager as fm
import finterstellar as fs
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False


def draw_chart(dataframe, left=None, right='Close'):
  fs.draw_chart(dataframe, left, right)


def draw_trade_results(dataframe):
  fs.draw_trade_results(dataframe)


def draw_band_chart(dataframe, band=['lb', 'center', 'ub'], log=False):
  fs.draw_band_chart(dataframe, band=['lb', 'center', 'ub'], log=False)
