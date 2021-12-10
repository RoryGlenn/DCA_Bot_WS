# https://support.kraken.com/hc/en-us/articles/360043283472-Python-WebSocket-recommended-Python-library-and-usage-examples

# https://github.com/krakenfx/kraken-wsclient-py/blob/master/kraken_wsclient_py/kraken_wsclient_py.py


import json
import sys
import os

from threading                   import Thread
from util.config_parser          import Config
from util.globals                import G
from bot_features.kraken_dca_bot import KrakenDCABot
from bot_features.kraken_enums   import *


def get_keys() -> str:
    if os.path.exists(CONFIG_JSON):
        with open(CONFIG_JSON) as file:
            try:
                config = json.load(file)[ConfigKeys.CONFIG]
                return config[ConfigKeys.KRAKEN_API_KEY], config[ConfigKeys.KRAKEN_SECRET_KEY]
            except Exception as e:
                print(e)
    sys.exit(0)

if __name__ == "__main__":
    os.system("cls")
    os.system("color")
    
    G.log.directory_create()
    G.log.file_create()    
    
    api_key, api_secret = get_keys()
    kraken_dca_bot = KrakenDCABot(api_key, api_secret)
    Thread(target=kraken_dca_bot.set_values_loop, daemon=True).start()
    kraken_dca_bot.start_trade_loop()
