from websocket._app import WebSocketApp


class SocketHandlerBase:
    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        print(message)
        return

    def ws_open(self, ws: WebSocketApp) -> None:
        print("Opened websocket")
        return

    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        print("Error:", error_message)
        return

    def ws_close(self, ws: WebSocketApp, close_status_code: int, close_msg: str) -> None:
        return

    def ws_thread(self, *args) -> None:
        while True:
            ws = WebSocketApp(
                url="wss://ws-auth.kraken.com/",
                on_open=self.ws_open,
                on_close=self.ws_close,
                on_message=self.ws_message,
                on_error=self.ws_error)
            ws.run_forever()
        return