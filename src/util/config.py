"""config_parser.py - scans for config.txt file and applies users settings."""

import json
import os
import sys

from pprint                              import pprint
# from util.globals                        import G
from bot_features.low_level.kraken_enums import *


class Config():
    def __init__(self) -> None:
        self.REGULAR_LIST: list = ['ETC',  'ETH',  'LTC',  'MLN',  'REP',  'XBT',  'XDG',  'XLM',  'XMR',  'XRP',  'ZEC']
        self.BUY_COINS:    list = []
        self.DCA_DATA:     dict = {}
        self.API_KEY:      str  = ""
        self.API_SECRET:   str  = ""
        self.set_values()
        return
    
    def set_values(self) -> None:
        if os.path.exists(CONFIG_JSON):
            with open(CONFIG_JSON) as file:
                try:
                    config          = json.load(file)[ConfigKeys.CONFIG]
                    self.API_KEY    = config[ConfigKeys.KRAKEN_API_KEY]
                    self.API_SECRET = config[ConfigKeys.KRAKEN_SECRET_KEY]
                    self.DCA_DATA   = {symbol: dca_data for (symbol, dca_data) in config['buy_set'].items()}
                except Exception as e:
                    G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
                    sys.exit(1)
        else:
            G.log.print_and_log("Could not find config.json file")
            sys.exit(0)
        return