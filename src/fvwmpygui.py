import os as _os
import sys as _sys
import struct as _struct
import threading as _threading
import time

from .constants  import *
from .packets    import _packet
from .exceptions import *
from .gui        import gui as _gui
from .fvwmpy     import *

class fvwmpygui(fvwmpy):
    def __init__(self):
        super().__init__()
        self.gui = _gui(self)
        ### How to read?
        # self.errorfile = open(_os.path.expanduser('~/.xsession-errors'))
        self.register_handler(M_ALL,self.gui.showpacket)

    def sendmessage(self,msg, context_window=None, finished=False):
        super().sendmessage(msg, context_window, finished)
        self.gui.showmessage(msg, context_window)

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self,m):
        self._mask_set(m)
        self.gui.showmask("mask",self.mask)
        
    @property
    def syncmask(self):
        return self._mask

    @syncmask.setter
    def syncmask(self,m):
        self._syncmask_set(m)
        self.gui.showmask("syncmask",self.syncmask)
        
    @property
    def nograbmask(self):
        return self._nograbmask

    @nograbmask.setter
    def nograbmask(self,m):
        self._nograbmask_set(m)
        self.gui.showmask("nograbmask",self.nograbmask)
        
    def readerr(self):
        while True:
            line=self.errorfile.readline()
            self.gui.showerr(line)

    def mainloop(self,):
        pt=1
        for i in range(37):
            p = self.packet()
            self.mask=pt
            time.sleep(2)
            pt <<= 1
        self.exit()
        
    def run(self):
        self.msg("Create thread")
        me = _threading.Thread(target=self.mainloop,
                               args=tuple())
        self.msg("Start thread")
        me.start()
        self.msg("Start GUI")
        self.gui.root.mainloop()
        self.msg("GUI Stoped")
        self.exit()



