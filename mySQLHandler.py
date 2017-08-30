# -*- coding: utf-8 -*-
'''
Created on 02/01/2014
'''

import pymysql
import logging
import time
 
class mySQLHandler(logging.Handler):
    """
    Logging handler for MySQL.
     
    Based on Vinay Sajip's DBHandler class (http://www.red-dove.com/python_logging.html)
    forked from ykessler/gae_handler.py (https://gist.github.com/ykessler/2662203)
    <from ykessler/gae_handler.py>
    This version sacrifices performance for thread-safety:
    Instead of using a persistent cursor, we open/close connections for each entry.
    AFAIK this is necessary in multi-threaded applications,
    because SQLite doesn't allow access to objects across threads.
    </from>
    <from onemoretime>
    please see:
        https://github.com/onemoretime/mySQLHandler for more up-to-date version
        README.md
        LICENSE
    </from>
    <from smilingworlock>
        edited for pymysql and python3
    </from smilingworlock>

    @todo: create SQL table if necessary, try/except when execute sql, ...
    @author: "onemoretime"
    @copyright: "Copyright 2014, onemoretime"
    @license: "WTFPL."
    @version: "0.1"
    @contact: "onemoretime"
    @email: "onemoretime@cyber.world.universe"
    @status: "Alpha"
    """
 
    initial_sql = """CREATE TABLE IF NOT EXISTS log(
    Host text,
    Created text,
    Name text,
    LogLevel int,
    LogLevelName text,
    Message text,
    Args text,
    Module text,
    FuncName text,
    LineNo int,
    Exception text,
    Process int,
    Thread text,
    ThreadName text
    )"""
 
    insertion_sql = """INSERT INTO log(
    Host,
    Created,
    Name,
    LogLevel,
    LogLevelName,
    Message,
    Args,
    Module,
    FuncName,
    LineNo,
    Exception,
    Process,
    Thread,
    ThreadName
    )
    VALUES (
    '%(host)s',
    '%(dbtime)s',
    '%(name)s',
    %(levelno)d,
    '%(levelname)s',
    '%(msg)s',
    '%(args)s',
    '%(module)s',
    '%(funcName)s',
    %(lineno)d,
    '%(exc_text)s',
    %(process)d,
    '%(thread)s',
    '%(threadName)s'
    );
    """
 
    def __init__(self, db):
        """
        Constructor
        @param db: ['host','port','dbuser', 'dbpassword', 'dbname'] 
        @return: mySQLHandler
        """
        try:
            logging.Handler.__init__(self)
            self.db = db
            # Try to connect to DB

            # Check if 'log' table in db already exists
            result = self.checkTablePresence()
            # If not exists, then create the table
            if not result:
                try:
                    conn=pymysql.connect(host=self.db['host'],port=self.db['port'],user=self.db['dbuser'],passwd=self.db['dbpassword'],db=self.db['dbname'])
                except pymysql.MySQLError as e:
                    raise Exception(e)
                    exit(-1)
                else:         
                    cur = conn.cursor()
                    try:
                        cur.execute(mySQLHandler.initial_sql)
                    except pymysql.MySQLError as e:
                        conn.rollback()
                        cur.close()
                        conn.close()
                        raise Exception(e)
                        exit(-1)
                    else:
                        conn.commit()
                    finally:
                        cur.close()
                        conn.close()
        except Exception as inst:
            print("mySQLHandler could not be initialized")
    def checkTablePresence(self):
        try:
            conn=pymysql.connect(host=self.db['host'],port=self.db['port'],user=self.db['dbuser'],passwd=self.db['dbpassword'],db=self.db['dbname'])
        except pymysql.MySQLError as e:
            raise Exception(e)
            exit(-1)
        else:
            # Check if 'log' table in db already exists
            cur = conn.cursor()
            stmt = "SHOW TABLES LIKE 'log';"
            cur.execute(stmt)
            result = cur.fetchone()
            cur.close()
            conn.close()
        
        if not result:
            return 0
        else:
            return 1

    def createTableLog(self):
        pass
        
    def formatDBTime(self, record):
        """
        Time formatter
        @param record:
        @return: nothing
        """ 
        record.dbtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
 
    def emit(self, record):
        """
        Connect to DB, execute SQL Request, disconnect from DB
        @param record:
        @return: 
        """ 
        try:
            # Use default formatting:
            self.format(record)
            # Set the database time up:
            self.formatDBTime(record)
            import socket
            record.host = socket.gethostname()
            if record.exc_info:
                record.exc_text = logging._defaultFormatter.formatException(record.exc_info)
            else:
                record.exc_text = ""

            try:
                conn=pymysql.connect(host=self.db['host'],port=self.db['port'],user=self.db['dbuser'],passwd=self.db['dbpassword'],db=self.db['dbname'])
            except pymysql.MySQLError as e:
                raise Exception(e)
                exit(-1)
            cur = conn.cursor()
            try:
                # Escape message
                record.msg = conn.escape_string(str(record.msg))
                cur.execute(mySQLHandler.insertion_sql % record.__dict__)
            except pymysql.MySQLError as e:
                errno, errstr = e.args
                if errno != 1146:
                    raise
                cur.close() # close current cursor
                cur = conn.cursor() # recreate it (is it mandatory?)
                try:            # try to recreate table
                    cur.execute(mySQLHandler.initial_sql)
            
                except pymysql.MySQLError as e:
                    # definitly can't work...
                    conn.rollback()
                    cur.close()
                    conn.close()
                    raise Exception(e)
                    exit(-1)
                else:   # if recreate log table is ok
                    conn.commit()                  
                    cur.close()
                    cur = conn.cursor()
                    cur.execute(sql)
                    conn.commit()
                    # then Exception vanished
                        
            except pymysql.MySQLError as e:
                conn.rollback()
                cur.close()
                conn.close()
                raise Exception(e)
                exit(-1)
            else:
                conn.commit()
            finally:
                cur.close()
                conn.close()
        except Exception as inst:
            print("mySQLHandler could not emit the log entry : \n" + str(record))
            raise inst
        
def main():
    def print_all_log(oLog):
        # Print all log levels
        oLog.debug('debug')
        oLog.info('info')
        oLog.warning('warning')
        oLog.error('error')
        oLog.critical('critical')
        try:
            raise ValueError("1+1=3")
        except ValueError as inst:
            oLog.exception(inst)
    
                
    logger = logging.getLogger('4120')
    logger.setLevel(logging.DEBUG)
        
    db = {'host': None, 'port': None, 'dbuser':None, 'dbpassword':None, 'dbname':None}
    
    sqlh = mySQLHandler(db)
    logger.addHandler(sqlh)
    # In main Thread
    print_all_log(logger)
    logger.debug(db)
    



if __name__ == '__main__':
    main()