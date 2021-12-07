import tornado
# from websocket import websocket_connect

from tornado.websocket import websocket_connect

url = "wss://ws.kraken.com/"

def t_test():
    conn = yield websocket_connect(url)
    while True:
        msg = yield conn.read_message()
        if msg is None: break
        # Do something with msg    

if __name__ == '__main__':
    t_test()