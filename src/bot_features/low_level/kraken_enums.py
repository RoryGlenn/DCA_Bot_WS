from enum import auto

# DCA
DECIMAL_MAX     = 8
URL_ASSET_PAIRS = 'https://api.kraken.com/0/public/AssetPairs'
CONFIG_JSON     = 'src/json/config.json'

WEBSOCKET_PRIVATE_URL = "wss://ws-auth.kraken.com/"

class DB:
    DATABASE_NAME = "DCA_Bot_WS"
    COLLECTION_OO = "open_orders"
    COLLECTION_OT = "own_trades"
    COLLECTION_B = "balances"
    COLLECTION_AO = "addOrder"
    COLLECTION_OS = "open_symbols"
    COLLECTION_SO = "safety_orders"

class API_Keys:
    KEY = ""
    SECRET = ""

class Status:
    STATUS   = "status"
    OPEN     = "open"
    PENDING  = "pending"
    CANCELED = "canceled"

class WS_API:
    API_DOMAIN_PUBLIC  = "wss://ws.kraken.com/"
    API_DOMAIN_PRIVATE = "wss://ws-auth.kraken.com/"

    API_STATUS         = {"ping"}
    API_PUBLIC         = {"trade", "book", "ticker", "spread", "ohlc"}
    API_PRIVATE        = {"openOrders", "ownTrades", "balances"}
    API_TRADING        = {"addOrder", "cancelOrder", "cancelAll", "cancelAllOrdersAfter"}

class Buy_:
    BUY          = auto()
    PRICES       = auto()
    TIME_MINUTES = 1
    USD_TO_SPEND = auto()
    SET          = set()

class TVData:
    SCREENER       = "crypto"
    EXCHANGE       = "kraken"
    RECOMMENDATION = "RECOMMENDATION"
    BUY            = "BUY"
    STRONG_BUY     = "STRONG_BUY"

class self:
    TARGET_PROFIT_PERCENT        = auto()
    TRAILING_DEVIATION           = auto()
    SAFETY_ORDERS_MAX            = auto()
    SAFETY_ORDERS_ACTIVE_MAX     = auto()
    SAFETY_ORDER_VOLUME_SCALE    = auto()
    SAFETY_ORDER_STEP_SCALE      = auto()
    SAFETY_ORDER_PRICE_DEVIATION = auto()
    
class TimeIntervals:
    INTERVAL_1_MINUTE   = "1m"
    INTERVAL_5_MINUTES  = "5m"
    INTERVAL_15_MINUTES = "15m"
    INTERVAL_30_MINUTES = "30m"
    INTERVAL_1_HOUR     = "1h"
    INTERVAL_2_HOURS    = "2h"
    INTERVAL_4_HOURS    = "4h"
    INTERVAL_1_DAY      = "1d"
    INTERVAL_1_WEEK     = "1W"
    INTERVAL_1_MONTH    = "1M"
    ALL_LIST            = ["1m","5m","15m","30m","1h","2h","4h","1d","1W","1M"]
    USER_INTERVALS      = set()

class ExportReport:
    DEFAULT_NAME   = "my_trades"
    DEFAULT_FORMAT = "CSV"
    REPORT         = "trades"
    DELETE         = "delete"
    CANCEL         = "cancel"

class Dicts:
    ORDER_MIN = "ordermin"
    ORDER = "order"
    PAIR_DECIMALS = "pair_decimals"
    LOT_DECIMALS = "lot_decimals"
    ALT_NAME = "altname"
    RESULT = "result"
    ERROR = "error"
    DECIMALS = "decimals"
    MINIMUM = "Minimum"
    ASSET = "Asset"
    DESCR = "descr"
    OPEN = "open"
    # For ticker information
    ASK_PRICE = "a"
    BID_PRICE = "b"
    LAST_TRADE_CLOSE = "c"
    VOLUME = "v"
    VOLUME_WEIGHTED_PRICE_AVG = "p"
    NUM_TRADES = "t"
    LOW = "l"
    HIGH = "h"

class StableCoins:
    STABLE_COINS_LIST = ['ZUSD', 'USDT', 'BUSD', 'PAX', 'USDC', 'USD', 'TUSD', 'DAI', 'UST', 'HUSD', 'USDN',
                         'GUSD', 'FEI',  'LUSD', 'FRAX', 'SUSD', 'USDX', 'MUSD', 'USDK', 'USDS', 'USDP', 'RSV', 'USDQ', 'USDEX']
    ZUSD              = "ZUSD"
    USD               = "USD"
    USDT              = "USDT"

class Trade:
    ZUSD = "ZUSD"
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop-loss"
    TAKE_PROFIT = "take-profit"
    STOP_LOSS_LIMIT = "stop-loss-limit"
    TAKE_PROFIT_LIMIT = "take-profit-limit"
    SETTLE_POSITION = "settle-position"
    BUY = "buy"
    SELL = "sell"
    RESULT = "result"
    MARKET_PRICE = "0"


class Method:
    # Market Data
    MARKET_DATA = "Ticker?pair="
    SERVER_TIME = "Time"
    SYSTEM_STATUS = "SystemStatus"
    ASSETS = "Assets"
    ASSET_PAIRS = "AssetPairs?pair="
    OHLC = "OHLC?pair="
    ORDER_BOOK = "Depth?pair="
    RECENT_TRADES = "Trades?pair="

    # User Data
    BALANCE = "Balance"
    TRADE_BALANCE = "TradeBalance"
    OPEN_ORDERS = "OpenOrders"
    CLOSED_ORDERS = "ClosedOrders"
    QUERY_ORDERS = "QueryOrders"
    TRADE_HISTORY = "TradesHistory"
    QUERY_TRADES = "QueryTrades"
    OPEN_POSITIONS = "OpenPositions"
    LEDGERS = "Ledgers"
    TRADE_VOLUME = "TradeVolume"
    ADD_EXPORT = "AddExport"
    EXPORT_STATUS = "ExportStatus"
    RETRIEVE_EXPORT = "RetrieveExport"
    REMOVE_EXPORT = "RemoveExport"

    # User Trading
    ADD_ORDER = "AddOrder"
    CANCEL_ORDER = "CancelOrder"
    CANCEL_ALL = "CancelAll"
    CANCEL_ALL_ORDERS_AFTER = "CancelAllOrdersAfter"

    # User Funding
    DEPOSIT_METHODS = "DepositMethods"
    DEPOSIT_ADDRESS = "DepositAddresses"
    DEPOSIT_STATUS = "DepositStatus"
    WITHDRAWL_INFO = "WithdrawInfo"
    WITHDRAWL = "Withdraw"
    WITHDRAWL_STATUS = "WithdrawStatus"
    WITHDRAWL_CANCEL = "WithdrawCancel"
    WALLET_TRANSFER = "WalletTransfer"

    # User Staking
    STAKE = "Stake"
    UNSTAKE = "Unstake"
    STAKEABLE_ASSETS = "Staking/Assets"
    PENDING = "Staking/Pending"
    TRANSACTIONS = "Staking/Transactions"

    # Websockets Authentication
    GET_WEBSOCKETS_TOKEN = "GetWebSocketsToken"


class Data:
    TXID = "txid"
    TRADES = "trades"
    USER_REF = "userref"
    DOCALCS = "docalcs"
    FEE_INFO = "fee-info"
    DESCRIPTION = "description"
    FORMAT = "format"
    REPORT = "report"
    ID = "id"
    TYPE = "type"
    ASSET = "asset"
    START = "start"
    SYMBOL_PAIR = "pair"
    TIMEOUT = "timeout"
    ORDER_TYPE = "ordertype"
    TYPE = "type"
    VOLUME = "volume"
    VOL = "vol"
    PRICE = "price"
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop-loss"
    TAKE_PROFIT = "take-profit"
    STOP_LOSS_LIMIT = "stop-loss-limit"
    TAKE_PROFIT_LIMIT = "take-profit-limit"
    SETTLE_POSITION = "settle-position"
    BUY = "buy"
    SELL = "sell"
    METHOD = "method"
    NEW = "new"
    KEY = "key"
    AMOUNT = "amount"
    REFID = "refid"
    FROM = "from"
    TO = "to"
    MARKET_PRICE = "0"
    ORDER_TXID = "ordertxid"
    CC_PAIR = 'close[pair]'
    CC_TYPE = 'close[type]'
    CC_ORDER_TYPE = 'close[ordertype]'
    CC_PRICE = 'close[price]'
    CC_VOLUME = 'close[volume]'


class Nap:
    NORMAL = 1
    LONG = 2

class FileMode:

    """
    Open text file for reading.  The stream is positioned at the
        beginning of the file.    
    """
    READ_ONLY = "r"

    """
    Open for reading and writing.  The stream is positioned at the
        beginning of the file.
    """
    READ_WRITE = "r+"

    """
    Truncate file to zero length or create text file for writing.
         The stream is positioned at the beginning of the file.    
    """
    WRITE_TRUNCATE = "w"

    """
    Open for reading and writing.  The file is created if it does not
         exist, otherwise it is truncated.  The stream is positioned at
         the beginning of the file.
         """
    READ_WRITE_CREATE = "w+"

    """
    Open for writing.  The file is created if it does not exist.  The
        stream is positioned at the end of the file.  Subsequent writes
        to the file will always end up at the then current end of file,
        irrespective of any intervening fseek(3) or similar.
    """

    WRITE_APPEND = "a"

    """
   Open for reading and writing.  The file is created if it does not
        exist.  The stream is positioned at the end of the file.  Subse-
        quent writes to the file will always end up at the then current
        end of file, irrespective of any intervening fseek(3) or similar.
    
    """
    READ_WRITE_APPEND = "a+"

    """
    Configuration file for the rake bot to use on users account and wallets
    """


class Misc:
    CLS   = "cls"
    CLEAR = "clear"

class KrakenFiles:
    WITHDRAWAL_MINIMUMS   = "src/kraken_files/csv_files/Withdrawal_Minimums_and_Fees.csv"
    ORDER_SIZE_MINIMUMS   = "src/kraken_files/csv_files/Minimum_Order_Sizes.csv"
    DEPOSIT_MINIMUMS      = "src/kraken_files/csv_files/Deposit_Minimums_and_Fees.csv"
    DEPOSIT_CONFIRMATIONS = "src/kraken_files/csv_files/Deposit_Confirmation.csv"

class ConfigKeys:
    CONFIG = "config"
    
    # kraken
    KRAKEN_API_KEY = "kraken_api_key"
    KRAKEN_SECRET_KEY = "kraken_secret_key"

    # buy
    BUY_SET = "buy_set"

    # dca
    DCA_TARGET_PROFIT_PERCENT = "dca_target_profit_percent"
    # DCA_TRAILING_DEVIATION = "dca_trailing_deviation"
    DCA_BASE_ORDER_SIZE = "dca_base_order_size"
    DCA_SAFETY_ORDERS_MAX = "dca_safety_orders_max"
    DCA_SAFETY_ORDERS_ACTIVE_MAX = "dca_safety_orders_active_max"
    DCA_SAFETY_ORDER_SIZE = "dca_safety_order_size"
    DCA_SAFETY_ORDER_VOLUME_SCALE = "dca_safety_order_volume_scale"
    DCA_SAFETY_ORDER_STEP_SCALE = "dca_safety_order_step_scale"
    DCA_SAFETY_ORDER_PRICE_DEVIATION = "dca_safety_order_price_deviation"
    DCA_ALL_OR_NOTHING = "dca_all_or_nothing"
    DCA_TIME_INTERVALS = "dca_time_intervals"
    

class KError:
    INSUFFICIENT_FUNDS = 'EOrder:Insufficient funds'
    INVALID_VOLUME     = 'EGeneral:Invalid arguments:volume'
          
class SQLTable:
    SAFETY_ORDERS     = "safety_orders"
    OPEN_BUY_ORDERS   = "open_buy_orders"
    OPEN_SELL_ORDERS  = "open_sell_orders"
    
    
class BaseOrderRow():
    def __init__(self, symbol_pair: str , symbol: str , safety_order_no: int, deviation: float, quantity: float,
                 total_quantity: float, price: float, average_price: float, required_price: float, required_change: float, 
                 profit: float, cost: float, total_cost: float, cancelled: bool, filled: bool, oso_txid: str, oso_no: int) -> None:
        self.symbol_pair:     str   = symbol_pair
        self.symbol:          str   = symbol
        self.safety_order_no: int   = safety_order_no
        self.deviation:       float = deviation
        self.quantity:        float = quantity
        self.total_quantity:  float = total_quantity
        self.price:           float = price
        self.average_price:   float = average_price
        self.required_price:  float = required_price
        self.required_change: float = required_change
        self.profit:          float = profit
        self.cost:            float = cost
        self.total_cost:      float = total_cost
        self.cancelled:       bool  = cancelled
        self.filled:          bool  = filled
        self.oso_txid:        str   = oso_txid
        self.oso_no:          int   = oso_no
        return