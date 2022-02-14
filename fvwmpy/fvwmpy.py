import os as _os
import sys as _sys
import struct as _struct
import time as _time

from   .constants     import *
from   .packet_reader import *
from   .packet_reader import _packet_reader
from   .packet        import packet
from   .exceptions    import *
from   .log           import _getloggers
from   .picker        import picker, glob, Glob

################################################################################
### Some helpers
def split_mask(mask):
    "Returns a list of all packet types matching the given mask"
    masks = list()
    cmask = 1
    while mask:
        if 1 & mask: masks.append(cmask)
        mask  >>= 1
        cmask <<= 1
    return masks

class _unique_id:
    uid = int(_time.perf_counter()*1000000000)
    def __call__(self,fmt="unique_id_0x{:x}"):
        self.uid += 1
        return fmt.format(self.uid)

unique_id =  _unique_id()

VERSION = "1.0.1"

################################################################################

class _fvwmvar:
    """
    Class for objects that provide access to FVWM variables.
    
    var.<name_of_var>

    returns value of the FVWM  variable in the same window context that
    the module was initiated.
    In the <name_of_var> underscores have to be used in place of dots 
    in the FVWM's names. The return value of the variable is always a 
    string. Attempts to assign to or delete FVWM variables result in
    IllegalOperation exception.

    var("<name_of_var1>","<name_of_var2>",...,context_window = None) 
    
    return a tuple of values of variables. In this invocation method it is 
    not necessary, (but is allowed) to replace dots with underscores in 
    variable names.
    context_window is id of the window in which context variable are to be 
    expanded. If None the the module's context window is assumed.
    If 0 no context is assumed.
    E.g. provided that window with id equal cwid exists

    var("w.name","pointer.wx","pointer_wy",context_window=cwid) 

    will return the name of the window, and x- and y-coordinates of the 
    pointer within window (as a triple of strings).
    The return value is always a tuple (of strings), even if the number of 
    arguments is not greater then one.

    If a variable with the given name does not exist
    literal string '$[<name.of.var>]' is returned in either access
    methods. 
    """

    _sep = "CrazySplitDelimiter3.1415"
    def __init__(self,module):
        super().__setattr__("_module",module)
        
    def __getattr__(self,var):
        vardots  = "$[{}]".format(var.replace("_","."))
        return self._module.getreply(vardots)

    def __setattr__(self,var,val):
        raise IllegalOperation("It is not possible to assign to Fvwm variables")

    def __delattr__(self,var):
        raise IllegalOperation("It is not possible to delete Fvwm variables")

    def __call__(self, *args,context_window=None):
        vardots = ["$[{}]".format(x.replace("_",".")) for x in args]
        varline = self._sep.join(vardots)
        reply = self._module.getreply(varline, context_window=context_window)
        values= reply.split(self._sep)
        if len(values) != len(args):
            raise FvwmError("fvwmvar: Something is wrong, "+
                            "more answers then questions or vice versa.",
                            values,args)
        return(values)
        
class _infostore:
    """An instance of _infostore class provide access to FVWM's
    infostore database.

    infostore.<name_of_var>
    infostore.<name_of_var> = val
    del infostore.<name_of_var>

    returns value, assigns and deletes the FVWM infostore variable.
    In the <name_of_var> underscores have to be used in place of dots 
    in the FVWM's names. The return value of the variable is always a 
    string.

    infostore("<name_of_var1>","<name_of_var2>",...) 
    
    return a tuple of values of variables. In this invocation method it is 
    necessary, (but is allowed) to replace dots with underscores in variable 
    names.
    The return value is always a tuple (of strings), even if the number of 
    arguments is not greater then one.

    If a variable with the given anme is absent from the FVWM's infostore 
    database, literal string '$[infostore.<name.of.var>]' is returned in 
    either access method. 
    """
    
    _sep = "|CrazySplitDelimiter3.1415|"
    def __init__(self,module):
        super().__setattr__("_module",module)
        
    def __getattr__(self,var):
        vardots  = "$[infostore.{}]".format(var.replace("_","."))
        return self._module.getreply(vardots)

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
        reply = self._module.getreply(varline).split(self._sep)
        if len(reply) != len(args):
            raise FvwmError("infostore: Something is wrong, "+
                            "more answers then questions or vice versa.",
                            str(reply),str(args))
        return(reply)
 
class _window(dict):
    """Instances of _window class are dictionaries
    containing key:value pairs corresponding to the fields in 
    M_CONFIGURE_WINDOW packet and other window packets, see
    fvwmpy.constants.M_FOR_WINLIST constant.
    Besides they contain additional values sent by fvwm during
    reply to Send_WindowList message. It has an additional method
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
        """Get the i^th flag of the window as a 0/1 integer
        """
        b,s = divmod(i,8)
        return self.flags[b] & ( 1 << s )

    def __str__(self):
        res = list()
        res.append("Fvwm Window: 0x{:x}".format(self["window"]) )
        for k,v in self.items():
            if k in {"window","frame"}:
                res.append("  | {} = 0x{:x}".format(k,v))
            else:
                res.append("  | {} = {}".format(k,v))
        return "\n".join(res)
    
    
class _winlist(dict):
    """Dictionary of all windows indexed by window id's  

    Additional method .filter(conditions) gives an
    iterators over windows satisfying conditions, where conditions is a 
    string of conditions acceptable to FVWM's conditional commands and 
    have the same meaning.
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
        self._module.debug( " Use condition {}",cond)
        self._module.sendmessage(
            "All ({}) SendToModule {} $[w.id]".
            format(cond, self._module.alias), context_window = 0 )
        self._module.sendmessage(
            "SendToModule {} finishedfilterwindows".
            format(self._module.alias), context_window = 0  )
        filteredlist = list()
        try:
            p = self._module.packets.read()
            self._module.debug( "Got {}",p.string )
            while p.ptype & M_STRING and p.string.startswith("0x"):
                filteredlist.append( int(p.string,0) )
                p = self._module.packets.read()
                self._module.debug( "Got {}",p.string )
            if p.ptype & M_ERROR:
                self._module.error("winlist: {}",p.string)
                raise FvwmError(p.string)
        finally:
            self._module.restore_masks()
                   
        ### Shall we just return a list of windows?
        ### Perhaps we just want to count them?
        for wid in filteredlist:
            yield self[wid]

    def __str__(self):
        res=list()
        for w in self.values():
            res.append(str(w))
        return "\n\n".join(res)

class _config(list):
    _max_colorsets = int("0x40",16)
    def __init__(self):
        self.DesktopSize  = (None, None)
        self.ImagePath = tuple()
        self.XineramaConfig = tuple()
        self.ClickTime = None
        self.IgnoreModifiers = tuple()
        self.colorsets = [None for i in range(self._max_colorsets)]

    def __str__(self):
        res = list()
        res.append("FVWM configuartion database")
        res.append("  DesktopSize = {}".format(self.DesktopSize))
        res.append("  ImagePath = {}".format(self.ImagePath))
        res.append("  XineramaConfig = {}".format(self.XineramaConfig))
        res.append("  ClickTime = {}".format(self.ClickTime))
        res.append("  IgnoreModifiers = {}".format(self.IgnoreModifiers))
        res.append("  colorsets:")
        for i, c in enumerate(self.colorsets):
            res.append("    {:x} = {}".format(i,c))
        res.append("  module(s) configuration:")
        for cl in self:
            res.append("    "+cl)
        return "\n".join(res)
        
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

        ( self.logger, self.debug, self.info,
          self.warn,   self.error, self.critical  ) = _getloggers(self.alias)
        self.logger.setLevel(L_WARN)

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
        self.packets      = _packet_reader(self)
        
    @property
    def alias(self):
        try:
            return self._alias
        except AttributeError:
            return self.me

    def sendmessage_hook(self,msg,context_window,finished):
        pass
    
    def sendmessage(self,msg, context_window=None, finished=False):
        """Send a possibly multiline string to fvwm using in context 
        window_context.
        If context_window==None, use context window in which module was 
        invoked. If context_window==0, use no context.
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
            self.debug(" Send message {}",l)
        if finished :
            self._tofvwm.write(b''.join( (cw,
                                          _struct.pack("L",3),
                                          b'NOP',
                                          FINISHED) ) )
        self._tofvwm.flush()
        self.sendmessage_hook(msg, context_window, finished)
        
    def finishedstartup(self):
        self.debug("FINISHED STARTUP")
        self.sendmessage("NOP FINISHED STARTUP")
        
    def exit(self,n=0):
        self.unlock(finished=True)
        self._tofvwm.close()
        self._fromfvwm.close()
        self.info(" Exit")
        _sys.exit(n)

    def unlock(self,finished=False):
        self.sendmessage("NOP UNLOCK",finished)

    def mask_setter_hook(self, mask_type, m):
        pass
        
    @property
    def mask(self):
        return self._mask
 
    @mask.setter
    def mask(self,m):
        if self._mask == m: return
        self._mask = m
        ml = self._mask & ( M_EXTENDED_MSG - 1 )
        mu = (self._mask >> 32) | M_EXTENDED_MSG
        self.sendmessage("SET_MASK {}\nSET_MASK {}".format(ml,mu))
        self.mask_setter_hook("mask",m)

    @property
    def syncmask(self):
        return self._syncmask

    @syncmask.setter
    def syncmask(self,m):
        if self._syncmask == m: return
        self._syncmask = m 
        ml = self._syncmask & ( M_EXTENDED_MSG - 1 )
        mu = (self._syncmask >> 32) | M_EXTENDED_MSG
        self.sendmessage("SET_SYNC_MASK {}\nSET_SYNC_MASK {}".format(ml,mu))
        self.mask_setter_hook("syncmask",m)
        
    @property
    def nograbmask(self):
        return self._nograbmask

    @nograbmask.setter
    def nograbmask(self,m):
        if self._nograbmask == m: return
        self._nograbmask = m
        ml = self._nograbmask & ( M_EXTENDED_MSG - 1 )
        mu = (self._nograbmask >> 32) | M_EXTENDED_MSG
        self.sendmessage( "SET_NOGRAB_MASK {}\nSET_NOGRAB_MASK {}".
                          format(ml,mu))
        self.mask_setter_hook("syncmask",m)

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

    def getreply(self,msg,context_window=None):
        if context_window is None:
            context_window = self.context_window
        uid = unique_id()
        self.push_masks(self.mask|MX_REPLY,0,0)
        try:
            self.sendmessage( "Send_Reply {}{}".format(uid,msg),
                              context_window = context_window)
            replypicker = picker(mask = MX_REPLY,string =Glob(uid+"*") )
            passes = 10
            delay  = 0.1
            for i in range(passes):
                packs = self.packets.pick(picker = replypicker,
                                          which  = "last",
                                          keep   = False )
                self.info("getreply: pass {}, got {} reply packets",i,len(packs))
                if packs:
                    break
                elif i < passes-1:
                    self.info( "getreply: FVWM seems to be slow, " +
                               "I will try again")
                    time.sleep(delay)
        finally:
            self.restore_masks()
        if len(packs) > 1:
           self.warn( "getreply: get more then one reply, "+
                      "return the last one")
        elif not packs:
            self.warn( "getreply: didn't get any reply, return None")
            return
        else:
            return packs[-1].string.replace(uid,"")

    def getconfig(self, handler=None, match=None):
        """Ask FVWM for module configuration information.
        ('*'+alias if mask==None).
        Pass the reply packets to handler (h_saveconfig if handler==None)
        """

        if match is None: match   = "*" + self.alias
        ### Ask first
        self.push_masks(self.mask|M_FOR_CONFIG,0,0)
        try:
            self.sendmessage("Send_ConfigInfo {}".format(match))
            if handler is None:
                handler = self.h_saveconfig
                self.info("getconfig: standard handler")
                self.config    = _config()
                self.rawconfig = list()

            confpicker = picker(mask = M_FOR_CONFIG)
            packs = list()
            passes = 10
            delay  = 0.1
            for i in range(passes):
                packs += self.packets.pick( picker = confpicker,
                                            which  = "all",
                                            keep   = False )
                self.info( "getconfig: pass {}, got {} " +
                           "config packets",i,len(packs))
                if packs and packs[-1].ptype & M_END_CONFIG_INFO:
                    break
                elif i < passes-1:
                    self.info( "getconfig: FVWM seems to be slow, " +
                           "I will try again")
                    time.sleep(delay)
                else:
                    self.warn( "getconfig: didn't get M_END_CONFIG_INFO packet")
        finally:
            self.restore_masks()
        for p in packs:
            handler(p)
            
    def getwinlist(self, handler = None):
        """Ask FVWM for the list of all windows.
        Pass replies to handler (h_updatewl if handler==None)
        """
        ### Ask FVWM first
        self.push_masks(self.mask|M_FOR_WINLIST,0,0)
        try:
            self.sendmessage("Send_WindowList")
            if handler is None:
                handler = self.h_updatewl
                self.winlist.clear()

            wlpicker = picker(mask = M_FOR_WINLIST)
            packs = list()
            passes = 10
            delay  = 0.1
            for i in range(passes):
                packs += self.packets.pick( picker = wlpicker,
                                            which  = "all",
                                            keep   = False)
                self.info( "getwinlist: pass {}, got {} winlist packets",
                           i,len(packs))
                if packs and any((p.ptype & M_END_WINDOWLIST for p in packs)):
                    break
                elif i < passes-1:
                    self.info( "getwinlist: FVWM seems to be slow, " +
                               "I will try again")
                    time.sleep(0.1)
                else:
                    self.warn( "getwinlist: didn't get M_END_WINLIST packet")
        finally:
            self.restore_masks()
        for p in packs:
            handler(p)

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
        """Execute all handlers in the queue for the packet p passing p as an 
        argument in the order they were registered.
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
        If packet p has wrong type IllegalOperation exception is raised.
        """
        if p.ptype == M_END_CONFIG_INFO: return
        if not p.ptype & M_FOR_CONFIG:
            raise IllegalOperation(
                "h_saveconfig: Packet must have type matching M_FOR_CONFIG" )
        ### FVWM is not consistent. Some strings have '\n' at the end.
        p.string = p.string.strip()
        ### For debugging DON'T FORGET!!!
        # self.rawconfig.append(p.string)
        
        if p.string == glob("[*]*"):
            self.config.append(p.string)
        elif p.string == glob("colorset *"):
            ### ToDo: parse colorsets
            cll = p.string.split()
            self.config.colorsets[int(cll[1],16)]=cll[2:]
        elif p.string == glob("desktopsize *"):
            cll = p.string.split()
            self.config.DesktopSize = ( int(cll[1]), int(cll[2]) )
        elif p.string == glob("imagepath *"):
            paths =  p.string.split()[1].strip().split(":")
            self.config.ImagePath   = tuple(paths)
        elif p.string == glob("xineramaconfig *"):
            cll = p.string.split()[1:]
            self.config.XineramaConfig = tuple(map(int,cll))
        elif p.string == glob("clicktime *"):
            self.config.ClickTime = int(p.string.split()[1])
        elif p.string == glob("ignoremodifiers *"):
            cll = p.string.split()[1:]
            self.config.IgnoreModifiers = tuple(map(int, cll))
        else:
            FvwmError("Can not parse the packet: {}".format(p.string))
            
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
        if p.ptype & M_END_WINDOWLIST: return
        if not p.ptype & M_FOR_WINLIST | M_DESTROY_WINDOW:
            raise IllegalOperation(
                "h_updatewl: Packet must have type matching " +
                "M_FOR_WINLIST or M_DESTROY_WINDOW" )
        if p.ptype == M_DESTROY_WINDOW:
            try:               del self.winlist[p.window]
            except KeyError(): pass
        else:
            if p.window not in self.winlist:
                self.winlist[p.window] = _window()
            up = dict(p)
            for key in {"body","ptype","time"}:
                try:             del up[key]
                except KeyError: pass
            self.winlist[p.window].update(up)

    def h_exit(self,p):
        """Handler. Packet types: M_ALL.

        Exit the module.
        """
        self.exit()

    def h_nop(self,p):
        pass

    h_pass = h_nop
    
    def run(self):
        """Mainloop.
        Read packets and execute corresponding handlers. 
        """
        self.debug(" Start main loop")
        while True:
            p = self.packets.read()
            self.call_handlers(p)
            


    
