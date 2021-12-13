
# """sell.py: Sells coin on kraken exchange based on users config file."""

# from pprint                                 import pprint
# from bot_features.dca                       import DCA
# from bot_features.kraken_enums    import *
# from bot_features.kraken_bot_base import KrakenBotBase
# from util.globals                           import G
# # from bot_features.my_sql                             import SQL
# from util.colors                            import Color


# class Sell(KrakenBotBase):
#     def __init__(self, parameter_dict: dict) -> None:
#         super().__init__(parameter_dict)
#         self.asset_pairs_dict:  dict = self.get_all_tradable_asset_pairs()[Dicts.RESULT]
#         self.dca:               DCA  = None
#         return
    
#     def __get_sell_order_txid(self, sell_order_result) -> str:
#         if not self.has_result(sell_order_result):
#             raise Exception(f"sell.__get_sell_order_txid: {sell_order_result}")        
#         return sell_order_result[Dicts.RESULT][Data.TXID][0]

#     def __cancel_open_sell_order(self, symbol_pair: str) -> None:
#         """
#             Cancel the open sell order based on txid stored in the open_sell_orders table.
#             Set cancelled=true in open_sell_orders table.

#         """
#         try:
#             sql = SQL()

#             result_set = sql.con_query(f"SELECT oso_txid FROM open_sell_orders WHERE symbol_pair='{symbol_pair}' AND cancelled=false AND filled=false")
            
#             if result_set.rowcount > 0:
#                 for oso_txid in result_set.fetchall():
#                     self.cancel_order(oso_txid[0])
#                     sql.con_update(f"UPDATE open_sell_orders SET cancelled=true WHERE symbol_pair='{symbol_pair}' AND cancelled=false AND filled=false and oso_txid='{oso_txid[0]}'")
                    
#                     row = sql.con_query(f"SELECT * FROM open_sell_orders WHERE symbol_pair='{symbol_pair}' AND cancelled=true AND filled=false and oso_txid='{oso_txid[0]}'")
                    
#                     if row.rowcount > 0:
#                         row = row.fetchall()[0]
#                         G.log.print_and_log(Color.BG_GREY + f"Cancelled Sell order {row[2]} {Color.ENDC} {row[0]}")
#         except Exception as e:
#             G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
#         return

#     def __place_sell_limit_order(self, symbol_pair: str, filled_buy_order_txid: str) -> dict:
#         """
#             Place limit order to sell the coin.
        
#         """
#         try:
#             sql = SQL()
            
#             # get row
#             result_set      = sql.con_query(f"SELECT MAX(safety_order_no) FROM open_buy_orders WHERE symbol_pair='{symbol_pair}' AND filled=true") # this works with quantity, req price needs to be one row after
#             safety_order_no = sql.parse_so_number(result_set)
#             row             = sql.con_get_row(SQLTable.SAFETY_ORDERS, symbol_pair, safety_order_no)
            
#             # get quantity
#             max_prec             = self.get_max_volume_precision(symbol_pair)
#             qty_to_sell          = self.round_decimals_down(row[5], max_prec)
            
#             # get price
#             nonrounded_req_price = row[8]
#             max_prec             = self.get_max_price_precision(symbol_pair)
#             required_price       = self.round_decimals_down(nonrounded_req_price, max_prec)
            
#             # sell order
#             sell_order_result    = self.limit_order(Trade.SELL, qty_to_sell, symbol_pair, required_price)
            
#             if self.has_result(sell_order_result):
#                 result_set       = sql.con_query(f"SELECT profit FROM open_buy_orders WHERE symbol_pair='{symbol_pair}' AND obo_txid='{filled_buy_order_txid}'")
#                 profit_potential = round(result_set.fetchone()[0] if result_set.rowcount > 0 else 0, 6)
#                 G.log.print_and_log(Color.BG_BLUE + f"Sell limit order placed{Color.ENDC} {symbol_pair} {sell_order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}, Profit Potential: ${profit_potential}")
#             else:
#                 G.log.print_and_log(Color.FG_YELLOW + f"Sell: {Color.ENDC} {symbol_pair} {sell_order_result[Dicts.ERROR]}" )
#             return sell_order_result
#         except Exception as e:
#             G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
#         return

# ##################################################################
# ### Place sell order for base order only!
# ##################################################################
#     def place_sell_limit_base_order(self, base_order_row: BaseOrderRow) -> dict:
#         """Create a sell limit order for the base order only!"""
#         sql = SQL()
#         try:
#             max_price_prec                = self.get_max_price_precision(base_order_row.symbol_pair)
#             base_order_row.required_price = self.round_decimals_down(base_order_row.required_price, max_price_prec)
#             sell_order_result             = self.limit_order(Trade.SELL, base_order_row.quantity, base_order_row.symbol_pair, base_order_row.required_price)

#             if self.has_result(sell_order_result):
#                 base_order_row.profit   = round(base_order_row.price * base_order_row.quantity * DCA_.TARGET_PROFIT_PERCENT/100, DECIMAL_MAX)
#                 base_order_row.oso_txid = sell_order_result[Dicts.RESULT][Data.TXID][0]
#                 G.log.print_and_log(Color.BG_BLUE + f"Sell order placed      {Color.ENDC} {base_order_row.symbol_pair} {sell_order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}, Profit Potential: ${base_order_row.profit}" + Color.ENDC)
                
#                 result_set = sql.con_query(f"SELECT MIN(so_no) FROM safety_orders WHERE symbol_pair='{base_order_row.symbol_pair}'")
#                 if result_set.rowcount > 0:
#                     base_order_row.oso_no = result_set.fetchone()[0]
                
#                 # put in base order specs
#                 sql.con_update(f"""INSERT INTO open_sell_orders {sql.oso_columns} VALUES 
#                               ('{base_order_row.symbol_pair}',    '{base_order_row.symbol}',         {base_order_row.safety_order_no}, {base_order_row.deviation},
#                                 {base_order_row.quantity},         {base_order_row.total_quantity},  {base_order_row.price},           {base_order_row.average_price},
#                                 {base_order_row.required_price},   {base_order_row.required_change}, {base_order_row.profit},          {base_order_row.cost},
#                                 {base_order_row.total_cost},       {base_order_row.cancelled},       {base_order_row.filled},         '{base_order_row.oso_txid}',
#                                 {base_order_row.oso_no}
#                               )""")
#             else:
#                 G.log.print_and_log(f"place_sell_limit_base_order: {base_order_row.symbol_pair} {sell_order_result[Dicts.ERROR]}")
#         except Exception as e:
#             G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
#         return sell_order_result
    
    
# ##################################################################
# ### Run the entire sell process for safety orders
# ##################################################################
#     def start(self, symbol_pair: str, filled_buy_order_txid: str) -> None:
#         """
#         Everytime an open_buy_order is filled we need to
#             1. Cancel the open_sell_order on 'symbol_pair'
#             2. Place a new sell order
#             3. insert new sell order into open_sell_order table

#         """
#         try:
#             sql = SQL()

#             self.__cancel_open_sell_order(symbol_pair)

#             sell_order_result = self.__place_sell_limit_order(symbol_pair, filled_buy_order_txid)
#             sell_order_txid   = self.__get_sell_order_txid(sell_order_result)
#             result_set        = sql.con_query(f"SELECT MAX(safety_order_no) FROM {SQLTable.OPEN_BUY_ORDERS} WHERE symbol_pair='{symbol_pair}' AND filled=true")

#             if result_set.rowcount > 0:
#                 safety_order_number = sql.parse_so_number(result_set)
#                 row                 = sql.con_get_row(SQLTable.OPEN_BUY_ORDERS, symbol_pair, safety_order_number)
                
#                 # insert sell order into sql
#                 sql.con_update(f"""INSERT INTO open_sell_orders {sql.oso_columns} VALUES 
#                               ('{row[0]}', '{row[1]}', {row[2]},   {row[3]},
#                                 {row[4]},   {row[5]},  {row[6]},   {row[7]},
#                                 {row[8]},   {row[9]},  {row[10]},  {row[11]},
#                                 {row[12]},  false,     false,     '{sell_order_txid}',
#                                 {row[15]}
#                             )""")
#         except Exception as e:
#             G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
#         return
