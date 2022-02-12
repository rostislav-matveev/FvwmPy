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
( logger, debug, info,
  warn,   error, critical  ) = _getloggers(':PacketReader')
logger.setLevel(L_DEBUG)
################################################################################

class _packet_reader:
    
    def __init__(self,module):
        ### I have to do it here because I need module.alias
        ### _packet_reader will be instancieated once per module
        ### so it is ok.
        ( self.logger, self.debug, self.info,
          self.warn,   self.error, self.critical  ) = _getloggers(
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
        self.debug(" Start readerthread as daemon")
        self._reader_thread.start()


    ### This is the one to be threaded
    def _reader(self):
        while True:
            ### we want to pass any exception to the main thread
            ### but then there could be a delay in handling.
            ### What is a better solution?
            try:
                p = packet(self._pipe)
                # self.debug("thread: got {} at {}",p.name,p.time)
                ### for debug DON'T FORGET!!!
                if p.ptype == M_STRING and p.string == "exception":
                    raise Exception
                self._queue_lock.acquire()
                self._queue.append(p)
                self._queue_nonempty.set()
            except PipeDesync as e:
                self.error("thread: {}",repr(e))
                self.error("thread: Resync the pipe. Packet(s) may be lost.")
                self.resync()
            except BaseException as e:
                self.error("thread: {}",repr(e))
                self.error("thread: pass to the main thread")
                self._thread_exception = e
                ### release self._queue_nonempty.wait() in the main thread
                ### main mast now check for non empty queue
                self._queue_nonempty.set()
            finally:
                if self._queue_lock.locked(): self._queue_lock.release()
            ### Slow it down for debugging. DON'T FORGET!
            time.sleep(0.001)

    def read(self,blocking=True,keep=False):
        ### Let's see if something bad happened in the thread.
        self.raise_thread_exception()
        self.debug( "main: queue size={}; queue_nonempty={}",
                    len(self._queue),
                    self._queue_nonempty.isSet() )
        if blocking:
            self._queue_nonempty.wait()
            self.raise_thread_exception()
        elif not self._queue:
            ### there are no packets and we have to return
            self.debug("main: queue is empty, returning None")
            return None
        
        ### here queue can not be empty unless exception happened in
        ### the thread, which we have reraised
        p = self._queue[0]
        self.debug( "main:   got {} at {}", p.name,p.time )
        if not keep:
            self._queue_lock.acquire()
            del self._queue[0]
            if not self._queue:
                self._queue_nonempty.clear()
            self._queue_lock.release()
        return p

    def peek(self,blocking=True):
        return( self(blocking=blocking, keep=True) )

    def raise_thread_exception(self):
        if self._thread_exception:
            e = self._thread_exception
            self._thread_exception = None
            ### thread sets nonempty lock for the main thread to proceed
            ### we have to clear it, if necessary
            if not self._queue:
                self._queue_nonempty.clear()
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
        ipacks = list()
        ### walk through the queue, if  nothing found
        ### then wait and check the rest of the queue repeatedly
        t = 0
        tstep = 10
        while t <= timeout:
            self._queue_lock.acquire()
            iq = enumerate(self._queue[start:],start)
            # ipacks += list(filter( lambda ip: picker(ip[1]), iq))
            ### for debug DONT FORGET!!!
            for i, p in iq:
                if picker(p): ipacks.append((i,p))
            ### for the next go
            start = len(self._queue)
            self._queue_lock.release()
            if ipacks:
                ### found something
                break
            else:
                ### let's have another chance
                t += tstep
                time.sleep(tstep/1000)
        if not ipacks:
            ### There is nothing
            return tuple()
        if which == "first":
            i, p = ipacks[0]
            # self.debug("pick: got {} {}",p.name,p.string)
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
            # debug("Check {}=p['ptype'] ?= {}",
                  # bin(p.get("ptype")),bin(m))
            if not bool(p["ptype"] & mask): return False
        for k,v in kw.items():
            # debug("Check {}=p[{}] ?= {}",p.get(k),k,v)
            if not ( k in p and p[k] == v ): return False
        return True
    return picker(fcn)

class glob(str):
    def __str__(self):
        return "glob('{}')".format(super().__str__())
    
    __repr__ = __str__

    def __eq__(self,other):
        if not isinstance(other,str):
            raise TypeError(
                "glob() can only match strings not {} objects".
                format(other.__class__) )
        return fnmatch.fnmatchcase(other.lower(),self.lower())
    
    def __ne__(self,other):
        return not self.__eq__(other)

class Glob(str):
    def __str__(self):
        return "Glob('{}')".format(super().__str__())
    
    __repr__ = __str__

    def __eq__(self,other):
        if not isinstance(other,str):
            raise TypeError(
                "glob() can only match strings not {} objects".
                format(other.__class__) )
        return fnmatch.fnmatchcase(str.__str__(other),str.__str__(self))
    
    def __ne__(self,other):
        return not self.__eq__(other)




