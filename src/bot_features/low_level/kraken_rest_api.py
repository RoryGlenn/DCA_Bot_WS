import base64
import datetime
import hashlib
import hmac
import math
import time
import urllib.parse
import requests

from util.globals              import G
from pprint                    import pprint
from bot_features.low_level.kraken_enums import *


class KrakenRestAPI():
    def __init__(self, api_key: str, api_secret: str) -> None:
        """ Create an object with authentication information. """
        self.key           = api_key
        self.secret        = api_secret
        self.uri           = 'https://api.kraken.com'
        self.apiversion    = '0'
        self.session       = requests.Session()
        self.response      = None
        self._json_options = {}

    def json_options(self, **kwargs):
        """ Set keyword arguments to be passed to JSON deserialization. """
        self._json_options = kwargs
        return self

    def close(self) -> None:
        """ Close this session."""
        self.session.close()
        return

    def load_key(self, key: str, secret: str) -> None:
        """ Load kraken key and kraken secret. """
        self.key    = key
        self.secret = secret
        return

    def __query(self, urlpath: str, data: dict, headers: dict = None, timeout: int = None):
        """ Low-level query handling. """
        if data is None:
            data = {}
        if headers is None:
            headers = {}
            
        url           = self.uri + urlpath
        self.response = self.session.post(url, data=data, headers=headers, timeout=timeout)
        if self.response.status_code not in (200, 201, 202):
            self.response.raise_for_status()
        return self.response.json(**self._json_options)

    def __query_public(self, method: str, data: dict = None, timeout: int = None):
        """ Performs an API query that does not require a valid key/secret pair. """
        if data is None:
            data = {}
        urlpath = '/' + self.apiversion + '/public/' + method
        return self.__query(urlpath, data, timeout = timeout)

    def __query_private(self, method: str, data=None, timeout=None):
        """ Performs an API query that requires a valid key/secret pair. """
        if data is None:
            data = {}

        if not self.key or not self.secret:
            raise Exception('Either key or secret is not set! (Use `load_key()`.')

        data['nonce'] = self.__nonce()
        urlpath       = '/' + self.apiversion + '/private/' + method
        headers       = { 'API-Key': self.key, 'API-Sign': self.__sign(data, urlpath) }
        return self.__query(urlpath, data, headers, timeout = timeout)

    def __nonce(self) -> int:
        """ An always-increasing unsigned integer (up to 64 bits wide) """
        return int(1000*time.time())

    def __sign(self, data: dict, urlpath: str) -> str:
        """ Sign request data according to Kraken's scheme. """
        postdata  = urllib.parse.urlencode(data)
        # Unicode-objects must be encoded before hashing
        encoded   = (str(data['nonce']) + postdata).encode()
        message   = urlpath.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())
        return sigdigest.decode()


######################################################################
### USER DATA
######################################################################

    def get_account_balance(self) -> dict:
        return self.__query_private(method=Method.BALANCE)

    def get_trade_balance(self) -> dict:
        return self.__query_private(method=Method.TRADE_BALANCE)

    def get_open_orders(self, trades: bool = True) -> dict:
        return self.__query_private(method=Method.OPEN_ORDERS, data={Data.TRADES: trades})

    def get_closed_orders(self, userref: int = None) -> dict:
        return self.__query_private(method=Method.CLOSED_ORDERS, data={Data.USER_REF: userref})

    def query_orders_info(self, txid: str, trades: bool = True) -> dict:
        return self.__query_private(method=Method.QUERY_ORDERS, data={Data.TXID: txid, Data.TRADES: trades})

    def get_trades_history(self, trades: bool = True) -> dict:
        return self.__query_private(method=Method.TRADE_HISTORY, data={Data.TRADES: trades})

    def query_trades_info(self, txid: str, trades: bool = True) -> dict:
        return self.__query_private(method=Method.QUERY_TRADES, data={Data.TXID: txid, Data.TRADES: trades})

    def get_open_positions(self, docalcs: bool = True) -> dict:
        return self.__query_private(method=Method.OPEN_POSITIONS, data={Data.DOCALCS: docalcs})

    def get_ledger_info(self, asset: str, start: int) -> dict:
        return self.__query_private(method=Method.LEDGERS, data={Data.ASSET: asset, Data.START: start})

    def get_trade_volume(self, pair: str, fee_info: str = True) -> dict:
        return self.__query_private(method=Method.TRADE_VOLUME, data={Data.FEE_INFO: fee_info, Data.SYMBOL_PAIR: pair})

    def request_export_report(self, file_name: str = ExportReport.DEFAULT_NAME, format: str = ExportReport.DEFAULT_FORMAT, report: str = ExportReport.REPORT) -> dict:
        return self.__query_private(method=Method.ADD_EXPORT, data={Data.DESCRIPTION: file_name, Data.FORMAT: format, Data.REPORT: report})

    def get_export_report_status(self, report: str = ExportReport.REPORT) -> dict:
        return self.__query_private(method=Method.EXPORT_STATUS, data={Data.REPORT: report})

    def retrieve_data_export(self, id: str) -> dict:
        return self.__query_private(method=Method.RETRIEVE_EXPORT, data={Data.ID: id})

    def delete_export_report(self, id: str, type: str = ExportReport.DELETE) -> dict:
        return self.__query_private(method=Method.REMOVE_EXPORT, data={Data.ID: id, Data.TYPE: type})


######################################################################
### USER TRADING
######################################################################

    def add_order(self, ordertype: str, type: str, volume: str, pair: str, price: str) -> dict:
        return self.__query_private(method=Method.ADD_ORDER, data={Data.ORDER_TYPE: ordertype, Data.TYPE: type, Data.VOLUME: volume, Data.SYMBOL_PAIR: pair, Data.PRICE: price})

    def market_order(self, type: str, volume: str, pair: str) -> dict:
        return self.__query_private(method=Method.ADD_ORDER, data={Data.ORDER_TYPE: Data.MARKET, Data.TYPE: type, Data.VOLUME: volume, Data.SYMBOL_PAIR: pair, Data.PRICE: Data.MARKET_PRICE})

    def limit_order(self, type: str, volume: str, pair: str, price: str) -> dict:
        return self.__query_private(method=Method.ADD_ORDER, data={Data.ORDER_TYPE: Data.LIMIT, Data.TYPE: type, Data.VOLUME: volume, Data.SYMBOL_PAIR: pair, Data.PRICE: price})

    def limit_order_conditional_close(self, type: str, volume: str, pair: str, price: str, cc_price: str, cc_volume: str) -> dict:
        return self.__query_private(method=Method.ADD_ORDER, data={Data.ORDER_TYPE: Data.LIMIT, Data.TYPE: type, Data.VOLUME: volume, Data.SYMBOL_PAIR: pair, Data.PRICE: price,
                                                                   Data.CC_PAIR: pair, Data.CC_TYPE: type, Data.CC_ORDER_TYPE: Data.LIMIT, Data.CC_PRICE: cc_price, Data.CC_VOLUME: cc_volume})

    def cancel_order(self, txid: str) -> dict:
        return self.__query_private(method=Method.CANCEL_ORDER, data={Data.TXID: txid})
    
    def cancel_all_orders(self) -> dict:
        return self.__query_private(method=Method.CANCEL_ALL, data={})

    def cancel_all_orders_after_x(self, timeout: str) -> dict:
        return self.__query_private(method=Method.CANCEL_ALL_ORDERS_AFTER, data={Data.TIMEOUT: timeout})


######################################################################
### USER FUNDING
######################################################################

    def get_deposit_methods(self, asset: str) -> dict:
        return self.__query_private(method=Method.DEPOSIT_METHODS, data={Data.ASSET: asset})

    def get_deposit_address(self, asset: str, method: str, new: bool) -> dict:
        return self.__query_private(method=Method.DEPOSIT_ADDRESS, data={Data.ASSET: asset, Data.METHOD: method, Data.NEW: new})
        
    def get_status_of_recent_deposits(self, asset: str) -> dict:
        return self.__query_private(method=Method.DEPOSIT_STATUS, data={Data.ASSET: asset})

    def get_withdrawal_information(self, asset: str, key: str, amount: str) -> dict:
        return self.__query_private(method=Method.WITHDRAWL_INFO, data={Data.ASSET: asset, Data.KEY: key, Data.AMOUNT: amount})

    def withdraw_funds(self, asset: str, key: str, amount: str) -> dict:
        return self.__query_private(method=Method.WITHDRAWL, data={Data.ASSET: asset, Data.KEY: key, Data.AMOUNT: amount})

    def get_withdraw_status(self, asset: str) -> dict:
        return self.__query_private(method=Method.WITHDRAWL_STATUS, data={Data.ASSET: asset})

    def request_withdrawl_cancelation(self, asset: str, refid: str) -> dict:
        return self.__query_private(method=Method.WITHDRAWL_CANCEL, data={Data.ASSET: asset, Data.REFID: refid})

    def request_wallet_transfer(self, asset: str, amount: str, from_: str, to_: str) -> dict:
        return self.__query_private(method=Method.WALLET_TRANSFER, data={Data.ASSET: asset, Data.AMOUNT: amount, Data.FROM: from_, Data.TO: to_})


######################################################################
### USER STAKING
######################################################################

    def stake_asset(self, asset: str, amount: str, method: str) -> dict:
        return self.__query_private(method=Method.STAKE, data={Data.ASSET: asset, Data.AMOUNT: amount, Data.METHOD: method})

    def unstake_asset(self, asset: str, amount: str, method: str) -> dict:
        return self.__query_private(method=Method.UNSTAKE, data={Data.ASSET: asset, Data.AMOUNT: amount, Data.METHOD: method})
    
    def get_stakeable_assets(self) -> dict:
        return self.__query_private(method=Method.STAKEABLE_ASSETS, data={})

    def get_pending_staking_transactions(self) -> dict:
        return self.__query_private(method=Method.PENDING, data={})

    def get_staking_transactions(self) -> dict:
        return self.__query_private(method=Method.TRANSACTIONS, data={})

######################################################################
### WEBSOCKETS AUTHENTICATION
######################################################################

    def get_web_sockets_token(self) -> dict:
        return self.__query_private(method=Method.GET_WEBSOCKETS_TOKEN, data={})

######################################################################
### MARKET DATA
######################################################################

    def get_server_time(self) -> dict:
        return self.__query_public(method=Method.SERVER_TIME, data={})

    def get_system_status(self) -> dict:
        return self.__query_public(method=Method.SYSTEM_STATUS, data={})

    def get_asset_info(self) -> dict:
        return self.__query_public(method=Method.ASSETS, data={})

    def get_tradable_asset_pairs(self, symbol_pairs: str) -> dict:
        return self.__query_public(method=Method.ASSET_PAIRS, data={Data.SYMBOL_PAIR: symbol_pairs})

    def get_ticker_information(self, pair: str) -> dict:
        return self.__query_public(method=Method.MARKET_DATA, data={Data.SYMBOL_PAIR: pair})

    def get_ohlc_data(self, pair: str) -> dict:
        return self.__query_public(method=Method.OHLC, data={Data.SYMBOL_PAIR: pair})

    def get_order_book(self, pair: str) -> dict:
        return self.__query_public(method=Method.ORDER_BOOK, data={Data.SYMBOL_PAIR: pair})

    def get_recent_trades(self, pair: str) -> dict:
        return self.__query_public(method=Method.RECENT_TRADES, data={Data.SYMBOL_PAIR: pair})
    

###################################################################################################
### ROUNDING ###
###################################################################################################

    def round_decimals_down(self, number: float, decimals: int = 2) -> int:
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
                for key in open_orders[txid].keys():
                    if key == Dicts.DESCR:
                        if open_orders[txid][Dicts.DESCR][Data.TYPE] == Data.BUY:
                            price     = float(open_orders[txid][Dicts.DESCR][Data.PRICE])
                            qty       = float(open_orders[txid][Dicts.DESCR][Dicts.ORDER].split(" ")[1])
                            buy_total += price * qty
                            break
        return round(buy_total, 3)

###################################################################################################
### TIME ###
###################################################################################################
    def get_current_time(self) -> datetime:
        return datetime.datetime.now().strftime("%H:%M:%S")
