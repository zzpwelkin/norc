
""" Norc-specific constants.

Any constants required for the core execution of Norc
should be defined here if possible.

"""

# The maximum number of tasks an Executor is allowed to run at once.
CONCURRENCY_LIMIT = 4

# How often a scheduler can poll the database for new schedules.
SCHEDULER_PERIOD = 5

# How many new schedules the scheduler can pull from the database at once.
SCHEDULER_LIMIT = 10000

EXECUTOR_PERIOD = 0.5

# A list of all Task implementations.
TASK_MODELS = [] # NOTE: This is dynamically generated by MetaTask.

# A list of all AbstractInstance implementations.
INSTANCE_MODELS = [] # NOTE: This is dynamically generated by MetaInstance.

# How often hearts should beat, in seconds.
HEARTBEAT_PERIOD = 3

# How long a heart can go without beating before being considered failed.
# This has serious implications for how long before an error in the system
# is caught.  If the number is too small, though, a slow database could
# cause failsafes to activate erroneously.
HEARTBEAT_FAILED = HEARTBEAT_PERIOD + 20


class MetaConstant(type):
    """Generates the NAMES attribute of the Status class."""
    
    def __new__(cls, name, bases, dct):
        """Magical function to dynamically create NAMES and ALL."""
        NAMES = {}
        ALL = []
        for k, v in dct.iteritems():
            if type(v) == int:
                assert not v in NAMES, "Can't have duplicate values."
                NAMES[v] = k
                ALL.append(v)
        dct['NAMES'] = NAMES
        dct['ALL'] = ALL
        return type.__new__(cls, name, bases, dct)
    
    def name(cls, item):
        return cls.NAMES.get(item)

class Status(object):
    """Class to hold all status constants.
    
    The MetaStatus class automatically generates a NAMES attribute which
    contains the reverse dict for retrieving a status name from its value.
    
    The numbers should probably be moved further apart, but SUCCESS being
    7 and FAILURE being 13 just seems so fitting...
    
    """
    __metaclass__ = MetaConstant
    
    # Transitive states.
    CREATED = 1         # Created but nothing else.
    RUNNING = 2         # Is currently running.
    PAUSED = 3          # Currently paused.
    STOPPING = 4        # In the process of stopping; should become ENDED.
    
    # Final states.
    SUCCESS = 7         # Succeeded.
    ENDED = 8           # Ended gracefully.
    KILLED = 9          # Forcefully killed.
    HANDLED = 12        # Was ERROR, but the problem's been handled.
    
    # Failure states.
    FAILURE = 13        # User defined failure (Task returned False).
    ERROR = 14          # There was an error during execution.
    TIMEDOUT = 15       # The execution timed out.
    INTERRUPTED = 16    # Execution was interrupted before completion.
    OVERFLOW = 17       # The task overflowed its memory limit.
    
    @staticmethod
    def is_final(status):
        """Whether the given status counts as final."""
        return status >= 7
    
    @staticmethod
    def is_failure(status):
        """Whether the given status counts as a failure."""
        return status >= 13
    
    @staticmethod
    def GROUPS(name):
        """Used for accessing groups of Statuses by a string name."""
        return {
            "active": filter(lambda s: s < 7, Status.ALL),
            "running": [Status.RUNNING],
            "succeeded": filter(lambda s: s >= 7 and s < 13, Status.ALL),
            "failed": filter(lambda s: s >= 13, Status.ALL),
            "final": filter(lambda s: s >= 7, Status.ALL),
        }.get(name.lower())
    

class Request(object):
    """"""
    
    __metaclass__ = MetaConstant
    
    # Requests to change to a final state.
    STOP = 1
    KILL = 2
    
    # Other features.
    PAUSE = 7
    RESUME = 8
    RELOAD = 9
    
    
