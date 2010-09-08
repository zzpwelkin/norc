
"""General logging utilities."""

import os
import sys
import datetime
import traceback

try:
    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
except ImportError:
    pass

from norc.settings import (LOGGING_DEBUG, NORC_LOG_DIR, LOG_BACKUP_SYSTEM,
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME)

def timestamp():
    """Returns a string timestamp of the current time."""
    now = datetime.datetime.utcnow()
    return now.strftime('%Y/%m/%d %H:%M:%S') + '.%06d' % now.microsecond

class AbstractLog(object):
    """Abstract class for creating a text log."""
    
    INFO = 'INFO'
    ERROR = 'ERROR'
    DEBUG = 'DEBUG'
    
    @staticmethod
    def format(msg, prefix):
        """The format of all log messages."""
        return '[%s] %s: %s\n' % (timestamp(), prefix, msg)
    
    def __init__(self, debug):
        """Initialize a Log object.
        
        If debug is not given, it defaults to the
        LOGGING_DEBUG setting of Norc.
        
        """
        self.debug_on = debug if debug != None else LOGGING_DEBUG
    
    def info(self, msg):
        """Log some informational message."""
        raise NotImplementedError
    
    def error(self, msg, trace):
        """Log about an error that occurred, with optional stack trace."""
        raise NotImplementedError
    
    def debug(self, msg):
        """Message for debugging purposes; only log if debug is true."""
        raise NotImplementedError
    

class Log(AbstractLog):
    """Implementation of Log that sends logs to a file."""
    
    def __init__(self, path=None, debug=None, echo=False):
        """ Parameters:
        
        path    Path to the file that all output should go in.
                Defaults to sys.stdout if no string is given.
        debug   Boolean; whether debug output should be logged.
        echo    Echoes all logging to stdout if True.
        
        """
        AbstractLog.__init__(self, debug)
        if path:
            if not os.path.isdir(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            self.out = self.err = open(path, 'a')
        else:
            self.out = sys.stdout
            self.err = sys.stderr
        self.path = path    
        self.echo = echo
    
    def _write(self, stream, msg, format_prefix):
        if format_prefix:
            msg = Log.format(msg, format_prefix)
        stream.write(msg)
        stream.flush()
        if self.echo:
            print >>sys.__stdout__, msg,
    
    def info(self, msg, format=True):
        self._write(self.out, msg, Log.INFO if format else False)
    
    def error(self, msg, trace=False, format=True):
        self._write(self.err, msg, Log.ERROR if format else False)
        if trace:
            self._write(self.err, traceback.format_exc(), False)
    
    def debug(self, msg, format=True):
        if self.debug_on:
            self._write(self.out, msg, Log.DEBUG if format else False)
    
    def start_redirect(self):
        """Redirect all stdout and stderr to this log's files."""
        sys.stdout = self.out
        sys.stderr = self.err
    
    def stop_redirect(self):
        """Restore stdout and stderr to their original values."""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
    
    def close(self):
        if self.out.name != '<stdout>':
            self.out.close()
        if self.err.name != '<stderr>' and self.err.name != '<stdout>':
            self.err.close()
    

class NorcLog(Log):
    
    def __init__(self, norc_path=None, *args, **kwargs):
        path = os.path.join(NORC_LOG_DIR, norc_path)
        Log.__init__(self, path, *args, **kwargs)
        self.norc_path = norc_path
    

class S3Log(NorcLog):
    """Outputs logs to S3 in addition to a local file."""
    
    @staticmethod
    def make_s3_key(path):
        c = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        b = c.get_bucket(AWS_BUCKET_NAME)
        if not b:
            b = c.create_bucket(AWS_BUCKET_NAME)
        k = Key(b)
        k.key = 'norc_logs/' + path
        return k
    
    def __init__(self, norc_path, *args, **kwargs):
        NorcLog.__init__(self, norc_path, *args, **kwargs)
        try:
            self.key = S3Log.make_s3_key(norc_path)
        except:
            traceback.print_exc()
            self._write(self.out, 'Error making S3 key.\n', False)
    
    def close(self):
        self.out.flush()
        if hasattr(self, 'key'):
            try:
                self.key.set_contents_from_filename(self.path)
            except:
                self.error('Unable to push log file to S3:\n', trace=True)
        NorcLog.close(self)

BACKUP_LOGS = {
    'AmazonS3': S3Log,
}

def make_log(norc_path, *args, **kwargs):
    """Make a log object with a subpath of the norc log directory."""
    log_class = BACKUP_LOGS.get(LOG_BACKUP_SYSTEM, NorcLog)
    return log_class(norc_path, *args, **kwargs)
