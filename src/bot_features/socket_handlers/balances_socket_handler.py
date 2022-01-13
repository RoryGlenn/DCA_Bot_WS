import json

from pprint                                           import pprint
from websocket._app                                   import WebSocketApp

from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.low_level.kraken_enums              import *

from util.globals                                     import G


class BalancesSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token = api_token
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)

        if isinstance(message, dict):
            if "balances" in message.keys():
                G.usd_lock.acquire()
                G.available_usd += float(message['balances']['USD'])
                G.log.print_and_log(f"balances: Available USD: {G.available_usd}", G.print_lock)
                G.usd_lock.release()
            elif 'heartbeat' not in message.values():
                # [13/01/2022 07:49:29] balances: {'ledgers': [{'amount': '-1.875000', 'asset': 'ADA', 'balance': '0.000000', 'fee': '0.000000', 'ledgerID': 'LM6OYU-B6HMJ-CGXOVG', 'refid': 'T552QN-XPJAA-S7NKCI', 'time': '1642084372.150882', 'type': 'trade'}], 'channel': 'balances', 'sequence': 14}
                # [13/01/2022 07:49:29] balances: {'ledgers': [{'amount': '2.46', 'asset': 'USD', 'balance': '2903.16', 'fee': '0.00', 'ledgerID': 'LIQ6GX-TYFXH-7FW4YQ', 'refid': 'T552QN-XPJAA-S7NKCI', 'time': '1642084372.151158', 'type': 'trade'}], 'channel': 'balances', 'sequence': 15}
                # [13/01/2022 07:49:29] balances: {'ledgers': [{'amount': '-17.76', 'asset': 'USD', 'balance': '2885.37', 'fee': '0.03', 'ledgerID': 'LLFBJ2-WBC7Y-MD7JY3', 'refid': 'TNXBEE-5S3AM-ZX2KBA', 'time': '1642087098.966361', 'type': 'trade'}], 'channel': 'balances', 'sequence': 16}
                # [13/01/2022 07:49:29] balances: {'ledgers': [{'amount': '6.25000', 'asset': 'EOS', 'balance': '9.75000', 'fee': '0.00000', 'ledgerID': 'L2X35Q-LDGBS-ROIT7Z', 'refid': 'TNXBEE-5S3AM-ZX2KBA', 'time': '1642087098.966634', 'type': 'trade'}], 'channel': 'balances', 'sequence': 17}
                # [13/01/2022 07:49:29] balances: {'ledgers': [{'amount': '-151.64', 'asset': 'USD', 'balance': '2733.49', 'fee': '0.24', 'ledgerID': 'LLXSBJ-DTXZJ-MFK4LE', 'refid': 'TEY6GU-TM3JX-ACHWQ4', 'time': '1642087158.072728', 'type': 'trade'}], 'channel': 'balances', 'sequence': 18}
                # [13/01/2022 07:49:29] balances: {'ledgers': [{'amount': '195.31250', 'asset': 'OCEAN', 'balance': '322.18750', 'fee': '0.00000', 'ledgerID': 'LS4IVP-JB7U4-3TQLTD', 'refid': 'TEY6GU-TM3JX-ACHWQ4', 'time': '1642087158.073012', 'type': 'trade'}], 'channel': 'balances', 'sequence': 19}
                # [13/01/2022 07:49:29] balances: {'ledgers': [{'amount': '-44.07', 'asset': 'USD', 'balance': '2689.35', 'fee': '0.07', 'ledgerID': 'LPAQB5-NJ6WZ-SK6NSJ', 'refid': 'TE6TTB-OLU4D-SKFBC2', 'time': '1642087163.346881', 'type': 'trade'}], 'channel': 'balances', 'sequence': 20}
                # [13/01/2022 07:49:29] balances: {'ledgers': [{'amount': '15.62500', 'asset': 'EOS', 'balance': '25.37500', 'fee': '0.00000', 'ledgerID': 'LHMZ2W-YM2MK-CGZZP7', 'refid': 'TE6TTB-OLU4D-SKFBC2', 'time': '1642087163.347268', 'type': 'trade'}], 'channel': 'balances', 'sequence': 21}
                G.log.print_and_log(f"balances: {message}", G.print_lock)
        return
            
    def ws_open(self, ws: WebSocketApp) -> None:
        G.log.print_and_log("balances: opened socket", G.print_lock)
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed": "balances", "token": self.api_token}
        ws.send(api_data)
        return

    def ws_close(self, ws: WebSocketApp, close_status_code: int, close_msg: str) -> None:
        G.log.print_and_log(f"balances: closed socket, status code: {close_status_code}, close message:{close_msg}", G.print_lock)
        return

    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        G.log.print_and_log("balances: Error " + str(error_message), G.print_lock)
        return
