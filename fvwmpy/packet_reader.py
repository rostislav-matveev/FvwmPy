import struct
import sys
import threading
import time

# from   .constants  import *
# from   .exceptions import *
# from   .log        import  _getloggers
# from   .packet     import packet

################################################################################
### some helpers

################################################################################
###

class _packet_queue:
    """Instance of the _packet_reader class represents the packet queue."""
    
    def __init__(self,module):
        ### I have to do it here because I need module.alias
        ### _packet_reader will be instancieated once per module
        ### so it is ok.
        ( self.logger, self.debug, self.info,
          self.warn,   self.error, self.critical  ) = _getloggers(
              module.alias+':packetreader')
        self.logger.setLevel(L_WARN)
        self._pipe            = module._fromfvwm
        self._queue           = list()
        self._notempty        = threading.Event()
        self._lock      = threading.Lock()
        self._thread_exception = None
        self._reader_thread   = threading.Thread( target = self._reader,
                                                  name   = "reader_thread",
                                                  daemon = True            )
        self.debug(" Start reader_thread as daemon")
        self._reader_thread.start()

    @property
    def locked(self):
        "True if queue is locked, otherwise False"
        return self._lock.isSet()

    def __bool__(self):
        return bool(self._queue)

    def __len__(self):
        return len(self._queue)

    ### This is the one to be threaded
    def _reader(self):
        while True:
            try:
                p = packet(self._pipe)
                self.debug("threaded_reader: got {} at {}",p.name,p.time)
                ### for testing DON'T FORGET to remove!!!
                if p.ptype == M_STRING and p.string == "exception":
                    raise Exception
                
                self._lock.acquire()
                self._queue.append(p)
                self._nonempty.set()
            except PipeDesync as e:
                self.error( "threaded_reader: {}",repr(e))
                self.error( "threaded_reader: Resync the pipe."+
                            "Packet(s) may be lost.")
                self._resync()
            except BaseException as e:
                ### We want to pass any exception to the main thread
                ### but then there could be a delay in handling.
                ### What is a better solution?
                self.error("threaded_reader: {}",repr(e))
                self.error("threaded_reader: pass to the main thread")
                self._thread_exception = e
                ### release self._nonempty.wait() in the main thread
                ### main mast now check for non empty queue
                self._nonempty.set()
            finally:
                if self._lock.locked(): self._lock.release()
            ### Slow it down for debugging. DON'T FORGET!!!
            # time.sleep(0.01)

    def read(self,keep=False,timeout=None):
        """Read the packet from the top of the queue.

        In timeout is not None wait for at most timeout millisecond.
        If no packet arrived meanwhile in the queue, return None.

        If keep is False, remove the packet from the queue, otherwise keep 
        it there.
        """
        ### Let's see if something bad happened in the thread.
        self._check_exception()
        self.debug( "main: queue size={}; queue_nonempty={}",
                    len(self._queue),
                    bool(self) )
        if timeout is not None: timeout /= 1000
        gotpack = self._nonempty.wait(timeout)
        ### Let's see if the thread got an exception while we were waiting
        self._check_exception()
        if gotpack:
            p = self._queue[0]
            self.debug("read: got {} at {} from {} packets", p.name,p.time,len(self))
            if not keep:
                self._lock.acquire()
                del self._queue[0]
                self._lock.release()
            return p
        else: 
            self.debug("read: queue is empty, returning None after timeout")
            return None

    def peek(self,timeout=None):
        """Read the packet from the top of the queue, but leave
        in the queue.
        """
        return( self.read(keep=True,timeout=timeout) )

    def _check_exception(self):
        if self._thread_exception:
            e = self._thread_exception
            self._thread_exception = None
            self.debug("_check_exception: {} detected in the thread",e)
            ### thread sets nonempty lock for the main thread to proceed
            ### we have to clear it, if necessary
            if not self._queue:
                self._nonempty.clear()
            raise e

    def _resync(self):
        """Seek the pipe to the start of the next packet"""
        found = False
        while not found:
            peek     = self._pipe.peek()
            position = peek.find(FVWM_PACK_START_b)
            if position == -1:
                self._pipe.read(len(peek))
                ### let's wait a bit
                time.sleep(0.05)
            else:
                self._pipe.read(position)
                found = True

            
    def clear(self):
        "Clear the queue."
        self._lock.acquire()
        self._queue.clear()
        self._lock.release()
        
    def pick( self, picker, which="first", keep=False, timeout=500 ):
        """Find all/first/last packet in the queue for which picker 
        evaluates to True
        """
        start = 0
        ipacks = list()
        ### walk through the queue, if  nothing found
        ### then wait and check the rest of the queue repeatedly
        t = 0
        tstep = 10
        while t <= timeout:
            ### ToDo: don't check all, if which in {"first","last"}!!!
            self._queue_lock.acquire()
            iq = enumerate(self._queue[start:],start)
            ipacks += list(filter( lambda ip: picker(ip[1]), iq))
            ### for debug DONT FORGET!!!
            # for i, p in iq:
                # if picker(p): ipacks.append((i,p))
            ### for the next go
            start = len(self._queue)
            self._queue_lock.release()
            if ipacks:
                ### found something
                break
            else:
                ### let's have another chance
                ### and give time for the threaded reader to fill the queue
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

