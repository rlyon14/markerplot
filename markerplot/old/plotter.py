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
#from tkinter import ttk
#from tkinter.ttk import *

class CastMeta(type):
    def __call__(cls, *args, **kwargs):

        ## combine class dictionary of matplotlib Axes class with new axes class
        dct = dict(kwargs['castAs'].__class__.__dict__)
        dct.update(dict(cls.__dict__))

        # __dict__ is in the class dictionary if object does not inherit from a parent class
        if ('__dict__' in dct):
            dct.pop('__dict__')

        ## make new class look like casted class
        name = kwargs['castAs'].__class__.__name__
        bases = kwargs['castAs'].__class__.__bases__

        ## call type's __new__ to create new class definition with updated class dictionary
        ## call __new__ of class definition to create instance object of class
        cls = type.__new__(CastMeta, name, bases, dct)
        self = cls.__new__(cls, bases, dct)

        ##update instance dictionary to match casted type
        self.__dict__.update(kwargs['castAs'].__dict__)

        ## call __init__ and return initialized object, this __init__ does not need to call super 
        ## because object has already been instantiated
        self.__init__(*args, **kwargs)
        return self

class Marker(object):
    def __init__(self, axes, xd, yd, showXline=True, showYdot=True):
        self.axes = axes
        self.showXline = showXline
        self.showYdot = showYdot
        self.xline = None
        self.lines = list(self.axes.datalines)
        self.labels = list(self.axes.labels)
        self.ydot = [None]*len(self.lines)
        self.ytext = [None]*len(self.lines)
        self.xidx = None
        self.renderer = self.axes.renderer
        self.ytext_loc = []
        self.ytext_space = None
        self.xlen = 0
        if (len(self.lines) < 1):
            raise RuntimeError()

        self.createMarker(xd, yd)

    def _find_xidx(self, xd, yd=None):
        mline, xidx, mdist = None, 0, np.inf
        if (yd == None or self.showXline):
            mline = self.lines[0]
            xidx = (np.abs(mline.get_xdata()-xd)).argmin()
        else:
            for l in self.lines:
                xl, yl = l.get_xdata(), l.get_ydata()

                dist = (xl - xd)**2 + (yl-yd)**2	## array of distances (squared) of every point on the line from the point xd, yd
                xidx_l, mdist_l = np.argmin(dist), np.min(dist)   ## index and distance of the point on the line with the closest distance to xd, yd
                if mdist_l < mdist:
                    mline, xidx, mdist  = l, xidx_l, mdist_l
        return mline, xidx

    def _set_yloc(self):
        for i, l in enumerate(self.lines):
            ytext_dim = self.ytext[i].get_window_extent(self.renderer)
            y1 = self.axes.display2axes((ytext_dim.x0, ytext_dim.y0))[1]
            y2 = self.axes.display2axes((ytext_dim.x1, ytext_dim.y1))[1]

            if(self.ytext_space == None):
                self.ytext_space = y2 - y1

            for ii, loc in enumerate(self.ytext_loc):
                if y1 > loc[1] and ii < (len(self.ytext_loc) -1):
                    continue
                
                ## before inserting y1, check upper and lower slots for overlap
                if (ii > 0):
                    overlap = self.ytext_space - (y1 - self.ytext_loc[ii - 1])
                    if overlap < 0:
                        self.ytext_loc.insert(ii, (i, y1))
                        break
                    
                    y1 += overlap/2
                    #other -= overla-/2 

        print(self.ytext_loc)


    def createMarker(self, xd, yd=None):
        mline, self.xidx = self._find_xidx(xd, yd)
        xd, yd = mline.get_xdata()[self.xidx], mline.get_ydata()[self.xidx]	
        xa, ya = self.axes.data2axes((xd, yd))

        if self.showXline:
            boxparams = dict(boxstyle='round', facecolor='black', edgecolor='black', alpha=0.7)
            self.xline = self.axes.axvline(xd, linewidth=0.5, color='r')
            txt = '{:.3f}'.format(xd) if self.axes.xdisplay == None else self.axes.xdisplay[self.xidx]
            self.xtext = self.axes.text(xa, -0.07, txt, color='white', fontsize=8, transform = self.axes.transAxes, verticalalignment='center', bbox=boxparams)
            xtext_dim = self.xtext.get_window_extent(self.renderer)
            print(xtext_dim)
            x1 = self.axes.display2axes((xtext_dim.x0, xtext_dim.y0))[0]
            x2 = self.axes.display2axes((xtext_dim.x1, xtext_dim.y1))[0]
            self.xlen = (x2-x1)/2
            self.xtext.set_position((xa-self.xlen +0.005, -0.07))
            #print(p1)

        for i, l in enumerate(self.lines):
            xd, yd = l.get_xdata()[self.xidx], l.get_ydata()[self.xidx]	
            xa, ya = self.axes.data2axes((xd, yd))
            boxparams = dict(facecolor='black', edgecolor=l.get_color(), boxstyle='round', alpha=0.7)
            label = '{:0.3f}'.format(yd) if self.labels[i] != None else '{:0.3f}'.format(yd)
            self.ytext[i] = self.axes.text(xa+0.01, ya, label ,color='white', fontsize=8, transform = self.axes.transAxes, verticalalignment='center', bbox=boxparams)

            if self.showYdot:
                self.ydot[i] = Line2D([xd], [yd], linewidth= 10, color=l.get_color(), markersize=10)
                self.ydot[i].set_marker('.')
                self.ydot[i].set_linestyle(':')
                self.axes.add_line(self.ydot[i])

    def moveToIdx(self, xidx):
        self.xidx = xidx
        xd = self.lines[0].get_xdata()[self.xidx]
        xa, ya = self.axes.data2axes((xd, 0))
        if self.showXline:
            self.xline.set_xdata([xd, xd])
            self.xtext.set_position((xa-self.xlen +0.005, -0.07))
            txt = '{:.3f}'.format(xd) if self.axes.xdisplay == None else self.axes.xdisplay[self.xidx]
            self.xtext.set_text(txt)

        for i, l in enumerate(self.lines):
            xd, yd = l.get_xdata()[self.xidx], l.get_ydata()[self.xidx]	
            xa, ya = self.axes.data2axes((xd, yd))
            self.ytext[i].set_position((xa+0.01, ya))
            self.ytext[i].set_text('{:0.3f}'.format(yd))
            if self.showYdot:
                self.ydot[i].set_data([xd], [yd])
            dim = self.ytext[i].get_window_extent(renderer=self.axes.renderer)

    def moveToPoint(self, xd, yd):
        self.mline, self.xidx = self._find_xidx(xd, yd)
        self.moveToIdx(self.xidx)

    def shiftMarker(self, direction):
        xlen = len(self.lines[0].get_xdata())
        nxidx = self.xidx -1 if direction else self.xidx +1
        if (nxidx >= xlen):
            nxidx = xlen-1
        elif (nxidx <= 0):
            nxidx = 0
        self.xidx = nxidx

        self.moveToIdx(self.xidx)

    def removeMarker(self):
        idx = self.axes.markers.index(self)
        self.axes.markers.pop(idx)
        self.xtext.set_visible(False)
        idx = self.axes.lines.index(self.xline)
        self.axes.lines.pop(idx)
        for i, l in enumerate(self.lines):		
            idx = self.axes.lines.index(self.ydot[i])
            self.axes.lines.pop(idx)
            idx = self.ytext[i].set_visible(False)

class Axes_i(Axes, SubplotBase, metaclass=CastMeta):
    def __init__(self, *args, **kwargs):
        self.grid(True)
        self.xdisplay = kwargs['xDisplay'] if ('xDisplay' in kwargs) else None

        self.grid(linewidth=0.5, linestyle='-')
        self.axes2display = self.transData.transform
        self.display2axes = self.transData.inverted().transform
        self.data2axes = self.transLimits.transform
        self.axes2data = self.transLimits.inverted().transform
        self.markers = []
        self.datalines = []
        self.labels = []
        self.activeMarker = None
        self.renderer = self.figure.canvas.get_renderer()
        #boxparams = dict(boxstyle='round', facecolor='white', alpha=0.4)
        boxparams = dict(facecolor='black', edgecolor='black', alpha=0.8, pad=1)

    def plot(self, *args, **kwargs):
        ret = super(SubplotBase, self).plot(*args, **kwargs)
        self.datalines.append(self.lines[-1])
        if 'label' in kwargs:
            self.labels.append(kwargs['label'])
        else:
            self.labels.append(None)
        return ret

    def addMarker(self, xd, yd=None):
        self.activeMarker = Marker(self, xd, yd)
        self.markers.append(self.activeMarker)

    def moveMarker(self, xd, yd):
        if (self.activeMarker == None): return
        self.activeMarker.moveToPoint(xd, yd)

    def getEventMarker(self, event):
        for m in self.markers:
            for ym in m.ytext:
                contains, attrd = ym.contains(event)
                if (contains):
                    return m
        return None

    def shiftMarker(self, direction):
        if (self.activeMarker == None): return
        self.activeMarker.shiftMarker(direction)

    def deleteMarker(self):
        if (self.activeMarker == None): return
        self.activeMarker.removeMarker()
        self.activeMarker = self.markers[-1] if len(self.markers) > 0 else None

    def savefig(self, *args, **kwargs):
        self.figure.savefig(*args, **kwargs)

            
class Figure_i(Figure, metaclass=CastMeta):
    ##matplotlib blocks overriding axes, this class allows us to add functionality in the Axes_i class.

    def __init__(self, *args, **kwargs):
        self.canvas.figure = self

    def __getattribute__(self, name):
        if (name == 'axes'):
            return self.__dict__[name]
        else:
            return super(Artist, self).__getattribute__(name)

    def __setattr__(self, name, value):
        if (name == 'axes'):
            self.__dict__[name] = value
        else:
            super(Artist, self).__setattr__(name, value)

class Plotter(object):
    def __init__(self, nrow=1 , ncolumn=1, figsize=None, xreversed=False, xDisplay = None):
        self.xDisplay = xDisplay
        self.xreversed = xreversed
        if (figsize == None):
            figsize = (10,5)
        self.fig, self.axes = plt.subplots(nrow,ncolumn, constrained_layout=True, figsize=figsize)
        #self.fig, self.axes = plt.subplots(nrow,ncolumn, figsize=(8,5))
        #self.renderer = self.fig.canvas.get_renderer()
        self.renderer = None
        self.axes = list(np.array([self.axes]).flatten())
        self.fig = Figure_i(castAs=self.fig)
        self.move = None
        #print(self.fig._axstack._elements)
        for i, ax in enumerate (self.axes):
            self.fig._axstack.remove(self.axes[i])
            self.axes[i] = Axes_i(castAs=ax, xDisplay=self.xDisplay)
            self.axes[i].figure = self.fig
            self.fig._axstack.add(self.axes[i], self.axes[i])
        
        self.fig.axes = self.axes
        self.shift_is_held = False
        self.activeAxes = None

        self.cidclick = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.cidpress = self.fig.canvas.mpl_connect('key_press_event', self.onkey_press)
        self.cidbtnrelease =self.fig.canvas.mpl_connect('key_release_event', self.onkey_release)
        self.cidmotion = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)
        self.cidkeyrelease = self.fig.canvas.mpl_connect('button_release_event', self.onrelease)

    def __getitem__(self, key):
        return self.axes[key]

    def show(self):
        plt.show()
        plt.get_fignums()

    def plot(self, xdata, ydata, axes=None, **kwargs):
        if (axes == None):
            axes = self.axes[0]        
        ret = axes.plot(xdata, ydata, **kwargs)
        axes.legend()
        return ret

    def onkey_release(self, event):
        if event.key == 'shift':
            self.shift_is_held = False

    def onkey_press(self, event):
        axes = self.activeAxes
        if event.key == 'shift':
            self.shift_is_held = True
        elif(event.key == 'left'):
            axes.shiftMarker(False) if self.xreversed else axes.shiftMarker(True)
        elif(event.key == 'right'):
            axes.shiftMarker(True) if self.xreversed else axes.shiftMarker(False)
        elif(event.key == 'delete'):
            axes.deleteMarker()
        #plt.tight_layout()
        self.fig.canvas.draw()

    def onmotion(self, event):
        xd = event.xdata
        yd = event.ydata
        axes = event.inaxes
        if axes == None or axes != self.move:
            return
        
        axes.moveMarker(xd, yd)
        #plt.tight_layout()
        self.fig.canvas.draw()

    def onrelease(self, event):
        self.move = None

    def onclick(self, event):
        xd = event.xdata
        yd = event.ydata
        axes = event.inaxes
        if (axes == None or len(axes.datalines) < 1):
            return
        self.move = axes

        for a in self.axes:
            m = a.getEventMarker(event)
            if (m != None): 
                a.activeMarker = m
                return
        
        if (len(axes.markers) > 0 and self.shift_is_held == False):
            axes.moveMarker(xd, yd)
        else:
            axes.addMarker(xd, yd)
        #plt.tight_layout()
        self.fig.canvas.draw()
        self.activeAxes= axes
        return

def interactive_plot(init_func, update_func, slider_num=1, slider_bounds=None, slider_names=None, title=''):
    """ init_func should return the matplotlib line that will be updated.
        update_func takes the line (in case you want to pull the current line data)
        and new value as parameters and should return the x and y data of the updated line
    """
    if slider_bounds == None:
        slider_bounds = [(0,1, 0.1)]*slider_num

    class Window(Frame):
        def __init__(self, master=None):
            self.init_func = init_func
            self.slider_num = slider_num
            self.update_func = update_func
            # parameters that you want to send through the Frame class. 
            Frame.__init__(self, master)   

            self.master = master
            self.init_window()

            plt.ion()
            self.update_line = self.init_func()

            self.grid(column=2,row=self.slider_num, sticky=(N,W,E,S) )
            self.columnconfigure(2, weight = 1)
            self.rowconfigure(self.slider_num, weight = 1)
            self.pack(pady = 20, padx = 20)

        #Creation of init_window
        def init_window(self):
            print(slider_bounds)

            self.master.title(title)
            # allowing the widget to take the full space of the root window
            self.pack(fill=BOTH, expand=1)

            self.slider = [None]*self.slider_num
            for s in range(self.slider_num):
                print(slider_bounds[s])
                self.slider[s] = Scale(self, from_=slider_bounds[s][0], to=slider_bounds[s][1], resolution=slider_bounds[s][2], orient='horizontal',length=300, command=self.slider_event)
                self.slider[s].grid(row =s, column = 1, sticky='nsew', padx=1, pady=1)
                self.slider[s].focus_set()
            if slider_names != None:
                for i, n in enumerate(slider_names):
                    l = Label(self, text=n)
                    l.grid(row =i, column = 0, sticky='nsew', padx=1, pady=1)
            
            #slider.bind('<KeyRelease>', self.onKeyPress)
            #self.valuelabel = Label(self, text="", width=20, anchor='w')
            #self.valuelabel.grid(row = 1, column = 0, padx=0)

        def slider_event(self, val):
            #self.valuelabel['text'] = str(val)
            vals = [None]*self.slider_num
            for s in range(self.slider_num):
                vals[s] = self.slider[s].get()
            self.update_func(self.update_line, vals)
            #self.update_line.set_data(xdata, ydata)
            #self.update_line.axes.figure.canvas.draw()
        
        def onKeyPress(self, event):
            slider = self.focus_get()
            print(slider)
            if event.keysym == 'Left' or event.keysym == 'Right':
                self.slider_event(self.slider.get()+0.1)
            #print('Got key press:', event.keysym)
            
    root = Tk()
    #creation of an instance
    app = Window(root)
    root.mainloop()  

if __name__ == "__main__":

    def plot():
        p = Plotter(1,1)
        #print(id(p.fig))
        ax = p.axes[0]
        ax.plot(np.arange(10), np.arange(10), label='test1')
        #ax.plot(np.arange(10), np.arange(10)+5, label='test2')
        ax.addMarker(5)
        #ax.activeMarker._set_yloc()
        #ax.plot(np.arange(10), np.arange(10)+5, label='test')
        #plt.show()
        #print(id(plt.figure))
        plt.legend()
        #plt.sca(ax)
        return p
        
    a = plot()
    #print(id(plt.figure))
    plt.show()

    #plot().show()
    #print(ax.markers)
    #plt.show()
    #plt.show()
    #print(engtools.sparam)
    #a = np.arange(10)
    #p = Plotter(1,1)
    #ax = p.axes[0]
    #plt.sca(ax)


    #s = Sparam(r"C:\Users\rlyon\gdrive\python\vector_modulator\data\0402.s2p")

    #s.plot(11)
    #plt.show()
    #print(p.axes[0])
    #ax.plot(a,a)
    #p.plot(a, a+5)
    #p.plot(a, a+10)
    #p.plot(a, a)
    #plt.show()
