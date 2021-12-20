"globals.py - Uses global variables that are shared between files in order to write to the log file."

from util.log  import Log
from threading import Event, Lock


class Globals:
    event:            Event   = Event()
    
    print_lock:       Lock    = Lock()
    usd_lock:         Lock    = Lock()
    add_orders_lock:  Lock    = Lock()

    log:              Log     = Log()
    available_usd:    float   = 0.0
    add_orders_queue: list    = []
    

# Global variable "G" is shared between files and classes
G: Globals = Globals()
