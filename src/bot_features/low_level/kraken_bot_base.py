"""
kraken_bot_base.py

    Supports base functionality for buying, selling. 
    Meant to be inherited from for additional classes.

"""
import math
import requests
import time
import datetime

from pprint                                 import pprint

from util.globals                           import G
from util.config                            import g_config
from bot_features.low_level.kraken_rest_api import KrakenRestAPI
from bot_features.low_level.kraken_enums    import *


class KrakenBotBase(KrakenRestAPI):
    def __init__(self, api_key: str = "", api_secret: str = "") -> None:
        """
        Returns new object with specified data
        
        """
        super().__init__(api_key, api_secret)
        self.asset_pairs_dict: dict = requests.get(URL_ASSET_PAIRS).json()[Dicts.RESULT]
        self.asset_info:       dict = self.get_asset_info()[Dicts.RESULT]
        # self.ticker_info:      dict = { }

        # for symbol in g_config.DCA_DATA:
        #     self.ticker_info[]

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
        symbol_pair_info = self.get_ticker_information(symbol_pair) # STORE THIS INFO IN A DICT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        current_price = self.parse_ticker_information(symbol_pair_info)
        return self.parse_ask_price(current_price)

    def get_bid_price(self, symbol_pair: str) -> float:
        """Gets the current bid price for a symbol pair"""
        # current_price = None
        # if symbol_pair in self.ticker_info.keys():
        #     current_price = self.ticker_info[symbol_pair]

        symbol_pair_info = self.get_ticker_information(symbol_pair) # STORE THIS INFO IN A DICT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        current_price = self.parse_ticker_information(symbol_pair_info)
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






###################################################################################################
### ROUNDING ###
###################################################################################################

    def round_decimals_down(self, number: float, decimals: int = 2) -> int | float:
        """Returns a value rounded down to a specific number of decimal places."""
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif decimals == 0:
            return math.floor(number)
        factor = 10 ** decimals
        return math.floor(number * factor) / factor


###################################################################################################
### PARSE DATA ###
###################################################################################################

    def parse_ticker_information(self, response: dict) -> dict:
        result = dict()
        if Dicts.RESULT in response.keys():
            response = response[Dicts.RESULT]
            for key in response.keys():
                result = response[key]
                break
        return result

    def parse_ask_price(self, response: dict) -> float:
        result = str()
        if Dicts.ASK_PRICE in response.keys():
            result = response[Dicts.ASK_PRICE][0]
        return float(result)

    def parse_bid_price(self, response: dict) -> float:
        result = str()
        if Dicts.BID_PRICE in response.keys():
            result = response[Dicts.BID_PRICE][0]
        
        # if result is empty, assets could be staked. If so, symbol will have a ".S" at the end of it.        
        if len(result) <= 0:
            return 0
        return float(result)

    def parse_account_balance(self, response: dict) -> dict:
        result = dict()
        if Trade.RESULT in response.keys():
            for key in sorted(response[Trade.RESULT].keys()):
                if float(response[Trade.RESULT][key]) > 0:
                    result[key] = float(response[Trade.RESULT][key])
        return result

    def get_parsed_account_balance(self):
        account_balance = self.get_account_balance()
        return self.parse_account_balance(account_balance)

    def get_coin_balance(self, symbol: str) -> float:
        try:
            temp = self.get_account_balance()
            account_balance = self.parse_account_balance(temp)
            if symbol in account_balance.keys():
                return account_balance[symbol]
        except Exception as e:
            # G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
            print(e)
        return 0.0

    def get_available_usd_balance(self) -> float:
        """Get available usd balance by subtracting open buy orders from total usd in wallet."""
        open_orders = self.get_open_orders()
        buy_total   = 0

        if Dicts.RESULT in open_orders.keys():
            for txid in open_orders[Dicts.RESULT][Dicts.OPEN]:
                for key in open_orders[Dicts.RESULT][Dicts.OPEN][txid].keys():
                    if key == Dicts.DESCR:
                        if open_orders[Dicts.RESULT][Dicts.OPEN][txid][Dicts.DESCR][Data.TYPE] == Data.BUY:
                            price     = float(open_orders[Dicts.RESULT][Dicts.OPEN][txid][Dicts.DESCR][Data.PRICE])
                            qty       = float(open_orders[Dicts.RESULT][Dicts.OPEN][txid][Dicts.DESCR][Dicts.ORDER].split(" ")[1])
                            buy_total += price * qty
                            break
        return round(buy_total, 3)
