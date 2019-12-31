import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes._axes import Axes
from matplotlib.axes._subplots import SubplotBase
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from datetime import datetime
from matplotlib.figure import Figure
import sys
import tkinter
from tkinter import *
import matplotlib


def interactive_slider(update_func, slider_num=1, slider_bounds=None, slider_names=None, title='', step_size=0.1):
    """ init_func should return the matplotlib line that will be updated.
        update_func takes the line (in case you want to pull the current line data)
        and new value as parameters and should return the x and y data of the updated line
    """
    if slider_bounds == None:
        slider_bounds = [(0,1, 0.1)]*slider_num

    class Window(Frame):
        def __init__(self, master=None):
            self.slider_num = slider_num
            self.update_func = update_func
            # parameters that you want to send through the Frame class. 
            Frame.__init__(self, master)   

            self.master = master
            self.init_window()

            plt.ion()
            plt.show(block=False)

            self.grid(column=2,row=self.slider_num, sticky=(N,W,E,S) )
            self.columnconfigure(2, weight = 1)
            self.rowconfigure(self.slider_num, weight = 1)
            self.pack(pady = 20, padx = 20)

        #Creation of init_window
        def init_window(self):
            self.master.title(title)
            # allowing the widget to take the full space of the root window
            self.pack(fill=BOTH, expand=1)

            self.slider = [None]*self.slider_num
            for s in range(self.slider_num):
                self.slider[s] = Scale(self, from_=slider_bounds[s][0], to=slider_bounds[s][1], resolution=slider_bounds[s][2], orient='horizontal',length=300, command=self.slider_event)
                self.slider[s].grid(row =s, column = 1, sticky='nsew', padx=1, pady=1)
                self.slider[s].focus_set()
            if slider_names != None:
                for i, n in enumerate(slider_names):
                    l = Label(self, text=n)
                    l.grid(row =i, column = 0, sticky='nsew', padx=1, pady=1)

            self.slider_event()
            
            #slider.bind('<KeyRelease>', self.onKeyPress)
            #self.valuelabel = Label(self, text="", width=20, anchor='w')
            #self.valuelabel.grid(row = 1, column = 0, padx=0)

        def slider_event(self, *args):
            #self.valuelabel['text'] = str(val)
            vals = [None]*self.slider_num
            for s in range(self.slider_num):
                vals[s] = self.slider[s].get()
            self.update_func(*vals)
            #self.update_line.set_data(xdata, ydata)
            #self.update_line.axes.figure.canvas.draw()
        
        def onKeyPress(self, event):
            slider = self.focus_get()
            if event.keysym == 'Left' or event.keysym == 'Right':
                self.slider_event(self.slider.get()+self.step_size)
            #print('Got key press:', event.keysym)
            
    root = Tk()
    #creation of an instance
    app = Window(root)
    root.mainloop()  
