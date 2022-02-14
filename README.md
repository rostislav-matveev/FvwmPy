# fvwmpy -- framework for developing FVWM modules in python

This module defines class `fvwmpy`, that can be used by itself or as a
base for derived classes for writing FVWM modules.  

## License
This module is released under GPLv3 license.

## Declaration
I love FVWM

## Features
- Simple interface for communication with the window manager.
- Asyncronous access to the packet queue.
- Possibility of maintaining dynamically updated list of windows and
  their properties.
- Possibility to iterate over windows satisfying given conditions.  
- Possibility of dynamically changing configuration
- Simple interface for accessing FVWM's variables and infostore
  database.
- Compatible with tkinter
- Simple interface for masking packets from FVWM
- Support for the concept of module aliases

A simple example of a module using fvwmpy may be written along the
following lines 
```
#!/usr/bin/python3
import fvwmpy

class myfvwmmodule(fvwmpy.fvwmpy):
    def h_config(self,pack):
        # process config lines from FVWM database
	
    def h_handler1(self,pack):
        # respond to the pack

    def h_handler2(self,pack):
        # respond to the pack
    ...

m = myfvwmmodule()
m.logger.setLevel(fvwmpy.L_DEBUG)

### Keep FVWM mute while we are setting things up
m.mask       = 0
m.syncmask   = 0
m.nograbmask = 0

### Check command line arguments
for arg in m.args:
   # process arg

### If we want to dynamically update configuration:
m.register_handler(fvwmpy.M_SENDCONFIG, m.h_config)

### If we want to keep config database up to date:
m.register_handler(fvwmpy.M_SENDCONFIG, m.h_saveconfig)


### If we want to have up to date list of windows
m.register_handler(fvwmpy.M_FOR_WINLIST, m.h_updatewl)

### Register handlers
m.register_handler(mask1,m.h_handler1)
m.register_handler(mask2,m.h_handler2)
...

### set masks
m.mask       = <some mask>
m.syncmask   = <some smask>
m.nograbmask = <some ngmask>

### for up to date winlist
m.mask |= fvwmpy.M_FOR_WINLIST

### for updating config dynamically
m.mask |= fvwmpy.M_SENDCONFIG 

### If we want FVWM to wait while we update config
m.syncmask |= fvwmpy.M_SENDCONFIG
m.register_handler(fvwmpy.M_SENDCONFIG, m.h_unlock)

### Tell FVWM that we are ready
m.finishedconfig()

### Fill the config database
m.getconfig()

### Read FVWM's database of module configuration lines and parse them
m.getconfig(m.h_config)

### Fill the winlist database
m.getwinlist()

### Do some other module stuff
m.info(' Looks like FVWM manages {} windows now',len(m.winlist))
...

### If the module is persistent (listens to FVWM and executes handlers)
m.run()
### otherwise
m.exit()
```

More snippets and examples are below.

## Structure of the `fvwmpy` module

The module define the following constants, functions and classes.

### Constants
The following constants are defined within the module

- **`fvwmpy.C_*`**

  Integers.
  
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

  Integers.
  
  Types of packets send from FVWM to the module. See section
  **packets**
  [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for the
  full list and meaning of packet types and other details.  In
  addition there are the following masks:

  - `fvwmpy.M_ALL` - matches all packet types;
  - `fvwmpy.M_FOR_WINLIST`
    matches packets emitted by FVWM during response to
    *'Send_WindowList'* command and `fvwmpy.M_DESTROY_WINDOW` and
    `fvwmpy.M_ADD_WINDOW`
  - `fvwmpy.M_FOR_CONFIG` -- mask matching all packets emitted by FVWM
    in response to *'Send_ConfigInfo'* command and `fvwmpy.M_SENDCONFIG`

- **`fvwmpy.packetnames`**

  Dictionary for converting packet types to their names.
  E.g.

  `fvwmpy.packetnames[fvwmpy.MX_LEAVE_WINDOW] == 'MX_LEAVE_WINDOW'`

- **`fvwmpy.packetcodes`**

  The inverse dictionary of `fvwmpy.packetnames`

- **`fvwmpy.FVWM_PACK_START`** and **`fvwmpy.FVWM_PACK_START_b`**

  Delimiter used by FVWM to tag the start of each packet.
  `FVWM_PACK_START` is an integer and `FVWM_PACK_START_b` is its
  bytes representation.

- **`fvwmpy.FINISHED`** and **`fvwmpy.NOT_FINISHED`**

  bytearrays containing tags to be sent to FVWM at the end of every
  message to notify whether module intends to continue or has finished
  working and is about to exit.

- **`fvwmpy.LONG_SIZE`**

  Integer. The size of C's long in bytes.

- **`fvwmpy.FVWM_STR_CODEX`**

  String. Codex for en/de-coding strings during communication with FVWM.

- **`fvwmpy.VERSION`**

  String. Naturally contains information about current version of the
  module.

- **`fvwmpy.L_CRITICAL`**, **`fvwmpy.L_ERROR`**, **`fvwmpy.L_WARN`**,
  **`fvwmpy.L_INFO`**, **`fvwmpy.L_DEBUG`**, **`fvwmpy.L_NOTSET`**

  Integer.
  
  Constants for setting logging level. For `fvwmpy.fvwmpy` and
  `fvwmpy.packet_reader` object or `fvwmpy.packet` class you can
  set `object.logger.setLevel(fvwmpy.L_DEBUG)` to see a lot of output
  from inner working of these objects. See also
  `object.debug`,...,`object.critical` methods below.

### Exceptions

- **`fvwmpy.FvwmPyException`**

  Base exception from which others are derived.

- **`fvwmpy.FvwmLaunch`**

  This exception is raised when the module can not start up normally,
  e.g it is not executed by FVWM, pipes can not be opened, etc.

- **`fvwmpy.IllegalOperation`**

  raised when one trying restore masks without saving them first, etc.
  It is also raised when one attempts to assign to FVWM variables (not
  infostore)

- **`fvwmpy.FvwmError`**

  raised when FVWM does not understand communication from the
  module or the other way around.

- **`fvwmpy.PipeDesync`**

  This exception is raised if pipe desyncronization is detected,
  e.g. when the packet from FVWM does not have begin-tag or when the
  content of the packet does not match its format.
  Instances of `fvwmpy._packet_reader` class have method `.resync()` to seek the
  stream to the next pack. See **packet queue** section for more details.

  
### Helper functions

- **`fvwmpy.split_mask(mask)`**

  `mask` is a mask used for packet matching.
  
  Returns a tuple of all packet types, that match the given mask.
  If all the packet types in the list are bitwise `or`ed, one gets the
  `mask` back.

- **`fvwmpy.unique_id()`**

  Returns a unique string, which almost guarantied not to match
  anything ever sent by FVWM. Can be used for tagging *'SendReply'*
  FVWM-command. Each invocation returns a different string.

- **`fvwmpy.picker(mask=None,**kwargs)`**

  Returns a callable object, that can be called on a packet and
  returns boolean value. See **Picker factory** section for more details.

- **`fvwmpy.glob(globstring)`**, **`fvwmpy.Glob(string)`**
  
  Both create glob patterns, against which you can match other
  strings.
  
  `globstring` is a string, that may contain '\*' and '?' characters
  and '[chars]' substrings.  Pattern '[chars]' may also contain ranges
  like '[a-z0-9]'.  Wildcard '\*' matches any substring, '?' matches
  any single character.  '[chars]' matches any single character which
  is one of 'chars'.  To match '\*' or '?' literally, use the
  corresponding character enclosed in '[]'.

  When glob instance is compared to another string with `==` or `!=`
  operator, it checks whether another string matches the pattern.

  E.g. `'abc*efg?xyz' == glob('*c[*]EFg[?]x??')` returns `True`.

  The difference between `glob` and `Glob` is that in the former
  matching is case insensitive, while objects of the later match
  string in a case-sensitive way, so
  `'abc*efg?xyz' == Glob('*c[*]EFg[?]x??')`  will be `False`.


### Class `fvwmpy.fvwmpy`

`m=fvwmpy.fvwmpy()`

Instances of `fvwmpy` have the following attributes and methods

#### Attributes

- **`m.me`**

  String. The name of the executable file containing the module

- **`m.alias`**

  String. Alias of the module. Alias is guessed from the command line
  arguments of the module during initialization. If the first
  command line argument does not start with '-', then it is assumed to
  be the alias of the module. Then `m.alias` is set (which affects
  logging functions and pruning of configuration lines) and this
  argument is not included in `m.args`. If the first argument is a
  single '-', then it is also removed from `m.args` and `m.alias` will
  be the same as `m.me`.  `m.alias` can not be changed afterwards.

- **`m.args`**

  List of strings. Contains command line arguments of the module. 
  If the first argument does not start with '-', then it is assumed to
  be the alias of the module. Then `m.alias` is set (which affects
  logging functions and pruning of configuration lines) and this
  argument is not included in `m.args`. If the first argument is a
  single '-', then it is also removed from `m.args`.
  
  -  If the module is invoked FVWM command
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
     Module FvwmMyModule -geometry 200x200+24+0 ...
     ```
     then `m.alias == 'FvwmMyModule'` and
     `m.args == ['-geometry', '200x200+24+0', ...]`
  
- **`m.mask`**

  Integer. Mask for communication from FVWM. The mask controls what
  kind of packets FVWM sends to the module. The normal and extended (bits
  higher then 32) masks are treated the same, so, for example
  `m.mask = fvwmpy.MX_LEAVE_WINDOW | fvwmpy.M_VISIBLE_NAME`
  is a legal instruction with intended consequences.

  Setting the mask to a new value will trigger communication with FVWM
  to let it know the new value, but only if the new value is
  different from the old, so no unnecessary communication takes
  place. Note, that if you previously changed the mask by some other
  method (sending an appropriate message to FVWM) the new value might
  not be communicated to the window manager when executing `m.mask =
  <new_value>`. Methods `m.push_mask()` and `m.restore_mask()` are
  safe to use in this respect.

  Every time new mask is set by `m.mask = newmask`,
  `m.mask_setter_hook('mask',newmask)` is called.
  `m.mask_setter_hook(...)` does nothing by default, but you may
  overload it, for example, to communicate new value of the mask to
  other parts of the program, e.g. gui.

  
  See `fvwmpy.M[X]_*` for possible values and interpretation thereof.

  See also `m.push_masks(...)` and `m.restore_masks()` methods for
  temporarily changing masks.
  
  See [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for
  the explanation of the concepts of masking.
  
- **`m.syncmask`** and **`m.nograbmask`**

  are similar to `m.mask` but contain values of syncmask and
  nograbmask, respectively. When new value is set,
  `m.mask_setter_hook('syncmask',newmask)` or
  `m.mask_setter_hook('nograbmask',newmask)` is called.

- **`m.context_window`**

  Integer. Contains id of the window in whose context the module was
  started or 0 if the module was executed outside of any window context.
  This will be used for all methods requiring context_window parameter
  if `None` is passed.
  
- **`m.context_deco`**

  Window decoration context in which module was started or 0 if  the
  module was executed outside of any window context. See `fvwmpy.C_*`
  and [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) for
  explanation of decoration contexts.

- **`m.logger`**

  A logger object associated with the instance.  You may call
  `m.logger.setLevel(<new_level>)` to change the severity threshold
  for logging messages.  Here `<new_level>` is one of the `fvwmpy.L_*`
  constants described above. `m.logger.level` is the current level.
  See also `m.debug`,...,`m.critical` methods below.

- **`m.config`**

  `m.config` is the database containing information sent by FVWM
  during execution of *Send_ConfigInfo* command and with `M_SENDCONFIG`
  packets. See also `m.getconfig()` method and `m.h_saveconfig()` handler.
  For more details see **config database** below

- **`m.winlist`** 

  `m.winlist` is the database of windows known to FVWM indexed by
  window id's. It can be filled by calling `m.getwinlist()` method. It
  is also possible to arrange to have `m.winlist` to be up to date at
  all times. See information on `m.h_updatewl` handler.
  
  `m.winlist` inherits from `dict`. `m.winlist[<window_id>]` is an
  instance of `fvwmpy._window` class and contains all the information
  about the window, that FVWM cares to communicate to us.
  For more details see **winlist database** below

  In addition to the usual `dict` methods it also has method
  `w.winlist.filter(conditions)` which return an iterator for cycling
  through windows satisfying conditions. It is described in more
  details in **winlist database** section.
  
- **`m.handlers`**

  A dictionary whose keys are packet types and values are lists of
  handler functions, each of which takes one argument, which is a
  packet.
  Initially all lists are empty. It is not advised to access it directly.
  See  `m.register_handler()`,  `m.unregister_handler()`,
  `m.clear_handlers()`, `m.registered_handler()` and
  `m.call_handlers()` methods and **handlers** section below.

- **`m.var`** and **`m.infostore`**

  These are special objects providing access to FVWM variables and
  infostore database.
  
  See **FVWM variables and infostore** below

- **`m.packets`**

  A packets queue from FVWM.
  
  See **Packets** section for the description and the structure of the
  packet data type.

#### Methods

     For all methods requiring context_window parameter if `None` is
     given, module's own context window is assumed.

- **`m.debug()`**, **`m.info()`**, **`m.warn()`**,
  **`m.error()`** and **`m.critical()`**

  logging functions. They should be called

  `m.<log_fcn>(message_string, *arguments)`
  
  and use `message_string.format(*arguments)` formatting paradigm.
  Logging messages are directed to *stderr*. For the module
  *stderr*-stream will be the same as for FVWM. Logging functions
  print the severity level followed by the alias of the module
  followed by the formatted message. The behavior of these functions
  is affected by the value of `m.logger.level`. Only messages with
  severity not less then `m.logger.level` will be printed.
  Use `m.logger.setLevel(value)` to change logging level.
  
- **`m.sendmessage(msg, context_window=None, finished=False)`**

  Send a (possibly multi-line) message to FVWM for execution in the
  context of `context_window`.

  `msg` is a multi-line string conatining FVWM commands. Empty lines
  (only with white spaces) are ignored. For example
  the following works
  ```
  cmds="""
       Focus
       WarpToWindow {} {}
       """
  m.sendmessage(cmd.format(30,50), context_window = wid )
  ```
  If `context_window` is not given or `None`, then the window context
  will be equal to the context at which module was called (that is
  `m.context_window`). If `context_window==0`, then FVWM executes
  commands without window context.  

  If `finished` then FVWM will be notified that the module is done
  working and is about to exit soon.

  Every time `m.sendmessage(...)` is executed `m.sendmessage_hook()`
  with the same arguments will also be called.
  `m.sendmessage_hook()` does nothing, but can be overloaded, for
  example to let GUI part know that a message was sent.

- **`m.getreply(msg,context_window=None)`**

  Send string message 'msg' to FVWM and request to send it back in the
  context `context_window`.
  
  There is no need to change masks before/after invoking this method,
  it works independently of the current values of masks.

  This method works reliably independently whether there are unhandled
  packets in the packet queue. The reply will be picked and removed
  from the queue and returned.
  ```
  ### Pollute the queue
  m.sendmessage('Send_WindowList')
  ### Now queue is full of packets
  
  w_name = m.getreply('$[w.name]',context_window=123456789)
  ### reply packet is found in the queue and is removed from it
  
  # do something with  w_name
  # handle packets remaining in the queue
  ```


- **`m.getconfig(handler=None, match=None)`**

  Ask FVWM for configuration info. Each received packet is passed to
  the `handler`.

  `handler` must be `None` or a callable taking one argument, which is a
  packet of type matching `fvwmpy.M_FOR_CONFIG`. If `handler` is not
  supplied then default handler `m.h_saveconfig` is
  used. `m.h_saveconfig` just fills `m.config` database with the
  information received from FVWM.

  `match` must be `None` or a string to match module configuration
  lines against.  If not supplied then `'*' + m.alias` is assumed.  If
  `match == ""` then all configuration lines are received and
  processed.

  There is no need to change masks before/after invoking this method,
  it works independently of the current values of masks.

  This method works reliably independently of the state of the packet
  queue. Even if queue is not empty at the start of this call,
  configuration packets will be found in the queue and removed from
  it. So the following works reliably
  ```
  ### Pollute the queue
  m.sendmessage('Send_WindowList')
  ### Now queue is full of packets
  m.getconfig()
  ### m.config is updated and config messages are removed from the
  ### queue

  # handle the packets remaining in the queue
  ```
  If you want to keep config database up to date all the time, then
  include the following
  ```
  m.getconfig()
  m.register_handler(fvwmpy.M_SENDCONFIG, m.h_saveconfig)
  m.mask |= fvwmpy.M_SENDCONFIG
  ```
  somewhere in your code.

  See **Config database** for more information and how to have config
  database up to date all the time.

- **`m.getwinlist(handler = None)`**

  Ask FVWM for the list of all windows it manages. Each packet
  received in response is passed to the handler.

  `handler` should be a callable taking one argument, which is a
  packet of type matching `fvwmpy.M_FOR_WINLIST`. If `handler` is not
  supplied then default handler `m.h_updatewl` is used. `m.h_updatewl`
  simply updates `m.winlist` database with the information received
  from FVWM. It also understands `fvwmpy.M_ADD_WINDOW` and
  `fvwmpy.M_DESTROY_WINDOW` packets removing corresponding entries
  from the database.

  It is not necessary to adjust the values of the masks before or
  after invoking `fvwmpy.getwinlist()`. It works independently of the
  current values of masks and preserves them.
  
  This method works reliably independently of the state of the packet
  queue. Even if queue is not empty at the start of this call,
  `fvwmpy.M_FOR_WINDOWLIST`-type packets will be found in the queue and removed from
  it. So the following works reliably
  ```
    ### Pollute the queue
  m.sendmessage('Send_ConfigInfo')
  ### Now queue is full of packets

  ### Mute FVWM
  m.mask = 0

  m.getwinlist()
  ### m.winlist is updated and the corresponding packets are
  ### removed from the queue

  ### m.mask is still 0
  
  # handle the packets remaining in the queue
  ```

  Note that `m.getwinlist()` will also pick packets of type
  `M_ADD_WINDOW` or `M_DESTROY_WINDOW` (these packets are not send in
  response *'Send_WindowList'* request, but correspond to events in
  FVWM) and they will be also removed from the queue.
  
  If you want to keep `m.winlist` up to date all the time, then
  include the following
  ```
  m.getwinlist()
  m.register_handler(fvwmpy.M_FOR_WINLIST, m.h_updatewl)
  m.mask |= fvwmpy.M_FOR_WINLIST
  ```
  somewhere in your code.
  
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

  Set mask, syncmask and nograbmask to new values temporarily.
  If any of the values is `None` than the corresponding mask is left
  unchanged.
  
  It is possible to have several embedded
  `m.push_masks`--`m.restore_masks` constructs.

- **`m.restore_masks()`**

  Restore masks previously overridden by `m.push_masks`.
  If mask stack is empty (more `m.restore_masks()`'s then
  `m.push_masks()`'s)
  `fvwmpy.IllegalOperation` exception is raised.

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

  There are some predefined packet handlers, (see below) but one could
  define more as functions or as methods in the derived class.
  
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
  `m.call_handlers()` on all packets received from FVWM except those
  which are removed from the queue by `m.get*` methods or
  `m.packets.pick(...,keep=False)` method.

- **`m.clear_handlers(mask)`**

  Clear all execution queues for packets matching `mask`.

- **`m.registered_handler(handler)`**

  Return the mask for the queues where handler is registered.

- **`m.run()`**

  Enter mainloop which simply reads packets from FVWM and for each
  packet executes handlers in the queue, until
  `m.exit()` or `m.h_exit()` method is called. It could be overloaded
  in the derived class.
  
##### Supplied handlers

- **`m.h_saveconfig(pack)`**

  Packets type: `M_FOR_CONFIG`
  
  This handler is capable of processing packets matching
  `fvwmpy.M_FOR_CONFIG`. It simply records the information in
  `m.config` database. You can insert the following lines in your code
  to keep the database up to date
  ```
  m.getconfig()
  m.register_handler(fvwmpy.M_FOR_CONFIG, m.h_saveconfig)
  m.mask |= fvwmpy.M_SENDCONFIG | fvwmpy.M_CONFIG_INFO
  ### If you want to process config in a synchronous manner
  m.register_handler(fvwmpy.M_FOR_CONFIG, m.h_unlock)
  m.syncmask |= fvwmpy.M_SENDCONFIG|fvwmpy.M_FOR_CONFIG
  ```
  `m.h_saveconfig(pack)` does not send *NOP UNLOCK* command to FVWM.
  In case you want to process configuration information synchronously
  register  `m.h_unlock` after `m.h_saveconfig`.

- **`m.h_unlock(pack)`**

  Packets type: `M_ALL`

  This handler completely ignores its argument and sends the *NOP UNLOCK*
  command to FVWM. FVWM waits for *NOP UNLOCK* after sending packets
  matching `m.syncmask`, so it make sense to always
  ```
  m.register_handler(m.syncmask,m.h_unlock)
  ```
  after all other handlers are added.
  If syncmask changes one should
  ```
  m.unregister_handler(fvwmpy.M_ALL, m.h_unlock)
  m.register_handler(m.syncmask, m.h_unlock)
  ```
  to make sure that  `m.h_unlock` is the last one in the queues
  
- **`m.h_exit(pack)`**

  Packet types: `M_ALL`

  This handler ignores its argument, cleans things up and terminates the
  module.

- **`m.h_nop(pack)`**

  Packet types: `M_ALL`

  Do nothing.
  
- **`m.h_updatewl(pack)`**

  Packet types: `M_FOR_WINLIST | M_ADD_WINDOW | M_DESTROY_WINDOW`
  
  This handler is capable to process packets matching
  `fvwmpy.M_FOR_WINLIST`. It uses information in the packet to update
  `m.winlist` database.
  
  
#### FVWM variables and InfoStore

Instances of `fvwmpy.fvwmpy` have two special objects `m.var` and
`m.infostore`, which provide access to FVWM variables and FVWM
infostore database in a transparent manner.

  The value of a variable (even non-existent) is always a string.
  If variable `no_such_var` does not exist in FVWM environment,
  the access methods below will return the literal string
  `'$[no.such.var]'`. It is client's business to check for this and to
  perform type casting, when necessary.

  The behavior of infostore database is analogous.

- **`m.var`**

  One can access FVWM variables in two ways

  1. `m.var.<var_name_with_underscores>` will be equal to the value of
      FVWM variable as a string. FVWM variables often have a dot in
      their names. To use this method you have to replace dots with
      underscores. That is `m.var.w_id` will return the value
      `$[w.id]`.  You can not assign to or delete FVWM variables, so
      `m.var.w_id = <value>` or `del m.var.w_id` will raise
      `fvwmpy.IllegalOperation()` exception.

   2. `m.var('var_name1',...,context_window=None)` will return a tuple
      with string-values of variables, whose names are given as string
      arguments. It is not necessary (but allowed) to replace dots
      with underscore in variable names, when using this method. If
      `context_window == None` then module's context_window is
      assumed. If `context_window == 0` then variable values are
      obtained outside of any context.

  The second method obtains all variable values in one communication
  cycle with FVWM, so it is preferable, when values of several
  variables are needed.

  It is not possible to get value of a variable, whose name contains
  underscore. To the best of my knowledge there are no such variables,
  at least none are mentioned in the FVWM man pages.

- **`m.var`**

  Similarly, one can access FVWM infostore database in two ways

  1. `m.infostore.<var_name_with_underscores>` will be equal to the
      value of FVWM infostore variable as a string. You have to
      replace dots with underscores in variable names. For example
      `m.infostore.my_variable` will return the FVWM's expansion of
      `$[infostore.my.variable]`.  You can also assign to or delete
      FVWM infostore variables, so `m.infostore.my_variable = <value>`
      or `del m.infostore.my_variable` are legal.

  2. Similarly `m.infostore('var_name1',...)` will return a tuple with
      string-values of variables, whose names are given as string
      arguments. It is not necessary (but allowed) to replace dots
      with underscore in variable names.

  The second method obtains all variable values in one communication cycle
  with FVWM, so it is preferable, when values of several variables are needed.
   
  Beware that it is not possible to get the value of, assign to, or
  delete an infostore variable, whose name contains underscore.

Access methods for both FVWM variables and infostore variables work
reliably independently of the state of the packet queue. So you may
have some stale packets in the queue and still get the values.
  
Note that each access attempt results in communication with FVWM, so it
is better access once and store values, if needed.
```
### Bad practice, 4 communication cycles with FVWM
area      = int(m.var.w_width) * int(m.var.w_height)
perimeter = 2*int(m.var.w_width) + 2*int(m.var.w_height)

### Good practice, 1 communication with FVWM
width, height = map( int, m.var('w.width','w.height') )
area      = width * height
perimeter = 2 * (width + height)
```


#### Winlist database **`m.winlist`**

`m.winlist` is a dictionary of windows indexed by window id's.  Each
window is an instance of `fvwmpy._window` class and has the attributes
and methods listed below. 

m.winlist has all the usual methods inherited from `dict`
and one extra described below.

- **`m.winlist.filter(conditions)`**

  This method returns an iterator that cycle through windows matching
  `conditions`

  `conditions` is a string containing the same conditions that are
  allowed in FVWM's conditional commands. See FVWM manual pages for
  explanations. For formatting convenience `conditions` may be a
  multi-line string. As an example look at the following (not very useful)
  snippet
  ```
  condition = """
  	      !FixedSize, !FixedPosition, 
  	      !Shaded,!Iconic,CurrentPage
  	      !Fvwm*, !stalonetray
  	      """
  for w in m.windowlist.filter(condition):
      dx = max( w.wdx//2, w.hints_min_width  )
      dy = max( w.wdy//2, w.hints_min_height )
      m.sendmessage( 'Resize {}p {}p'.format(dx,dy),
      		     context_window=w.window        )
  ```
  
  Note that `winlist.filter` may have troubles, if the
  winlist database is not up to date.

  Winlist has \_\_str\_\_ method which gives some nice human readable
  representation of entire database. The following very simple module
  will print the database into the file when it is instructed to
  do so by FVWM command *'SendToModule MyModule dumpwinlist'*
  
  ```
  class MyModule(fvwmpy.fvwmpy):					
      def h_dumpwinlist(self,p):
          if p.string == glob('dumpwinlist *'):
              with open('winlist.txt','wt') as file:
                  print(self.winlist,file=file)
          elif p.string == glob('exit *'):
	      self.exit()

  m=MyModule()
  m.register_handler(fvwmpy.M_STRING,m.h_dumpwinlist)
  m.register_handler(fvwmpy.M_FOR_WINLIST,m.h_updatewl)
  m.finishedconfig()
  
  m.mask       = fvwmpy.M_STRING | fvwmpy.M_FOR_WINLIST
  m.syncmask   = 0
  m.nograbmask = 0
  m.getwinlist()
  m.run()
  ```
  
##### Attributes and methods of instances of `fvwmpy._window` class.

  For more comprehensive information and meaning of different
  attributes refer to [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) and
  consult **fvwm.h, window_flags.h, Module.h vpacket.h** files in FVWM
  source tree.

  Each value of `m.winlist` is `fvwmpy._window` object.
  `fvwmpy._window` inherits from `dict`. Values of the dictionary can
  also be accessed as attributes via `w.key`, which is completely
  equivalent to `w['key']`. Also both raise `KeyError()` exception,
  if the key/attribute is missing.

  The attributes/keys are

- **`w.window`** window id
- **`w.frame`** id of the frame window
- **`w.wx`**, **`w.wy`** x,y location of the window’s frame
- **`w.wdx`**, **`w.wdy`** width and height of the window’s frame
- **`w.desk`** desktop number
- **`w.layer`** layer
- **`w.hints_base_width`**, **`w.hints_base_height`** window base width
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
- **`w.mini_ico_filename`** **NOTE** there seems to be a bug in
  FVWM. This value can not be decoded to a meaningful string with
  neither 'ascii' nor 'utf8' codex.
- **`w.ico_filename`**
- **`w.flag(i)`** returns the value of the i^th flag as 0/1 integer.

  **ToDo:** access flags by meaningful names.

  **ToDo:** It seems that FVWM sends window position relative to the
  current viewport. Shall we recalculate it to be absolute within the
  desk? 
  
The winlist database is filled by `m.getwinlist()` method.
You can keep it up to date, see examples above.

#### Config database
`m.config` is a database of configuration information sent in response
to *Send_ConfigInfo* command. It is a list of strings, each is a
module configuration line.

  **Note** Each configuration line is concatenation of module name and
  configuration parameters without any delimiter. So the line
  `*FvwmMymodule:Geometry 100x100+0-0` in FVWM's config is passed to
  the module as '*FvwmMymoduleGeometry 100x100+0-0'. I am not sure
  whether this is a FVWM bug or intentional.


In addition it has the following attributes

- **`m.config.DesktopSize`** the size of the desktop (in pages)
- **`m.config.ImagePath`** a tuple of strings, each is the path where FVWM
  searches for images
- **`m.config.XineramaConfig`** a tuple of integers. See FVWM manual pages
  for the meaning.
- **`m.config.ClickTime`** integer. Click time in milliseconds
- **`m.config.IgnoreModifiers`** tuple of integers. Modifiers that are ignored.
- **`m.config.colorsets`** list of colorsets, each represented as a list of
  strings.

**ToDo:** We really need to parse colorsets and create meaningful
access to them.
`m.config` has __str__ method that returns human readable
representation of the database. The following module prints it to file
when instructed by `SendToModule MyModule dumpconfig` command.
```
class MyModule(fvwmpy.fvwmpy):					
    def h_cmd(self,p):
        if p.string == glob('dumpwinlist *'):
            self.info('Save window list to winlist.txt')
            with open('winlist.txt','wt') as file:
                print(self.winlist,file=file)
        if p.string == glob('dumpconfig *'):
            self.info('Save config to config.txt')
            with open('config.txt','wt') as file:
                print(self.config,file=file)
        elif p.string == glob('exit *'):
            self.info('Exiting...')
            self.exit()

m=MyModule()
m.register_handler(fvwmpy.M_STRING,      m.h_cmd)
m.register_handler(fvwmpy.M_FOR_WINLIST, m.h_updatewl)
m.register_handler(fvwmpy.M_SENDCONFIG,  m.h_saveconfig)
  
m.mask       = ( fvwmpy.M_STRING     | fvwmpy.M_FOR_WINLIST |
                 fvwmpy.M_FOR_CONFIG | fvwmpy.M_SENDCONFIG    )
m.syncmask   = 0
m.nograbmask = 0

m.finishedconfig()

m.getwinlist()
m.getconfig()
m.run()	
```


#### Packet queue

An instance of `fvwmpy.fvwmpy` class has attribute `m.packets` that
represents the queue of packets from FVWM. The structure of each packet
data type is described below.
`m.packets` is an object of `fvwmpy._packet_reader` class.
One can change the level of logging produced by `m.packets` by calling
`m.packets.logger.setLevel(<new_level>)` where <new_level> is
one of `fvwmpy.L_*` constants described above. The default level is
`fvwmpy.L_WARN`, which makes it mostly quiet.

The packets are read from the FVWM-to-module pipe synchronously and
put into the queue.

`m.packets` has the following attributes and methods

- **`m.packets.__len__`

  You can see how many packets are waiting to be handled with
  `len(m.packets)`. 

- **`m.packets._queue_nonempty`**

  This is `threading.Event()` object which is set when the queue has
  packets in it. You can `m.packets._queue_nonempty.wait()` to block
  until a packet has arrived. It is unsafe and not advised to do so,
  but better use `m.packets.read()` method, because it takes care of
  clearing and setting the event when necessary.

- **`m.packets.clear()`**

  Empty the queue discarding all of its content.

- **`m.packets.read(blocking = True)`**

  Returns and removes the packet from the top of the queue. If queue
  is empty and `blocking` is `True` it waits for the packet to arrive.
  If queue is empty and `blocking` is `False`, return immediately with
  return value `None`.

  **ToDo:** Implement `timeout` parameter, so that when packet
  arrives return it immediately. If no packet has arrived in the empty
  queue within `timeout` milliseconds, return `None`.
  
- **`m.packets.peek(blocking = True)`**

  This is like `m.packets.read` method, except the packet remains in
  the queue and will be returned with the next `m.packets.read` or
  `m.packets.peek` call, unless it will have been  `m.packets.pick`ed
  meanwhile.
  
- **`m.packets.pick(picker, which='first', keep=False, timeout=500)`**

  Return all/first/last packet(s) from the queue for which
  `picker` evaluates to true, possibly removing them from the queue.
  
  **Note:** the return value is always a `tuple`, even if returning
  one or zero packets.

  **Note:**
  ```
  m.packets.pick( picker = lambda p: True,
                  which='last',
                  timeout=500   )
  ```
  can be used as `timeout`ed read.
  
  - `picker` is a callable, which takes single packet as an argument
    and returns a boolean value. Only packets for which `picker` is true
    are returned. See **Picker factory** section for a simple and
    flexible way to create such callables.

  - `which` must be one of 'first', 'last', 'all'.
    If the value is 'first' `m.packets.pick` returns the oldest
    packet satisfying conditions. If the value is 'last' the packet
    returned will be the most recent and for 'all' all matching
    packets will be returned.

  - `keep` is a boolean that indicates whether packets should be
    removed from the queue.

  - `timeout` is an integer that indicates how many milliseconds shall
    we wait until at least something is found. When no matching
    packets are found then `m.packets.pick` checks the queue at some
    regular intervals until `timeout` is exhausted.
    
    Note that if `which` is 'all' or 'last' and some packets are found
    at some point, then `m.packets.pick` returns whatever is found
    immediately, not waiting for the full `timeout`.

- **`m.packets.resync()`**

  It may happen that the pipe gets desyncronized and confusion arises
  as to where the boundaries of packets are. `m.packets.resync()`
  seeks to the beginning of the next packet in the pipe. These
  situations are dealt internally in `m.packets`, so it is unlikely
  that one has to deal with this on the user side.
  (Pipe desyncronization never happened so far during testing)

##### FVWM packets

`m.packets.{read,peek,pick}()` return an instance of `fvwmpy._packet`
class, which inherits from `dict`. Values can also be accessed via
`p.key` or `p['key']` which are completely equivalent in that both
raise `KeyError()` exception, if the key is missing.

The available keys/attributes depend on the packet and described below
for all types of packets. See [FVWM module
  interface](https://www.fvwm.org/Archive/ModuleInterface/) when each
  packet is sent and what information it contains.

Any packet has always the following attributes
- **`p.ptype`** - Integer. Type of the packet. See `fvwmpy.M[X]_*` constants.
- **`p.name`** - String. Type of the packet as a character string
  matching `glob('M[X]_*|M_*'). This is a property, there is no
  corresponding key.
- **`p.time`** - Integer. Time stamp
- **`p.body` - Bytearray. The raw body of the packet without the header.

Other attributes/keys depend on the packet. Below they are listed for
each type of packets.

- **`fvwmpy.M_NEW_PAGE`**
  - **`p.px`**, **`p.py`** - Integer. Coordinates of the NW corner of the current
    viewport.
  - **`p.desk`** - Integer. Current desk number.
  - **`p.max_x`**, **`p.max_y`** - Integer. Sizes of the current viewport.
  - **`p.nx`**, **`p.ny`** - Integer. Number of pages in the desktop
    in x- and y-directions.

- **`fvwmpy.M_NEW_DESK`**
  - **`p.desk`** - Integer. Current desk number.

- **`fvwmpy.M_OLD_ADD_WINDOW`**, **`fvwmpy.M_EXTENDED_MSG`**,
  **`fvwmpy.M_UNKNOWN1`**, **`fvwmpy.END_WINDOWLIST`**,
  **`M_END_CONFIG_INFO`** 

  None


- **`fvwmpy.M_RAISE_WINDOW`**, **`fvwmpy.M_LOWER_WINDOW`**,
  **`fvwmpy.M_DESTROY_WINDOW`**, **`fvwmpy.M_MAP`**, **`fvwmpy.M_WINDOWSHADE`**,
  **`fvwmpy.M_DEWINDOWSHADE`**, **`fvwmpy.MX_ENTER_WINDOW`**,
  **`fvwmpy.MX_LEAVE_WINDOW`**
  - **`p.window`** - Integer. Window id
  - **`p.frame`** - Integer. Frame window id

- **`fvwmpy.M_FOCUS_CHANGE`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.focus_change_type`**
  - **`p.text_pix`**
  - **`p.border_pix`**

- **`fvwmpy.M_ICONIFY`**, **`fvwmpy.M_DEICONIFY`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.ix`**,  **`p.iy`** - These and below are integers.
  - **`p.idx`**,  **`p.idy`**
  - **`p.fx`**,  **`p.fy`**
  - **`p.fdx`**,  **`p.fdy`**

- **`fvwmpy.M_WINDOW_NAME`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.win_name`** - String. Name of the window.

- **`fvwmpy.M_ICON_NAME`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.ico_name`** - String. Name of the icon window.

- **`fvwmpy.M_RES_CLASS`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.res_class`** - String.

- **`fvwmpy.M_RES_NAME`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.res_name`** - String.

- **`fvwmpy.M_ICON_LOCATION`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.ix`**, **`p.iy`** - These and below are integers.
  - **`p.idx`**, **`p.dy`**

- **`fvwmpy.M_ERROR`**, **`fvwmpy.M_CONFIG_INFO`**,
  **`fvwmpy.M_SENDCONFIG`**
  - **`p.string`** - String. The content depends on the type of the packet.

- **`fvwmpy.M_ICON_FILE`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.ico_filename`** - String. Name of the image file. 

- **`fvwmpy.M_DEFAULTICON`**
  - **`p.ico_defaultfilename`** - Supposed to be a string, but FVWM
  seems to send garbage.

- **`fvwmpy.M_STRING`**, **`fvwmpy.MX_REPLY`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.string`** - String.

- **`fvwmpy.M_MINI_ICON`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.mini_ico_dx`**, **`p.mini_ico_dy`** - Integer.
  - **`p.mini_ico_depth`** - Integer
  - **`p.winid_pix`**
  - **`p.winid_mask`**
  - **`p.mini_ico_filename`** - String.

- **`fvwmpy.M_VISIBLE_NAME`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.win_vis_name`** - String.

- **`fvwmpy.M_RESTACK`**
  - **`p.win_stack`** - List of triples of integers.

- **`fvwmpy.MX_VISIBLE_ICON_NAME`**
  - **`p.window`** - As above.
  - **`p.frame`** - As above.
  - **`p.ico_vis_name`** - String.

- **`fvwmpy.MX_PROPERTY_CHANGE`**
  - **`p.prop_type`** - Integer
  - **`p.val_1`**,  **`p.val_2`** - Integer
  - **`p.prop_str`** - String.

- **`fvwmpy.ADD_WINDOW`**, **`fvwmpy.M_CONFIGURE_WINDOW`**
  The attributes of the packets of these types are the same as the
  first 29 attributes of an instance of `fvwmpy._window` class above
  (up to and including `w.flags`)
  


## Picker factory

The `fvwmpy` module has a special class `fvwmpy.picker` that can be
used for creating callables that take a packet as an argument and
returns a boolean value. There are two invocation signatures

- **`fvwmpy.picker(fcn)`**

  `fcn` is a callable with packet as an argument. 
  Return a callable (picker object) equivalent to the `fcn` in the sense that
  `fvwmpy.picker(fcn)(p) == bool(fcn(p))` for any packet `p`.

- **`fvwmpy.picker(mask=None,**kwargs)`** 

  Returns a callable object, that can be called on a packet and
  returns boolean value.

  If
  ```
  pck = picker(mask=M, key1=val1, key2=val2,...)
  ```

  then `pck(p)` returns `True` iff the packet `p` matches mask `M` and has
  key:value pairs `key1:val1`, `key2:val2`,...

  If one of the keys is missing in packet `p`, then the return value
  of pck(p) is `False`. If mask is `None`, then no mask matching is performed.
  
  In place of `val1`, `val2`, you can use `glob` and `Glob` objects ,
  described above to check matching of strings against glob
  patterns. See examples below.

  picker objects can be conjoined with `|`, `&` or unary `~`
  operators. The resulting picker evaluated on packet `p` returns
  value which is `or`, `and` or `not` of the value(s) of operand(s)
  evaluated on `p`. These operators short-circuit from left to
  right. You can build arbitrary boolean polynomials with picker
  objects and the above operators.

  For example, if
  ```
  pck1 = (
           picker(win_name=glob('Fvwm*')  ) |
           picker(res_name=glob('*term*') )
	 )

  pck2 = picker(mask = M_ENTER_WINDOW|M_LEAVE_WINDOW, window=1234567)
  
  pck3 = picker(window = 987654321) & ~picker(mask=M_DESTROY_WINDOW)
  ```
  then `pck1(p)` will be true iff
  packet `p` has key 'win_name' with a string value starting with 'fvwm' OR
  if `p` has key 'res_name' with a value containing  'term'.

  `pck2(p)` will be only true for packets emitted by FVWM when
  pointer enters of leaves window with `id==1234567`.

  `pck3(p)` will evaluate true on all packets related to window with
  `id==987654321` except `M_DESTROY_WINDOW` packet.
  
  `picker` objects are handy for `m.packets.pick()` method, described
  above and also for use in packet handlers.
  
