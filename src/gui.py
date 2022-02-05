import tkinter as tk
from tkinter import ttk
import logging
import threading
import time
from .constants import *
from .fvwmpy import *

######################################################################

class gui:
    def __init__(self,m):
        self.module = m
        ######################################################################
        self.root = tk.Tk()
        self.root.rowconfigure(0,weight=1)
        self.root.columnconfigure(0,weight=1)
        ######################################################################
        self.panes_lr = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.panes_lr.rowconfigure(0,weight=1)
        self.panes_lr.columnconfigure(0,weight=1)
        self.panes_lr.columnconfigure(1,weight=1)
        self.panes_lr.pack(fill="both",expand=1)
        ######################################################################
        self.panes_l_ud = tk.PanedWindow(self.panes_lr, orient=tk.VERTICAL)
        self.panes_l_ud.rowconfigure(0,weight=1)
        self.panes_l_ud.rowconfigure(1,weight=1)
        self.panes_l_ud.columnconfigure(0,weight=1)
        self.panes_lr.add(self.panes_l_ud,stretch="always")
        ######################################################################
        self.panes_r_ud = tk.PanedWindow(self.panes_lr,orient=tk.VERTICAL)
        self.panes_r_ud.rowconfigure(0,weight=1)
        self.panes_r_ud.rowconfigure(1,weight=1)
        self.panes_r_ud.columnconfigure(0,weight=1)
        self.panes_lr.add(self.panes_r_ud,stretch="always")
        ######################################################################
        self.lf_packs = tk.LabelFrame(self.panes_l_ud,text='FVWM packets')
        self.lf_packs.rowconfigure(0,weight=1)
        self.lf_packs.rowconfigure(1,weight=0)
        self.lf_packs.rowconfigure(2,weight=0)
        self.lf_packs.columnconfigure(0,weight=1)
        self.lf_packs.columnconfigure(1,weight=0)
        self.panes_l_ud.add(self.lf_packs,stretch="always")
        ######################################################################
        self.txt_packs = tk.Text(self.lf_packs,wrap='none')
        self.txt_packs['state'] = 'disabled'
        self.txt_packs.tag_configure('packtitle',
                                     foreground='red',
                                     font='TkBoldFont',
                                     relief='raised')
        self.txt_packs.tag_configure('packbody',
                                     foreground='black',
                                     font='TkLargeFont',
                                     relief='raised')
        self.txt_packs.grid(row=0,column=0,sticky=(tk.N,tk.W,tk.E,tk.S))
        ######################################################################
        self.sbv_packs = tk.Scrollbar(self.lf_packs,
                                      orient=tk.VERTICAL,
                                      command=self.txt_packs.yview)
        self.txt_packs['yscrollcommand'] = self.sbv_packs.set
        self.sbv_packs.grid(row=0,column=1,sticky=(tk.N,tk.S))
        ######################################################################
        self.sbh_packs = tk.Scrollbar(self.lf_packs,
                                      orient=tk.HORIZONTAL,
                                      command=self.txt_packs.xview)
        self.txt_packs['xscrollcommand'] = self.sbh_packs.set
        self.sbh_packs.grid(row=1,column=0,sticky=(tk.W,tk.E))
        ######################################################################
        self.packs_sdown = tk.IntVar(name="packs_sdown")
        def hhh(a,b,c):
            self.module.msg("HHH:", self.root.getvar(a))
        self.packs_sdown.trace_add("write",hhh)
        self.cb_packs = tk.Checkbutton(self.lf_packs,
                                       text="",
                                       variable=self.packs_sdown)
        self.cb_packs.grid(row=1,column=1,sticky=(tk.W,tk.E,tk.N,tk.E))
        ######################################################################
        ### lbl_packs
        self.n_packs = 0
        self.n_packs_str = tk.StringVar(value='Packets: {}'.format(self.n_packs))
        self.lbl_packs = tk.Label(self.lf_packs,textvariable=self.n_packs_str)
        self.lbl_packs.grid(row=2,column=0,sticky=(tk.W,))
        ######################################################################
        self.lf_msg = tk.LabelFrame(self.panes_l_ud,text=('Module messages'))
        self.lf_msg.rowconfigure(0,weight=1)
        self.lf_msg.rowconfigure(1,weight=0)
        self.lf_msg.rowconfigure(2,weight=0)
        self.lf_msg.columnconfigure(0,weight=1)
        self.lf_msg.columnconfigure(1,weight=0)
        self.panes_l_ud.add(self.lf_msg,stretch="always")
        ######################################################################
        self.txt_msg = tk.Text(self.lf_msg)
        self.txt_msg['state'] = 'disabled'
        self.txt_msg.tag_configure('msgtitle',
                                   foreground='blue',
                                   font='TkBoldFont',
                                   relief='raised')
        self.txt_msg.tag_configure('msgbody',
                                   foreground='black',
                                   font='TkLargeFont',
                                   relief='raised')
        self.txt_msg.grid(row=0,column=0,sticky=(tk.N,tk.W,tk.E,tk.S))
        ######################################################################
        self.sbv_msg = tk.Scrollbar(self.lf_msg,
                                    orient=tk.VERTICAL,
                                    command=self.txt_msg.yview)
        self.txt_msg['yscrollcommand'] = self.sbv_msg.set
        self.sbv_msg.grid(row=0,column=1,sticky=(tk.N,tk.S))
        ######################################################################
        self.sbh_msg = tk.Scrollbar(self.lf_msg,
                                    orient=tk.HORIZONTAL,
                                    command=self.txt_msg.xview)
        self.txt_msg['xscrollcommand'] = self.sbh_msg.set
        self.sbh_msg.grid(row=1,column=0,sticky=(tk.W,tk.E))
        ######################################################################
        self.msg_sdown = tk.IntVar(name="msg_sdown")
        # def hhh(a,b,c):
            # self.module.msg("HHH: self.root.getvar(a)")
        self.msg_sdown.trace_add("write",hhh)
        self.cb_msg = ttk.Checkbutton(self.lf_msg,
                                     text="",
                                     variable= self.msg_sdown)
        self.msg_sdown.set(1)
        self.cb_msg.grid(row=1,column=1,sticky=(tk.W,tk.E,tk.N,tk.E))
        ######################################################################
        self.fr_msg = tk.Frame(self.lf_msg)
        self.fr_msg.rowconfigure(0,weight=1)
        self.fr_msg.columnconfigure(0,weight=0)
        self.fr_msg.columnconfigure(1,weight=0)
        self.fr_msg.columnconfigure(2,weight=1)
        self.fr_msg.columnconfigure(3,weight=0)
        self.fr_msg.columnconfigure(4,weight=1)
        self.fr_msg.columnconfigure(5,weight=0)
        self.fr_msg.grid(row=2,column=0,sticky=(tk.W,))
        ######################################################################
        ### lbl_n_msg
        self.n_msg = 0
        self.n_msg_str = tk.StringVar(value='Messages: 0')
        self.lbl_n_msg = tk.Label(self.fr_msg,textvariable=self.n_msg_str)
        self.lbl_n_msg.grid(row=0,column=0,sticky=(tk.W),padx=(0,30))
        ######################################################################
        self.lbl_msg_wc = tk.Label(self.fr_msg,text='Context window:')
        self.lbl_msg_wc.grid(row=0,column=1,sticky=(tk.W))
        ######################################################################
        self.msgcw_str = tk.StringVar()
        self.entry_msg_cw = tk.Entry(self.fr_msg,
                                     width=10,
                                     textvariable=self.msgcw_str)
        self.entry_msg_cw.grid(row=0,column=2,sticky=(tk.W,tk.E))
        ######################################################################
        self.lbl_msg = tk.Label(self.fr_msg,text='Message:')
        self.lbl_msg.grid(row=0,column=3,sticky=(tk.W))
        ######################################################################
        self.msg_str = tk.StringVar()
        self.entry_msg = tk.Entry(self.fr_msg,
                                  width=30,
                                  textvariable=self.msg_str)
        self.entry_msg.grid(row=0,column=4,sticky=(tk.W,tk.E))
        ######################################################################
        self.btn_msg   = tk.Button(self.fr_msg,
                                   text="Send",
                                   command=self.sendmessage)
        self.btn_msg.grid(row=0,column=5,sticky=(tk.E,),padx=(10,0))
        ### These do not work. Why?
        self.fr_msg.bind('<Return>',lambda e: self.btn_msg.invoke())
        self.btn_msg.bind('<Return>',lambda e: self.btn_msg.invoke())
        ######################################################################
        self.lf_err = tk.LabelFrame(self.panes_r_ud,text='Error log')
        self.lf_err.rowconfigure(0,weight=1)
        self.lf_err.rowconfigure(1,weight=0)
        self.lf_err.columnconfigure(0,weight=1)
        self.lf_err.columnconfigure(1,weight=0)
        self.panes_r_ud.add(self.lf_err,stretch="always")
        ######################################################################
        self.txt_err = tk.Text(self.lf_err)
        self.txt_err['state'] = 'disabled'
        self.txt_err.grid(row=0,column=0,sticky=(tk.N,tk.W,tk.E,tk.S))
        ######################################################################
        self.sbv_err = tk.Scrollbar(self.lf_err,
                                    orient=tk.VERTICAL,
                                    command=self.txt_err.yview)
        self.txt_err['yscrollcommand'] = self.sbv_err.set
        self.sbv_err.grid(row=0,column=1,sticky=(tk.N,tk.S))
        ######################################################################
        self.sbh_err = tk.Scrollbar(self.lf_err,
                                    orient=tk.HORIZONTAL,
                                    command=self.txt_err.xview)
        self.txt_err['xscrollcommand'] = self.sbh_err.set
        self.sbh_err.grid(row=1,column=0,sticky=(tk.W,tk.E))
        ######################################################################
        self.err_sdown = tk.IntVar()
        self.cb_err = tk.Checkbutton(self.lf_msg,
                                       text="",
                                       variable=self.err_sdown)
        self.cb_err.grid(row=1,column=1,sticky=(tk.W,tk.E,tk.N,tk.E))
        ######################################################################
        self.nb_settings = ttk.Notebook(self.panes_r_ud)
        self.nb_settings.rowconfigure(0,weight=1)
        self.nb_settings.columnconfigure(0,weight=1)
        self.panes_r_ud.add(self.nb_settings,stretch="always")
        ######################################################################
        self.fr_mask       = tk.Frame(self.nb_settings)
        self.nb_settings.add(self.fr_mask,text="mask")
        ######################################################################
        self.fr_syncmask   = tk.Frame(self.nb_settings)
        self.nb_settings.add(self.fr_syncmask,text="syncmask")
        ######################################################################
        self.fr_nograbmask = tk.Frame(self.nb_settings)
        self.nb_settings.add(self.fr_nograbmask,text="nograbmask")
        ######################################################################
        self.fr_var = tk.Frame(self.nb_settings)
        self.fr_var.rowconfigure(0,weight=1)
        self.fr_var.rowconfigure(1,weight=1)
        self.fr_var.columnconfigure(0,weight=1)
        self.nb_settings.add(self.fr_var,text="variables")
        ######################################################################
        self.fr_config = tk.LabelFrame(self.nb_settings)
        self.fr_config.rowconfigure(0, weight=1)
        self.fr_config.rowconfigure(1, weight=0)
        self.fr_config.rowconfigure(2, weight=0)
        self.fr_config.columnconfigure(0, weight=1)
        self.fr_config.columnconfigure(1, weight=0)
        self.nb_settings.add(self.fr_config,text="config")
        ######################################################################
        ### chb_m, chb_sm, chb_ngm
        self.maskvars   = list()
        self.maskmute = False
        for i, p in enumerate(sorted(packetnames,key=int)):
            (r, c) = divmod(i,3)
            x       = tk.IntVar(name=":".join(("mask",str(p))))
            x.trace_add("write", self.mask_handler )
            self.maskvars.append(x)
            chb_m   = tk.Checkbutton( self.fr_mask,
                                      text=packetnames[p],
                                      variable=x )
            chb_m.grid(row=r,column=c,sticky=(tk.W,))
            ##################################################
            x       = tk.IntVar(name=":".join(("syncmask",str(p))))
            x.trace_add("write", self.mask_handler )
            self.maskvars.append(x)
            chb_m   = tk.Checkbutton( self.fr_syncmask,
                                      text=packetnames[p],
                                      variable=x )
            chb_m.grid(row=r,column=c,sticky=(tk.W,))
            ##################################################
            x       = tk.IntVar(name=":".join(("nograbmask",str(p))))
            x.trace_add("write", self.mask_handler )
            self.maskvars.append(x)
            chb_m   = tk.Checkbutton( self.fr_nograbmask,
                                      text=packetnames[p],
                                      variable=x )
            chb_m.grid(row=r,column=c,sticky=(tk.W,))
        ####################################################################
        self.lf_var = tk.LabelFrame(self.fr_var,text="Variables")
        self.lf_var.grid(row=0,column=0,sticky=(tk.W,tk.E),pady=(20,0),padx=5)
        ######################################################################
        self.lf_infostore = tk.LabelFrame(self.fr_var,text="Infostore")
        self.lf_infostore.grid(row=1, column=0,
                               sticky=(tk.W,tk.E),
                               pady=(20,0), padx=5)
        ######################################################################
        self.lbl_var_wid   = tk.Label(self.lf_var,text='Context window:')
        self.lbl_var_wid.grid(row=0,column=0,sticky=(tk.W,))
        ######################################################################
        ### entry_var_wid
        self.var_wid = tk.StringVar()
        self.entry_var_wid = tk.Entry(self.lf_var,
                                      textvariable=self.var_wid,
                                      width=10)
        self.entry_var_wid.grid(row=0,column=1,sticky=(tk.W,))
        ######################################################################
        self.lbl_var = tk.Label(self.lf_var,text='Variable:')
        self.lbl_var.grid(row=0,column=2,sticky=(tk.W,),padx=(10,0))
        ######################################################################
        ### entry_var
        self.var = tk.StringVar()
        self.entry_var = tk.Entry(self.lf_var,textvariable=self.var)
        self.entry_var.grid(row=0,column=3,sticky=(tk.W,tk.E))
        ######################################################################
        self.lbl_var_eq   = tk.Label(self.lf_var,text='=')
        self.lbl_var_eq.grid(row=0,column=4,sticky=(tk.W,))
        ######################################################################
        ### lbl_var_val
        self.var_val = tk.StringVar()
        self.lbl_var_val = tk.Label(self.lf_var,
                                    textvariable=self.var_val,
                                    width=10)
        self.lbl_var_val.grid(row=0,column=5,sticky=(tk.W,))
        ######################################################################
        self.btn_var   = tk.Button(self.lf_var,text="Get")
        self.btn_var.grid(row=0,column=6,sticky=(tk.W,))
        ######################################################################
        self.lbl_infostore = tk.Label(self.lf_infostore,
                                      text='Infostore variable:')
        self.lbl_infostore.grid(row=0,column=0,sticky=(tk.W,))
        ######################################################################
        ### entry_infostore
        self.infostore = tk.StringVar()
        self.entry_infostore = tk.Entry(self.lf_infostore,
                                        textvariable=self.infostore)
        self.entry_infostore.grid(row=0,column=1,sticky=(tk.W,tk.E))
        ######################################################################
        self.lbl_infostore_eq   = tk.Label(self.lf_infostore,text='=')
        self.lbl_infostore_eq.grid(row=0,column=2,sticky=(tk.W,))
        ######################################################################
        ### entry_infostore_val
        self.infostore_val = tk.StringVar()
        self.entry_infostore_val = tk.Entry(self.lf_infostore,
                                            textvariable=self.infostore_val)
        self.entry_infostore_val.grid(row=0,column=3,sticky=(tk.W,tk.E))
        ######################################################################
        self.btn_infostore_get = tk.Button(self.lf_infostore,text="Get")
        self.btn_infostore_get.grid(row=0,column=4,sticky=(tk.W,),padx=(10,2))
        ######################################################################
        self.btn_infostore_set = tk.Button(self.lf_infostore,text="Set")
        self.btn_infostore_set.grid(row=0,column=5,sticky=(tk.W,),padx=(2,2))
        ######################################################################
        self.btn_infostore_del = tk.Button(self.lf_infostore,text="Delete")
        self.btn_infostore_del.grid(row=0,column=6,sticky=(tk.W,),padx=(2,2))
        ######################################################################
        self.lb_config  = tk.Listbox(self.fr_config)
        self.lb_config.grid(row=0,column=0,sticky=(tk.N,tk.W,tk.E,tk.S))
        ######################################################################
        self.sbh_config = tk.Scrollbar(self.fr_config,
                                       orient=tk.HORIZONTAL,
                                       command=self.lb_config.xview)
        self.lb_config['xscrollcommand'] = self.sbh_config.set
        self.sbh_config.grid(row=1,column=0,sticky=(tk.W,tk.E))
        ######################################################################
        self.sbv_config = tk.Scrollbar(self.fr_config,
                                       orient=tk.VERTICAL,
                                       command=self.lb_config.yview)
        self.lb_config['yscrollcommand'] = self.sbv_config.set
        self.sbv_config.grid(row=0,column=1,sticky=(tk.N,tk.S))
        ######################################################################
        self.fr_readconfig = tk.Frame(self.fr_config)
        self.fr_readconfig.grid(row=2,column=0,columnspan=2)
        ######################################################################
        self.lbl_match = tk.Label(self.fr_readconfig,text='Match:')
        self.lbl_match.grid(row=0,column=0)
        ######################################################################
        ### entry_match
        self.configmatch = tk.StringVar()
        self.entry_match = tk.Entry(self.fr_readconfig,
                                    textvariable=self.configmatch) 
        self.entry_match.grid(row=0,column=1)
        ######################################################################
        self.btn_readconf = tk.Button(self.fr_readconfig,
                                      text='(Re)Read config')
        self.btn_readconf.grid(row=0,column=2,padx=(10,0))
        ######################################################################

    def showpacket(self,p):
        # self.module.msg("GUI: packet {}".format(p.ptype))
        self.txt_packs['state'] = 'normal'
        pack=str(p).splitlines()
        self.txt_packs.insert('end',"\n")
        self.txt_packs.insert('end',pack[0],('packtitle',))
        self.txt_packs.insert('end',"\n")
        self.txt_packs.insert('end',"\n".join(pack[1:]),('packbody',))
        self.txt_packs.insert('end',"\n")
        if self.packs_sdown.get():
            self.txt_packs.see('end')
        self.txt_packs['state'] = 'disabled'
        self.n_packs += 1
        self.n_packs_str.set("Packets: {}".format(self.n_packs))

    def showmessage(self,msg,context_window):
        self.module.msg("GUI: message {}".format(msg))
        self.txt_msg['state'] = 'normal'
        ml = msg.splitlines()
        for m in ml:
            t = m.split()
            self.txt_msg.insert('end',"\n")
            self.txt_msg.insert('end',t[0],('msgtitle',))
            self.txt_msg.insert('end',"\t"+" ".join(t[1:]),('msgbody',))
            self.n_msg += 1
        if self.cb_msg.instate(("selected",)):
            self.txt_msg.see('end')
        self.txt_msg['state'] = 'disabled'
        self.n_msg_str.set("Messages: {}".format(self.n_msg))

    def showerrors(self,line):
        self.txt_err['state'] = 'normal'
        self.txt_err.insert('end',line)
        if self.err_sdown.get():
            self.txt_err.see('end')
        self.txt_err['state'] = 'normal'

    def showmask(self,mtype,val):
        p=1
        self.maskmute = True
        self.module.msg("GUI:showmask:")
        for n in range(37):
            p <<= 1
            if p&val:
                self.root.setvar(":".join((mtype,str(p))),1)
            else:
                self.root.setvar(":".join((mtype,str(p))),0)
            self.maskmute = False
        
    def sendmessage(self):
        msg = self.msg_str.get().strip()
        try:
            cwid = int(self.msgcw_str.get().strip())
        except:
            cwid = 0
            self.msgcw_str.set("")
        if msg:
            self.module.sendmessage(msg,context_window = cwid)


    def mask_handler(self,name,b,c):
        if self.maskmute: return
        mtype, p = name.split(":")
        p = int(p)
        val = int(self.root.getvar(name))
        if mtype == "mask":
            ms = self.module._mask_set
            mg = self.module.mask
        elif mtype == "syncmask":
            ms = self.module._syncmask_set
            mg = self.module.syncmask
        elif mtype == "nograbmask":
            ms = self.module._nograbmask_set
            mg = self.module.nograbmask
        else:     return
        if val:
            ms( mg | p )
        else:
            ms( mg & ~p )

# class gui:
    # def __init__(self,m):
        # self.root=tk.Tk()
        # self.root.title("abc")
        # self.lbl=tk.Label(self.root,text="1234567890")
        # self.lbl.pack()

 
