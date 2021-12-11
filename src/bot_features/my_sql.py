import mysql.connector
import os

from mysql.connector.cursor               import MySQLCursorBuffered
from mysql.connector.connection           import MySQLConnection, MySQLCursor
from bot_features.kraken_enums            import *


class SQL():
    def __init__(self, host_name: str = "localhost", user_name: str = "root", user_password: str = "12345", db_name: str = "dca") -> None:
        self.host_name:     str              = host_name
        self.user_name:     str              = user_name
        self.user_password: str              = user_password
        self.db_name:       str              = db_name
        self.so_columns:    str              = "(symbol_pair, symbol, safety_order_no, deviation, quantity, total_quantity, price, average_price, required_price, required_change, profit, cost, total_cost, order_placed, so_no)"
        self.obo_columns:   str              = "(symbol_pair, symbol, safety_order_no, deviation, quantity, total_quantity, price, average_price, required_price, required_change, profit, cost, total_cost, filled, obo_txid, obo_no)"
        self.oso_columns:   str              = "(symbol_pair, symbol, safety_order_no, deviation, quantity, total_quantity, price, average_price, required_price, required_change, profit, cost, total_cost, cancelled, filled, oso_txid, oso_no)"
        self.connection:    MySQLConnection  = None
        return

    def __create_db_connection(self) -> None:
        self.connection = mysql.connector.connect(
            host=self.host_name,
            user=self.user_name,
            passwd=self.user_password,
            database=self.db_name)
        return 
    
    def __close_db_connection(self) -> None:
        if self.connection is not None:
            cursor  = self.connection.cursor()
            cursor.close()
            self.connection.close()
        else:
            print("MySQL no connection open")
        return

    def __update(self, query: str) -> MySQLCursor:
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()
        return cursor

    def __query(self, query: str) -> MySQLCursorBuffered:
        cursor = self.connection.cursor(buffered=True)
        cursor.execute(query)
        return cursor
    
    def con_query(self, query: str) -> MySQLCursorBuffered:
        self.__create_db_connection()
        result_set = self.__query(query)
        self.__close_db_connection()
        return result_set
    
    def con_update(self, query: str) -> None:
        self.__create_db_connection()
        result_set = self.__update(query)
        result_set.close()
        self.__close_db_connection()
        return
    
    def drop_all_tables(self) -> None:
        self.con_update("DROP TABLE open_sell_orders")
        self.con_update("DROP TABLE open_buy_orders")
        self.con_update("DROP TABLE safety_orders")
        return

    def create_tables(self) -> None:
        """Drops and creates the tables."""
        
        safety_orders = """
            CREATE TABLE safety_orders (
                symbol_pair         VARCHAR(20) NOT NULL,
                symbol              VARCHAR(10) NOT NULL,
                safety_order_no     INT         NOT NULL,
                deviation           FLOAT       NOT NULL,
                quantity            FLOAT       NOT NULL,
                total_quantity      FLOAT       NOT NULL,
                price               FLOAT       NOT NULL,
                average_price       FLOAT       NOT NULL,
                required_price      FLOAT       NOT NULL,
                required_change     FLOAT       NOT NULL,
                profit              FLOAT       NOT NULL,
                cost                FLOAT       NOT NULL,
                total_cost          FLOAT       NOT NULL,
                order_placed        BOOLEAN     NOT NULL,
                so_no               INT         NOT NULL AUTO_INCREMENT,
                PRIMARY KEY (so_no)
            );  """

        open_buy_orders = """
            CREATE TABLE open_buy_orders (
                symbol_pair         VARCHAR(20) NOT NULL,
                symbol              VARCHAR(10) NOT NULL,
                safety_order_no     INT         NOT NULL,
                deviation           FLOAT       NOT NULL,
                quantity            FLOAT       NOT NULL,
                total_quantity      FLOAT       NOT NULL,
                price               FLOAT       NOT NULL,
                average_price       FLOAT       NOT NULL,
                required_price      FLOAT       NOT NULL,
                required_change     FLOAT       NOT NULL,
                profit              FLOAT       NOT NULL,
                cost                FLOAT       NOT NULL,
                total_cost          FLOAT       NOT NULL,
                filled              BOOLEAN     NOT NULL,
                obo_txid            VARCHAR(30) NOT NULL,
                obo_no              INT         NOT NULL,
                PRIMARY KEY (obo_no)
            );  """

        open_sell_orders = """
            CREATE TABLE open_sell_orders (
                symbol_pair         VARCHAR(20) NOT NULL,
                symbol              VARCHAR(10) NOT NULL,
                safety_order_no     INT         NOT NULL,
                deviation           FLOAT       NOT NULL,
                quantity            FLOAT       NOT NULL,
                total_quantity      FLOAT       NOT NULL,
                price               FLOAT       NOT NULL,
                average_price       FLOAT       NOT NULL,
                required_price      FLOAT       NOT NULL,
                required_change     FLOAT       NOT NULL,
                profit              FLOAT       NOT NULL,
                cost                FLOAT       NOT NULL,
                total_cost          FLOAT       NOT NULL,
                cancelled           BOOLEAN     NOT NULL,
                filled              BOOLEAN     NOT NULL,
                oso_txid            VARCHAR(30) NOT NULL,
                oso_no              INT         NOT NULL
            );  """
        
        self.con_update(safety_orders)
        self.con_update(open_buy_orders)
        self.con_update(open_sell_orders)
        return

    def create_kraken_coins_table(self) -> None:
        self.con_update("DROP TABLE kraken_coins")
        self.con_update("""
            CREATE TABLE kraken_coins (
                symbol     VARCHAR(10) NOT NULL,
                symbol_no  INT         NOT NULL AUTO_INCREMENT,
                PRIMARY KEY (symbol_no)
                );""")
        
        if os.path.exists(KRAKEN_COINS_JSON):
            with open(KRAKEN_COINS_JSON, 'r') as file:
                lines = file.readlines()
                lines.sort()
                for line in lines:
                    symbol = line.replace("\n", "")
                    self.con_update(f"INSERT INTO kraken_coins (symbol) VALUES ('{symbol}')")
        return

    def con_get_symbols(self) -> set:
        bought_set = set()
        result_set: MySQLCursorBuffered = self.con_query("SELECT symbol FROM safety_orders")
        if result_set.rowcount > 0:
            for symbol in result_set.fetchall():
                bought_set.add(symbol[0])
        return bought_set
    
    def con_get_symbol_pairs(self) -> set:
        """Gets the symbol pairs that are currently in the database under the safety_orders table."""
        bought_set = set()
        result_set: MySQLCursorBuffered = self.con_query("SELECT symbol_pair FROM safety_orders")
        if result_set.rowcount > 0:
            for symbol in result_set.fetchall():
                bought_set.add(symbol[0])
        return bought_set
        
    def con_get_required_price(self, table_name: str, symbol_pair: str) -> float:
        # result_set: MySQLCursorBuffered = self.con_query(f"SELECT required_price FROM {table_name} WHERE symbol_pair='{symbol_pair}' AND order_placed=false LIMIT 1")
        result_set: MySQLCursorBuffered = self.con_query(f"SELECT MAX(required_price) FROM {table_name} WHERE symbol_pair='{symbol_pair}' AND filled=false LIMIT 1")
        if result_set.rowcount > 0:
            req_price_list = result_set.fetchall()
        return req_price_list[0][0] if result_set.rowcount > 0 else -1
    
    def con_get_open_buy_orders(self, symbol_pair: str) -> int:
        result_set: MySQLCursorBuffered = self.con_query(f"SELECT symbol_pair FROM open_buy_orders WHERE symbol_pair='{symbol_pair}' AND filled=false")
        if result_set.rowcount > 0:
            return len(result_set.fetchall())
        return 0
        
    def con_get_quantities(self, symbol_pair: str) -> list:
        result_set: MySQLCursorBuffered = self.con_query(f"SELECT quantity FROM safety_orders WHERE symbol_pair='{symbol_pair}' AND order_placed=false")
        return [quantity[0] for quantity in result_set.fetchall()] if result_set.rowcount > 0 else []
    
    def con_get_prices(self, symbol_pair: str) -> list:
        result_set: MySQLCursorBuffered = self.con_query(f"SELECT price FROM safety_orders WHERE symbol_pair='{symbol_pair}' AND order_placed=false")
        return [price[0] for price in result_set.fetchall()] if result_set.rowcount > 0 else []
    
    def con_get_row(self, tablename: str, symbol_pair: str, safety_order_number: int) -> tuple:
        result_set = self.con_query(f"SELECT * FROM {tablename} WHERE symbol_pair='{symbol_pair}' AND safety_order_no={safety_order_number}")
        if result_set.rowcount > 0:
            return result_set.fetchone()
        return tuple()
    
    def parse_so_number(self, result_set: MySQLCursorBuffered) -> int:
        """Return the safety order number that previously queried."""
        if result_set.rowcount > 0:
            num = result_set.fetchone()
            if isinstance(num, tuple):
                return num[0]
            else:
                return num
        return tuple()
    