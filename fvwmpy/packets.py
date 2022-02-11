import struct
import sys
import threading
import time

from   .constants  import *
from   .exceptions import *
from   .log        import  _getloggers

################################################################################
### some helpers
### convert between our and FVWM packet types 
def _ptype_f2m(t):
    """Transform packet type from FVWM representation to fvwmpy 
    representation.
    """
    if not t & M_EXTENDED_MSG:
        return t
    else:
        return ( t & (M_EXTENDED_MSG - 1) ) << 32

def _ptype_m2f(t):
    """Transform packet type from fvwmpy representation to FVWM
    representation.
    """
    if t <= M_EXTENDED_MSG:
        return t
    else:
        return (t >> 32) | M_EXTENDED_MSG

### This is like struct.unpack_from() except returning value instead of
### a list of lenth 1
def _unpack(fmt,body,offset):
    x = struct.unpack_from(fmt,body,offset)
    return x[0] if len(x) == 1 else x

################################################################################

### _packet does the actual reading and parsing
class _packet(dict):
    """
    Instances are packets received from fvwm. 
 
    p = FvwmPacket(buf) 

    read the packet from buf. 
    Attributes can be equivallently accessed as p.key or p["key"].
    Attributes always present:
    p.ptype -- integer representing the type of the packet.
               See Fvwm.constants.M[X]_* for the types.
    p.name  -- string representation of the type of the packet.
    p.time  -- timestamp
    p.raw   -- bytearray containing the body of the packet withou the header
 
    Other attributes depend on the type of the packet. 
    """
    ( logger, dbg, info,
      warn,   err, crit  ) = _getloggers("fvwmpy:packet")
    logger.setLevel(L_ERROR)
    
    ### standard formats for reading packet fields
    ### list of pairs (<name_of_field>, <format>)
    ### formats can be anything acceptable to struct.unpack
    ### or "string" or "raw".
    ### There is another possibility
    ### (<name_of_field>, "list", <format>)
    ### In that case the value at that key will be a list of values,
    ### corresponding to format, that are read until input is exhosted.
    ### If the name of the field is an empty string, then the
    ### corresponding value is skipped over and not stored.
    ### If the name_of_field == "", then the value is skipped over.
    ### See vpacket.h in fvwm source tree and
    ### https://www.fvwm.org/Archive/ModuleInterface/
    
    ### Common parts
    ### window id -- 3 unsigned longs (last to ignore)
    _wid     = ( ("window","L"), ("frame", "L"), ("", "L") )
    ### These we get with M_[DE]ICONIFY packs
    _iconify = ( ("ix", "L"), ("iy", "L"),
                 ("idx", "L"), ("idy", "L"),
                 ("fx", "L"), ("fy", "L"),
                 ("fdx", "L"), ("fdy", "L") )
    ### empty packet
    _empty   = tuple()

    ### ignore 3 unsigned longs 
    _skip3L  = ( ("","L"), ("","L"), ("","L") )

    ### this formats are derived from vpacket.h in fvwm source tree
    ### We get this with M_(CONFIGURE|ADD)_WINDOW
    ### Consult fvwm source for the meaning of the flags
    _addwindow = ( _wid +
                   ( ( "wx", "l" ),
                     ( "wy", "l" ),
                     ( "wdx", "L" ),
                     ( "wdy", "L" ),
                     ( "desk", "L" ), 
                     ( "layer", "L" ), 
                     ( "hints_base_width", "L" ), 
                     ( "hints_base_height", "L" ), 
                     ( "hints_width_inc", "L" ), 
                     ( "hints_height_inc", "L" ), 
                     ( "orig_hints_width_inc", "L" ), 
                     ( "orig_hints_height_inc", "L" ), 
                     ( "hints_min_width", "L" ), 
                     ( "hints_min_height", "L" ), 
                     ( "hints_max_width", "L" ), 
                     ( "hints_max_height", "L" ), 
                     ( "icon_w", "L" ), 
                     ( "icon_pixmap_w", "L" ), 
                     ( "hints_win_gravity", "L" ), 
                     ( "text_pixel", "L" ), 
                     ( "back_pixel", "L" ), 
                     ( "ewmh_hint_layer", "L" ), 
                     ( "ewmh_hint_desktop", "L" ), 
                     ( "ewmh_window_type", "L" ), 
                     ( "title_height", "H" ), 
                     ( "border_width", "H" ), 
                     ( "", "H" ), ### Two short dummies 
                     ( "", "H" ),
                     ### consult fvwm source for the meaning of the flags
                     ( "flags", "raw") ) 
                    )
    
    _packetformats = {    
        M_NEW_PAGE:       ( ("px", "L"), ("py", "L"), ("desk", "L"),
                            ("max_x", "L"), ("max_y", "L"), ("nx", "L"),
                            ("ny", "L") ),
        M_NEW_DESK:       ( ("desk", "L"), ),
        M_OLD_ADD_WINDOW: ( ("body", "raw"), ),
        M_RAISE_WINDOW:   _wid,
        M_LOWER_WINDOW:   _wid,
        M_OLD_CONFIGURE_WINDOW:
                          ( ("body", "raw"), ),
        M_FOCUS_CHANGE:   ( ("window", "L"), ("frame", "L"),
                            ("focus_change_type", "L"), ("text_pix", "L"),
                            ("border_pix", "L") ),
        M_DESTROY_WINDOW: _wid,
        M_ICONIFY:        _wid + _iconify,
        M_DEICONIFY:      _wid + _iconify,
        M_WINDOW_NAME:    _wid + ( ("win_name", "string"), ),
        M_ICON_NAME:      _wid + ( ("ico_name", "string"), ),
        M_RES_CLASS:      _wid + ( ("res_class", "string"), ),
        M_RES_NAME:       _wid + ( ("res_name", "string"), ),
        M_END_WINDOWLIST: _empty,
        M_ICON_LOCATION:  _wid + ( ("ix", "L"), ("iy", "L"),
                                  ("idx", "L"), ("idy", "L") ),
        M_MAP:            _wid,
        M_ERROR:          _skip3L + ( ("string", "string"), ), 
        M_CONFIG_INFO:    _skip3L + ( ("string", "string"), ),
        M_END_CONFIG_INFO: _empty,
        M_ICON_FILE:      _wid + ( ("ico_filename", "string"), ),
        M_DEFAULTICON:    ( ("ico_defaultfilename", "string"), ),
        M_STRING:         _wid + ( ("string", "string"), ),
        M_MINI_ICON:      _wid + ( ("mini_ico_dx", "L"), ("mini_ico_dy", "L"),
                                  ("mini_ico_depth", "L"), ("winid_pix", "L"),
                                  ("winid_mask", "L"),
                                  ("mini_ico_filename", "string") ),
        M_WINDOWSHADE:    _wid,
        M_DEWINDOWSHADE:  _wid,
        M_VISIBLE_NAME:   _wid + ( ("win_vis_name", "string"), ),
        M_SENDCONFIG:     ( ("string", "string"), ),
        M_RESTACK:        ( ( "win_stack", "listof", "3L" ), ),
        M_ADD_WINDOW:     _addwindow,
        M_CONFIGURE_WINDOW: _addwindow,
        M_EXTENDED_MSG:   ( ("body", "raw"), ),

        MX_VISIBLE_ICON_NAME:
                          _wid + ( ("ico_vis_name", "string"), ),
        MX_ENTER_WINDOW:  _wid,
        MX_LEAVE_WINDOW:  _wid,
        MX_PROPERTY_CHANGE:
                          ( ("prop_type", "L"), ("val_1", "L"), ("val_2", "L"),
                            ("prop_str", "string") ),
        MX_REPLY:         _wid + ( ("string", "string"), ),
        M_UNKNOWN1:        ( ("body", "raw"), )
        }

    def __init__(self,buf):
        try:
            (start,ptype,size,time) = struct.unpack_from(
                "4L", buf.read(LONG_SIZE*4), 0 )
        except struct.error:
            raise PipeDesync("Can not read the head of the packet")
        if start != FVWM_PACK_START:
            raise PipeDesync(
                "Expected {}, got {} at the beginning of the packet".
                format(hex(FVWM_PACK_START),hex(start)) )
        
        self.ptype = _ptype_f2m(ptype)
        self.time  = time
        self.info("Read {} at {}",packetnames[self.ptype],self.time)
        ### Read and parse the rest of the packet according to the format
        ### corresponding to the type of the packet
        body = buf.read(LONG_SIZE * (size-4))
        self.raw = body
        fmt = self._packetformats[self.ptype]
        offset = 0
        for field in fmt:
            self.dbg("field",field)
            self.dbg("offset",offset)
            if field[1] == "string":
                self[field[0]] = ( body[offset:].
                                   decode(errors='replace').
                                   strip("\x00") )
                offset = len(body)
                break
            elif field[1] == "raw":
                self[field[0]] = body[offset:]
                offset = len(body)
                break
            elif field[1] == "listof":
                self[field[0]] = list()
                itemsize = struct.calcsize(field[2])
                while offset + itemsize <= len(body):
                    self[field[0]].append(_unpack(field[2],body,offset)) 
                    offset += itemsize
                if offset != len(body):
                    raise PipeDesync(
                        """While parsing packet {}:
                        Format doesn't match the body of the packet 
                        (while reading 'listof' format)
                        """.format(packetnames[self.ptype]))
            else:
                try:
                    self[field[0]] = _unpack(field[1], body, offset)
                except struct.error:
                    raise PipeDesync(
                        """While parsing packet {}:
                        Format doesn't match the body of the packet 
                        (body of the packet is too short)
                        """.format(packetnames[self.ptype]))
                offset += struct.calcsize( field[1] )
            ### There are variable length packs with optional fields at
            ### the end, like M_ICONIFY, so we break if the body of the pack
            ### is exhosted.
            if offset == len(body): break
        if offset != len(body):
            raise PipeDesync("Format doesn't match the body of the\
            packet (body of the packet is too long")
        ### remove dummies
        if "" in self: del self[""]


    @property
    def name(self):
        return packetnames[self.ptype]
    
    def __getattr__(self,attr):
        return self[attr]

    def __setattr__(self,attr,val):
        self[attr] = val

    def __delattr__(self,attr):
        del self[attr]

    def clean(self):
        del self["raw"]
        return self
    
    def __str__(self):
        res = list()
        res.append( "Fvwm Packet: {} at {}".format(self.name,self.time) )
        for k,v in self.items():
            if k in {"raw", "time"}: continue
            res.append("\t| {} = {}".format(k,v))
        return "\n".join(res)


class _packet_reader:
    ( logger, dbg, info,
      warn,   err, crit  ) = _getloggers("fvwmpy:packetreader")
    logger.setLevel(L_ERROR)

    def __init__(self,module):
        self._pipe         = module._fromfvwm
        self._queue        = list()
        self._lockread     = threading.Lock()
        self._lockqueue    = threading.Lock()
        self._readerthread = threading.Thread( target=self._reader )
        self.dbg(" Start readerthread")
        self._readerthread.start()

    def _reader(self):
        ### ToDo I need to handle PipeDesync here!
        while True:
            self._lockread.acquire()
            self.dbg("thread: Waiting for the packet")
            p = _packet(self._pipe)
            self.dbg("thread: got {} at {}",p.name,p.time)
            self._lockqueue.acquire()
            self._queue.append(p)
            self._lockqueue.release()
            self._lockread.release()
            ### Let's give a bit of time to the reader in the main thread
            time.sleep(0.001)

    def read(self,blocking=True,keep=False):
        if not self._queue:
            self.dbg("main: queue is empty")
            if blocking:
                self.dbg("main: waiting for the threaded reader")
                self._lockread.acquire()
                self._lockread.release()
                self.dbg("main: threaded reader yielded something")
            else:
                ### there are no packets and we have to return
                self.dbg("main: returning None")
                return None
        ### here queue can not be empty
        p = self._queue[0]
        if not keep:
            self._lockqueue.acquire()
            del self._queue[0]
            self._lockread.release()
        self.dbg(
            "main: there is a packet in the queue: {} at {}",p.name,p.time )
        return p

    def resync(self):
        self.warn(
            " Resync the from-fvwm pipe. Package(s) may be lost.")
        found = False
        while not found:
            peek     = self._fromfvwm.peek()
            position = peek.find(FVWM_PACK_START_b)
            if position == -1:
                self._fromfvwm.read(len(peek))
            else:
                self._fromfvwm.read(position)
                found = True
                
    def peek(self,blocking=True):
        return( self(blocking=blocking, keep=True) )
    
    def __len__(self):
        return len(self._queue)

    def clear(self):
        self._lockqueue.acquire()
        self._queue.clear()
        self._lockqueue.release()
        
    def pick( self, picker, which="first", keep=False, timeout=500 ):
        start = 0
        ipacks = 0
        ### walk through the queue twice if necessary
        ### waiting for timeout before the second go
        for i in range(2):
            self._lockqueue.acquire()
            iq = enumerate(self.queue[start:],start)
            ipacks += list(filter( lambda ip: picker(ip[1]), iq))
            ### for the second go
            start = len(self._queue)
            self._lockqueue.release()
            if ipack:
                ### found something
                break
            else:
                ### let's have another chance
                time.sleep(timeout/1000)
        if not ipacks:
            ### There is nothing
            return tuple()
        if which == "first":
            i, p = ipacks[0]
            if not keep:
                self._lockqueue.acquire()
                del self._queue[i]
                self._lockqueue.release()
            return (p,)
        elif which == "last":
            i, p = ipacks[-1]
            if not keep:
                self._lockqueue.acquire()
                del self._queue[i]
                self._lockqueue.release()
            return (p,)
        elif which == "all":
            if not keep:
                self._lockqueue.acquire()
                for i,p in ipacks:
                    del self._queue[i]
                self._lockqueue.release()
            return tuple( (p for i,p in ipacks) )
        else:
            raise ValueError(
                "which must be one of 'first', 'last' or 'all'" )
