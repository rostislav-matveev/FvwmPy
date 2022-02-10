# fvwmpy -- framework for developing FVWM modules in python

This module defines class `fvwmpy`, that can be used by itself or as a
base for derived classes for writing FVWM modules.  

## License
This module is released under GPLv3 license.

## Declaration
I love FVWM

## Features
- Simple interface for communicating with the window manager.
- Possibility of maintaining dynamically updated list of windows and
  their properties.
- Possibility to iterate over windows satisfying given conditions.  
- Possibility of dynamically change configuration
- Simple interface for accessing FVWM's variables and infostore
  database.
- Compatible with tkinter
- Simple interface for masking packets from FVWM
- Possibility to temporary change change masks and restore values
  later.
- Support for the concept of module aliases

A typical example of a module using fvwmpy may look along the following lines
```
#!/usr/bin/python3
import fvwmpy

class mymodule(fvwmpy):
    def h_config(self,pack):
        ### process config lines from FVWM database
	
    def h_handler1(self,pack):
        ### respond to the pack

    def h_handler2(self,pack):
        ### respond to the pack
    ...

### Let's have lot's of debugging output
LOGGINGLEVEL = fvwmpy._logging.DEBUG

m = mymodule()

### Keep FVWM mute while we are setting things up
m.mask       = 0
m.syncmask   = 0
m.nograbmask = 0

### Check command line arguments
for arg in m.args:
   ### process arg

### Read FVWM's database of module configuration lines and parse them
### using `m.h_config` handler
m.getconfig(m.h_config)

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
m.register_handler(fvwmpy.M_SENDCONFIG, m.h_config)
m.mask |= fvwmpy.M_SENDCONFIG | fvwmpy.M_CONFIGINFO

### If we want FVWM to wait while we update config
m.syncmask |= fvwmpy.M_SENDCONFIG
m.register_handler(fvwmpy.M_SENDCONFIG, m.h_unlock)

### If we want to have up to date list of windows
m.getwinlist()
m.register_handler(fvwmpy.M_FOR_WINLIST, m.h_updatewl)
m.mask |= fvwmpy.M_FOR_WINLIST

### Do some other module stuff
m.info(" Looks like FVWM manages now {} windows",len(m.winlist))

### If the module is persistent (listens to FVWM and executes handlers)
m.run()
### otherwise
m.exit()
```


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
  packet types;   `fvwmpy.M_FOR_WINLIST` -- matches packets emitted by
  FVWM during response to *Send_WindowList* command;
  `fvwmpy.M_FOR_CONFIG` -- mask matching all packets emitted by
  FVWM in response to *Send_ConfigInfo* command.

- **`fvwmpy.packetnames`**

  Dictionary for converting packet types to their names.
  E.g.

  `fvwmpy.packetnames[fvwmpy.MX_LEAVE_WINDOW] == "MX_LEAVE_WINDOW"`

- **`fvwmpy.packetcodes`**

  The inverse dictionary of `fvwmpy.packetnames`

- **`fvwmpy.FVWM_PACK_START`** and **`fvwmpy.FVWM_PACK_START_b`**

  Delimiter used by FVWM at the start of each packet.
  `FVWM_PACK_START` is an integer and `FVWM_PACK_START_b` is its
  bytearray representation.

- **`fvwmpy.FINISHED`** and **`fvwmpy.NOT_FINISHED`**

  bytearrays containing tags to be sent to FVWM at the end of every
  message to notify whether module intends to continue or has finished
  working and is about to exit.

- **`fvwmpy.LONG_SIZE`**

  Integer. The size of C's long in bytes.

- **`fvwmpy.FVWM_STR_CODEX`**

  String. Codex for en/de-coding strings during communication with FVWM.

- **`fvwmpy.VERSION`**

  String. Naturally contains information about current version.

- **`fvwmpy.LOGGINGLEVEL`**

  This is logging level as described in the documentation for the
  **logging** python module. It affects behaviour of `m.<ligging_fcn>`
  where `m` is an instance of (derived from) `fvwmpy.fvwmpy` class.
  You may change the value of `fvwmpy.LOGGINGLEVEL`. This has to be
  done before instantiating  `fvwmpy.fvwmpy` object.
  the standard values can be accessed as `fvwmpy._logging.CRITICAL`
  `fvwmpy._logging.ERROR`, `fvwmpy._logging.WARNING`,
  `fvwmpy._logging.INFO`, `fvwmpy._logging.DEBUG` and `fvwmpy._logging.NOTSET`
### Helper functions

- **`fvwmpy.split_mask(mask)`**

  Returns a tuple of all packet types, that match the given mask.
  If all the packet types in the list are bitwise `or`ed, one gets the
  `mask` back.

- **`fvwmpy.crit()`**, **`fvwmpy.dbg()`**, **`fvwmpy.err()`**,
  **`fvwmpy.info()`**, **`fvwmpy.warn()`**

  Logging functions. They should be called

  `fcn(message_string, arguments)`

  and use `message_string.format(arguments)` formatting paradigm. Instances of
  `fvwmpy.fvwmpy` class have their own similar logging functions.
  
  
### Exceptions

- **`fvwmpy.FvwmPyException`**

  Base exception from which others are derived.

- **`fvwmpy.FvwmLaunch`**

  This exception is raised when the module can not start up normally,
  e.g it is not executed by FVWM, pipes can not be opened, etc.

- **`fvwmpy.IllegalOperation`**

  raised when one trying restore masks without saving them first, etc.
  It is also raised when one attempts to assign to FVWM variables (not
  infostore) or when FVWM does not understand communication from the
  module or the other way around.

- **`fvwmpy.PipeDesync`**

  This exception is raised if pipe desyncronization is detected,
  e.g. when the packet from FVWM does not have begin-tag or when the
  content of the packet does not match its format.
  Instances of `fvwmpy.fvwmpy` class have method `.resync()` to seek the
  stream to the next pack.


### Class `fvwmpy.fvwmpy`

`m=fvwmpy.fvwmpy()`

Instances of `fvwmpy` have the following attributes and methods

#### Attributes

- **`m.me`**

  String. The name of the executable file containing the module

- **`m.alias`**

  String. Alias of the module. Alias is guessed from the command line
  arguments of the module during initialization.  If the first
  commandline argument does not start with '-', then it is assumed to
  be the alias of the module. Then `m.alias` is set (which affects
  logging functions and pruning of configuration lines) and this
  argument is not included in `m.args`. If the first argument is a
  single '-', then it is also removed from `m.args` and `m.alias` will
  be the same as `m.me`.  `m.alias` can be changed afterwards. Such
  action will affect logging functions and prunning of configuration
  lines.

- **`m.mask`**

  Integer. Mask for communication from FVWM. The mask controls what
  kind of packets FVWM sends to the module. The normal and extended (bits
  higher then 32) masks are treated the same, so, for example
  `m.mask = fvwmpy.MX_LEAVE_WINDOW | fvwmpy.M_VISIBLE_NAME`
  is a legal instruction with intended consequences.

  Setting the mask to a new value will trigger communication with FVWM
  to let FVWM know the new value, but only if the new value is
  different from the old, so no unnecessary communication takes
  place. Note, that if you previously changed the mask by some other
  method (sending an appropriate message to FVWM) the new value might
  not be communicated to the window manager when executing `m.mask =
  <new_value>`. Methods `m.push_mask()` and `m.restore_mask()` are
  safe in this respect.
  
  See `fvwmpy.M[X]_*` .

  See also `m.push_masks(...)` and `m.restore_masks()` methods for
  temporarily changing masks.
  
  See [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for
  the explanation of the concepts of masking.
  
- **`m.syncmask`** and **`m.nograbmask`**

  are similar to `m.mask` but contain values of syncmask and
  nograbmask.

- **`m.winlist`** 

  `m.winlist` is the database of windows known to FVWM indexed by
  window id's. It can be filled by calling `m.getwinlist()` method. It
  is also possible to arrange to have `m.winlist` to be up to date at
  all times. See information on `m.h_updatewl` handler.
  
  `m.winlist` inherits from `dict`. `m.winlist[<window_id>]` is an
  instance of `fvwmpy._window` class and contains all the information
  abot the window. For more details see **winlist database** below

  In addition to the usual `dict` methods it has method
  `w.winlist.filter(conditions)` which return an iterator for cycling
  through windows satisfying conditions. It is described in more
  details in **winlist database** section.
  
- **`m.config`**

  `m.config` is the database containing information sent by FVWM
  during execution of *Send_ConfigInfo* command and with M_SENDCONFIG
  packets. See `m.getconfig()` method and `m.h_saveconfig()` handler.
  For more details see **config database** below

- **`m.context_window`**

  Integer. Contains id of the window in whose context the module was
  started or 0 if the module was executed outside of any window context.

- **`m.context_deco`**

  Window decoration context in which module was started or 0 if  the
  module was executed outside of any window context. See `fvwmpy.C_*`
  and [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for
  explanation of decoration contexts.

- **`m.args`**

  List of strings. Contains command line arguments of the module. 
  If the first argument does not start with '-', then it is assumed to
  be the alias of the module. Then `m.alias` is set (which affects
  logging functions and pruning of configuration lines) and this
  argument is not included in `m.args`. If the first argument is a
  single '-', then it is also removed from `m.args`.
  -  If the module is invoked by
     ```
     Module FvwmMyModule FvwmAkaModule arg1 arg2 ...
     ```
     then `m.alias == 'FvwmAkaModule'` and `m.args == ['arg1', 'arg2', ...]`
  
  -  If the module is invoked by
     ```
     Module FvwmMyModule - FvwmAkaModule arg1 arg2 ...
     ```
     then `m.alias == 'FvwmMyModule'` and
     `m.args == ['FvwmAkaModule', 'arg1', 'arg2', ...]`
  
  -  If the module is invoked by
     ```
     Module FvwmMyModule - FvwmAkaModule arg1 arg2 ...
     ```
     then `m.alias == 'FvwmMyModule' and
     `m.args == ['FvwmAkaModule', 'arg1', 'arg2', ...]`
  
  -  If the module is invoked by
     ```
     Module FvwmMyModule -geometry 200x200+24+0 ...
     ```
     then `m.alias == 'FvwmMyModule'` and
     `m.args == ['-geometry', '200x200+24+0', ...]`
  
- **`m.handlers`**

  A dictionary whose keys are packet types and values are lists of
  handler functions, each of which takes one argument, which is a
  packet.
  Initially all lists are empty.

  See also `m.register_handler()`,  `m.unregister_handler()`,
  `m.clear_handlers()`, `m.registered_handler()` and
  `m.call_handlers()` methods and **handlers** below.

- **`m.var`** and **`m.infostore`**

  See **FVWM variables and infostore** below


#### Methods

- **`m.logger`**, **`m.dbg()`**, **`m.info()`**, **`m.warn()`**,
  **`m.err()`** and **`m.crit()`**

  Logger and logging functions. They should be called

  `m.<log_fcn>(message_string, *arguments)`
  
  and use `message_string.format(*arguments)` formatting paradigm.
  Logging is directed to *stderr*. For the module *stderr*-stream will
  be the same as for FVWM. Logging functions print the severity level
  followed by the alias of the module followed by the formatted
  message.
  
- **`m.sendmessage(msg, context_window=None, finished=False)`**

  Send a (possibly multiline) message to FVWM for execution in the
  context of `context_window`.
  
  If `context_window` is not given or `None`, then the window context
  will be equal to the context at which module was called (that is
  `m.context_window`). If `context_window==0`, then FVWM executes
  commands without window context.  

  If `finished` then FVWM will be notified that the module is done
  working and is about to exit soon.

- **`m.packet(parse=True, raw=False)`**

  Read and return a packet from 'FVWM to module'-pipe. See
  **Packets** for the structure of the packet data type.

  If `parse` then decode the packet and store the fields.

  If `raw` then set p["raw"] to the raw bytearray of the packet
  (without the header)

- **`m.resync()`**

  Seek the 'FVWM to module'-pipe to the start of the next packet.
  Useful in case of pipe desyncronization.

- **`m.finishedstartup()`**

  Tell FVWM that the module has finished setting thing up and is ready to
  start working.

- **`m.exit(n=0)`**

  Clean up and exit with exit status `n`.
  See also `m.h_exit()` handler.

- **`m.unlock(finished=False)`**

  During synchronous operations, tell FVWM that module is ready to
  continue working and is listening to FVWM.

  If `finished` then notify FVWM that the module is about to exit.

- **`m.push_masks(mask,syncmask,nograbmask)`**

  Set mask, syncmask and nograbmask to new values temporarily, if
  don't want to receive packets of some type during some operation
  (E.g. during *Send_WindowList* or *Send_ConfigInfo* commands).
  If any of the values is `None` than the corresponding mask is left
  unchanged.
  
  It is possible to have several embedded
  `m.push_masks`--`m.restore_masks` constructs.

- **`m.restore_masks()`**

  Restore masks previously overridden by `m.push_masks`.
  If mask stack is empty (more `m.restore_masks()`'s then
  `m.push_masks()`'s)
  `fvwmpy.IllegalOperation` exception is raised.

- **`m.getconfig(handler=None, match=None)`**

  Ask FVWM for configuration info. Each received packet is passed to
  the `handler`.

  `handler` must be `None` or a callable taking one argument, which is a
  packet of type matching `fvwmpy.M_FOR_CONFIG`. If `handler` is not
  supplied then default handler `m.h_saveconfig` is
  used. `m.h_saveconfig` just fills `m.config` database with the
  information received from FVWM.

  `match` must be `None` or a string to match module configuration
  lines against.  If not supplied then `"*" + m.alias` is assumed.  If
  `match == ""` then all configuration lines are received and
  processed.

  Note that all packets not matching `fvwmpy.M_FOR_CONFIG` are masked
  away during `m.getconfig()` call.

  See **Config database** for more information.

- **`m.getwinlist(handler = None)`**

  Ask FVWM for the list of all windows it manages. Each packet
  received in response is passed to the handler.

  `handler` should be a callable taking one argument, which is a
  packet of type matching `fvwmpy.M_FOR_WINLIST`. If `handler` is not
  supplied then default handler `m.h_updatewl` is
  used. `m.h_updatewl` simply updates `m.winlist` database with the
  information received from FVWM. It also understands
  `fvwmpy.M_DESTROY_WINDOW` packets remving corresponding entries from
  the database.

  Note that all packets mot matching `fvwmpy.M_FOR_WINLIST` are masked
  away during `m.getwinlist()` call.
  
  If you want to keep `m.winlist` up to date all the time, then
  include the following
  ```
  m.getwinlist()
  m.register_handler(fvwmpy.M_FOR_WINLIST, m.h_updatewl)
  m.mask |= fvwmpy.M_FOR_WINLIST
  ```
  somewhere in your code.
  
- **`m.register_handler(mask, handler)`**

  Register `handler` for packets of type matching `mask`.
  The default mainloop executes all the handlers for all matching
  packets in the order they were registered.

  `handler` should be a callable taking one argument, which is a
  packet of type matching `mask` and should be capable of processing
  such a packet.

  If `handler` is already registered previously for some packet types,
  it will not be registered again, neither it will be moved to the end
  of execution queue for that type. If you want to move some registered
  handler to the end of the queue, you have to unregister it first.
  
- **`m.unregister_handler(mask, handler)`**

  Remove handler from the execution queue for the packets matching
  `mask`. It is **not** an error to try to unregister a handler, which
  is not registered. So, for example,
  ```
  m.unregister_handler(fvwmpy.M_ALL, m.h_handler)
  ```
  removes `m.h_handler` from all queues where it is present.

- **`m.call_handlers(pack)`**

  Execute all handlers in the queue corresponding to the `pack`'s
  packet type passing packet `pack` to them. The default mainloop calls
  `m.call_handlers()` on all packets received from FVWM.

- **`m.clear_handlers(mask)`**

  Clear all execution queues for packets matching `mask`.

- **`m.registered_handler(handler)`**

  Return the mask for the queues where handler is registered.

- **`m.run()`**

  Enter mainloop which simply reads packets from FVWM and for each
  packet executes handlers in the corresponding queue, until
  `m.exit()` or `m.h_exit()` method is called. 
  
##### Supplied handlers

- **`m.h_saveconfig(pack)`**

  This handler is capable of processing packets matching
  `fvwmpy.M_FOR_CONFIG`. It simply records the information in
  `m.config` database. You can insert the following lines in your code
  to keep the database up to date
  ```
  m.getconfig()
  m.register_handler(fvwmpy.M_FOR_CONFIG, m.h_saveconfig)
  m.mask |= M_SENDCONFIG | M_CONFIG_INFO
  ### If you want to process config in a synchronous manner
  ### e.g. the masks may be affected
  #m.register_handler(fvwmpy.M_FOR_CONFIG, m.h_unlock)
  #m.syncmask |= M_FOR_CONFIG
  ```
  `m.h_saveconfig(pack)` does not send *NOP UNLOCK* command to FVWM.
  In case you want to process configuration information synchronously
  register  `m.h_unlock` after `m.h_saveconfig`.

- **`m.h_unlock(pack)`**

  This handler completely ignores its argument and send the *NOP UNLOCK*
  command to FVWM. FVWM waits for *NOP UNLOCK* after sending packets
  matching `m.syncmask`, so it make sense to
  ```
  m.register_handler(m.syncmask,m.h_unlock)
  ```
  When syncmask changes one should
  ```
  m.unregister_handler(fvwmpy.M_ALL, m.h_unlock)
  m.register_handler(m.syncmask, m.h_unlock)
  ```
  to make sure that  `m.h_unlock(pack)` is the last one in the queues
  
- **`m.h_exit(pack)`**

  This handler ignores its argument, cleans things up and terminates the
  module.

- **`m.h_updatewl(pack)`**

  This handler is capable to process packets matching
  `fvwmpy.M_FOR_WINLIST`. It uses information in the packet to update
  `m.winlist` database.
  
  
#### Winlist database **`m.winlist`**

`m.winlist` is a dictionary of windows indexed by window id's.
Each window is an instance of `fvwmpy._window` class and has the
attributes and methods listed below. Attributes can also be accessed
via `w.attribute`, which is completely equivalent to `w["attribute"]`
in that both raise `KeyError()` exception, if the attribute is missing.

m.winlist has all the usual methods inherited from `dict`
and another one descrimed below.

- **`m.winlist.filter(conditions)`**

  This method return an iterator that cycle through windows matching
  `conditions`

  `conditions` is a string containg the same conditions that are
  allowed in FVWM's conditional commands. See FVWM manual pages for
  explanations. For formatting convenience `conditions` may be a
  multiline string. As an example look at the following (not very usefull)
  code
  ```
  condition = """
  	      !FixedSize, !FixedPosition, 
  	      !Shaded,!Iconic,CurrentPage
  	      !Fvwm*, !stalonetray
  	      """
  for w in m.windowlist.filter(condition):
      dx = max( w.wdx//2, w.hints_min_width  )
      dy = max( w.wdy//2, w.hints_min_height )
      m.sendmessage( "Resize {}p {}p".format(dx,dy),
      		     context_window=w.window        )
  ```
  
  Note that `winlist.filter` may have troubles performing if the
  winlist database is not up to date, since it delegates tha actual
  filtering to the window manager.
  
##### Attributes and methods of instances of `fvwmpy._window` class.

For more comprehensive information refer to [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) and
  consult **fvwm.h, window_flags.h, Module.h vpacket.h** files in FVWM
  source tree.

- **`w.window`** window id
- **`w.frame`** id of the frame window
- **`w.wx`**, **`w.wy`** x,y location of the window’s frame
- **`w.wdx`**, **`w.wdy`** width and height of the window’s frame
- **`w.desk`** desktop number
- **`w.layer`** layer
- **`w.hints_base_width`**, **`w.hints_base_width`** window base width
  and height
- **`w.hints_width_inc`**, **`w.hints_height_inc`** window resize
  width/height increment 
- **`w.orig_hints_width_inc`**, **`w.orig_hints_height_inc`**
  original window resize width/height increment 
- **`w.hints_min_width`**, **`w.hints_min_height`**,
  **`w.hints_max_width`**, **`w.hints_max_height`** 
  window minimum/maximum width/height
- **`w.icon_w`** icon label window id, or 0
- **`w.icon_pixmap_w`** icon pixmap window id, or 0
- **`w.hints_win_gravity`** window gravity
- **`w.text_pixel`** pixel value of the text color
- **`w.back_pixel`** pixel value of the window border color
- **`w.ewmh_hint_layer`** ewmh layer
- **`w.ewmh_hint_desktop`** ewmh desktop
- **`w.ewmh_window_type`** ewmh window type
- **`w.title_height`** window title height
- **`w.border_width`** border width
- **`w.flags`** is a bytearray containing style flags and action
  flags. See also `w.flag()` method.
- **`w.win_name`** window name
- **`w.ico_name`** icon name
- **`w.win_vis_name`** window visible name
- **`w.ico_vis_name`** icon visible name
- **`w.res_class`** resolution class
- **`w.res_name`** resolution name
- **`w.mini_ico_dx`**, **`w.mini_ico_dy`** **ToDo these**
- **`w.mini_ico_depth`**
- **`w.winid_pix`**
- **`w.winid_mask`**
- **`w.mini_ico_filename`**
- **`w.ico_filename`**
- **`w.flag(i)`** returns the value of the i^th flag as 0/1 integer.

  **ToDo:** access flags by meaningful names.

  **ToDo:** It seems that FVWM sends window position relative to the
  current viewport. Shall we recalculate it to be absolute within the
  desk?
  
The winlist database is filled by `m.getwinlist()` method.
You can keep it up to date by inserting the following lines in your code
```
m.getwinlist()
m.register_handler(fvwmpy.M_FOR_WINLIST, m.h_updatewl)
m.mask |= fvwmpy.M_FOR_WINLIST
```


#### Config database
`m.config` is a database of configuration information sent in response
to *Send_ConfigInfo* command. It is a list of strings, each is a
module configuration line. In addition it has the following attributes

- **`c.DesktopSize`** the size of the desktop (in pages)
- **`c.ImagePath`** a tuple of strings, each is the path where FVWM
  searches for images
- **`c.XineramaConfig`** a tuple of integers. See FVWM manual pages
  for the meaning.
- **`c.ClickTime`** integer. Click time in milliseconds
- **`c.IgnoreModifiers`** tuple of integers. Modifiers that are ignored.
- **`c.colorsets`** list of colorsets, each represented as a list of
  strings.

  **ToDo:** We really need to parse colorsets and create meaningful
    access to it's fields.

#### FVWM Packets

`m.packet()` returns an instance of `fvwmpy._packet` class, which
inherits from `dict`. Attributes can also be accessed
via `p["attribute"]` which is completely equivalent to `p.attribute`
in that both raise `KeyError()` exception, if the attribute is missing.

It has always the following attributes
- **`p.ptype`** integer type of the packet. See `fvwmpy.M[X]_*` constants.
- **`p.name`** type of the packet as a character string matching "M[X]_*".
- **`p.time`** time stamp

If the packet was read using `p=m.packet(raw=True)` it will also have
- **`p.raw`** the bytearray representation of the packet as sent by
  FVWM, but without the header.

Other attributes/keys depend on the packet. They will only be set if
`pasre=True` passed to the `m.packet()` method.

Depending on the packet type the attributes are as follows.

- **`fvwmpy.M_NEW_PAGE`**
  - **`p.px`**, **`p.py`** coordinates of the nw corner of the current
    viewport
  - **`p.desk`** current desk
  - **`p.max_x`**, **`p.max_y`** sizes of the current viewport
  - **`p.nx`**, **`p.ny`** number of pages in the desktop
    in x and y directions.

- **`fvwmpy.M_NEW_DESK`**
  - **`p.desk`** current desk number

- **`fvwmpy.M_OLD_ADD_WINDOW`**, **`fvwmpy.M_EXTENDED_MSG`**,
  **`fvwmpy.M_UNKNOWN1`**
  - **`p.body`** body of the package as a bytearray 


- **`fvwmpy.M_RAISE_WINDOW`**, **`fvwmpy.M_LOWER_WINDOW`**,
  **`fvwmpy.M_DESTROY_WINDOW`**, **`fvwmpy.M_MAP`**, **`fvwmpy.M_WINDOWSHADE`**,
  **`fvwmpy.M_DEWINDOWSHADE`**, **`fvwmpy.MX_ENTER_WINDOW`**,
  **`fvwmpy.MX_LEAVE_WINDOW`**
  - **`p.window`** window id
  - **`p.frame`** frame window id

- **`fvwmpy.M_FOCUS_CHANGE`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.focus_change_type`**
  - **`p.text_pix`**
  - **`p.border_pix`**

- **`fvwmpy.M_ICONIFY`**, **`fvwmpy.M_DEICONIFY`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.ix`**,  **`p.iy`**
  - **`p.idx`**,  **`p.idy`**
  - **`p.fx`**,  **`p.fy`**
  - **`p.fdx`**,  **`p.fdy`**

- **`fvwmpy.M_WINDOW_NAME`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.win_name`**

- **`fvwmpy.M_ICON_NAME`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.ico_name`**

- **`fvwmpy.M_RES_CLASS`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.res_class`**

- **`fvwmpy.M_RES_NAME`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.res_name`**

- **`fvwmpy.END_WINDOWLIST`**, **`M_END_CONFIG_INFO`**
  None

- **`fvwmpy.M_ICON_LOCATION`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.ix`**, **`p.iy`**
  - **`p.idx`**, **`p.dy`**

- **`fvwmpy.M_ERROR`**, **`fvwmpy.M_CONFIG_INFO`**,
  **`fvwmpy.M_SENDCONFIG`**
  - **`p.string`**

- **`fvwmpy.M_ICON_FILE`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.ico_filename`**

- **`fvwmpy.M_DEFAULTICON`**
  - **`p.ico_defaultfilename`**

- **`fvwmpy.M_STRING`**, **`fvwmpy.MX_REPLY`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.string`**

- **`fvwmpy.M_MINI_ICON`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.mini_ico_dx`**, **`p.mini_ico_dy`**, 
  - **`p.mini_ico_depth`**
  - **`p.winid_pix`**
  - **`p.winid_mask`**
  - **`p.mini_ico_filename`**

- **`fvwmpy.M_VISIBLE_NAME`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.win_vis_name`**

- **`fvwmpy.M_RESTACK`**
  - **`p.win_stack`** list of triples of integers

- **`fvwmpy.MX_VISIBLE_ICON_NAME`**
  - **`p.window`**
  - **`p.frame`**
  - **`p.ico_vis_name`**

- **`fvwmpy.MX_PROPERTY_CHANGE`**
  - **`p.prop_type`**
  - **`p.val_1`**
  - **`p.val_2`**
  - **`p.prop_str`**

- **`fvwmpy.ADD_WINDOW`**, **`fvwmpy.M_CONFIGURE_WINDOW`**
  The attributes of the packets of these types are the same as the
  first 29 attributes of an instance of `fvwmpy._window` class above
  (up to and including `w.flags`)
  


#### FVWM variables and InfoStore
One can access FVWM variables in two ways

1. `m.var.<var_name_with_underscores>` will be equal to the value of
   FVWM variable as a string. FVWM variables often have a dot in their
   names. To use this method you have to replace dots with
   underscores. That is `m.var.w_id` will return the value `$[w.id]`.
   You can not assign to or delete FVWM variables, so
   `m.var.w_id = <value>` or `del m.var.w_id` will raise
   `fvwmpy.IllegalOperation()` exception.

2. `m.var("var_name1",...,context_window=None)` will return a tuple
   with string-values of variables, whose names are given as string
   arguments. It is not necessary (but allowed) to replace dots with
   underscore in variable names, when using this method. If
   `context_window == None` then module's context_window is
   assumed. If `context_window == 0` then variable values are obtained
   outside of any context.

The second method obtains all variable values in one communication cycle
with FVWM, so it is preferable, when values of several variables are needed.

If no variable with such name exist the return value will be literally
`"$[{}]".format(varname)`.

It is not possible to get value of a variable, whose name contains
underscore. To the best of my knowledge there are no such variables,
at least none are mentioned in the FVWM man pages.

Similarly, one can access FVWM infostore database in two ways

1. `m.infostore.<var_name_with_underscores>` will be equal to the
   value of FVWM infostore variable as a string. You have to replace
   dots with underscores in variable names. For example
   `m.infostore.my_variable` will return the FVWM's value
   `$[infostore.my.variable]`.  You can also assign to or delete
   FVWM infostore variables, so
   `m.infostore.my_variable = <value>` or
   `del m.infostore.my_variable` are legal.

2. Similarly `m.infostore("var_name1",...)` will return a tuple
   with string-values of variables, whose names are given as string
   arguments. It is not necessary (but allowed) to replace dots with
   underscore in variable names. 

The second method obtains all variable values in one communication cycle
with FVWM, so it is preferable, when values of several variables are needed.
   
Beware that it is not possible to get the value of an infostore variable,
whose name contains underscore. 
