import struct
import sys
import threading
import time

from   .constants  import *
from   .exceptions import *
from   .log        import  _getloggers
from   .packet     import packet

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
        self._nonempty        = threading.Event()
        self._lock            = threading.Lock()
        self._spack_found     = threading.Event()
        self._spack_picker    = None
        self._spack           = None
        self._thread_exception = None
        self._packet_picker   = None
        self._reader_thread   = threading.Thread( target = self._reader,
                                                  name   = "reader_thread",
                                                  daemon = True            )
        self.debug(" Start reader_thread as daemon")
        self._reader_thread.start()

    def __bool__(self):
        return bool(self._queue)

    def __len__(self):
        return len(self._queue)

    ### This is the one to be threaded (daemon)
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
                ### Are we waiting for some special packet?
                if self._spack_picker and self._spack_picker(p):
                    ### Were waiting and packer arrived
                    self.debug("threaded_reader: found special pack {}",p.name)
                    self._spack = (len(self._queue)-1, p)
                    self._spack_picker = None
                    self._spack_found.set()
                self._nonempty.set()
            except PipeDesync as e:
                self.error( "threaded_reader: {}",repr(e))
                self.error( "threaded_reader: Resync the pipe. "+
                            "Packet(s) may be lost.")
                self._resync()
            except BaseException as e:
                ### We want to pass any exception to the main thread
                ### but then there could be a delay in handling.
                ### What is a better solution?
                self.error("threaded_reader: {}",repr(e))
                self.error("threaded_reader: pass to the main thread")
                self._thread_exception = e
                ### set events so there is no waiting in the main thread
                ### main must now check and clear events
                self._packet_picked.set()
                self._nonempty.set()
            finally:
                if self._lock.locked(): self._lock.release()
            ### Slow it down for debugging. DON'T FORGET!!!
            # time.sleep(0.01)

    def read(self,keep=False,timeout=None):
        """Read the packet from the top of the queue.

        If timeout is not None, wait for at most timeout second.
        If meanwhile no packet arrived in the queue, return None.

        If keep is False, remove the packet from the queue, otherwise keep 
        it there.
        """
        ### Let's see if something bad happened in the thread.
        self._check_exception()
        self.debug( "read: queue size={}; queue_nonempty={}",
                    len(self._queue),
                    bool(self) )
        gotpack = self._nonempty.wait(timeout)
        ### Let's see if the thread got an exception while we were waiting
        self._check_exception()
        if gotpack:
            p = self._queue[0]
            self.debug( "read: got {} at {} from {} packets",
                          p.name,p.time,len(self))
            if not keep:
                self._lock.acquire()
                del self._queue[0]
                if not self._queue: self._nonempty.clear()
                self._lock.release()
            return p
        else: 
            self.debug("read: queue is empty, returning None after timeout")
            return None

    def pick(self,picker,until=None,timeout=0.5,keep=False):
        """Find and return all packets in the queue for which picker 
        evaluates to True and which arrived before the first packet for which
        until picker evaluates to true.
        Return with whatever found after timeout seconds, if the 'wait_for' packet 
        did not arrive. 
        Keep packets in the queue if keep is True, otherwise remove them.
        That does not includes the packet that marks the end of the search,
        unless it is also picked.
        """
        self._check_exception()
        if until is None:
            until = picker
        packs = list()
        indices = list()
        try:
            self._lock.acquire()
            if not any( map(until,self._queue) ):
                self.debug("pick: Didn'r reach until. Wait for the threaded reader")
                self._spack_picker = until
                self._spack_found.clear()
                self._lock.release()
                self._spack_found.wait(timeout)
                self._check_exception()
                self._lock.acquire()
            for i, p in enumerate(self._queue):
                if picker(p):
                    self.debug("pick: {}. picked a pack {}",i,p.name)
                    indices.append(i)
                    packs.append(p)
                if until(p):
                    self.debug("pick: reached until")
                    break
            self.debug("pick: found {} out of {} packs",
                       len(indices),len(self)    )
            if not keep:
                self.debug("pick: deleting found")
                for i in reversed(indices):
                    del self._queue[i]
            if not self._queue: self._nonempty.clear()
            return packs
        finally:
            self._spack_picker = None
            if self._lock.locked(): self._lock.release()
            
    def clear(self):
        "Clear the queue."
        self._lock.acquire()
        self._queue.clear()
        self._lock.release()

    def _check_exception(self):
        if self._thread_exception:
            e = self._thread_exception
            self._thread_exception = None
            self.debug("check_exception: {} detected in the thread",repr(e))
            ### thread sets events for the main thread to proceed
            ### we have to clear, if necessary
            self._packet_picked.clear()
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

