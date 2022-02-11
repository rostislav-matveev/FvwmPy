#!/usr/bin/python3

from fvwmpy import *

class fvwmmymod(fvwmpy):
    def dumppack(self,p):
        print(p,file=self.packfile)
        self.packfile.flush()
        
    def packet(self,*args,**kwargs):
        p = super().packet(*args,**kwargs)
        self.dumppack(p)
        return p
    
    def command(self,cmd):
        args = cmd.split()
        cmd = args[0]
        del args[0]
        if cmd == "var":
            self.info("Get variable {}={}","pointer.x",self.var.pointer_x)
            self.info("Get variables {}={}","(pointer.x,pointer.x)",
                      self.var("pointer_x","pointer_y") )
            self.info("In window context:")
            self.push_masks(M_STRING,0,0)
            self.sendmessage(
                "All (FvwmConsole) SendToModule {} $[w.id] $[w.name]".
                format(self.alias) )
            self.sendmessage(
                "SendToModule {} stop".
                format(self.alias) )
            windows = list()
            p=self.packet()
            while p.string != "stop":
                windows.append(p.string.split())
                p = self.packet()
                
            for w in windows:
                cw = int(w[0],0)
                wname = w[1]
                self.info("In window {}",wname)
                self.info( "Get variables {}={}","(w.id,pointer.wx,pointer.wy)",
                           self.var( "w.id","pointer_wx","pointer.wy",
                                     context_window = cw ) )
            self.restore_masks()
        elif cmd == "delvar":
            self.info("Try to delete page.nx")
            del self.var.page_nx
        elif cmd == "setvar":
            self.info("Try to set page.nx")
            self.var.page_nx = 7
        elif cmd == "infostore":
            self.info("Set infostore {}={}","var.1",17)
            self.infostore.var_1=17
            self.info("Set infostore {}={}","var.2","string value")
            self.infostore.var_2="string value"
            self.info("Get infostore {}={}","var.2",self.infostore.var_2)
            self.info("Get infostores {}={}","(var.1,var.2)",
                      self.infostore("var.1","var_2") )
            self.info("Get infostores {}={}","(var.1,var.2,unknown)",
                      self.infostore("var.1","var_2","unknown") )
            self.info("Get infostore {}={}","unknown",
                      self.infostore.unknown )
            self.info("Del infostore {}","unknown")
            del self.infostore.unknown
            self.info("Del infostore {}","var.1")
            del self.infostore.var_1
            self.info("Del infostore {}","var.2")
            del self.infostore.var_2
            self.info("Get infostores {}={}","(var.1,var.2,unknown)",
                      self.infostore("var.1","var_2","unknown") )
        elif cmd == "addmask":
            self.mask |= packetcodes[args[0].upper()]
            self.command("mask")
        elif cmd == "mask":
            self.info(" MASK")
            for m in split_mask(self.mask):
                self.info("\t{}",packetnames[m])
        elif cmd == "removemask":
            self.mask &= ~packetcodes[args[0].upper()]
            self.command("mask")
        elif cmd == "config":
            self.getconfig(match = "")
        elif cmd == "winlist":
            self.getwinlist()
        elif cmd == "exit":
            self.exit(0)
        elif cmd == "sendmessage":
            self.message(" ".join(args))
        elif cmd == "dumpwinlist":
            with open("winlist.txt","wt") as file:
                print(self.winlist,file=file)
        elif cmd == "dumpconfig":
            with open("config.txt","wt") as file:
                print(self.config,file=file)
                print(self.config.colorsets,file=file)
        elif cmd == "filterwinlist":
            self.getwinlist()
            condition = """
  	    !FixedSize,
  	    !Shaded,!Iconic,CurrentPage
  	    !Fvwm*
  	    """
            self.info("Filtered winlist")
            for w in self.winlist.filter(condition):
                self.info("Window {}",w.win_name)

    def h_cmd(self,p):
        self.command(p.string)
        
m=fvwmmymod()
m.logginglevel = L_INFO
m.mask         = M_STRING | MX_REPLY | M_ERROR
m.syncmask     = 0
m.nograbmask   = 0
m.packfile = open('packfile.txt',"wt")
m.register_handler(M_STRING, m.h_cmd)
m.info("Start {} as {}",m.me,m.alias)
m.run()


