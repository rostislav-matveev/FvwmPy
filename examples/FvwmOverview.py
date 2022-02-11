#!/usr/bin/python3

from fvwmpy import *

class fvwmoverview(fvwmpy):
    def h_config(self,p):
        match = "".join("*",self.config.alias.lower())
        line  = p["string"].strip().lower()
        if not line.startswith(match) : return
        line = line.replace(match,"",1).strip()
        if line.startswith("transient") : self.config.transient = True
        elif line.startswith("matchwindows"):
            try:
                self.config.matchwindows += line.replace("matchwindows",",",1)
            except AttributeError:
                self.config.matchwindows = (
                    line.replace("matchwindows","",1).strip() )
        else:
            warn(" Unrecognized config line: '{}'. Exiting...",p["string"])
            self.exit(1)
            
m=g.fvwmpyoverview()

### don't listen to fvwm for now
m.mask         = 0
m.syncmask     = 0
m.nograbmask   = 0


### is there an alias?
if ( m.config.args and
     m.config.args[0].lower() not in ("transient","matchwindows") ):
    m.config.alias = m.config.args[0]
    m.config.args.remove(m.config.args[0])

### get config before processing command line argument
m.register_handler(M_CONFIG_INFO | M_SENDCONFIG, m.h_config)
m.getconfig()
### Do we want to watch for changes?
# m.unregister_handler(M_CONFIG_INFO | M_SENDCONFIG, m.h_config)

### Command line args:
i=0
while i < len(m.config.args):
    arg = m.config.args[i].lower()
    if arg == "transient":
        self.config.transient = True
        i += 1
    elif arg == "overview":
        m.start_overview()
    elif arg == "exit":
        m.exit(0)
    elif


