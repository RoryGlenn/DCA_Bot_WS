import websocket
import _thread

# https://websocket-client.readthedocs.io/en/latest/examples.html

def on_message(ws, message):
    return

def on_error(ws, error):
    return

def on_close(ws, close_status_code, close_msg):
    return

def on_open(ws):
    def run(*args):
        ws.send('{"event":"subscribe", "subscription":{"name":"trade"}, "pair":["XBT/USD","XRP/USD"]}')
    _thread.start_new_thread(run, ())

if __name__ == "__main__":
    ws = websocket.WebSocketApp("wss://ws.kraken.com/",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()