#!/usr/bin/python3
import logging
import threading
import time
import tkinter as tk
import sys, os
import signal

root=tk.Tk()
lbltext=tk.StringVar()
lbl = tk.Label(root,textvariable=lbltext)
lbl.pack()

def thread_function(name,var):
    logging.info("Thread %s: starting", name)
    for i in range(10):
        var.set(str(i))
        print(var.get())
        time.sleep(1)
    logging.info("Thread %s: finishing", name)
    os.kill(os.getpid(), signal.SIGINT)

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                    datefmt="%H:%M:%S")

logging.info("Main    : before creating thread")
x = threading.Thread(target=thread_function, args=(1,lbltext))
logging.info("Main    : before running thread")
x.start()
logging.info("Main    : start gui")
root.mainloop()
# x.join()
logging.info("Main    : all done")
