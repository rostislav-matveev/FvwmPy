import fnmatch

################################################################################
### some helpers
# from .log import _getloggers
# from .constants import *
# ( logger, debug, info,
  # warn,   error, critical  ) = _getloggers('fvwmpy:picker')
# logger.setLevel(L_WARN)
################################################################################

class picker:
    def __init__(self, fcn=None, mask=None, **kwargs):
        if fcn is None:
            self.fcn = self._picker_factory(mask,**kwargs)
            _str = list()
            if mask:
                _str.append("mask=0x{:x}".format(mask))
            for k,v in kwargs.items():
                _str.append("{}={}".format(k,v))
            self._str="picker(" + ",".join(_str) + ")"
        elif mask is None and not kwargs:
            self.fcn = fcn
            self._str= "picker({})".format(fcn)
        else:
            raise ValueError( "Wrong arguments signature. "+
                              "Must be either picker(fcn=fcn) or " +
                              "picker(mask=mask,**kwargs)" )
        
    def __str__(self):
        return self._str

    __repr__ = __str__
    
    def __call__(self,p):
        return self.fcn(p)
    
    def __and__(self,other):
        def fcn(p):
            return self.fcn(p) and other.fcn(p)
        pick = picker(fcn=fcn)
        pick._str = "(" + self._str + " & " + other._str + ")"
        return pick

    __rand__ = __and__
    
    def __or__(self,other):
        def fcn(p):
            return self.fcn(p) or other.fcn(p)
        pick = picker(fcn=fcn)
        pick._str = "(" + self._str + " | " + other._str + ")"
        return pick

    __ror__ = __or__
    
    def __invert__(self):
        def fcn(p):
            return not self.fcn(p)
        pick = picker(fcn=fcn)
        pick._str = "~" + self._str
        return pick


    @classmethod
    def _picker_factory(cls, mask=None,**kwargs):
        def fcn(p):
            debug("picker_fcn: working")
            if ( (mask is not None) and
                 (not p["ptype"] & mask) ):
                # debug("Check {}=p['ptype'] ?= {}",
                      # bin(p.get("ptype")),bin(mask))
                return False
            for k,v in kwargs.items():
                # debug("Check {}=p[{}] ?= {}",p.get(k),k,v)
                if not ( k in p and p[k] == v ): return False
            return True
        return fcn

class glob(str):
    """Instance of glob is a string considered as a glob pattern.
    It may contain '*' and '?' characters and '[chars]' substrings.
    Pattern '[chars]' may also contain ranges like '[a-z0-9]'.
    '*' matches any substring, '?' matches any single character. 
    '[chars]' matches any sigle character which is one of 'chars'. 
    To match '*', '?', literally, use the corresponding character
    enclosed in '[]'. Check the documentation of the fnmatch package
    for more details.

    When glob instance is compared to another string with '==' or '!=' 
    operator, it checks whether another string matches the glob pattern. 
    Matching is case insensitive.

    E.g. "abc*efg?xyz" == glob("*c[*]EFg[?]x??") returns true.
    """

    def __str__(self):
        return "glob('{}')".format(super().__str__())
    
    __repr__ = __str__

    def __eq__(self,other):
        return fnmatch.fnmatchcase(other.lower(),self.lower())
    
    def __ne__(self,other):
        return not self.__eq__(other)

class Glob(str):
    """Instance of glob is a string considered as a glob pattern.
    It may contain '*' and '?' characters and '[chars]' substrings.
    Patterns '[chars]' may also contain ranges like '[a-z]'.
    '*' matches any substring, '?' matches any single character.
    '[chars]' matches any sigle character which is one of 'chars'. 
    To match '*', '?', literally, use the corresponding character
    enclosed in '[]'.

    When glob instance is compared to another string with '==' or '!=' 
    operator, it checks whether another string matches the glob pattern. 
    Matching is case sensitive.

    E.g. "abc*Efg?xyz" == Glob("*c[*]Efg[?]x??") returns true.
    """

    def __str__(self):
        return "Glob('{}')".format(super().__str__())
    
    __repr__ = __str__

    def __eq__(self,other):
        return fnmatch.fnmatchcase(str.__str__(other),str.__str__(self))
    
    def __ne__(self,other):
        return not self.__eq__(other)
