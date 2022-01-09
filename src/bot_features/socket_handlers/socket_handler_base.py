from websocket._app                      import WebSocketApp
from bot_features.low_level.kraken_enums import WEBSOCKET_PRIVATE_URL


class SocketHandlerBase:
    def __init__(self) -> None:
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        return

    def ws_open(self, ws: WebSocketApp) -> None:
        return

    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        return

    def ws_close(self, ws: WebSocketApp, close_status_code: int, close_msg: str) -> None:
        return

    def ws_thread(self, *args) -> None:
        while True:
            ws = WebSocketApp(
                url=WEBSOCKET_PRIVATE_URL,
                on_open=self.ws_open,
                on_close=self.ws_close,
                on_message=self.ws_message,
                on_error=self.ws_error)
            ws.run_forever()
        return