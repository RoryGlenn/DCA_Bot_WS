"""config_parser.py - scans for config.txt file and applies users settings."""

import json
import os
import sys
import time

from pprint import pprint
from util.globals import G
from bot_features.kraken_enums import *


class Config():
    def __init__(self) -> None:
        self.REGULAR_LIST = ['ETC',  'ETH',  'LTC',  'MLN',  'REP',  'XBT',  'XDG',  'XLM',  'XMR',  'XRP',  'ZEC']
        
        # api keys.
        self.API_KEY:                      str   = ""
        self.API_SECRET:                   str   = ""
        
        # DCA vars.
        self.TARGET_PROFIT_PERCENT:        float = 0.0
        self.SAFETY_ORDER_VOLUME_SCALE:    float = 0.0
        self.SAFETY_ORDERS_MAX:            int   = 0
        self.SAFETY_ORDERS_ACTIVE_MAX:     int   = 0
        self.SAFETY_ORDER_STEP_SCALE:      float = 0.0
        self.SAFETY_ORDER_PRICE_DEVIATION: float = 0.0
        self.BASE_ORDER_SIZE:              float = 0.0
        self.SAFETY_ORDER_SIZE:            float = 0.0

        # coins to buy.
        self.BUY_COINS:                    list   = []
        
        # time intervals for trading view.
        self.TRADINGVIEW_TIME_INTERVALS:   set   = set()
        
        # if symbol is in this list, prepend 'X' to the symbol.
        # (this applies to the kraken exchange only)
        return
    
    def set_values(self) -> None:
        if os.path.exists(CONFIG_JSON):
            with open(CONFIG_JSON) as file:
                try:
                    config = json.load(file)[ConfigKeys.CONFIG]
                    
                    self.API_KEY    = config[ConfigKeys.KRAKEN_API_KEY]
                    self.API_SECRET = config[ConfigKeys.KRAKEN_SECRET_KEY]
                
                    for symbol in config[ConfigKeys.BUY_SET]:
                        if symbol in self.REGULAR_LIST:
                            symbol = "X" + symbol
                        if symbol not in self.BUY_COINS:
                            self.BUY_COINS.append(symbol)

                    self.BUY_COINS.sort()
                    
                    # DCA
                    self.TARGET_PROFIT_PERCENT          = float(config[ConfigKeys.DCA_TARGET_PROFIT_PERCENT])
                    self.SAFETY_ORDER_VOLUME_SCALE      = float(config[ConfigKeys.DCA_SAFETY_ORDER_VOLUME_SCALE])
                    self.SAFETY_ORDERS_MAX              = int  (config[ConfigKeys.DCA_SAFETY_ORDERS_MAX])
                    self.SAFETY_ORDERS_ACTIVE_MAX       = int  (config[ConfigKeys.DCA_SAFETY_ORDERS_ACTIVE_MAX])
                    self.SAFETY_ORDER_STEP_SCALE        = float(config[ConfigKeys.DCA_SAFETY_ORDER_STEP_SCALE])
                    self.SAFETY_ORDER_PRICE_DEVIATION   = float(config[ConfigKeys.DCA_SAFETY_ORDER_PRICE_DEVIATION])
                    self.SAFETY_ORDER_SIZE              = float(config[ConfigKeys.DCA_SAFETY_ORDER_SIZE])
                    self.BASE_ORDER_SIZE                = float(config[ConfigKeys.DCA_BASE_ORDER_SIZE])
                    self.ALL_OR_NOTHING                 = bool(config[ConfigKeys.DCA_ALL_OR_NOTHING])

                    for interval in config[ConfigKeys.TIME_INTERVALS]:
                        if interval in TimeIntervals.ALL_LIST:
                            self.TRADINGVIEW_TIME_INTERVALS.add(interval)
                except Exception as e:
                    G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
                    sys.exit(1)
        else:
            G.log.print_and_log("Could not find config.json file")
            sys.exit(0)
        
        return