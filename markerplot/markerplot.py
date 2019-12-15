
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib

##TODO: fix wanrning when marker lands on nan value
class Marker(object):
    def __init__(self, axes, xd, yd):
        ## xmode=True, show_xline=True, show_dot=True, yformat=None, xformat=None, show_xlabel=True, xreversed=False, alpha=0.7
        
        self.axes = axes
        self.show_xline = axes.marker_params['show_xline']
        self.show_xlabel = axes.marker_params['show_xlabel']
        self.xformat = axes.marker_params['xformat']
        self.xreversed = axes.marker_params['xreversed']

        self.height_ylabel = 0

        #self.data2display = self.axes.transData.transform
        #self.display2data = self.axes.transData.inverted().transform
        #self.data2axes = self.axes.transLimits.transform
        #self.axes2data = self.axes.transLimits.inverted().transform

        scale_func = {'log': np.log10, 'linear': lambda x: x}

        ## future matplotlib versions (and maybe past versions) might keep the tranform functions synced with the scale.
        ## for 3.1.1 we have to do this manually
        def data2axes(ax, point):
            xscale = ax.get_xscale()
            yscale = ax.get_yscale()

            assert xscale in scale_func, 'x-axes scale: {} not supported'.format(xscale)
            assert yscale in scale_func, 'y-axes scale: {} not supported'.format(yscale)

            xd = scale_func[xscale](point[0])
            yd = scale_func[yscale](point[1])

            return ax.transLimits.transform((xd,yd))

        self.data2axes = data2axes
        self.axes2display = self.axes.transAxes.transform
        self.display2axes = self.axes.transAxes.inverted().transform

        ## set ylabel_gap to 8 display units, convert to axes coordinates
        self.ylabel_gap = self.display2axes((8,0))[0] - self.display2axes((0,0))[0]

        self.lines = []

        ## keep track of all lines we want to add markers to
        for l in self.axes.lines:
            if (l not in self.axes.marker_ignorelines):
                self.lines.append((self.axes, l))

        ## get lines from any shared axes
        ## if kwargs were supplied, add these 
        for ax in self.axes.get_shared_x_axes().get_siblings(self.axes):
            if ax == self.axes:
                continue
            for l in ax.lines:
                if (l not in ax.marker_ignorelines):
                    self.lines.append((ax,l))
                
        self.ydot = [None]*len(self.lines)
        self.ytext = [None]*len(self.lines)
        self.xdpoint = None
        self.xidx = [0]*len(self.lines)
        self.renderer = self.axes.figure.canvas.get_renderer()
        self.line_xbounds = [None]*len(self.lines)

        if (len(self.lines) < 1):
            raise RuntimeError('Markers cannot be added to axes with no data lines.')

        self.create(xd, yd)

    ## TODO: find nearest using axes or display coordinates, not data coordinates
    def find_nearest_xdpoint(self, xd, yd=None):
        mline, xdpoint, mdist = None, 0, np.inf

        for ax, l in self.lines:
            xl, yl = l.get_xdata(), l.get_ydata()

            if yd==None or ax.marker_params['xmode']:
                dist = (xl - xd)**2
            else:
                dist = (xl - xd)**2 + (yl-yd)**2
            xidx_l, mdist_l = np.argmin(dist), np.min(dist)  
            
            if mdist_l < mdist:
                mline, xdpoint, mdist  = l, l.get_xdata()[xidx_l], mdist_l
        return xdpoint

    def create(self, xd, yd=None):
        self.xdpoint = self.find_nearest_xdpoint(xd, yd)

        ## vertical x line
        boxparams = dict(boxstyle='round', facecolor='black', edgecolor='black', alpha=0.7)
        self.xline = self.axes.axvline(self.xdpoint, linewidth=0.5, color='r')
        self.axes.marker_ignorelines.append(self.xline)

        ## x label
        self.xtext = self.axes.text(0, 0, '', color='white', transform=self.axes.transAxes, fontsize=8, verticalalignment='center', bbox=boxparams)
        
        ## ylabels and ydots for each line
        for i, (ax,l) in enumerate(self.lines):
    
            boxparams = dict(facecolor='black', edgecolor=l.get_color(), linewidth=1.6, boxstyle='round', alpha=ax.marker_params['alpha'])
            self.ytext[i] = ax.text(0, 0, '0' ,color='white', fontsize=8, transform = ax.transAxes, verticalalignment='center', bbox=boxparams)

            self.ydot[i] = Line2D([0], [0], linewidth=10, color=l.get_color(), markersize=10)
            self.ydot[i].set_marker('.')
            self.ydot[i].set_linestyle(':')
            ax.add_line(self.ydot[i])
            self.axes.marker_ignorelines.append(self.ydot[i])
            ax.marker_ignorelines.append(self.ydot[i])
            
            if not ax.marker_params['show_dot']:
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

        for i, (ax,l) in enumerate(self.lines):
            self.xidx[i] = np.argmin(np.abs(l.get_xdata()-self.xdpoint))
        
        ## vertical line placement
        self.xline.set_xdata([self.xdpoint, self.xdpoint])

        xa, ya = self.data2axes(self.axes, (self.xdpoint, 0))

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
        for i, (ax,l) in enumerate(self.lines):

            ## turn off ylabel and dot if ypoint is out of bounds
            if (self.xdpoint > self.line_xbounds[i][1]) or (self.xdpoint < self.line_xbounds[i][0]):
                self.ytext[i].set_visible(False)
                self.ydot[i].set_visible(False)
            else:
                self.ytext[i].set_visible(True)
                self.ydot[i].set_visible(True)

            ## ylabel and dot position
            xd, yd = l.get_xdata()[self.xidx[i]], l.get_ydata()[self.xidx[i]]

            xa, ya = self.data2axes(ax, (xd, yd))
            self.ytext[i].set_position((xa+self.ylabel_gap, ya))
            self.ydot[i].set_data([xd], [yd])

            ## ylabel text
            if ax.marker_params['yformat'] != None:
                txt = ax.marker_params['yformat'](xd, yd)
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

        for i, (ax,l) in enumerate(self.lines):
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
                new_xpoint = self.lines[l_idx][1].get_xdata()[self.xidx[l_idx]] + step_size
                self.move_to_point(new_xpoint)
        else:
            l_idx = np.argmax(xloc)
            if np.max(xloc) > -np.inf:
                new_xpoint = self.lines[l_idx][1].get_xdata()[self.xidx[l_idx]] - step_size
                self.move_to_point(new_xpoint)

    def remove(self):

        self.xtext.set_visible(False)
        idx = self.axes.lines.index(self.xline)
        self.axes.lines.pop(idx)

        for i, (ax,l) in enumerate(self.lines):		
            idx = ax.lines.index(self.ydot[i])
            ax.lines.pop(idx)
            idx = self.ytext[i].set_visible(False)

    def contains_event(self, event):
        for ym in self.ytext:
            contains, attrd = ym.contains(event)
            if (contains):
                return True
        return False

class MarkerManager(object):
    def __init__(self, fig, linked_axes=None):
        self.fig = fig
        self.linked_axes = [] if linked_axes == None else linked_axes

        self.move = None
        self.shift_is_held = False
        self.active_marker = {}
        for ax in fig.axes:
            self.active_marker[id(ax)] = None
        for ax in self.linked_axes:
            self.active_marker[id(ax)] = None

        self.cidclick = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.cidpress = self.fig.canvas.mpl_connect('key_press_event', self.onkey_press)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('key_release_event', self.onkey_release)
        self.cidmotion = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('button_release_event', self.onrelease)

    def move_linked(self, xd, yd):
        for ax in self.linked_axes:
            active_marker = self.active_marker[id(ax)]
            active_marker.move_to_point(xd, yd)

    def add_linked(self, xd, yd):
        for ax in self.linked_axes:
            self.active_marker[id(ax)] = ax.marker_add(xd, yd)  

    def shift_linked(self, direction):
        for ax in self.linked_axes:
            active_marker = self.active_marker[id(ax)]
            active_marker.shift(direction)
        
    def delete_linked(self):
        for ax in self.linked_axes:
            self.active_marker[id(ax)] = ax.marker_delete(active_marker)

    def draw_linked(self):
        for ax in self.linked_axes:
            fig = ax.figure
            if fig != self.fig:
                fig.canvas.draw()


    def get_event_marker(self, axes, event):
        for m in axes.markers:
            if m.contains_event(event):
                return m
        return None

    def get_event_axes(self, event):
        axes = event.inaxes
        if id(axes) in self.active_marker.keys():
            return axes
        else:
            return None

    def onkey_release(self, event):
        if event.key == 'shift':
            self.shift_is_held = False

    def onkey_press(self, event):
        axes = self.get_event_axes(event)
        if axes == None:
            return

        active_marker = self.active_marker[id(axes)]

        if active_marker == None:
            return
        elif event.key == 'shift':
            self.shift_is_held = True
        elif(event.key == 'left'):
            active_marker.shift(-1)
            self.shift_linked(-1)
        elif(event.key == 'right'):
            active_marker.shift(1)
            self.shift_linked(1)
        elif(event.key == 'delete'):
            self.active_marker[id(axes)] = axes.marker_delete(active_marker)
            self.delete_linked()
        self.fig.canvas.draw()
        self.draw_linked()

    def onmotion(self, event):
        xd = event.xdata
        yd = event.ydata
        axes = self.get_event_axes(event)

        if axes == None:
            return

        active_marker = self.active_marker[id(axes)]

        if axes != self.move or active_marker == None:
            return
        
        active_marker.move_to_point(xd, yd)
        self.move_linked(xd, yd)
        self.fig.canvas.draw()
        self.draw_linked()

    def onrelease(self, event):
        self.move = None

    def onclick(self, event):
        xd = event.xdata
        yd = event.ydata
        axes = self.get_event_axes(event)

        if (axes == None):
            return
        self.move = axes

        m = self.get_event_marker(axes, event)
        active_marker = self.active_marker[id(axes)]

        if (m == None and (active_marker == None or self.shift_is_held == True)):
            self.active_marker[id(axes)] = axes.marker_add(xd, yd)  
            self.add_linked(xd, yd)
        elif (m != None): 
            self.active_marker[id(axes)] = m
        elif (active_marker != None):
            active_marker.move_to_point(xd, yd)
            self.move_linked(xd, yd)
        else:
            return
        
        self.fig.canvas.draw()
        self.draw_linked()
        return

