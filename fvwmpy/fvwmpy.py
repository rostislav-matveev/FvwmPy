import os as _os
import sys as _sys
import struct as _struct

from   .constants  import *
from   .packets    import _packet_reader
from   .exceptions import *
from   .log        import _getloggers

################################################################################
### Some helpers
def split_mask(mask):
    "Returns a list of all packet types matching the mask"
    masks = list()
    cmask = 1
    while mask:
        if 1 & mask: masks.append(cmask)
        mask  >>= 1
        cmask <<= 1
    return masks


VERSION = "1.0.1"

################################################################################

class _fvwmvar:
    """
    var = _fvwmvar(module)
    Class for objects that provide access to FVWM variables.
    """

    _sep = " CrazySplitDelimiter3.1415 "
    def __init__(self,module):
        super().__setattr__("_module",module)
        
    def __getattr__(self,var):
        self._module.push_masks(MX_REPLY | M_ERROR, 0, 0)
        vardots  = var.replace("_",".")
        try:
            self._module.sendmessage("Send_Reply $[{}]".format(vardots))
            p = self._module.packet.read()
            if p.ptype == M_ERROR:
                self._module.err("var: {}",p.string)
                raise FvwmError(p.string)
        finally:
            self._module.restore_masks()
        return p.string

    def __setattr__(self,var,val):
        raise IllegalOperation("It is not possible to assign to Fvwm variables")

    def __delattr__(self,var):
        raise IllegalOperation("It is not possible to delete Fvwm variables")

    def __call__(self, *args,context_window=None):
        self._module.push_masks(MX_REPLY | M_ERROR, 0, 0)
        vardots = ["$[{}]".format(x.replace("_",".")) for x in args]
        varline = self._sep.join(vardots)
        try:
            self._module.sendmessage(
                "Send_Reply " + varline, context_window = context_window )
            p = self._module.packet.read()
            if p.ptype == M_ERROR:
                self._module.err("var: {}",p.string)
                raise FvwmError(p.string)
        finally:
            self._module.restore_masks()
        return(p.string.split(self._sep))
        
class _infostore:
    _sep = "CrazySplitDelimiter3.1415"
    def __init__(self,module):
        super().__setattr__("_module",module)
        
    def __getattr__(self,var):
        self._module.push_masks(MX_REPLY | M_ERROR, 0, 0)
        vardots  = var.replace("_",".")
        try:
            self._module.sendmessage("Send_Reply $[infostore.{}]".
                                     format(vardots))
            p = self._module.packet.read()
            if p.ptype == M_ERROR:
                self._module.err("infostore: {}", p.string)
                raise FvwmError(p.string)
        finally:
            self._module.restore_masks()
        return p.string

    def __setattr__(self,var,val):
        vardots  = var.replace("_",".")
        self._module.sendmessage("InfoStoreAdd {} ' {}'".
                                 format(vardots, str(val)))

    def __delattr__(self,var):
        vardots  = var.replace("_",".")
        self._module.sendmessage("InfoStoreRemove {}".format(vardots))

    def __call__(self, *args,context_window=None):
        self._module.push_masks(MX_REPLY | M_ERROR, 0, 0)
        vardots = [ "$[infostore.{}]".format(x.replace("_","."))
                    for x in args ]
        varline = self._sep.join(vardots)
        try:
            self._module.sendmessage(
                "Send_Reply " + varline, context_window = context_window )
            p = self._module.packet.read()
            if p.ptype == M_ERROR:
                self._module.err("infostore: {}",p.string)
                raise FvwmError(p.string)
        finally:
            self._module.restore_masks()
        return(p.string.split(self._sep))
 
class _window(dict):
    """Instances of _window class are dictionaries
    containing key:value pairs corresponding to the fields in 
    M_CONFIGURE_WINDOW packet and other window packets, see
    fvwmpy.constants.M_FOR_WINLIST constant.
    Besides they contain additional values sent by fvwm during
    reply to SendWindowList message. It has an additional method
    w.flag(int: i), that gives the value of i^th flag, see 
    file vpacket.h in fvwm source tree for the meaning of the flags.
    The __str__ method gives some human readable representation of the 
    instance of the _window class.

    ToDo: Access flags by meaningfull names.
    """

    def __getattr__(self,attr):
        return self[attr]

    def __setattr__(self,attr,val):
        self[attr] = val

    def flag(self,i):
        """
        Get i^th flag as a 0/1 integer
        """
        b,s = divmod(i,8)
        return self.flags[b] & ( 1 << s )

    def __str__(self):
        string = "Fvwm Window: {}\n ".format(self["window"])
        for k,v in self.items():
            string += "\t| {} = {}\n".format(k,v)
        return string

    
class _winlist(dict):
    """Dictionary of all windows indexed by window id's  

    Additional method .filter(conditions) gives
    iterators over windows satisfying conditions, where conditions is a 
    string of conditions acceptable in FVWM's conditional commands. 
    """
    def __init__(self,module):
        super().__init__()
        super().__setattr__("_module",module)
        
    def filter(self,conditions):
        self._module.push_masks(M_STRING|M_ERROR,0,0)
        cl = conditions.splitlines()
        cl = map(lambda x: x.strip(" \t,"),cl)
        cl = filter(None, cl)
        cond = ",".join(cl)
        self._module.dbg( " Use condition {}",cond)
        self._module.sendmessage(
            "All ({}) SendToModule {} $[w.id]".
            format(cond, self._module.alias), context_window = 0 )
        self._module.sendmessage(
            "SendToModule {} finishedfilterwindows".
            format(self._module.alias), context_window = 0  )
        filteredlist = list()
        try:
            p = self._module.packet.read()
            self._module.dbg( "Got {}",p.string )
            while p.ptype & M_STRING and p.string.startswith("0x"):
                filteredlist.append( int(p.string,0) )
                p = self._module.packet.read()
                self._module.dbg( "Got {}",p.string )
            if p.ptype & M_ERROR:
                self._module.err("winlist: {}",p.string)
                raise FvwmError(p.string)
        finally:
            self._module.restore_masks()

        ### Shall we just return a list of windows?
        ### Perhaps we just want to count them?
        for wid in filteredlist:
            yield self[wid]


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
        self.me     = _os.path.split(_sys.argv[0])[1]
        if len(_sys.argv) < 6:
            raise FvwmLaunch("{}: Should only be executed by fvwm!".
                             format(self.alias))
        try:
            self._tofvwm     = _os.fdopen(int(_sys.argv[1]), "wb")
            self._fromfvwm   = _os.fdopen(int(_sys.argv[2]), "rb")
        except:
            raise FvwmLaunch("{}: Can not open read/write pipes".
                             format(self.alias))
        self.context_window = int(_sys.argv[4],0)
        self.context_deco   = int(_sys.argv[5],0);
        if _sys.argv[6:]:
            if not _sys.argv[6].startswith('-'):
                self._alias = _sys.argv[6]
                self.args =  _sys.argv[7:]
            elif _sys.argv[6] == '-':
                self.args =  _sys.argv[7:]
            else:
                self.args =  _sys.argv[6:]
        else:
            self.args = list()

        ( self.logger, self.dbg, self.info,
          self.warn,   self.err, self.crit  ) = _getloggers(self.alias)
        self.logginglevel = L_INFO

        self.handlers     = { pack : [] for pack in packetnames }
        ### We have to do that because mask.setter assumes 
        ### that _mask already exists.
        self._mask        = -1
        self._syncmask    = -1
        self._nograbmask  = -1
        self.mask         = 0
        self.syncmask     = 0
        self.nograbmask   = 0
        self._mask_stack  = list()
        self.winlist      = _winlist(self)
        self.config       = _config()
        self.var          = _fvwmvar(self)
        self.infostore    = _infostore(self)
        self.packet       = _packet_reader(self)
        
    @property
    def alias(self):
        try:
            return self._alias
        except AttributeError:
            return self.me

    @property
    def logginglevel(self):
        return self.logger.level

    @logginglevel.setter
    def logginglevel(self,val):
        self.logger.setLevel(val)
            
    def sendmessage(self,msg, context_window=None, finished=False):
        """Send a possibly multiline string to fvwm using window context.
        If context_window==None, use self.context_window
        If finished, notify FVWM the the module has finished working and 
        will exit soon.
        """
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
        "Temporarily assign new values to masks"
        if mask       is None: mask       = self.mask
        if syncmask   is None: syncmask   = self.syncmask
        if nograbmask is None: nograbmask = self.nograbmask
        self._mask_stack.append( (self.mask,self.syncmask,self.nograbmask) )
        self.mask, self.syncmask, self.nograbmask = (
            mask, syncmask, nograbmask ) 
        
    def restore_masks(self):
        "Restore previous values of masks"
        try:
           self.mask, self.syncmask, self.nograbmask = self._mask_stack.pop() 
        except IndexError:
            raise IllegalOperation(
                "Can not restore masks. Mask stack is empty" )
        
    def getconfig(self, handler=None, match=None):
        """Ask FVWM for module configuration information matching match 
        ('*'+alias if mask==None).
        Pass the reply packets to handler (h_saveconfig if handler==None)
        """
        self.push_masks( M_FOR_CONFIG | M_ERROR, 0, 0)
        if handler is None: handler = self.h_saveconfig
        if match   is None: match   = "*" + self.alias
        if handler is self.h_saveconfig:
            self.config = _config()
        self.sendmessage("Send_ConfigInfo {}".format(match))
        try:
            p = self.packet.read()
            while not p.ptype & (M_ERROR | M_END_CONFIG_INFO):
                handler(p)
                p = self.packet.read()
            if p.ptype & M_ERROR:
                self.err("getconfig: {}",p.string)
                raise FvwmError(p.string)
        finally:
            self.restore_masks()
            
    def getwinlist(self, handler = None):
        """Ask FVWM for the list of all windows.
        Pass replies to handler (h_updatewl if handler==None)
        """
        self.push_masks( M_FOR_WINLIST | M_ERROR, 0, 0 )
        if handler is None: handler = self.h_updatewl
        if handler is self.h_updatewl: self.winlist.clear()
        self.sendmessage("Send_WindowList")
        try:
            p = self.packet.read()
            while not p.ptype & (M_ERROR | M_END_WINDOWLIST):
                handler(p)
                p = self.packet.read()
            if p.ptype & M_ERROR:
                self.err("getwinlist: {}",p.string)
                raise FvwmError(p.string)
        finally:
            self.restore_masks()

    def register_handler(self,mask,handler):
        """Add handler to the end of execution queues for all packets 
        matching mask.
        """
        for m in self.handlers:
            if (m & mask) and not (handler in self.handlers[m]):
                self.handlers[m].append(handler)

    def unregister_handler(self,mask,handler):
        """Remove handler from all execution queues for packets matching 
        masks. If handler is not in a queue, do nothing.
        """
        for m in self.handlers:
            if (m & mask):
                try:
                    self.handlers[m].remove(handler)
                except ValueError:
                    continue

    def call_handlers(self,p):
        """Execute all handlers in the queue for the packet p in the order 
        they were registered.
        """
        for h in self.handlers[p.ptype]:
            h(p)
        
    def clear_handlers(self,mask):
        """Clear all queues for packets matching mask."""
        for h in self.handlers[p.ptype]:
            if h & mask:
                self.handlers[p.ptype] = list()
         
    def registered_handler(self,handler):
        """Return the mask matching all packet types for which handler 
        is registered.
        """
        mask = 0
        for m in self.handlers:
            if handler in self.handlers[m]:
                mask |= m
        return mask
    
            
    ### HANDLERS
    def h_saveconfig(self,p):
        """Handler. Packet types: M_FOR_CONFIG.

        This handler simply stores the information in the packet in the 
        config database.
        If packet p has other type IllegalOperation exception is raised.
        """
        if p.ptype == M_END_CONFIG_INFO: return
        if not p.ptype & M_FOR_CONFIG:
            raise IllegalOperation(
                "Packet must have type matching M_FOR_CONFIG" )
        cl = p.string.lower()
        if cl.startswith("*"):
            ### We append p.string and not cl bacause config lines may
            ### be case sensetive.
            self.config.append(p.string)
        elif cl.startswith("colorset"):
            ### ToDo: parse colorsets
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
            IllegalOperation("Can not parse the packet: {}".format(p.string))
            
    def h_unlock(self, p):
        """Handler. Packet types: M_ALL.

        This handler sends 'NOP UNLOCK' command to FVWM. It should be added to 
        the end of queues for packets in syncmask.
        """
        self.unlock()
        
    ### Update winlist
    def h_updatewl(self,p):
        """Handler. Packet types: M_FOR_WINLIST | M_DESTROY_WINDOW

        This handler updates the winlist database with the information in the 
        packet p.
        """
        if not p.ptype & M_FOR_WINLIST | M_DESTROY_WINDOW:
            raise IllegalOperation(
                "Packet must have type matching M_FOR_WINLIST or M_DESTROY_WINDOW" )
        if p.ptype == M_DESTROY_WINDOW:
            try:
                del self.winlist[p.window]
            except KeyError():
                pass
        else:
            if p.window not in self.winlist:
                self.winlist[p.window] = _window()
        self.winlist[p.window].update(p)

    def h_exit(self,p):
        """Handler. Packtet types: M_ALL.

        Exit the module.
        """
        self.exit()

    def run(self):
        """Mainloop.

        Read packets and execute corresponding handlers. If PipeDesync 
        exception is raised, try to resync the pipe and go on.
        """
        self.dbg(" Start main loop")
        while True:
            try:
                p = self.packet.read()
                self.call_handlers(p)
            except PipeDesync as e:
                self.warn(" Pipe desyncronised: {}".e.args)
                self.warn(" Trying to resync the pipe. Some packets may be lost")
                self.resync()
