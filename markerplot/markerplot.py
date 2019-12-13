
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib

class Marker(object):
    def __init__(self, axes, xd, yd, xmode=True, show_xline=True, show_dot=True, yformat=None, xformat=None, show_xlabel=True, xreversed=False):
        
        self.axes = axes
        self.yformat = yformat
        self.xformat = xformat
        self.xreversed = xreversed
        self.show_xlabel = show_xlabel
        self.show_xline = show_xline
        self.show_dot = show_dot
        self.xline = None
        self.height_ylabel = 0
        self.xmode = xmode

        #self.data2display = self.axes.transData.transform
        #self.display2data = self.axes.transData.inverted().transform
        #self.data2axes = self.axes.transLimits.transform
        #self.axes2data = self.axes.transLimits.inverted().transform

        scale_func = {'log': np.log10, 'linear': lambda x: x}

        ## future matplotlib versions (and maybe past versions) might keep the tranform functions synced with the scale.
        ## for 3.1.1 we have to do this manually
        def data2axes(point):
            xscale = self.axes.get_xscale()
            yscale = self.axes.get_yscale()

            assert xscale in scale_func, 'x-axes scale: {} not supported'.format(xscale)
            assert yscale in scale_func, 'y-axes scale: {} not supported'.format(yscale)

            xd = scale_func[xscale](point[0])
            yd = scale_func[yscale](point[1])

            return self.axes.transLimits.transform((xd,yd))

        self.data2axes = data2axes
        self.axes2display = self.axes.transAxes.transform
        self.display2axes = self.axes.transAxes.inverted().transform

        ## set ylabel_gap to 8 display units, convert to axes coordinates
        self.ylabel_gap = self.display2axes((8,0))[0] - self.display2axes((0,0))[0]

        self.lines = []
        
        ## keep track of all lines we want to add markers to
        for l in self.axes.lines:
            if (l not in self.axes.marker_ignorelines):
                self.lines.append(l)
                
        self.ydot = [None]*len(self.lines)
        self.ytext = [None]*len(self.lines)
        self.xdpoint = None
        self.xidx = [0]*len(self.lines)
        self.renderer = self.axes.figure.canvas.get_renderer()
        self.line_xbounds = [None]*len(self.lines)

        if (len(self.lines) < 1):
            raise RuntimeError('Markers cannot be added to axes with no data lines.')

        self.create(xd, yd)

    def find_nearest_xdpoint(self, xd, yd=None):
        mline, xdpoint, mdist = None, 0, np.inf

        for l in self.lines:
            xl, yl = l.get_xdata(), l.get_ydata()

            if yd==None or self.xmode:
                dist = (xl - xd)**2
            else:
                dist = (xl - xd)**2 + (yl-yd)**2
            xidx_l, mdist_l = np.argmin(dist), np.min(dist)  
            
            if mdist_l < mdist:
                mline, xdpoint, mdist  = l, l.get_xdata()[xidx_l], mdist_l
        return xdpoint

    def create(self, xd, yd=None):
        self.xdpoint = self.find_nearest_xdpoint(xd, yd)
        xa, ya = self.data2axes((self.xdpoint, 0))

        ## vertical x line
        boxparams = dict(boxstyle='round', facecolor='black', edgecolor='black', alpha=0.7)
        self.xline = self.axes.axvline(self.xdpoint, linewidth=0.5, color='r')
        self.axes.marker_ignorelines.append(self.xline)

        ## x label
        self.xtext = self.axes.text(xa, 0, '', color='white', transform=self.axes.transAxes, fontsize=8, verticalalignment='center', bbox=boxparams)
        
        ## ylabels and ydots for each line
        for i, l in enumerate(self.lines):
    
            boxparams = dict(facecolor='black', edgecolor=l.get_color(), linewidth=1.6, boxstyle='round', alpha=0.7)
            self.ytext[i] = self.axes.text(xa+self.ylabel_gap, 0, '0' ,color='white', fontsize=8, transform = self.axes.transAxes, verticalalignment='center', bbox=boxparams)

            self.ydot[i] = Line2D([0], [0], linewidth=10, color=l.get_color(), markersize=10)
            self.ydot[i].set_marker('.')
            self.ydot[i].set_linestyle(':')
            self.axes.add_line(self.ydot[i])
            self.axes.marker_ignorelines.append(self.ydot[i])
            if not self.show_dot:
                self.ydot[i].set_visible(False)
            self.line_xbounds[i] = np.min(l.get_xdata()), np.max(l.get_xdata())

        ## compute height of ylabels, these should all be identical
        ytext_dim = self.ytext[0].get_window_extent(self.renderer)
        y1 = self.display2axes((ytext_dim.x0, ytext_dim.y0))[1]
        y2 = self.display2axes((ytext_dim.x1, ytext_dim.y1))[1]
        self.height_ylabel = (y2-y1)*1.8

        ## move objects to current point
        self.move_to_point(xd, yd)

        ## set visibility
        if not self.show_xlabel:
            self.xtext.set_visible(False)
        if not self.show_xline:
            self.xline.set_visible(False)


    def space_ylabels(self, xa):
        ylabels = list(self.ytext)
        zipped = zip(self.yloc, ylabels, xa)
        zipped_sorted  = sorted(zipped, key=lambda x: x[0])
        yloc, ylabels, xa = zip(*zipped_sorted)

        yloc = list(yloc)
        for i, y in enumerate(yloc):
            if i >= len(yloc) -1:
                break
            ovl = (yloc[i+1] - self.height_ylabel/2) - (y + self.height_ylabel/2)

            if ovl < 0:
                yloc[i] -= abs(ovl)/2
                yloc[i+1] += abs(ovl)/2
                for j in range(i-1, -1, -1):
                    ovl = (yloc[j+1] - self.height_ylabel/2) - (yloc[j] + self.height_ylabel/2)
                    if ovl < 0:
                        yloc[j] -= abs(ovl)

        for i, y in enumerate(yloc):
            ylabels[i].set_position((xa[i]+self.ylabel_gap, y))
        self.yloc = yloc


    def move_to_point(self, xd, yd=None):
        self.xdpoint = self.find_nearest_xdpoint(xd, yd)

        for i, l in enumerate(self.lines):
            self.xidx[i] = np.argmin(np.abs(l.get_xdata()-self.xdpoint))
        
        ## vertical line placement
        self.xline.set_xdata([self.xdpoint, self.xdpoint])

        xa, ya = self.data2axes((self.xdpoint, 0))

        ## xlabel text
        if self.xformat != None:
            txt = self.xformat(self.xdpoint)
        else:
            txt = '{:.3f}'.format(self.xdpoint) 

        self.xtext.set_text(txt)

        ## xlabel placement
        xtext_dim = self.xtext.get_window_extent(self.renderer)
        x1 = self.display2axes((xtext_dim.x0, xtext_dim.y0))[0]
        x2 = self.display2axes((xtext_dim.x1, xtext_dim.y1))[0]
        xlen = (x2-x1)/2

        self.xtext.set_position((xa-xlen, 0))

        xloc =[]
        self.yloc = []
        for i, l in enumerate(self.lines):

            ## turn off ylabel and dot if ypoint is out of bounds
            if (self.xdpoint > self.line_xbounds[i][1]) or (self.xdpoint < self.line_xbounds[i][0]):
                self.ytext[i].set_visible(False)
                self.ydot[i].set_visible(False)
            else:
                self.ytext[i].set_visible(True)
                self.ydot[i].set_visible(True)

            ## ylabel and dot position
            xd, yd = l.get_xdata()[self.xidx[i]], l.get_ydata()[self.xidx[i]]

            xa, ya = self.data2axes((xd, yd))
            self.ytext[i].set_position((xa+self.ylabel_gap, ya))
            self.ydot[i].set_data([xd], [yd])

            ## ylabel text
            if self.yformat != None:
                txt = self.yformat(yd)
            else:
                txt = '{:0.3f}'.format(yd)

            self.ytext[i].set_text(txt)
            
            xloc.append(xa)
            self.yloc.append(ya)
        
        self.space_ylabels(xloc)


    def shift(self, direction):
        direction = -direction if self.xreversed else direction
        xmax, xmin = -np.inf, np.inf
        line = None
        step_sizes = np.array([0.0]*len(self.lines), dtype='float64')
        if direction > 0:
            xloc = np.array([np.inf]*len(self.lines))
        else:
            xloc = np.array([-np.inf]*len(self.lines))

        for i, l in enumerate(self.lines):
            xdata = l.get_xdata()

            if direction > 0:
                
                if (self.xidx[i] +1) < len(xdata):
                    step_sizes[i] = xdata[self.xidx[i] +1] - xdata[self.xidx[i]]
                    xloc[i] = xdata[self.xidx[i]]

            else:
                if (self.xidx[i] -1) >= 0:
                    step_sizes[i] = xdata[self.xidx[i]] - xdata[self.xidx[i] -1]
                    xloc[i] = xdata[self.xidx[i]]
    
        step_size = np.max(step_sizes)
        if direction > 0:
            l_idx = np.argmin(xloc)
            if np.min(xloc) < np.inf:
                new_xpoint = self.lines[l_idx].get_xdata()[self.xidx[l_idx]] + step_size
                self.move_to_point(new_xpoint)
        else:
            l_idx = np.argmax(xloc)
            if np.max(xloc) > -np.inf:
                new_xpoint = self.lines[l_idx].get_xdata()[self.xidx[l_idx]] - step_size
                self.move_to_point(new_xpoint)

    def remove(self):

        self.xtext.set_visible(False)
        idx = self.axes.lines.index(self.xline)
        self.axes.lines.pop(idx)

        for i, l in enumerate(self.lines):		
            idx = self.axes.lines.index(self.ydot[i])
            self.axes.lines.pop(idx)
            idx = self.ytext[i].set_visible(False)

    def contains_event(self, event):
        for ym in self.ytext:
            contains, attrd = ym.contains(event)
            if (contains):
                return True
        return False

class MarkerManager(object):
    def __init__(self, fig):
        self.fig = fig

        self.move = None
        self.shift_is_held = False
        self.active_marker = None

        self.cidclick = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.cidpress = self.fig.canvas.mpl_connect('key_press_event', self.onkey_press)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('key_release_event', self.onkey_release)
        self.cidmotion = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('button_release_event', self.onrelease)

    def get_event_marker(self, axes, event):
        for m in axes.markers:
            if m.contains_event(event):
                return m
        return None

    def onkey_release(self, event):
        if event.key == 'shift':
            self.shift_is_held = False

    def onkey_press(self, event):
        axes = event.inaxes

        if self.active_marker == None or axes == None:
            return
        elif event.key == 'shift':
            self.shift_is_held = True
        elif(event.key == 'left'):
            self.active_marker.shift(-1)
        elif(event.key == 'right'):
            self.active_marker.shift(1)
        elif(event.key == 'delete'):
            self.active_marker = axes.marker_delete(self.active_marker)
        self.fig.canvas.draw()

    def onmotion(self, event):
        xd = event.xdata
        yd = event.ydata
        axes = event.inaxes
        if axes == None or axes != self.move or self.active_marker == None:
            return
        
        self.active_marker.move_to_point(xd, yd)
        self.fig.canvas.draw()

    def onrelease(self, event):
        self.move = None

    def onclick(self, event):
        xd = event.xdata
        yd = event.ydata
        axes = event.inaxes
        if (axes == None):
            return
        self.move = axes

        m = self.get_event_marker(axes, event)

        if (m == None and (self.active_marker == None or self.shift_is_held == True)):
            self.active_marker = axes.marker_add(xd, yd)
        elif (m != None): 
            self.active_marker = m
        elif (self.active_marker != None):
            self.active_marker.move_to_point(xd, yd)
        else:
            return
        
        self.fig.canvas.draw()
        return

