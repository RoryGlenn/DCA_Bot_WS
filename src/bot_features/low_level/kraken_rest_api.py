from bot_features.low_level.base_request import BaseRequest

from bot_features.low_level.kraken_enums import *


class KrakenRestAPI(BaseRequest):
    def __init__(self, api_key: str, api_secret: str) -> None:
        """ Create an object with authentication information. """
        super().__init__(api_key, api_secret)
        return

######################################################################
### USER DATA
######################################################################

    def get_account_balance(self) -> dict:
        return self.query_private(method=Method.BALANCE)

    def get_trade_balance(self) -> dict:
        return self.query_private(method=Method.TRADE_BALANCE)

    def get_open_orders(self, trades: bool = True) -> dict:
        return self.query_private(method=Method.OPEN_ORDERS, data={Data.TRADES: trades})

    def get_closed_orders(self, userref: int = None) -> dict:
        return self.query_private(method=Method.CLOSED_ORDERS, data={Data.USER_REF: userref})

    def query_orders_info(self, txid: str, trades: bool = True) -> dict:
        return self.query_private(method=Method.QUERY_ORDERS, data={Data.TXID: txid, Data.TRADES: trades})

    def get_trades_history(self, trades: bool = True) -> dict:
        return self.query_private(method=Method.TRADE_HISTORY, data={Data.TRADES: trades})

    def query_trades_info(self, txid: str, trades: bool = True) -> dict:
        return self.query_private(method=Method.QUERY_TRADES, data={Data.TXID: txid, Data.TRADES: trades})

    def get_open_positions(self, docalcs: bool = True) -> dict:
        return self.query_private(method=Method.OPEN_POSITIONS, data={Data.DOCALCS: docalcs})

    def get_ledger_info(self, asset: str, start: int) -> dict:
        return self.query_private(method=Method.LEDGERS, data={Data.ASSET: asset, Data.START: start})

    def get_trade_volume(self, pair: str, fee_info: str = True) -> dict:
        return self.query_private(method=Method.TRADE_VOLUME, data={Data.FEE_INFO: fee_info, Data.SYMBOL_PAIR: pair})

    def request_export_report(self, file_name: str = ExportReport.DEFAULT_NAME, format: str = ExportReport.DEFAULT_FORMAT, report: str = ExportReport.REPORT) -> dict:
        return self.query_private(method=Method.ADD_EXPORT, data={Data.DESCRIPTION: file_name, Data.FORMAT: format, Data.REPORT: report})

    def get_export_report_status(self, report: str = ExportReport.REPORT) -> dict:
        return self.query_private(method=Method.EXPORT_STATUS, data={Data.REPORT: report})

    def retrieve_data_export(self, id: str) -> dict:
        return self.query_private(method=Method.RETRIEVE_EXPORT, data={Data.ID: id})

    def delete_export_report(self, id: str, type: str = ExportReport.DELETE) -> dict:
        return self.query_private(method=Method.REMOVE_EXPORT, data={Data.ID: id, Data.TYPE: type})


######################################################################
### USER TRADING
######################################################################

    def add_order(self, ordertype: str, type: str, volume: str, pair: str, price: str) -> dict:
        return self.query_private(method=Method.ADD_ORDER, data={Data.ORDER_TYPE: ordertype, Data.TYPE: type, Data.VOLUME: volume, Data.SYMBOL_PAIR: pair, Data.PRICE: price})

    def cancel_order(self, txid: str) -> dict:
        return self.query_private(method=Method.CANCEL_ORDER, data={Data.TXID: txid})
    
    def cancel_all_orders(self) -> dict:
        return self.query_private(method=Method.CANCEL_ALL, data={})

    def cancel_all_orders_after_x(self, timeout: str) -> dict:
        return self.query_private(method=Method.CANCEL_ALL_ORDERS_AFTER, data={Data.TIMEOUT: timeout})


######################################################################
### USER FUNDING
######################################################################

    def get_deposit_methods(self, asset: str) -> dict:
        return self.query_private(method=Method.DEPOSIT_METHODS, data={Data.ASSET: asset})

    def get_deposit_address(self, asset: str, method: str, new: bool) -> dict:
        return self.query_private(method=Method.DEPOSIT_ADDRESS, data={Data.ASSET: asset, Data.METHOD: method, Data.NEW: new})
        
    def get_status_of_recent_deposits(self, asset: str) -> dict:
        return self.query_private(method=Method.DEPOSIT_STATUS, data={Data.ASSET: asset})

    def get_withdrawal_information(self, asset: str, key: str, amount: str) -> dict:
        return self.query_private(method=Method.WITHDRAWL_INFO, data={Data.ASSET: asset, Data.KEY: key, Data.AMOUNT: amount})

    def withdraw_funds(self, asset: str, key: str, amount: str) -> dict:
        return self.query_private(method=Method.WITHDRAWL, data={Data.ASSET: asset, Data.KEY: key, Data.AMOUNT: amount})

    def get_withdraw_status(self, asset: str) -> dict:
        return self.query_private(method=Method.WITHDRAWL_STATUS, data={Data.ASSET: asset})

    def request_withdrawl_cancelation(self, asset: str, refid: str) -> dict:
        return self.query_private(method=Method.WITHDRAWL_CANCEL, data={Data.ASSET: asset, Data.REFID: refid})

    def request_wallet_transfer(self, asset: str, amount: str, from_: str, to_: str) -> dict:
        return self.query_private(method=Method.WALLET_TRANSFER, data={Data.ASSET: asset, Data.AMOUNT: amount, Data.FROM: from_, Data.TO: to_})


######################################################################
### USER STAKING
######################################################################

    def stake_asset(self, asset: str, amount: str, method: str) -> dict:
        return self.query_private(method=Method.STAKE, data={Data.ASSET: asset, Data.AMOUNT: amount, Data.METHOD: method})

    def unstake_asset(self, asset: str, amount: str, method: str) -> dict:
        return self.query_private(method=Method.UNSTAKE, data={Data.ASSET: asset, Data.AMOUNT: amount, Data.METHOD: method})
    
    def get_stakeable_assets(self) -> dict:
        return self.query_private(method=Method.STAKEABLE_ASSETS, data={})

    def get_pending_staking_transactions(self) -> dict:
        return self.query_private(method=Method.PENDING, data={})

    def get_staking_transactions(self) -> dict:
        return self.query_private(method=Method.TRANSACTIONS, data={})

######################################################################
### WEBSOCKETS AUTHENTICATION
######################################################################

    def get_web_sockets_token(self) -> dict:
        return self.query_private(method=Method.GET_WEBSOCKETS_TOKEN, data={})

######################################################################
### MARKET DATA
######################################################################

    def get_server_time(self) -> dict:
        return self.query_public(method=Method.SERVER_TIME, data={})

    def get_system_status(self) -> dict:
        return self.query_public(method=Method.SYSTEM_STATUS, data={})

    def get_asset_info(self) -> dict:
        return self.query_public(method=Method.ASSETS, data={})

    def get_tradable_asset_pairs(self, symbol_pairs: str) -> dict:
        return self.query_public(method=Method.ASSET_PAIRS, data={Data.SYMBOL_PAIR: symbol_pairs})

    def get_ticker_information(self, pair: str) -> dict:
        return self.query_public(method=Method.MARKET_DATA, data={Data.SYMBOL_PAIR: pair})

    def get_ohlc_data(self, pair: str) -> dict:
        return self.query_public(method=Method.OHLC, data={Data.SYMBOL_PAIR: pair})

    def get_order_book(self, pair: str) -> dict:
        return self.query_public(method=Method.ORDER_BOOK, data={Data.SYMBOL_PAIR: pair})

    def get_recent_trades(self, pair: str) -> dict:
        return self.query_public(method=Method.RECENT_TRADES, data={Data.SYMBOL_PAIR: pair})