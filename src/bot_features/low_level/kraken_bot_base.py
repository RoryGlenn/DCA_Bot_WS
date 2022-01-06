"""spot.py: Supports base functionality for buying, selling and transfering. Meant to be inherited from for additional classes"""

import requests
import time
import datetime

from pprint                                 import pprint

from util.globals                           import G
from bot_features.low_level.kraken_rest_api import KrakenRestAPI
from bot_features.low_level.kraken_enums    import *


class KrakenBotBase(KrakenRestAPI):
    def __init__(self, api_key: str = "", api_secret: str = "") -> None:
        """
        Returns new Spot object with specified data
        
        """
        super().__init__(api_key, api_secret)
        self.asset_pairs_dict: dict = requests.get(URL_ASSET_PAIRS).json()[Dicts.RESULT]
        self.asset_info:       dict = self.get_asset_info()[Dicts.RESULT]
        return

    def get_elapsed_time(self, start_time: float) -> str:
        end_time     = time.time()
        elapsed_time = round(end_time - start_time)
        minutes      = elapsed_time // 60
        seconds      = elapsed_time % 60
        return f"{minutes} minutes {seconds} seconds"

    def get_buy_time(self) -> str:
        """Returns the next time to buy as specified in the config file."""
        return ( datetime.timedelta(minutes=Buy_.TIME_MINUTES) + datetime.datetime.now() ).strftime("%H:%M:%S")

    def get_current_time(self) -> str:
        """Returns the current time in hours:minutes:seconds format."""
        return datetime.datetime.now().strftime("%H:%M:%S")

    def wait(self, message: str = "", timeout: int = Nap.NORMAL) -> bool:
        """
        Sleep function that also checks if the global exit event has been triggered.
        
        """
        if message != "":
            G.log.print_and_log(message, G.print_lock)

        # timeout in number of seconds
        if not G.event.wait(timeout):
            return True
        return False


    def get_all_tradable_asset_pairs(self) -> None:
        """
        Returns a dictionary containing all legal trading pairs on kraken
        For example, if you want to trade XLTC/USD, search the keys
        of the returned dictionary for the symbol pair. If the pair is
        not in the dictionary, the pair cannot be used to buy or sell.
        
        """
        self.asset_pairs_dict = requests.get(URL_ASSET_PAIRS).json()
        return
            
    def get_order_min(self, symbol_pair: str) -> float:  
        """
        Returns the min quantity of coin we can order per USD.
        
        """
        return float(self.asset_pairs_dict[symbol_pair][Dicts.ORDER_MIN])
    
    def get_max_price_precision(self, symbol_pair: str) -> int:
        """
        Returns the maximum price precision in number of decimals
        
        """
        return int(self.asset_pairs_dict[symbol_pair][Dicts.PAIR_DECIMALS])

    def get_max_volume_precision(self, symbol_pair: str) -> int:
        """
        Returns the maximum volume precision in terms number of decimals
        
        """
        return int(self.asset_pairs_dict[symbol_pair][Dicts.LOT_DECIMALS])
        
    def get_withdrawal_precision_max(self, symbol: str) -> int:
        """Gets maximum decimal places when withdrawal of coin"""
        return int(self.asset_info[symbol][Dicts.DECIMALS])
        
    def get_ask_price(self, symbol_pair: str) -> float:
        """
        Gets the current ask price for a symbol pair on kraken. 
        
        """
        current_price = self.get_ticker_information(pair=symbol_pair)
        current_price = self.parse_ticker_information(current_price)
        return self.parse_ask_price(current_price)

    def get_bid_price(self, symbol_pair: str) -> float:
        """Gets the current bid price for a symbol pair"""
        current_price = self.get_ticker_information(pair=symbol_pair)
        current_price = self.parse_ticker_information(current_price)
        return self.parse_bid_price(current_price)

    def get_alt_name(self, symbol: str) -> str | None:
        if symbol in self.asset_info.keys():
            return self.asset_info[symbol][Dicts.ALT_NAME]
        if 'X' + symbol in self.asset_info.keys():
            return self.asset_info['X'+symbol][Dicts.ALT_NAME]
        return None

    def get_tradable_asset_pair(self, symbol: str) -> str:
        """Returns the asset pair that matches the symbol and can be traded with either USD or ZUSD."""
        while len(symbol) > 0:
            if symbol + StableCoins.USD in self.asset_pairs_dict.keys():
                return symbol + StableCoins.USD
            elif symbol + StableCoins.ZUSD in self.asset_pairs_dict.keys():
                return symbol + StableCoins.ZUSD
            else:
                """
                If we couldn't find the symbol pair, try removing the first character in the symbol and search again
                This will probably happen with symbols like "XXDG"
                
                """
                symbol = symbol[1:]
        return "NOT FOUND"

    def get_pair_decimals(self, symbol_pair: str) -> int:
        """Returns pair_decimals: this is the maximum amount of decimals you can use to order the coin in terms of USD.
        For example, if you want to order 1 FILUSD, the max decimals you can use for price will be determined by the pair_decimals key.
        If pair_decimals is 3, then 60.111 will be the most specific price you can use.
        If pair_decimals is 4, then 60.1111 will be the most specific price you can use."""
        return self.asset_pairs_dict[symbol_pair][Dicts.PAIR_DECIMALS]

    def has_result(self, dictionary: dict) -> bool:
        """Returns True if "result" is returned in dict.
        If "result" not in dict, an error occurred."""
        return bool(Dicts.RESULT in dictionary.keys()) if isinstance(dictionary, dict) else False

    def get_quantity_owned(self, symbol: str) -> float:
        account_balance = self.get_account_balance()
        for sym, value in account_balance.items():
            if sym == symbol:
                return float(value)
        return 0
