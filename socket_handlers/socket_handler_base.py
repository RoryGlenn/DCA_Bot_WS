import websocket

from websocket._app import WebSocketApp


class SocketHandlerBase:
    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        print(message)

    def ws_open(self, ws: WebSocketApp) -> None:
        print("Opened websocket")
        
    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        print("Error:", error_message)
        # ws.close()

    def ws_thread(self, *args) -> None:
        ws = websocket.WebSocketApp(
            url="wss://ws-auth.kraken.com/",
            on_open=self.ws_open,
            on_message=self.ws_message,
            on_error=self.ws_error)
        ws.run_forever()
