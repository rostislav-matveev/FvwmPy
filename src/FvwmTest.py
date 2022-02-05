#!/usr/bin/python3

from fvwmpy import *
import fvwmpy.fvwmpygui as g



m=g.fvwmpygui()
m.mask         = 1
m.syncmask     = 0
m.nograbmask   = 0
m.msg("Test: MASK",m.mask)
m.run()


