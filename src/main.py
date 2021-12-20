# https://support.kraken.com/hc/en-us/articles/360043283472-Python-WebSocket-recommended-Python-library-and-usage-examples

# https://github.com/krakenfx/kraken-wsclient-py/blob/master/kraken_wsclient_py/kraken_wsclient_py.py


import json
import os
import sys

from bot_features.kraken_dca_bot import KrakenDCABot
from bot_features.low_level.kraken_enums   import *
from util.globals                import G


def get_keys() -> str:
    if os.path.exists(CONFIG_JSON):
        with open(CONFIG_JSON) as file:
            try:
                config = json.load(file)[ConfigKeys.CONFIG]
                return config[ConfigKeys.KRAKEN_API_KEY], config[ConfigKeys.KRAKEN_SECRET_KEY]
            except Exception as e:
                G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
    sys.exit(0)

if __name__ == "__main__":
    os.system("cls")
    os.system("color")
    
    G.log.directory_create()
    G.log.file_create()
    
    api_key, api_secret = get_keys()
    KrakenDCABot(api_key, api_secret).start_trade_loop()
