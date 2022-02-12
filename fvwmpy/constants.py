import struct as _struct
################################################################################
### logging levels
from logging import CRITICAL as L_CRITICAL
from logging import DEBUG    as L_DEBUG
from logging import ERROR    as L_ERROR
from logging import INFO     as L_INFO
from logging import NOTSET   as L_NOTSET
from logging import WARN     as L_WARN

################################################################################
### FVWM contexts

C_NO_CONTEXT  =     0 # no context
C_WINDOW      =     1 # an application window
C_TITLE       =     2 # a title bar
C_ICON        =     4 # an icon window
C_ROOT        =     8 # the root window
C_FRAME       =    16 # a corner piece
C_SIDEBAR     =    32 # a side-bar
C_L1          =    64 # left button #1
C_L2          =   128 # left button #2
C_L3          =   256 # left button #3
C_L4          =   512 # left button #4
C_L5          =  1024 # left button #5
C_R1          =  2048 # right button #1
C_R2          =  4096 # right button #2
C_R3          =  8192 # right button #3
C_R4          = 16384 # right button #4
C_R5          = 32768 # right button #5
C_UNKNOWN     = -1

contexts=( "C_NO_CONTEXT", "C_WINDOW", "C_TITLE", "C_ICON", "C_ROOT",
           "C_FRAME", "C_SIDEBAR",
           "C_L1", "C_L2", "C_L3", "C_L4", "C_L5", "C_R1", "C_R2", "C_R3",
           "C_R4", "C_R5", "C_UNKNOWN" )

contextnames = { globals()[k] : k for k in contexts}
contextcodes = { k : globals()[k] for k in contexts}
del contexts

################################################################################
### FVWM packet types.

### We use different conventions for extended packets
### so that fvwm's (1<<31) + (1<<n) becomes (1 << (32+n))
### Conversion is taken care of automatically when reading the packet
### from the pipe or when setting masks.
### In addition M_UNKNOWN = (1 << 37) is introduced, to assign to packets that
### are not recognized 
M_NEW_PAGE       	= (1 << 0 )
M_NEW_DESK             	= (1 << 1 )
M_OLD_ADD_WINDOW       	= (1 << 2 )
M_RAISE_WINDOW         	= (1 << 3 )
M_LOWER_WINDOW         	= (1 << 4 )
M_OLD_CONFIGURE_WINDOW 	= (1 << 5 )
M_FOCUS_CHANGE         	= (1 << 6 )
M_DESTROY_WINDOW       	= (1 << 7 )
M_ICONIFY              	= (1 << 8 )
M_DEICONIFY            	= (1 << 9 )
M_WINDOW_NAME          	= (1 << 10)
M_ICON_NAME            	= (1 << 11)
M_RES_CLASS            	= (1 << 12)
M_RES_NAME             	= (1 << 13)
M_END_WINDOWLIST       	= (1 << 14)
M_ICON_LOCATION        	= (1 << 15)
M_MAP                  	= (1 << 16)
M_ERROR                	= (1 << 17)
M_CONFIG_INFO          	= (1 << 18)
M_END_CONFIG_INFO      	= (1 << 19)
M_ICON_FILE            	= (1 << 20)
M_DEFAULTICON          	= (1 << 21)
M_STRING               	= (1 << 22)
M_MINI_ICON            	= (1 << 23)
M_WINDOWSHADE          	= (1 << 24)
M_DEWINDOWSHADE        	= (1 << 25)
M_VISIBLE_NAME         	= (1 << 26)
M_SENDCONFIG           	= (1 << 27)
M_RESTACK              	= (1 << 28)
M_ADD_WINDOW           	= (1 << 29)
M_CONFIGURE_WINDOW     	= (1 << 30)
M_EXTENDED_MSG         	= (1 << 31)

MX_VISIBLE_ICON_NAME   	= (1 << 32 )
MX_ENTER_WINDOW        	= (1 << 33 )
MX_LEAVE_WINDOW        	= (1 << 34 )
MX_PROPERTY_CHANGE      = (1 << 35 )
MX_REPLY               	= (1 << 36 )

M_UNKNOWN1              = (1 << 37 )

M_ALL = ((1<<37)-1)

### These are packets that are sent when window list is requested
M_FOR_WINLIST  = ( M_CONFIGURE_WINDOW | M_ADD_WINDOW | M_WINDOW_NAME |
                   M_ICON_NAME |
                   M_VISIBLE_NAME | MX_VISIBLE_ICON_NAME | M_RES_CLASS |
                   M_RES_NAME | M_MINI_ICON | M_END_WINDOWLIST |
                   M_DESTROY_WINDOW )

### This are packets that are sent when configuration is requested
M_FOR_CONFIG   = ( M_CONFIG_INFO | M_END_CONFIG_INFO | M_SENDCONFIG )

packets = { "M_NEW_PAGE", "M_NEW_DESK", "M_OLD_ADD_WINDOW", "M_RAISE_WINDOW",
            "M_LOWER_WINDOW", "M_OLD_CONFIGURE_WINDOW", "M_FOCUS_CHANGE",
            "M_DESTROY_WINDOW", "M_ICONIFY", "M_DEICONIFY", "M_WINDOW_NAME",
            "M_ICON_NAME", "M_RES_CLASS", "M_RES_NAME", "M_END_WINDOWLIST",
            "M_ICON_LOCATION", "M_MAP", "M_ERROR", "M_CONFIG_INFO",
            "M_END_CONFIG_INFO", "M_ICON_FILE", "M_DEFAULTICON", "M_STRING",
            "M_MINI_ICON", "M_WINDOWSHADE", "M_DEWINDOWSHADE",
            "M_VISIBLE_NAME", "M_SENDCONFIG", "M_RESTACK", "M_ADD_WINDOW",
            "M_CONFIGURE_WINDOW", "M_EXTENDED_MSG", "MX_VISIBLE_ICON_NAME",
            "MX_ENTER_WINDOW", "MX_LEAVE_WINDOW", "MX_PROPERTY_CHANGE",
            "MX_REPLY", "M_UNKNOWN1" }

### get the name of the packet from value
packetnames = { globals()[k] : k for k in packets }
packetcodes = { k : globals()[k] for k in packets }
del packets

#################################################################
### communication with FVWM
### First word in packets sent from FVWM.
FVWM_PACK_START    = int("0xffffffff",0)
FVWM_PACK_START_b  = _struct.pack("L",FVWM_PACK_START)

NOT_FINISHED       = _struct.pack("L",1)
FINISHED           = _struct.pack("L",0)

LONG_SIZE          = _struct.calcsize("L")

### This is used for encoding/decoding strings sent to/from fvwm
#FVWM_STR_CODEX             = "ascii"
FVWM_STR_CODEX     = "utf8"
