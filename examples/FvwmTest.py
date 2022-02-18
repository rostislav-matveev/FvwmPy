#!/usr/bin/python3
import sys
import time
import threading

from fvwmpy import *

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
            self.push_masks(M_FOR_CONFIG,0,0)
            self.sendmessage("Send_ConfigInfo")
            self.restore_masks()
            self.info("var: Get {}={}","pointer.x",self.var.pointer_x)
            self.info("var: Get {}={}","(pointer.x,pointer.y)",
                      self.var("pointer.x","pointer_y") )
            self.info("var: In window context:")
            self.sendmessage(
                "All (Focused) SendToModule {} XXXX$[w.id] $[w.name]".
                format(self.alias) )
            winpicker = picker(mask=M_STRING,string=glob("XXXX*"))
            (pack,) = self.packets.pick( picker=winpicker)
            wid, wname = pack.string.replace("XXXX","").split()
            cw = int(wid,16)
            self.info("var: In window {} {}",wname,wid)
            self.info( "var: Get variables {}={}","(w.id,pointer.wx,pointer.wy)",
                       self.var( "w.id","pointer_wx","pointer.wy",
                                 context_window = cw ) )
            try:
                self.info("var: Try to delete page.nx")
                del self.var.page_nx
            except IllegalOperation as e:
                self.info("var: {}",repr(e))
            try:
                self.info("var: Try to set page.nx")
                self.var.page_nx = 7
            except IllegalOperation as e:
                self.info("var: {}",repr(e))
            ########################################
            self.push_masks(M_FOR_WINLIST,0,0)
            self.sendmessage("Send_WindowList")
            self.restore_masks()
            self.info("infostore: Set {}={}","var.1",17)
            self.infostore.var_1=17
            self.info("infostore: Set {}={}","var.2","string value")
            self.infostore.var_2="string value"
            self.info("infostore: Get {}={}","var.2",self.infostore.var_2)
            self.info("infostore: Get {}={}","(var.1,var.2)",
                      self.infostore("var.1","var_2") )
            self.info("infostore: Get {}={}","(var.1,var.2,unknown)",
                      self.infostore("var.1","var_2","unknown") )
            self.info("infostore: Get {}={}","unknown",
                      self.infostore.unknown )
            self.info("infostore: Del {}","unknown")
            del self.infostore.unknown
            self.info("infostore: Del {}","var.1")
            del self.infostore.var_1
            self.info("infostore: Del {}","var.2")
            del self.infostore.var_2
            self.info("infostore: Get {}={}","(var.1,var.2,unknown)",
                      self.infostore("var.1","var_2","unknown") )
        elif cmd == "mask":
            self.info(" MASK")
            for m in split_mask(self.mask):
                self.info("\t{}",packetnames[m])
        elif cmd == "config":
            self.push_masks(M_FOR_WINLIST,0,0)
            self.sendmessage("Send_WindowList")
            self.restore_masks()
            self.getconfig(match = "")
            with open("config.txt","wt") as file:
                print(self.config,file=file)
            try:
                with open("rawconfig.txt","wt") as file:
                    for cl in self.rawconfig:
                        print(cl,file=file)
            except AttributeError: pass
        elif cmd == "winlist":
            self.push_masks(M_FOR_CONFIG,0,0)
            self.sendmessage("Send_ConfigInfo")
            self.restore_masks()
           
            self.getwinlist()
            with open("winlist.txt","wt") as file:
                print(self.winlist,file=file)
        elif cmd == "pick":
            self.push_masks(M_ALL,0,0)
            self.info("pick: from polluted queue")
            ### lets pollute the queue
            self.sendmessage("Send_WindowList")
            self.sendmessage("Send_ConfigInfo")
            self.sendmessage("Send_WindowList")
            time.sleep(3)
            ######################################
            self.info("pick: 1. from {} packets",len(self.packets))
            packs = self.packets.pick(picker(mask=M_FOR_CONFIG,
                                             string=glob("XineramaConfig*"))|
                                      picker(mask=M_CONFIG_INFO,
                                             string=glob("ClickTime")) )
            self.info("pick: 1.1 got {}/1 packets out of {}",
                      len(packs),len(self.packets))
            packs = self.packets.pick(picker(mask=M_FOR_CONFIG,
                                             string=glob("XineramaConfig*"))|
                                      picker(mask=M_CONFIG_INFO,
                                             string=glob("ClickTime*")) )
            self.info("pick: 1.2 got {}/1 packets out of {}",
                      len(packs),len(self.packets))
            #######################################
            self.info("pick: 2. timed out")
            packs = self.packets.pick(picker(mask=M_STRING,
                                             string=glob("NoSuchString*")),
                                      timeout=1)
            self.info("pick: 2. got {}/0 packets out of {}",
                      len(packs),len(self.packets))
            ########################################
            self.info("pick: 3. keep=True")
            self.info("pick: 3.1 keep=True")
            packs = self.packets.pick(picker(string=glob("DesktopSize*")),keep=True)
            self.info("pick: 3.1 got {}/1 packets out of {}",
                      len(packs),len(self.packets))
            self.info("pick: 3.2 keep=True")
            packs = self.packets.pick(picker(string=glob("DesktopSize*")),keep=True)
            self.info("pick: 3.2 got {}/1 packets out of {}",
                      len(packs),len(self.packets))
            ########################################
            self.info("pick: 4. with until")
            packs = self.packets.pick(picker(string=glob("colorset*")),
                                      until=picker(mask=M_END_CONFIG_INFO),
                                      keep=True)
            self.info("pick: 4.1 got {}/many packets out of {}",
                      len(packs),len(self.packets))
            packs = self.packets.pick(picker(string=glob("colorset*")),
                                      until=picker(mask=M_END_CONFIG_INFO))
            self.info("pick: 4.2 got {}/many packets out of {}",
                      len(packs),len(self.packets))
            #######################################
            self.packets.clear()
            self.info("pick: {} packets in the queue",len(self.packets))
            def fillq():
                time.sleep(0.1)
                self.sendmessage("Send_WindowList")
                self.sendmessage("Send_ConfigInfo")
                self.sendmessage("Send_WindowList")
            ######################################
            fillqt = threading.Thread(target=fillq)
            self.packets.clear()
            fillqt.start()
            self.info("pick: 5. {} packets in the queue",len(self.packets))
            packs = self.packets.pick(picker(mask=M_FOR_CONFIG,
                                             string=glob("XineramaConfig*"))|
                                      picker(mask=M_CONFIG_INFO,
                                             string=glob("ClickTime*")) )
            self.info("pick: 5.1 got {}/1 packets out of {}",
                      len(packs),len(self.packets))
            packs = self.packets.pick(picker(mask=M_FOR_CONFIG,
                                             string=glob("XineramaConfig*"))|
                                      picker(mask=M_CONFIG_INFO,
                                             string=glob("ClickTime*")) )
            self.info("pick: 5.2 got {}/1 packets out of {}",
                      len(packs),len(self.packets))
            #######################################
            fillqt = threading.Thread(target=fillq)
            self.packets.clear()
            fillqt.start()
            self.info("pick: 6. {} packets in the queue",len(self.packets))
            self.info("pick: 6. timed out")
            packs = self.packets.pick(picker(mask=M_STRING,
                                             string=glob("NoSuchString*")),
                                      timeout=1)
            self.info("pick: 6. got {}/0 packets out of {}",
                      len(packs),len(self.packets))
            ########################################
            fillqt = threading.Thread(target=fillq)
            self.packets.clear()
            fillqt.start()
            self.info("pick: 7. {} packets in the queue",len(self.packets))
            self.info("pick: 7. keep=True")
            self.info("pick: 7.1 keep=True")
            packs = self.packets.pick(picker(string=glob("DesktopSize*")),keep=True)
            self.info("pick: 7.1 got {}/1 packets out of {}",
                      len(packs),len(self.packets))
            self.info("pick: 7.2 keep=True")
            packs = self.packets.pick(picker(string=glob("DesktopSize*")),keep=True)
            self.info("pick: 7.2 got {}/1 packets out of {}",
                      len(packs),len(self.packets))
            ########################################
            fillqt = threading.Thread(target=fillq)
            self.packets.clear()
            fillqt.start()
            self.info("pick: 8. {} packets in the queue",len(self.packets))
            self.info("pick: 8. with until")
            packs = self.packets.pick(picker(string=glob("colorset*")),
                                      until=picker(mask=M_END_CONFIG_INFO),
                                      keep=True)
            self.info("pick: 8.1 got {}/many packets out of {}",
                      len(packs),len(self.packets))
            packs = self.packets.pick(picker(string=glob("colorset*")),
                                      until=picker(mask=M_END_CONFIG_INFO))
            self.info("pick: 8.2 got {}/many packets out of {}",
                      len(packs),len(self.packets))
            #######################################
            self.restore_masks()
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
        elif cmd == "all":
            self.info("="*60)
            self.info(" ")
            self.command("var")
            self.packets.clear()
            
            self.info("="*60)
            self.info(" ")
            self.command("infostore")
            self.packets.clear()
            
            self.info("="*60)
            self.info(" ")
            self.command("mask")
            self.packets.clear()

            self.info("="*60)
            self.info(" ")
            self.command("config")
            self.packets.clear()

            self.info("="*60)
            self.info(" ")
            self.command("winlist")
            self.packets.clear()

            self.info("="*60)
            self.info(" ")
            self.command("reply")
            self.packets.clear()

            self.info("="*60)
            self.info(" ")
            self.command("filterwinlist")
            self.packets.clear()           
        else:
            self.info(" unknown command {}",cmd)
                
    def h_cmd(self,p):
        self.command(p.string)
        
m=fvwmmymod()
m.logger.setLevel(L_INFO)
m.packets.logger.setLevel(L_INFO)
packet.logger.setLevel(L_INFO)
# m.mask = M_STRING | MX_REPLY | M_ERROR | M_FOR_CONFIG | MX_ENTER_WINDOW | M_FOR_WINLIST
m.mask = M_STRING 
m.syncmask     = 0
m.nograbmask   = 0
m.packfile = open('packfile.txt',"wt",buffering=1<<20)
m.register_handler(M_ALL,m.h_dumppack)
m.register_handler(M_STRING, m.h_cmd)
m.info(" Start {} as {}",m.me,m.alias)
m.run()


