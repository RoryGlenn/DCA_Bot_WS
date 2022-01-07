# https://support.kraken.com/hc/en-us/articles/360043283472-Python-WebSocket-recommended-Python-library-and-usage-examples
# https://github.com/krakenfx/kraken-wsclient-py/blob/master/kraken_wsclient_py/kraken_wsclient_py.py


import os

from bot_features.kraken_dca_bot.kraken_dca_bot import KrakenDCABot
from bot_features.low_level.kraken_enums        import *

from util.globals                               import G


if __name__ == "__main__":
    os.system("cls")
    os.system("color")
    
    G.log.directory_create()
    G.log.file_create()
    
    kraken_dca_bot = KrakenDCABot()
    kraken_dca_bot.start_trade_loop()
