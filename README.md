# FvwmPy -- framework for developing FVWM modules in python

This module defines class `fvwmpy`, that can be used by itself or as a
base for derived classes for writing FVWM modules.  

##### Constants

- **`fvwmpy.C_*`**

  These constants refer to FVWM decoration contexts.
  See [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for the complete 
  list and definitions. 

- `fvwmpy.contextnames`
  A dictionary with keys being contexts, and values -- character strings
  containing the names of the corresponding context.

- `fvwmpy.contextcodes`
  The inverse of the `fvwmpy.contextnames` dictionary.

- `fvwmpy.M[X]_*`
  Types of packets send from FVWM to the module. See [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for details.
  
- `fvwmpy.M_ALL`
  Mask matching all packets

- `fvwmpy.M_FOR_WINLIST`
  Mask matching all packets that are sent after `Send_WindowList`
  command is received by FVWM.

- `fvwmpy.M_FOR_CONFIG`
  Mask matching all packets that are sent after `Send_ConfigInfo`
  command is received by FVWM.

- `fvwmpy.packetnames`
  Dictionary for converting packet types to their names.
  E.g. fvwmpy.packetnames[MX_LEAVE_WINDOW] = "MX_LEAVE_WINDOW"

- `fvwmpy.packetcodes`
  The inverse dictionary of `fvwmpy.packetnames`

- `fvwmpy.FVWM_PACK_START` and `fvwmpy.FVWM_PACK_START_b`
  Delimiter used by FVWM at the start of each packet.
  `FVWM_PACK_START` is an integer and `FVWM_PACK_START_b` is its
  `bytearray` representation.

- `fvwmpy.NOT_FINISHED` and `fvwmpy.NOT_FINISHED`
  `bytearray`s containing tags to be sent to FVWM at the end of every
  message to notify whether module intends to continue of finished
  working.

- `fvwmpy.LONG_SIZE`
  Integer. The size of C's long in bytes.

- `FVWM_STR_CODEX`
  String. Codex for en/de-coding strings during communication with FVWM.

##### Helper functions

- **`split_mask(mask)`**
  Returns a tuple of packet types, that match the given mask.
  If all the packet types in the list are bitwise `or`ed, one gets the
  `mask` back.



fvwmpy(



Constants:
C_*
FINISHED
NOT_FINISHED
FVWM_PACK_START
FVWM_PACK_START_b
FVWM_STR_CODEX
M[X]_*
LONG_SIZE
contextcodes
contextnames
packetcodes
packetnames

Exceptions:

FvwmPyException
FvwmLaunch
IllegalOp
PipeDesync

Logging functions:
crit(
dbg(
err(
info(
warn(


helpers:
split_mask(



me                   -- the name of the executable file
alias 		     -- alias of the module. Initially set to be equal to
		        inst.me. You may change it upon processing
			command line arguments.
mask    	     -- mask for messages from fvwm. The normal and
       		        extended (bits higher then 32) masks are
			treated the same. If you
			set the mask it will be split and sent to fvwm
			automatically. See M_* and MX_* constants.
syncmask             -- The same for sync- and nograb- masks
nograbmask

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
