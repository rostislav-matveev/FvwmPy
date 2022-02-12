import struct
import sys
import threading
import time
import fnmatch

from   .constants  import *
from   .exceptions import *
from   .log        import  _getloggers
from   .packet     import packet

################################################################################
### some helpers

################################################################################

class _packet_reader:
    
    def __init__(self,module):
        ### I have to do it here because I need module.alias
        ### _packet_reader will be instancieated once per module
        ### so it is ok.
        ( self.logger, self.dbg, self.info,
          self.warn,   self.err, self.crit  ) = _getloggers(
              module.alias+':packetreader')
        self.logger.setLevel(L_DEBUG)
        self._pipe            = module._fromfvwm
        self._queue           = list()
        self._queue_nonempty  = threading.Event()
        self._queue_lock      = threading.Lock()
        self._thread_exception = None
        self._reader_thread   = threading.Thread( target = self._reader,
                                                  name   = "reader_thread",
                                                  daemon = True            )
        self.dbg(" Start readerthread as daemon")
        self._reader_thread.start()


    ### This is the one to be threaded
    def _reader(self):
        while True:
            ### we want to pass any exception to the main thread
            ### but then there could be a delay in handling.
            ### What is a better solution?
            try:
                self.dbg("thread: Waiting for the packet")
                p = packet(self._pipe)
                self.dbg("thread: got {} at {}",p.name,p.time)
                ### for debug
                if p.ptype == M_STRING and p.string == "exc":
                    raise Exception
                self._queue_lock.acquire()
                self._queue.append(p)
                self._queue_nonempty.set()
            except PipeDesync as e:
                self.err("thread: {}",repr(e))
                self.err("thread: Resync the pipe. Packet(s) may be lost.")
                self.resync()
            except BaseException as e:
                self.err("thread: {}",repr(e))
                self.err("thread: pass to the main thread")
                self._thread_exception = e
            finally:
                if self._lockqueue.locked(): self._lockqueue.release()
            time.sleep(0.001)

    def read(self,blocking=True,keep=False):
        ### Let's see if something bad happened in the thread.
        self.raise_thread_exception()
        self.dbg( "main: queue size ={}",len(self._queue) )
        if not self._queue:
            self._queue_nonempty.clear()
            if blocking:
                self.dbg( "main: queue_nonempty={}, " +
                          "waiting for the threaded reader",
                          self._queue_nonempty.isSet())
                self._queue_nonempty.wait()
                self.dbg( "main: queue_nonempty={}, proceed",
                          self._queue_nonempty.isSet())
                self.dbg("main: threaded reader yielded something")
            else:
                ### there are no packets and we have to return
                self.dbg("main: queue is empty, returning None")
                return None
        
        ### here queue can not be empty unless exception happened in the thread
        self.raise_thread_exception()
        p = self._queue[0]
        if not keep:
            self._queue_lock.acquire()
            del self._queue[0]
            if not self._queue:
                self._queue_nonempty.clear()
            self._queue_lock.release()
        self.dbg( "main: Got a packet from the queue: {} at {}",p.name,p.time )
        return p

    def peek(self,blocking=True):
        return( self(blocking=blocking, keep=True) )

    def raise_thread_exception(self):
        if self._thread_exception:
            e = self._thread_exception
            self._thread_exception = None
            raise e

    def resync(self):
        found = False
        while not found:
            peek     = self._fromfvwm.peek()
            position = peek.find(FVWM_PACK_START_b)
            if position == -1:
                self._fromfvwm.read(len(peek))
            else:
                self._fromfvwm.read(position)
                found = True
            
    def __len__(self):
        return len(self._queue)

    def clear(self):
        self._queue_lock.acquire()
        self._queue.clear()
        self._queue_lock.release()
        
    def pick( self, picker, which="first", keep=False, timeout=500 ):
        start = 0
        ipacks = 0
        ### walk through the queue several times if necessary
        ### waiting for timeout before the second go
        time = 0
        tstep = 10
        while time <= timeout:
            self._queue_lock.acquire()
            iq = enumerate(self.queue[start:],start)
            ipacks += list(filter( lambda ip: picker(ip[1]), iq))
            ### for the second go
            start = len(self._queue)
            self._queue_lock.release()
            if ipack:
                ### found something
                break
            else:
                ### let's have another chance
                time += tstep
                time.sleep(tstep/1000)
        if not ipacks:
            ### There is nothing
            return tuple()
        if which == "first":
            i, p = ipacks[0]
            if not keep:
                self._queue_lock.acquire()
                del self._queue[i]
                if not self._queue: self._queue_nonempty.clear()
                self._queue_lock.release()
            return (p,)
        elif which == "last":
            i, p = ipacks[-1]
            if not keep:
                self._queue_lock.acquire()
                del self._queue[i]
                if not self._queue: self._queue_nonempty.clear()
                self._queue_lock.release()
            return (p,)
        elif which == "all":
            packs = tuple( (p for i,p in ipacks) )
            inds  = tuple( (i for i,p in ipacks) )
            if not keep:
                self._queue_lock.acquire()
                for i in reversed(inds):
                    del self._queue[i]
                if not self._queue: self._queue_nonempty.clear()
                self._queue_lock.release()
            return packs
        else:
            raise ValueError(
                "parameter `which` must be one of 'first', 'last' or 'all'" )

class picker:
    def __init__(self,fcn=None):
        if fcn is None: self.fcn = lambda p: True
        else:           self.fcn = fcn
        
    def __call__(self,p):
        return self.fcn(p)
    
    def __and__(self,other):
        def fcn(p):
            return self.fcn(p) and other.fcn(p)
        return picker(fcn)

    __rand__ = __and__
    
    def __or__(self,other):
        def fcn(p):
            return self.fcn(p) or other.fcn(p)
        return picker(fcn)

    __ror__ = __or__
    
    def __invert__(self):
        def fcn(p):
            return not self.fcn(p)
        return picker(fcn)
    

def picker_factory(mask=None,**kwargs):
    fcns = list()
    m = mask
    kw = kwargs.copy()
    def fcn(p):
        if m is not None:
            # print("Check {}=p['ptype'] ?= {}".format(bin(p.get("ptype")),bin(m)))
            if not bool(p["ptype"] & mask): return False
        for k,v in kw.items():
            # print("Check {}=p[{}] ?= {}".format(p.get(k),k,v))
            if isinstance(v,glob):
                if not ( k in p and fnmatch.fnmatch(p[k],v) ): return False
            else:
                if not ( k in p and p[k] == v ): return False
        return True
    return picker(fcn)

class glob(str):
    pass

################################################################################
# class box(dict):
    # pass
# p87abc=picker_factory(i=8,j=7,s=glob("abc*") )
# p89abc=picker_factory(i=8,j=9,s=glob("abc*") )
# pm=picker_factory(mask=3,i=8,j=9,s=glob("abc*") )
# x9=box(ptype = 1, i=8, j=9, s="abcd")
# x7=box(ptype = 1, i=8, j=7, s="abcd")
# y=box(ptype = 1, i=8, s="abcd")


