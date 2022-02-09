# fvwmpy -- framework for developing FVWM modules in python

This module defines class `fvwmpy`, that can be used by itself or as a
base for derived classes for writing FVWM modules.  

A typical example of a module using fvwmpy may look along the following lines
```
#!/usr/bin/python3
import fvwmpy

class mymodule(fvwmpy):
    def h_conf(self,pack):
        ### process config lines from FVWM database
	
    def h_handler1(self,pack):
        ### respond to the pack

    def h_handler2(self,pack):
        ### respond to the pack
    ...
    
m = mymodule()

### Keep FVWM mute while we setting things up
m.mask       = 0
m.syncmask   = 0
m.nograbmask = 0

### Check command line args
for arg in m.args:
   ### process arg

### Read FVWM's database of module config lines and parse them
### using `m.h_config` handler
m.getconfig(m.h_config, apply_other_handlers = False)

### Register handlers
m.register_handler(mask1,m.h_handler1)
m.register_handler(mask2,m.h_handler2)
...

### Tell FVWM that we are ready
m.finishedconfig()

### set masks
m.mask       = <some mask>
m.syncmask   = <some smask>
m.nograbmask = <some ngmask>

### If we want to dynamically update configuration:
m.register_handler(M_SENDCONFIG, m.h_config)
m.mask |= fvwmpy.M_SENDCONFIG
### If we want FVWM to wait while we update config
### (in that case m.h_config has to contain the line
###   `self.unlock()` at the end, to let FVWM know that it has finished.)
m.syncmask |= fvwmpy.M_SENDCONFIG

### Do some other stuff

### If the module is persistent (listens to FVWM and executes handlers)
m.run()
### otherwise
m.exit()
```


## License
This module is released under GPLv3 license.

## Structure of the module

### Constants

- **`fvwmpy.C_*`**

  These constants refer to FVWM decoration contexts.
  See [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for the complete 
  list and definitions. 

- **`fvwmpy.contextnames`**

  A dictionary with keys being contexts, and values -- character strings
  containing the names of the corresponding context.

- **`fvwmpy.contextcodes`**

  The inverse of the `fvwmpy.contextnames` dictionary.

- **`fvwmpy.M[X]_*`**

  Types of packets send from FVWM to the module. See [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for details.
  In addition there are following masks: `fvwmpy.M_ALL` -- matches all
  packet types;   `fvwmpy.M_FOR_WINLIST` -- matches packets emmited by
  FVWM during response to *Send_WindowList* command;
  `fvwmpy.M_FOR_CONFIG` -- mask matching all packets emmited by
  FVWM in response to *Send_ConfigInfo* command.

- **`fvwmpy.packetnames`**

  Dictionary for converting packet types to their names.
  E.g. fvwmpy.packetnames[MX_LEAVE_WINDOW] = "MX_LEAVE_WINDOW"

- **`fvwmpy.packetcodes`**

  The inverse dictionary of `fvwmpy.packetnames`

- **`fvwmpy.FVWM_PACK_START`** and **`fvwmpy.FVWM_PACK_START_b`**

  Delimiter used by FVWM at the start of each packet.
  `FVWM_PACK_START` is an integer and `FVWM_PACK_START_b` is its
  `bytearray` representation.

- **`fvwmpy.NOT_FINISHED`** and **`fvwmpy.NOT_FINISHED`**
  `bytearray`s containing tags to be sent to FVWM at the end of every
  message to notify whether module intends to continue of finished
  working.

- **`fvwmpy.LONG_SIZE`**

  Integer. The size of C's long in bytes.

- **`fvwmpy.FVWM_STR_CODEX`**

  String. Codex for en/de-coding strings during communication with FVWM.

- **`fvwmpy.VERSION`**
  String.
  
### Helper functions

- **`split_mask(mask)`**

  Returns a tuple of packet types, that match the given mask.
  If all the packet types in the list are bitwise `or`ed, one gets the
  `mask` back.

- **`crit()`**, **`dbg()`**, **`err()`**, **`info()`**, **`warn()`**

  Logging functions. They should be called

  `fcn(message_string, arguments)`

  and use `str.format(arguments)` formatting paradigm. Instances of
  `fvwmpy` class have their own similar logging functions.
  
  
### Exceptions

- **`FvwmPyException`**

  Base exception from which others are derived.

- **`FvwmLaunch`**

  This exception is raised when the module can not start up normally,
  e.g it is not executed by FVWM, pipes can not be opened, etc.

- **`IllegalOperation`**

  raised when one trying restore masks without saving them first, etc.
  It is also raised when one attempts to assign to FVWM variables (not
  infostore) or when FVWM does not understand communication from the
  module.

- **`PipeDesync`**

  This exception is raised if pipe desyncronization is detected,
  e.g. when the packet from FVWM does not have begin-tag or when the
  content of the packet does not match its format.
  Instance of fvwmpy class has method `fvwmpy.resync()` to seek the
  stream to the next pack.


### Class fvwmpy

`m=fvwmpy()`

Instances of `fvwmpy` have the following attributes and methods

- **`m.me`**

  String. The name of the executable file containing the module

- **`m.alias`**

  String. Alias of the module. Initially is equal to `m.me`.
  It can be changed, e.g. upon processing command line arguments.
  It is used in logging functions, and for filtering config lines.

- **`m.mask`**

  Integer. Mask for communication from FVWM. The mask control what
  kind of packets FVWM sends to the module. The normal and extended (bits
  higher then 32) masks are treated the same. If you update the value
  of the mask attribute it will be split into normal and extended
  parts and sent to fvwm automatically, if the new value is different
  from the old. See `fvwmpy.M[X]_*` constants. See also `m.push_masks(...)`
  and `m.pull_masks()` methods for temporarily changing masks.
  See [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for
  explanation of the concepts.
  
- **`m.syncmask`** and **`m.nograbmask`**

  are similar to `m.mask` but contain values of syncmask and nograb
  masks.
  

tofvwm,fromfvwm      -- pipes for communicating with fvwm

window               -- id of the context window at which the module
                        was started

decoration           -- window decoration in which the module was
                        launched. See C_* constants.

args                 -- the list of strings. Command line arguments of
                        the module

handlers             -- The dictionary of handlers indexed my M[X]_*
		        masks. In the standard run() routine
			all handlers in inst.handlers[m] are executed
			whenever a packet of type m ( in { M[X]_* } )
			is received from fvwm. Packet is passed to the
		        handler as an argument.

winlist              -- The list of all windows. Initially it is
                        empty. It is build by inst.getwinlist method.
			To keep it up to date register inst.h_updatewl
                        method for the appropriate masks
	inst.register_handler(FvwmPy.M_FOR_WINLIST,inst.h_updatewl)

The following attributes are updated by getconfig method:

colorset             -- list of colorsets. It is updated by getconfig
                        method. 
      
config               -- list of config lines matching alias attribute.
                        Updated by getconfig method.

DesktopSize          -- tuple of two integers

ImagePath            -- tuple of strings

XineramaConfig       -- tuple of integers

ClickTime 	     -- integer

IgnoreModifiers	     -- tuple of integers

Methods:

getwl()              -- update winlist

msg(...)             -- write a message prepended with module name to
		        stderr. Takes the same arguments as print(...)

sendmessage(string,window=0,done=False)
                     -- Send text message to fvwm at window context
		        and indicate whether module has finished
			working.

finishedstartup()    -- tell fvwm that module is ready to process
                        packets.   

exit(n=0)            -- cleanup notify fvwm and exit with status n.

unlock(done=False)   -- In case of syncronous operation tell fvwm to
                        go on and indicate whether finished.

getconfig(match=None, merge = False)
                     -- ask fvwm and update config database. Also
		        update values of some other attributes, see
			above.

getwinlist()         -- update winlist database.
                        To keep it up to date at all times register

	inst.register_handler(FvwmPy.M_FOR_WINLIST,inst.h_updatewl)
			
			and include appropriate masks

	inst.mask |= FvwmPy.M_FOR_WINLIST

register_handler(mask,handler)
		     -- register handler to be executed for packets
		        matching mask. Handler should take one
			argument which is the packet.
		

unregister_handler(self,mask,handler)
		     -- remove handler from the execution queue	
