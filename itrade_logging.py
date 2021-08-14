#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_logging.py
#
# Description: Logging facilities
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2008 the
# Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see http://www.gnu.org/licenses/gpl.html
#
# History       Rev   Description
# 2004-04-11    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import sys
import types
import atexit
import logging

# iTrade system
import itrade_ansicolors
import itrade_config

# ============================================================================
# Formatter
# ============================================================================

deadExceptions = [KeyboardInterrupt, SystemExit]

class Formatter(logging.Formatter):
    def formatException(self, xxx_todo_changeme):
        # dead exceptions shall be raised, not logged
        (E, e, tb) = xxx_todo_changeme
        for exn in deadExceptions:
            if issubclass(e.__class__, exn):
                raise
        return logging.Formatter.formatException(self, (E, e, tb))

# ============================================================================
# myStreamHandler
# ============================================================================

class myStreamHandler(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        if not hasattr(types, "UnicodeType"):
            self.stream.write("%s\n" % msg)
        else:
            try:
                self.stream.write("%s\n" % msg)
            except UnicodeError:
                self.stream.write("%s\n" % msg.encode("UTF-8"))
        self.flush()

# ============================================================================
# myFileHandler
# ============================================================================

class myFileHandler(logging.FileHandler):
    def emit(self, record):
        msg = self.format(record)
        if not hasattr(types, "UnicodeType"):
            self.stream.write("%s\n" % msg)
        else:
            try:
                self.stream.write("%s\n" % msg)
            except UnicodeError:
                self.stream.write("%s\n" % msg.encode("UTF-8"))
        self.flush()

# ============================================================================
# myStdoutStreamHandler
# ============================================================================

class myStdoutStreamHandler(myStreamHandler):
    def disable(self):
        self.setLevel(sys.maxsize)
        itrade_logger.removeHandler(self)
        logging._acquireLock()
        try:
            del logging._handlers[self]
        finally:
            logging._releaseLock()

    def emit(self, record):
        try:
            myStreamHandler.emit(self, record)
        except ValueError:
            # disable this handler because sys.stdout is closed
            self.disable()
            error('Error logging to stdout : shall remove the stdout handler !')
            exception('Uncaught exception in myStdoutStreamHandler:')

# ============================================================================
# myColorFormatter
# ============================================================================

class myColorFormatter(Formatter):
    def formatException(self, xxx_todo_changeme1):
        (E, e, tb) = xxx_todo_changeme1
        if itrade_config.useColors:
            return ''.join([itrade_ansicolors.BOLD, itrade_ansicolors.RED,Formatter.formatException(self, (E, e, tb)),itrade_ansicolors.RESET])
        else:
            return Formatter.formatException(self, (E, e, tb))

    def format(self, record, *args, **kwargs):
        if itrade_config.useColors:
            color = itrade_ansicolors.WHITE
            if record.levelno == logging.CRITICAL:
                color = itrade_ansicolors.WHITE + itrade_ansicolors.BOLD
            elif record.levelno == logging.ERROR:
                color = itrade_ansicolors.RED
            elif record.levelno == logging.WARNING:
                color = itrade_ansicolors.YELLOW
            return ''.join([color,Formatter.format(self, record, *args, **kwargs),itrade_ansicolors.RESET])
        else:
            return Formatter.format(self, record, *args, **kwargs)

# ============================================================================
#
# ============================================================================

# ============================================================================
# Install the logger
# ============================================================================

itrade_logger = logging.getLogger('itrade')

# export me
debug = itrade_logger.debug
info = itrade_logger.info
warning = itrade_logger.warning
error = itrade_logger.error
critical = itrade_logger.critical
exception = itrade_logger.exception
setLevel = itrade_logger.setLevel
log = itrade_logger.log

# be sure to shutdown gracefully
atexit.register(logging.shutdown)

# install fileout handler
_fileoutHandler = myFileHandler('itrade.log')
_fileoutFormatter = Formatter('%(pathname)s,%(lineno)s(%(levelname)s)-%(asctime)s: %(message)s')
_fileoutHandler.setFormatter(_fileoutFormatter)
_fileoutHandler.setLevel(logging.DEBUG)
itrade_logger.addHandler(_fileoutHandler)

# install stdout handler
_stdoutHandler = myStdoutStreamHandler(sys.stdout)
_stdoutFormatter = myColorFormatter('%(filename)s,%(lineno)s(%(levelname)s): %(message)s')
_stdoutHandler.setFormatter(_stdoutFormatter)
#_stdoutHandler.setLevel(logging.WARNING)   __x read a configuration
_stdoutHandler.setLevel(logging.DEBUG)
#_stdoutHandler.setLevel(logging.INFO)
itrade_logger.addHandler(_stdoutHandler)

# __x on windows, install also NT event logger handler - if run as service

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    info('information:' + itrade_config.__author__)
    warning('warning:' + itrade_config.__revision__)
    error('error:' + itrade_config.__version__)
    try:
        a = 0 / 0
    except:
        exception('Uncaught divide by 0 exception')
    critical('critical')
    debug('debug: __main__')
    log(30, 'info')


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
