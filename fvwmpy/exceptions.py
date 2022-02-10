class FvwmPyException(Exception):
    """
    Base exception for fvwmpy
    """
    pass

class NoException(FvwmPyException): pass

class FvwmLaunch(FvwmPyException):
    """
    fvwm module should only be executed by fvwm!
    """
    pass

class PipeDesync(FvwmPyException):
    """ 
    Indicates that packet from Fvwm can not be read or
    parsed, probably because some pipe desyncronization.
    """
    pass

class IllegalOperation(FvwmPyException):
    """ 
    Indicates that some illegal action was attempted
    like assigning to Fvwm variable.
    """
    pass
