"""Simple Logger"""

from __future__ import print_function

import os
import sys
import inspect
import datetime
import traceback
from enum import IntEnum

OUTPUT = sys.stderr

LEVEL = ["CRIT", "ERR ", "WARN", "NOTE", "INFO", "DBUG", "...."]
CLEVEL = ["\x1B[41mCRIT\x1B[0m",
          "\x1B[31mERR \x1B[0m",
          "\x1B[33mWARN\x1B[0m",
          "\x1B[32mNOTE\x1B[0m",
          "\x1B[34mINFO\x1B[0m",
          "\x1B[90mDBUG\x1B[0m",
          "\x1B[90m....\x1B[0m"]

MSG = "{0}  {1}  {2}  {3}  {4}  {5}  ::  {6}"
CMSG = "[{1}]\x1B[90m {2}  {3}:{5} [{4}]\x1B[0m {6}\x1B[0m"
CMULTI = "[{1}]\x1B[90m {2}\x1B[0m"


class Level(IntEnum):
    """Log Level enumeration"""
    VERB_CRITICAL = 0
    VERB_ERROR = 1
    VERB_WARN = 2
    VERB_NOTICE = 3
    VERB_INFO = 4
    VERB_DEBUG = 5
    VERB_NONE = -1


class Log:
    """Logger"""
    log_dir = ""
    log_pfx = "main"

    level_console = Level.VERB_ERROR
    level_file = Level.VERB_NONE
    level_full = False

    count = [0, 0, 0, 0, 0, 0]

    def __init__(self):
        self.prog_name = sys.argv[0].rsplit("/", 1)[-1]
        self.prog_name = self.prog_name.split(".", 1)[0]
        self.log_pfx = self.prog_name

    def __del__(self):
        if self.level_console >= 5:
            crit, err, warn, note, inf, dbug = tuple(self.count)
            os.write(1, "[\x1B[90m\x1B[90mDBUG\x1B[90m] Log Counters" +
                     f" crit:{crit}" +
                     f" err:{err}" +
                     f" warn: {warn}" +
                     f" note: {note}" +
                     f" info: {inf}" +
                     f" dbug: {dbug}\x1B[0m\n")

    def set_dir(self, name: str):
        """Set output directory"""
        if not os.path.isdir(name):
            os.makedirs(name)
        self.log_dir = name

    def output(self, level: Level, message: str, frame=1):
        """Write a message to console or log, conditionally."""
        if level < 0 or level > 5:
            level = 5

        self.count[level] += 1

        # function_name = inspect.stack()[1][3]
        cur_date = datetime.datetime.now()

        (frame, file, ln, fn, _, _) = inspect.getouterframes(
            inspect.currentframe())[frame]

        message = str(message).split("\n")
        cmsg = CMSG if self.level_full else CMULTI

        if self.level_console >= level:

            if len(message) == 1:
                if self.level_full:
                    arg = (str(cur_date),
                           CLEVEL[level],
                           self.prog_name,
                           file, fn, ln, message[0])
                else:
                    arg = str(cur_date), CLEVEL[level], message[0]

                print(cmsg.format(*arg), file=OUTPUT)
            else:
                if self.level_full:
                    arg = str(cur_date), CLEVEL[
                        level], self.prog_name, file, fn, ln, ""
                    print(cmsg.format(*arg), file=OUTPUT)

                for line in message:
                    print(CMULTI.format(str(cur_date),
                                        CLEVEL[Level.VERB_NONE], line),
                          file=OUTPUT)

        if self.level_file >= level:
            self.set_dir("./logs")
            log_file_name = os.path.join(
                self.log_dir,
                self.log_pfx + str(cur_date.strftime('%Y-%m-%d')) + ".txt")

            with open(log_file_name, "a") as logger:
                logger.write(MSG.format(str(cur_date),
                                        LEVEL[level],
                                        self.prog_name,
                                        file, fn, ln, message[0]) + "\n")
                for line in message[1:]:
                    logger.write(MSG.format(str(cur_date),
                                            LEVEL[Level.VERB_NONE],
                                            self.prog_name,
                                            file, fn, ln, line) + "\n")

    def fatal(self, message: str):
        """Log a fatal error"""
        self.output(Level.VERB_CRITICAL, message, 2)
        sys.exit(1)

    def critical(self, message: str):
        """Log a critical error"""
        self.output(Level.VERB_CRITICAL, message, 2)

    def error(self, message: str):
        """Log a normal error"""
        self.output(Level.VERB_ERROR, message, 2)

    def warning(self, message: str):
        """Log a warning"""
        self.output(Level.VERB_WARN, message, 2)

    def notice(self, message: str):
        """Log a notice"""
        self.output(Level.VERB_NOTICE, message, 2)

    def info(self, message: str):
        """Log an informational"""
        self.output(Level.VERB_INFO, message, 2)

    def debug(self, message: str):
        """Log a debug"""
        self.output(Level.VERB_DEBUG, message, 2)


default = Log()

fatal = default.fatal
critical = default.critical
error = default.error
warning = default.warning
notice = default.notice
info = default.info
debug = default.debug


class LogException:
    """Catches an exception to log it"""
    stop = None

    def __init__(self, stop: bool = True):
        self.stop = stop

    def __enter__(self, stop: bool = True):
        pass

    def __exit__(self, exc_type, value, trace) -> bool:

        if exc_type is None:
            return True

        if exc_type is SystemExit and value.args == (0,):
            return True

        log_string, _ = fmt_exception(exc_type, value, trace)
        default.output(Level.VERB_CRITICAL, 'Failure\n\n' + log_string, 2)

        if self.stop is False:
            return False

        fatal("ABORTING EXECUTION")
        return False


def fmt_exception(exc_type, exc_value, exc_traceback):
    """format exception to string"""
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    log_string = ''.join(line for line in lines)
    email_string = ''.join('<br />' + line for line in lines)

    return log_string, email_string


exception = LogException
