"globals.py - Uses global variables that are shared between files in order to write to the log file."

from util.log  import Log
from threading import Event, Lock

class Globals:
    event:               Event   = Event()

    print_lock:          Lock    = Lock()
    usd_lock:            Lock    = Lock()
    safety_orders_lock:  Lock    = Lock()
    base_orders_lock:    Lock    = Lock()
   
    log:                 Log     = Log()
    available_usd:       float   = 0.0
    safety_order_queue:  list    = []
    base_order_queue:    list    = []

    socket_handler_open_orders   = None
    socket_handler_own_trades    = None
    socket_handler_balances      = None
        
    x_list:   list = ['XETC', 'XETH', 'XLTC', 'XMLN', 'XREP', 'XXBT', 'XXDG', 'XXLM', 'XXMR', 'XXRP', 'XZEC']
    reg_list: list = ['ETC',  'ETH',  'LTC',  'MLN',  'REP',  'XBT',  'XDG',  'XLM',  'XMR',  'XRP',  'ZEC']
    x_dict: dict = {
        'ETC':'XETC',
        'ETH':'XETH',
        'LTC':'XLTC',
        'MLN':'XMLN',
        'REP':'XREP',
        'XBT':'XXBT',
        'XDG':'XXDG',
        'XLM':'XXLM',
        'XMR':'XXMR',
        'XRP':'XXRP',
        'ZEC':'XZEC'
        }


# Global variable "G" is shared between files and classes
G: Globals = Globals()
