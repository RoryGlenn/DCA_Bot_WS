import datetime
import os
import re

from pprint import PrettyPrinter

from pprint import pprint
from threading import Lock
from bot_features.low_level.kraken_enums import FileMode
from util.colors   import Color

class Log():
    def __init__(self):
        self.log_directory_path = "src/logs"
        self.log_file_path      = "src/logs" + "/" + str(datetime.date.today()) + ".txt"

    def get_current_time(self) -> str:
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    def get_current_date(self) -> str:
        return datetime.datetime.today().strftime("%d/%m/%Y")

    def directory_create(self) -> None:
        try:
            if not os.path.exists(self.log_directory_path):
                os.mkdir(self.log_directory_path)
        except Exception as e:
            print(Color.BG_RED + f"ERROR:{Color.ENDC} || {e}, {type(e).__name__} {__file__} {e.__traceback__.tb_lineno}" )
        return

    def file_create(self):
        try:
            if not os.path.exists(self.log_file_path):
                # create the file
                file = open(self.log_file_path, FileMode.READ_WRITE_CREATE)
                file.close()

            # If its out first time opening the file since we started up,
            # write a new line to make it a little neater
            with open(self.log_file_path, FileMode.WRITE_APPEND) as file:
                file.write(
                    "\n=========================================================================================\n")
        except Exception as e:
            print(Color.BG_RED + f"ERROR:{Color.ENDC} || {e}, {type(e).__name__} {__file__} {e.__traceback__.tb_lineno}" )
        return

    def write(self, text):
        """Writes to the end of the log file"""
        try:
            file_path="src/logs/" + str(datetime.date.today()) + ".txt"
            with open(file_path, FileMode.WRITE_APPEND) as file:
                file.write(f"{text}\n")
        except Exception as e:
            print(Color.BG_RED + f"ERROR:{Color.ENDC} || {e}, {type(e).__name__} {__file__} {e.__traceback__.tb_lineno}" )
        return

    def __remove_color(self, message: str) -> str:
        """Strip out ansi escape sequence by using regular expression."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', message)

    def print_and_log(self, message: str = "", lock: Lock = None, money: bool = False, end: bool = False, e=False, error_type: str = "", filename: str = "", tb_lineno: str = "") -> None:
        """Print to the console and write to the log file. 
        If something went wrong, just print the error to console."""
        try:
            lock.acquire()
            current_time = self.get_current_time()
            current_date = self.get_current_date()
            
            result_no_color = f"[{current_date} {current_time}] {self.__remove_color(message)}"
            result          = Color.FG_BRIGHT_BLACK + f"[{current_date} {current_time}]{Color.ENDC} {message}"

            if money:
                print(     result)
                self.write(result_no_color)
                result.strip()
                return
            if e:
                print(f"{result}{Color.BG_RED}ERROR:{Color.ENDC} || {e}, {error_type} {filename} {tb_lineno}" )
                self.write(f"{result_no_color} ERROR: || {e}, {error_type} {filename} {tb_lineno}")
                return
            if end:
                print(     result)
                self.write(result_no_color)
                return
            
            print(     result)
            self.write(result_no_color)
        except:
            print(f"{result} {Color.BG_RED}ERROR:{Color.ENDC} || {e}, {error_type} {filename} {tb_lineno}" )
        
        lock.release()
        return
    
    def pprint_and_log(self, message: str = "", dictionary: dict = {}, lock: Lock = None, e=False, error_type: str = "", filename: str = "", tb_lineno: str = "") -> None:
        """Print to the console and write to the log file. 
        If something went wrong, just print the error to console."""
        try:
            
            lock.acquire()

            pprinter = PrettyPrinter()
            
            current_time = self.get_current_time()
            current_date = self.get_current_date()
            
            result_no_color = f"[{current_date} {current_time}] {self.__remove_color(message)}"
            result          = Color.FG_BRIGHT_BLACK + f"[{current_date} {current_time}]{Color.ENDC} {message}"
            
            formated_result_no_color = f"{result_no_color} {pprinter.pformat(dictionary)}"
            formated_result          = f"{result} {pprinter.pformat(dictionary)}"

            print(formated_result)
            self.write(formated_result_no_color)
        except Exception as e:
            print(f"{result} {Color.BG_RED}ERROR:{Color.ENDC} || {e}, {error_type} {filename} {tb_lineno}" )
        
        lock.release()
        return