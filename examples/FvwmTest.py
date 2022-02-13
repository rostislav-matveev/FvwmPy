#!/usr/bin/python3

from fvwmpy import *
import sys

class fvwmmymod(fvwmpy):
    def h_dumppack(self,p):
        print(p,file=self.packfile)
        self.packfile.flush()
        
    def command(self,cmd):
        args = cmd.split()
        cmd = args[0]
        del args[0]
        if cmd == "var":
            ### pollute the Q
            self.sendmessage("Send_ConfigInfo")
            self.info("Get variable {}={}","pointer.x",self.var.pointer_x)
            self.info("Get variables {}={}","(pointer.x,pointer.x)",
                      self.var("pointer_x","pointer_y") )
            self.info("In window context:")
            self.sendmessage(
                "All (Focused) SendToModule {} XXXX$[w.id] $[w.name]".
                format(self.alias) )
            winpicker = picker(mask=M_STRING,string=glob("XXXX*"))
            (pack,) = self.packets.pick( picker=winpicker,
                                         which="last")
            wid, wname = pack.string.replace("XXXX","").split()
            cw = int(wid,16)
            self.info("In window {} {}",wname,wid)
            self.info( "Get variables {}={}","(w.id,pointer.wx,pointer.wy)",
                           self.var( "w.id","pointer_wx","pointer.wy",
                                      context_window = cw ) )
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
        elif cmd == "config" or cmd == "getconfig":
            self.getconfig(match = "")
            with open("config.txt","wt") as file:
                print(self.config,file=file)
            try:
                with open("rawconfig.txt","wt") as file:
                    for cl in self.rawconfig:
                        print(cl,file=file)
            except AttributeError: pass
        elif cmd == "pick":
            mp = picker(mask=M_FOR_CONFIG,string=glob("color*"))
            self.push_masks(M_ALL,0,0)
            ### lets pollute the queue
            self.sendmessage("Send_WindowList")
            self.sendmessage("Send_ConfigInfo")
            self.sendmessage("Send_WindowList")
            time.sleep(3)
            self.info(" Pick: q size {}",len(self.packets))
            self.info(" Pick first")
            (p, ) = self.packets.pick(mp,which="first")
            self.info(" Got")
            print(p,file=sys.stderr)
            self.info(" Pick: q size {}",len(self.packets))
            self.info(" Pick last")
            (p, ) = self.packets.pick(mp,which="last")
            self.info(" Got")
            print(p,file=sys.stderr)
            self.info(" Pick: q size {}",len(self.packets))
            self.info(" Pick all")
            packs = self.packets.pick(mp,which="all")
            self.info(" Got {}",len(packs))
            self.info(" Pick: q size {}",len(self.packets))
            self.restore_masks()
        elif cmd == "qsize":
            self.info(" qsize: q size {}",len(self.packets))            
        elif cmd == "winlist" or cmd == "getwinlist":
            self.getwinlist()
            with open("winlist.txt","wt") as file:
                print(self.winlist,file=file)
        elif cmd == "exit":
            self.exit(0)
        elif cmd == "sendmessage":
            self.sendmessage(" ".join(args))
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
        elif cmd == "reply":
            ### pollute the queue
            self.sendmessage("Send_WindowList")
            self.sendmessage("Send_ConfigInfo")
            self.sendmessage("Send_WindowList")
            msg="xyz$[pointer.y]kkk"        
            reply=self.getreply(msg)
            self.info("reply: sent {}, got {}",msg,reply)
        elif cmd == "dir":
            with open("dir.txt","wt") as file:
                print("self",file=file)
                print(dir(self),file=file)
                print("\n\npacket reader",file=file)
                print(dir(self.packets),file=file)
        else:
            self.info(" unknown command {}",cmd)
                
    def h_cmd(self,p):
        self.command(p.string)
        
m=fvwmmymod()
m.logger.setLevel(L_INFO)
m.packets.logger.setLevel(L_INFO)
packet.logger.setLevel(L_INFO)
m.mask = M_STRING | MX_REPLY | M_ERROR | M_FOR_CONFIG | MX_ENTER_WINDOW
m.syncmask     = 0
m.nograbmask   = 0
m.packfile = open('packfile.txt',"wt",buffering=1<<20)
m.register_handler(M_ALL,m.h_dumppack)
m.register_handler(M_STRING, m.h_cmd)
m.info(" Start {} as {}",m.me,m.alias)
m.run()


