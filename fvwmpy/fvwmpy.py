import os as _os
import sys as _sys
import struct as _struct
import logging as _logging

from .constants  import *
from .packets    import _packet
from .exceptions import *

################################################################################
### Some helpers
def split_mask(mask):
    masks = list()
    cmask = 1
    while mask:
        if 1 & mask: masks.append(cmask)
        mask  >>= 1
        cmask <<= 1
    return masks

class _BraceString(str):
    def __mod__(self, other):
        return self.format(*other)
    def __str__(self):
        return self


class _StyleAdapter(_logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        super(_StyleAdapter, self).__init__(logger, extra)

    def process(self, msg, kwargs):
        msg = _BraceString(msg)
        return msg, kwargs
    
_logging.basicConfig(stream=_sys.stderr)

DEBUGLEVEL = _logging.DEBUG
_l   = _StyleAdapter(_logging.getLogger("fvwmpy"))
_l.setLevel(LOGGINGLEVEL)
dbg  = _l.debug
info = _l.info
warn = _l.warning
err  = _l.error
crit = _l.critical

VERSION = "0.0.1"

################################################################################

class _fvwmvar:
    _sep = " CrazySplitDelimiter3.1415 "
    def __init__(self,module):
        super().__setattr__("_module",module)
        
    def __getattr__(self,var):
        vardots  = var.replace("_",".")
        savemask       = self._module.mask
        savesyncmask   = self._module.syncmask
        savenograbmask = self._module.nograbmask
        self._module.mask       = MX_REPLY | M_ERROR
        self._module.syncmask   = 0
        self._module.nograbmask = 0
        self._module.sendmessage("Send_Reply $[{}]".format(vardots))
        p = self._module.packet()
        self._module.mask       = savemask
        self._module.syncmask   = savesyncmask
        self._module.nograbmask = savenograbmask
        if p.ptype == M_ERROR:
            self._module.warn(" An error occured: {}",p["string"])
            return None
        return p["string"]

    def __setattr__(self,var,val):
        raise IllegalOperation("It is not possible to assign to Fvwm variables")

    def __delattr__(self,var):
        raise IllegalOperation("It is not possible to delete Fvwm variables")

    def __call__(self, *args,context_window=None):
        vardots = ["$[{}]".format(x.replace("_",".")) for x in args]
        varline = self._sep.join(vardots)
        savemask       = self._module.mask
        savesyncmask   = self._module.syncmask
        savenograbmask = self._module.nograbmask
        self._module.mask       = MX_REPLY | M_ERROR
        self._module.syncmask   = 0
        self._module.nograbmask = 0
        self._module.sendmessage("Send_Reply " + varline,
                                 context_window = context_window)
        p = self._module.packet()
        self._module.mask       = savemask
        self._module.syncmask   = savesyncmask
        self._module.nograbmask = savenograbmask
        if p.ptype == M_ERROR:
            warn(" An error occured: {}",p["string"])
            return [ None for a in args ]
        return(p["string"].split(self._sep))
        
class _infostore:
    _sep = "CrazySplitDelimiter3.1415"
    def __init__(self,module):
        super().__setattr__("_module",module)
        
    def __getattr__(self,var):
        vardots  = var.replace("_",".")
        savemask       = self._module.mask
        savesyncmask   = self._module.syncmask
        savenograbmask = self._module.nograbmask
        self._module.mask       = MX_REPLY | M_ERROR
        self._module.syncmask   = 0
        self._module.nograbmask = 0
        self._module.sendmessage("Send_Reply $[infostore.{}]".
                                 format(vardots))
        p = self._module.packet()
        self._module.mask       = savemask
        self._module.syncmask   = savesyncmask
        self._module.nograbmask = savenograbmask
        if p.ptype == M_ERROR:
            warn("An error occured: {}",p["string"])
            return None
        return p["string"]

    def __setattr__(self,var,val):
        vardots  = var.replace("_",".")
        self._module.sendmessage("InfoStoreAdd {} ' {}'".
                                 format(vardots, str(val)))

    def __delattr__(self,var):
        vardots  = var.replace("_",".")
        self._module.sendmessage("InfoStoreRemove {}".format(vardots))

    def __call__(self, *args,context_window=None):
        vardots = [ "$[infostore.{}]".format(x.replace("_","."))
                    for x in args ]
        varline = self._sep.join(vardots)
        savemask       = self._module.mask
        savesyncmask   = self._module.syncmask
        savenograbmask = self._module.nograbmask
        self._module.mask       = MX_REPLY | M_ERROR
        self._module.syncmask   = 0
        self._module.nograbmask = 0
        self._module.sendmessage("Send_Reply " + varline,
                                 context_window = context_window)
        p = self._module.packet()
        self._module.mask       = savemask
        self._module.syncmask   = savesyncmask
        self._module.nograbmask = savenograbmask
        if p.ptype == M_ERROR:
            warn(" An error occured: {}",p["string"])
            return None
        return(p["string"].split(self._sep))
        
        

class _window(dict):
    """Instances of _window class are dictionaries
    containing key:value pairs corresponding to the fields in 
    M_CONFIGURE_WINDOW packet and other window packets, see
    fvwmpy.constants.M_FOR_WINLIST constant.
    Besides they contain additional values sent by fvwm during
    reply to SendWindowList message. It has an additional method
    w.flag(int: i), that gives the value of i^th flag, see 
    file vpacket.h in fvwm source tree for the meaning of the flags.
    ToDo: Access flags by meaningfull names.
    """

    def __getattr__(self,attr):
        return self[attr]

    def __setattr__(self,attr,val):
        self[attr] = val

    def flag(self,i):
        """
        Get i^th flag
        """
        b,s = divmod(i,8)
        return self.flags[b] & ( 1 << s )

    def __str__(self):
        string = "Fvwm Window: {}\n ".format(self["window"])
        for k,v in self.items():
            string += "\t| {} = {}\n".format(k,v)
        return string

    
class _winlist(dict):
    """List of all windows.  

    Additional method .filter(conditions) gives
    iterators over windows satisfying conditions.  

    ToDo: Implement all the conditions available in Fvwm conditional
    commands.

    Currently implemented conditions are 
    None
    """
    def __init__(self,module):
        super().__init__()
        super().__setattr__("_module",module)
        
    def filter(self,conditions):
        self._module.push_masks(M_STRING,0,0)
        cl = conditions.splitlines()
        cl = map(lambda x: x.strip(" \t,"),cl)
        cl = filter(None, cl)
        cond = ",".join(cl)
        self._module.dbg( " Use condition {}",cond)
        self._module.sendmessage(
            "All ({}) SendToModule {} $[w.id]".format(cond,
                                                      self._module.alias) )
        self._module.sendmessage(
            "SendToModule {} finishedfilterwindows".
            format(self._module.alias) )
        filteredlist = list()
        p = self._module.packet()
        self._module.dbg( "Got {}",p.string )
        while p.string.startswith("0x"):
            filteredlist.append( int(p.string,0) )
            p = self._module.packet()
            self._module.dbg( "Got {}",p.string )
        for wid in filteredlist:
            yield self[wid]
        self._module.restore_masks()

class _config(list):
    _max_colorsets = int("0x40",16)
    def __init__(self):
        self.DesktopSize  = (None, None)
        self.ImagePath = tuple()
        self.XineramaConfig = tuple()
        self.ClickTime = None
        self.IgnoreModifiers = tuple()
        self.colorsets = [None for i in range(self._max_colorsets)]
 
class fvwmpy:
    """Base class for developing Fvwm modules"""
   
    def __init__(self):
        self.config       = _config()
        self.me     = _os.path.split(_sys.argv[0])[1]
        self.logger = _StyleAdapter(_logging.getLogger(self.alias))
        self.logger.setLevel(LOGGINGLEVEL)
        self.dbg    = self.logger.debug
        self.info   = self.logger.info
        self.warn   = self.logger.warning
        self.err    = self.logger.error
        self.crit   = self.logger.critical
        # self.dbg(" Starting...")
        if len(_sys.argv) < 6:
            raise FvwmLaunch("{}: Should only be executed by fvwm!".
                             format(self.me))
        # self.dbg(" Arguments: {}",_sys.argv)
        try:
            self._tofvwm     = _os.fdopen(int(_sys.argv[1]), "wb")
            self._fromfvwm   = _os.fdopen(int(_sys.argv[2]), "rb")
        except:
            raise FvwmLaunch("{}: Can not open read/write pipes".
                             format(self.me))
        self.dbg(" Opened pipes")
        self.context_window = int(_sys.argv[4],0)
        self.context_deco   = int(_sys.argv[5],0);
        if _sys.argv[6:]:
            if not _sys.argv[6].startswith('-'):
                self.alias = _sys.argv[6]
                self.args =  _sys.argv[7:]
            elif _sys.argv[6] == '-':
                self.args =  _sys.argv[7:]
            else:
                self.args =  _sys.argv[6:]
        else:
            self.args = list()
        self.handlers     = { pack : [] for pack in packetnames }
        ### 
        self._mask        = -1
        self._syncmask    = -1
        self._nograbmask  = -1
        self.mask        = 0
        self.syncmask    = 0
        self.nograbmask  = 0
        self.mask_stack  = list()
        self.winlist     = _winlist(self)
        self.var         = _fvwmvar(self)
        self.infostore   = _infostore(self)
        
    @property
    def alias(self):
        try:
            return self._alias
        except AttributeError:
            return self.me

    @alias.setter
    def alias(self,val):
        del self.crit, self.err, self.warn, self.info, self.dbg, self.logger
        self._alias = val
        self.logger = _StyleAdapter(_logging.getLogger(self.alias))
        self.dbg    = self.logger.debug
        self.info   = self.logger.info
        self.warn   = self.logger.warning
        self.err    = self.logger.error
        self.crit   = self.logger.critical
        ### How do I let FVWM know, that I should be known by my alias,
        ### e.g for SendToModule command?
    
    def sendmessage(self,msg, context_window=None, finished=False):
        "Send a string(s) to fvwm using window context"
        if context_window is None:
            context_window = self.context_window
        lines = map( lambda x: x.strip(), msg.splitlines() )
        lines = filter(None,lines)
        lines = tuple(map(lambda l: l.encode(FVWM_STR_CODEX), lines))
        cw   = _struct.pack("L",context_window)
        for l in lines :
            self._tofvwm.write( b''.join( (cw,
                                           _struct.pack("L",len(l)),
                                           l,
                                           NOT_FINISHED) ) )
            self.dbg(" Send message {}",l)
        if finished :
            self._tofvwm.write(b''.join( (cw,
                                          _struct.pack("L",3),
                                          b'NOP',
                                          FINISHED) ) )
        self._tofvwm.flush()
        
    def packet(self, parse=True, raw=False):
        """
        M.packet(parse=True, raw=False)

        Return a dictionary with two additional attributes:
           p.ptype  -- the type of the packet
           p.time   --- the time stamp
        Obtained by reading fvwm packet from the pipe, 
        parse(?)ing it and writing the content into appropriate fields. 
        And adding raw(?) content to the "raw" field.
        """
        return _packet(self._fromfvwm, parse=parse, raw=raw)

    def resync(self):
        self.warn(" Resync the from-fvwm pipe. Package(s) may be lost.")
        found = False
        while not found:
            peek     = self._fromfvwm.peek()
            position = peek.find(FVWM_PACK_START_b)
            if position == -1:
                self._fromfvwm.read(len(peek))
            else:
                self._fromfvwm.read(position)
                found = True
            
    def finishedstartup(self):
        self.dbg("FINISHED STARTUP")
        self.sendmessage("NOP FINISHED STARTUP")
        
    def exit(self,n=0):
        self.unlock(finished=True)
        self._tofvwm.close()
        self._fromfvwm.close()
        self.dbg(" Exit")
        _sys.exit(n)

    def unlock(self,finished=False):
        self.sendmessage("NOP UNLOCK",finished)

    def _mask_set(self,m):
        ### To save on communication with Fvwm
        if self._mask == m: return
        self._mask = m
        ###split the mask and send separately
        ml = self._mask & ( M_EXTENDED_MSG - 1 )
        mu = (self._mask >> 32) | M_EXTENDED_MSG
        self.sendmessage("SET_MASK {}\nSET_MASK {}".format(ml,mu))
        
    @property
    def mask(self):
        return self._mask
 
    @mask.setter
    def mask(self,m):
        self._mask_set(m)

    def _syncmask_set(self,m):
        ### To save on communication with Fvwm
        if self._syncmask == m: return
        self._syncmask = m 
        ###split the mask and send separately
        ml = self._syncmask & ( M_EXTENDED_MSG - 1 )
        mu = (self._syncmask >> 32) | M_EXTENDED_MSG
        self.sendmessage("SET_SYNC_MASK {}\nSET_SYNC_MASK {}".format(ml,mu))
        
    @property
    def syncmask(self):
        return self._syncmask

    @syncmask.setter
    def syncmask(self,m):
        self._syncmask_set(m)

    def _nograbmask_set(self,m):
        ### To save on communication with Fvwm
        if self._nograbmask == m: return
        self._nograbmask = m
        ###split the mask and send separately
        ml = self._nograbmask & ( M_EXTENDED_MSG - 1 )
        mu = (self._nograbmask >> 32) | M_EXTENDED_MSG
        self.sendmessage("SET_NOGRAB_MASK {}\nSET_NOGRAB_MASK {}".
                         format(ml,mu))

        
    @property
    def nograbmask(self):
        return self._nograbmask

    @nograbmask.setter
    def nograbmask(self,m):
        self._nograbmask_set(m)

    def push_masks(self,mask,syncmask,nograbmask):
        if mask       is None: mask       = self.mask
        if syncmask   is None: syncmask   = self.syncmask
        if nograbmask is None: nograbmask = self.nograbmask
        self.mask_stack.append( (self.mask,self.syncmask,self.nograbmask) )
        self.mask       = mask
        self.syncmask   = syncmask
        self.nograbmask = nograbmask
        
    def restore_masks(self):
        try:
           self.mask, self.syncmask, self.nograbmask = self.mask_stack.pop() 
        except IndexError:
            raise IllegalOperation(
                "Can not restore masks. Mask stack is empty" )
        
    def getconfig(self, handler=None, match=None):
        self.push_masks( M_FOR_CONFIG | M_ERROR, 0, 0)
        if handler is None:
            handler = self.h_saveconfig
        if match is None:
            match = "*" + self.alias
        if handler == self.h_saveconfig:
            ### reset the config database
            self.config = _config()
        try:
            self.sendmessage("Send_ConfigInfo {}".format(match))            
            while True:
                p = self.packet()
                handler(p)
                if p.ptype == M_END_CONFIG_INFO: break
        except Exception as e:
            raise e
        finally:
            ### restore masks
            self.restore_masks()
            
    def getwinlist(self, handler = None):
        self.push_masks( M_FOR_WINLIST | M_ERROR, 0, 0 )
        if handler is None:
            handler = self.h_updatewl
        self.winlist.clear()
        try:
            self.sendmessage("Send_WindowList")
            while True:
                p = self.packet()
                handler(p)
                if p.ptype == M_END_WINDOWLIST : break
        except Exception as e:
            raise e
        finally:
            self.restore_masks()

    def register_handler(self,mask,handler):
        for m in self.handlers:
            if (m & mask) and not (handler in self.handlers[m]):
                self.handlers[m].append(handler)

    def unregister_handler(self,mask,handler):
        for m in self.handlers:
            if (m & mask):
                try:
                    self.handlers[m].remove(handler)
                except ValueError:
                    continue

    def call_handlers(self,p):
        for h in self.handlers[p.ptype]:
            h(p)
        return p
        
    def clear_handlers(self,mask):
        for h in self.handlers[p.ptype]:
            if h & mask:
                self.handlers[p.ptype] = list()
         
    def registered_handler(self,handler):
        mask = 0
        for m in self.handlers:
            if handler in self.handlers[m]:
                mask |= m
        return mask
    
            
    ### HANDLERS
    def h_saveconfig(self,p):
        if p.ptype == M_END_CONFIG_INFO: return
        cl = p["string"].lower()
        if cl.startswith("*"):
            self.config.append(p["string"])
        elif cl.startswith("colorset"):
            ### ToDo: parse
            cll = cl.split()
            self.config.colorsets[int(cll[1],16)]=cll[2:]
        elif cl.startswith("desktopsize"):
            cll = cl.split()
            self.config.DesktopSize = ( int(cll[1]), int(cll[2]) )
        elif cl.startswith("imagepath"):
            cll = cl.split(" ")[1].split(":")
            self.config.ImagePath   = tuple(cll)
        elif cl.startswith("xineramaconfig"):
            cll = cl.split()[1:]
            self.config.XineramaConfig = tuple([int(x) for x in cll])
        elif cl.startswith("clicktime"):
            self.config.ClickTime = int(cl.split()[1])
        elif cl.startswith("ignoremodifiers"):
            cll = cl.split()[1:]
            self.config.IgnoreModifiers = tuple([int(x) for x in cll])
        else:
            IllegalOperation("Can not parse the packet")
            
    def h_unlock(self, p):
        self.unlock()
        
    ### Update winlist
    def h_updatewl(self,p):
        if not p.ptype & M_FOR_WINLIST & ~M_END_WINDOWLIST: return
        if p.ptype == M_DESTROY_WINDOW:
            try:
                del self.winlist[ p["window"] ]
            except KeyError():
                pass
            return
        if p["window"] not in self.winlist:
            self.winlist[ p["window"] ] = _window()
        self.winlist[ p["window"] ].update(p)

    def h_exit(self,p):
        self.exit()

    def run(self):
        self.dbg(" Start main loop")
        while True:
            try:
                p = self.packet()
                self.call_handlers(p)
            except PipeDesync as e:
                self.warn(" Pipe desyncronised: {}".e.args)
                self.warn(" Trying to resync the pipe. Some packets may be lost")
                self.resync()
            
