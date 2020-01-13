
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from time import time
from threading import Timer, Semaphore


class Marker(object):
    
    def __init__(self, axes, xd=None, idx=None, disp=None):
        """ create marker on axes at a given x data value, data index value or display coordinate

            Parameters
            ----------
                xd: (float) x-value in data coordinates
                disp: (tuple) x,y tuple of display cordinates
                idx: (int) index of x-data (only used in index mode)
        """
        self.axes = axes 

        ## marker will inherit these parameters from axes, ignoring params from linked axes
        self.show_xline = axes.marker_params['show_xline']
        self.show_xlabel = axes.marker_params['show_xlabel'] if self.axes.name != 'polar' else False
        self.xreversed = axes.marker_params['xreversed']
        self.wrap = axes.marker_params['wrap']
        self.xlabel_pad = axes.marker_params['xlabel_pad']
        self.ylabel_xpad = axes.marker_params['ylabel_xpad']
        self.ylabel_ypad = axes.marker_params['ylabel_ypad']

        self.ylabel_xpad *= (self.axes.figure.dpi/100)
        self.ylabel_ypad *= (self.axes.figure.dpi/100)
        self.xlabel_pad *= (self.axes.figure.dpi/100)

        #self.data2display = self.axes.transData.transform
        #self.display2data = self.axes.transData.inverted().transform

        scale_func = {'log': np.log10, 'linear': lambda x: x}

        ## future matplotlib versions (and maybe past versions) might keep the tranform functions synced with the scale.
        ## for 3.1.1 we have to do this manually
        ## TODO: fix this to handle numpy arrays
        def data2display(ax, point):
            xscale = ax.get_xscale()
            yscale = ax.get_yscale()
            
            assert xscale in scale_func, 'x-axes scale: {} not supported'.format(xscale)
            assert yscale in scale_func, 'y-axes scale: {} not supported'.format(yscale)

            xd = scale_func[xscale](point[0])
            yd = scale_func[yscale](point[1])

            return ax.transData.transform((xd,yd))

        self.data2display = data2display
        self.axes2display = self.axes.transAxes.transform
        self.display2data = self.axes.transData.inverted().transform

        self.lines = []

        ## keep track of all lines we want to add markers to
        for l in self.axes.lines:
            if (l not in self.axes.marker_ignorelines):
                self.lines.append((self.axes, l))

        ## get lines from any shared axes
        for ax in self.axes.get_shared_x_axes().get_siblings(self.axes):
            if ax == self.axes:
                continue
            for l in ax.lines:
                if (l not in ax.marker_ignorelines) and (l not in self.axes.marker_ignorelines):
                    self.lines.append((ax,l))
        
        self.ydot = [None]*len(self.lines)
        self.ytext = [None]*len(self.lines)
        self.xdpoint = None
        self.xidx = [0]*len(self.lines)
        self.renderer = self.axes.figure.canvas.get_renderer()
        self.line_xbounds = [None]*len(self.lines)

        if (len(self.lines) < 1):
            raise RuntimeError('Markers cannot be added to axes without data lines.')

        ## check if all lines have identical x-data
        ## turn on index mode if so. 
        xcheck = np.zeros(shape=(len(self.lines), 3))
        for i, (ax,l) in enumerate(self.lines):
            xdata = l.get_xdata()
            xcheck[i] = xdata[0], xdata[-1], len(xdata)
            #TODO: fix this for different x and y scales
            l.xy = ax.transData.transform(l.get_xydata())

        for ax in self.axes.marker_linked_axes:
            for l in ax.lines:
                if (l not in ax.marker_ignorelines):
                    xdata = l.get_xdata()
                    xcheck = np.append(xcheck, [[xdata[0], xdata[-1], len(xdata)]], axis=0)

        self.index_mode = np.all(xcheck == xcheck[0,:]) if not self.axes._force_index_mode else True

        ## xlabel only valid if every line has identical x-data, (?? xline might not be valid either ??)
        self.show_xlabel = False if not self.index_mode else self.show_xlabel

        self.create(xd, idx=idx, disp=disp)

    def update_marker(self):
        """ updates marker (without drawing on canvas) if the dpi or figure size changes
        """
        self.xlabel_pad = self.axes.marker_params['xlabel_pad']
        self.ylabel_xpad = self.axes.marker_params['ylabel_xpad']
        self.ylabel_ypad = self.axes.marker_params['ylabel_ypad']

        self.ylabel_xpad *= (self.axes.figure.dpi/100)
        self.ylabel_ypad *= (self.axes.figure.dpi/100)
        self.xlabel_pad *= (self.axes.figure.dpi/100)

        self.display2data = self.axes.transData.inverted().transform

        for i, (ax,l) in enumerate(self.lines):
            l.xy = self.axes.transData.transform(l.get_xydata())

        self.move_to_point(self.xdpoint, idx=self.xidx[0])

    def find_nearest_xdpoint(self, xd=None, disp=None):
        mline, xdpoint, mdist = None, 0, np.inf

        if disp != None:
            x, y = disp

        for ax, l in self.lines:
            if self.show_xline:
                if disp != None:
                    xd, yd = self.display2data(disp)
                xl = l.get_xdata()
                if (ax.name == 'polar'):
                    dist = np.full(fill_value=np.inf, shape=(3, len(xl)))
                    dist[0] = np.abs(xl - xd)
                    dist[1] = np.abs((xl +2*np.pi) -xd)
                    dist[2] = np.abs((xl -2*np.pi) -xd)

                    xlist = np.zeros(shape=(len(dist), 2))
                    for i in range(len(dist)):
                        idx = np.argmin(dist[i])
                        xlist[i] = idx, dist[i][idx]

                    min_idx = np.argmin(xlist[:,1])
                    xidx_l, mdist_l = xlist[min_idx]
                else:
                    dist = np.abs(xl - xd)
                    xidx_l, mdist_l = np.argmin(dist), np.min(dist) 
                
            else:
                if disp != None:
                    xl, yl = l.xy[:,0], l.xy[:,1]
                    dist = np.abs(xl - x) + np.abs(yl-y)
                else:
                    xl, yl = l.get_data()
                    dist = np.abs(xl - xd)

                xidx_l, mdist_l = np.argmin(dist), np.min(dist)  
            
            if mdist_l < mdist:
                mline, xdpoint, mdist  = l, l.get_xdata()[int(xidx_l)], mdist_l

        return mline, xdpoint

    def create(self, xd=None, disp=None, idx=None):

        mline, self.xdpoint = self.find_nearest_xdpoint(xd, disp=disp)

        ## vertical x line
        boxparams = dict(boxstyle='round', facecolor='black', edgecolor='black', alpha=0.7)
        self.xline = self.axes.axvline(self.xdpoint, linewidth=0.5, color='r')
        self.axes.marker_ignorelines.append(self.xline)

        ## x label
        x0, y0 = self.axes2display((0,0))
        self.xtext = self.axes.text(x0,y0, '0', color='white', transform=None, fontsize=8, verticalalignment='center', bbox=boxparams)
        self.xtext.set_zorder(20)

        ## ylabels and ydots for each line
        for i, (ax,l) in enumerate(self.lines):
    
            boxparams = dict(facecolor='black', edgecolor=l.get_color(), linewidth=1.6, boxstyle='round', alpha=ax.marker_params['alpha'])
            self.ytext[i] = ax.text(0, 0, '0' ,color='white', fontsize=8, transform=None, verticalalignment='center', bbox=boxparams)

            self.ydot[i] = Line2D([0], [0], linewidth=10, color=l.get_color(), markersize=10)
            self.ydot[i].set_marker('.')
            self.ydot[i].set_linestyle(':')
            ax.add_line(self.ydot[i])
            self.axes.marker_ignorelines.append(self.ydot[i])
            ax.marker_ignorelines.append(self.ydot[i])
            
            if not ax.marker_params['show_dot']:
                self.ydot[i].set_visible(False)
                self.ydot[i].set_zorder(0)
            self.line_xbounds[i] = np.min(l.get_xdata()), np.max(l.get_xdata())

        ## move objects to current point
        self.move_to_point(xd, disp=disp, idx=idx)

        ## set visibility
        if not self.show_xlabel:
            self.xtext.set_visible(False)
        if not self.show_xline:
            self.xline.set_visible(False)

    def compute_shift_label(self, loc_array, idx, shift):
        loc_array[idx, :] += shift
        if shift > 0:
            for i in range(idx+1, len(loc_array)):
                ovl = loc_array[i, 0] - loc_array[i-1, 1]
                if ovl < 0:
                    loc_array[i, :] += abs(ovl)
        else:
            for i in range(idx-1, -1, -1):
                ovl = loc_array[i+1, 0] - loc_array[i, 1]
                if ovl < 0:
                    loc_array[i, :] -= abs(ovl)


    def _compute_ylabel_loc(self, loc_array, ymin, ymax):

        size = len(loc_array)
        for i in range(int(size/2),  size):
            if i > (size-2):
                continue
            ovl = loc_array[i+1, 0] - loc_array[i, 1]
            if ovl > 0: 
                continue

            self.compute_shift_label(loc_array, i, -abs(ovl)/2)
            self.compute_shift_label(loc_array, i+1, abs(ovl)/2)

        for i in range(int(size/2), -1, -1):
            if i < 1:
                continue
            ovl = loc_array[i, 0] - loc_array[i-1, 1]
            if ovl > 0: 
                continue

            self.compute_shift_label(loc_array, i-1, -abs(ovl)/2)
            self.compute_shift_label(loc_array, i, abs(ovl)/2)

        max_ovl = ymax - loc_array[-1, 1]
        min_ovl = loc_array[0, 0] - ymin

        if max_ovl < 0:
            self.compute_shift_label(loc_array, len(loc_array)-1, max_ovl)
        if min_ovl < 0:
            self.compute_shift_label(loc_array, 0, abs(min_ovl))

    
    def space_labels(self):
        """ seperates overlapping ylabels with a spacing given by self.ylabel_ypad
        """
        xmin, ymin = self.axes2display((0,0))
        xmax, ymax = self.axes2display((1,1))

        ymax -= self.ylabel_ypad
        ymin += self.ylabel_ypad
        xmax -= self.ylabel_xpad
        xmin += self.ylabel_xpad

        xlabel_dim = self.xtext.get_window_extent(self.renderer)
        if self.show_xlabel:
            ymin = xlabel_dim.y1 + self.ylabel_ypad

        ## generate list of ylabel locations
        dims = []
        ylocs = []
        for i, ytext in enumerate(self.ytext):
            dim = ytext.get_window_extent(self.renderer)
            dims.append(dim)
            ylocs.append((dim.y1 + dim.y0)/2)

        ## sort ylabels by their positions on the axes
        ylabels = list(self.ytext)
        zipped = zip(ylocs, ylabels, dims)
        zipped_sorted  = sorted(zipped, key=lambda x: x[0])
        ylocs, ylabels, dims = zip(*zipped_sorted)
        
        loc_array = np.zeros(shape=(len(dims), 2))
        for i, dim in enumerate(dims):
            loc_array[i,:] = dim.y0-self.ylabel_ypad, dim.y1+self.ylabel_ypad

        self._compute_ylabel_loc(loc_array, ymin, ymax)

        for i, ytext in enumerate(ylabels):
            xloc = dims[i].x0
            yloc = (loc_array[i, 1] + loc_array[i, 0])/2
            ytext.set_position((xloc, yloc))
            if dims[i].x1 > xmax:
                xloc -= (dims[i].x1 - dims[i].x0) + self.ylabel_xpad*2
            ytext.set_position((xloc, yloc))
        
        if xlabel_dim.x0 < xmin:
            ypos = (xlabel_dim.y1 + xlabel_dim.y0)/2
            xpos = xmin
            self.xtext.set_position((xpos, ypos))

        if xlabel_dim.x1 > xmax:
            ypos = (xlabel_dim.y1 + xlabel_dim.y0)/2
            xpos = xmax - (xlabel_dim.x1 - xlabel_dim.x0)
            self.xtext.set_position((xpos, ypos))

    def move_to_point(self, xd=None, disp=None, idx=None):

        mline, self.xdpoint = self.find_nearest_xdpoint(xd, disp=disp)

        if not self.index_mode:
            for i, (ax,l) in enumerate(self.lines):
                self.xidx[i] = np.argmin(np.abs(l.get_xdata()-self.xdpoint))
                if l == mline:
                    self.xdpoint = l.get_xdata()[self.xidx[i]]
        else:
            if idx == None:
                idx = np.argmin(np.abs(mline.get_xdata()-self.xdpoint))
            for i, (ax,l) in enumerate(self.lines):
                self.xidx[i] = idx
            self.xdpoint = mline.get_xdata()[self.xidx[0]]
        
        ## vertical line placement
        self.xline.set_xdata([self.xdpoint, self.xdpoint])

        xl, yl = self.data2display(self.axes, (self.xdpoint, 0))

        ## xlabel text
        txt = self.axes.marker_params['xformat'](self.xdpoint)

        self.xtext.set_text(txt)

        ## xlabel placement
        self.renderer = self.axes.figure.canvas.get_renderer()
        xtext_dim = self.xtext.get_window_extent(self.renderer)
        x0, y0 = self.axes2display((0,0))

        x1, y1 = xtext_dim.x0, xtext_dim.y0
        x2, y2 = xtext_dim.x1, xtext_dim.y1
        xlen = x2-x1

        xlabel_ypos = y0 + (y2-y1)/2 + self.xlabel_pad
        self.xtext.set_position((xl-xlen/2, xlabel_ypos))

        xloc = []
        yloc = []
        for i, (ax,l) in enumerate(self.lines):
            self.ytext[i].set_visible(True)
            self.ydot[i].set_visible(True)

            if not self.index_mode:
                ## turn off ylabel and dot if ypoint is out of bounds
                if (self.xdpoint > self.line_xbounds[i][1]) or (self.xdpoint < self.line_xbounds[i][0]):
                    self.ytext[i].set_visible(False)
                    self.ydot[i].set_visible(False)

            ## ylabel and dot position
            xd, yd = l.get_xdata()[self.xidx[i]], l.get_ydata()[self.xidx[i]]
            xl, yl = self.data2display(ax, (xd, yd))

            if (not np.isfinite(yd)):
                self.ytext[i].set_visible(False)
                self.ydot[i].set_visible(False)

            else:
                self.ytext[i].set_position((xl+self.ylabel_xpad, yl))
                self.ydot[i].set_data([xd], [yd])

                ## ylabel text
                txt = ax.marker_params['yformat'](xd, yd, idx=self.xidx[i])

                self.ytext[i].set_text(txt)
        
        self.space_labels()

    def shift(self, direction):
        direction = -direction if self.xreversed else direction
        xmax, xmin = -np.inf, np.inf

        if self.index_mode:
            xlen = len(self.lines[0][1].get_xdata())
            nxidx = self.xidx[0] -1 if direction < 0 else self.xidx[0] +1
            if (nxidx >= xlen):
                nxidx = 0 if self.wrap else xlen-1
            elif (nxidx <= 0):
                nxidx = xlen-1 if self.wrap else 0
            self.move_to_point(self.lines[0][1].get_xdata()[nxidx])
            return

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
        contains, attrd = self.xtext.contains(event)
        if (contains):
            return True
            
        for ym in self.ytext:
            contains, attrd = ym.contains(event)
            if (contains):
                return True
        return False

    def set_animated(self, state):
        self.xline.set_animated(state)
        self.xtext.set_animated(state)
        for i, (ax,l) in enumerate(self.lines):
            self.ydot[i].set_animated(state)
            self.ytext[i].set_animated(state)

    def draw(self):
        """ draws marker on canvas
            assumes the canvas has already been restored correctly
        """
        self.axes.draw_artist(self.xline)
        for i, (ax,l) in enumerate(self.lines):
            self.ydot[i].axes.draw_artist(self.ydot[i])
            self.ytext[i].axes.draw_artist(self.ytext[i])
        self.axes.draw_artist(self.xtext)

        blit_axes = []
        for i, (ax,l) in enumerate(self.lines):
            if ax in blit_axes: continue
            ax.figure.canvas.blit(ax.bbox)
            blit_axes.append(ax)


class MarkerManager(object):
    def __init__(self, fig, top_axes=None):
        self.fig = fig

        if top_axes == None:
            self.top_axes = []
        elif not isinstance(top_axes, (tuple, list, np.ndarray)):
            self.top_axes = [top_axes]
        else:
            self.top_axes = top_axes

        for ax in self.top_axes:
            self.axes_to_top(ax)

        self.move = None
        self.shift_is_held = False 

        self.zoom = False

        self.cidclick = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.cidpress = self.fig.canvas.mpl_connect('key_press_event', self.onkey_press)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('key_release_event', self.onkey_release)
        self.cidmotion = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('button_release_event', self.onrelease)
        self.ciddraw = self.fig.canvas.mpl_connect('draw_event', self.on_draw)
        
    def axes_to_top(self, axes):
        max_zorder = 0
        for ax in axes.get_shared_x_axes().get_siblings(axes):
            if ax.get_zorder() > max_zorder:
                max_zorder = ax.get_zorder()
        axes.set_zorder(max_zorder+1)
        axes.patch.set_visible(False)
        
    def move_linked(self, axes, x, y):
        axes.marker_active.move_to_point(disp=(x,y))
        idx = axes.marker_active.xidx[0] if axes._force_index_mode else None
        for ax in axes.marker_linked_axes:
            ax.marker_active.move_to_point(xd=axes.marker_active.xdpoint, idx=idx)

    def add_linked(self, axes, x, y):
        marker = axes.marker_add(disp=(x,y))  
        idx = axes.marker_active.xidx[0] if axes._force_index_mode else None
        for ax in axes.marker_linked_axes:
            ax.marker_add(xd=axes.marker_active.xdpoint, idx=idx)

        self.make_linked_active(axes, marker)
        self.draw_all()

    def shift_linked(self, axes, direction):
        axes.marker_active.shift(direction)
        idx = axes.marker_active.xidx[0] if axes._force_index_mode else None
        for ax in axes.marker_linked_axes:
            ax.marker_active.move_to_point(xd=axes.marker_active.xdpoint, idx=idx)
            #ax.marker_active.shift(direction)
        
    def delete_linked(self, axes):
        new_marker = axes.marker_delete(axes.marker_active)
        for ax in axes.marker_linked_axes:
            ax.marker_delete(ax.marker_active)

        self.make_linked_active(axes, new_marker)

    def make_linked_active(self, axes, marker):
        axes.marker_active = marker
        if (marker != None):
            idx = axes.markers.index(axes.marker_active)
            for ax in axes.marker_linked_axes:
                ax.marker_active = ax.markers[idx]
        else:
            for ax in axes.marker_linked_axes:
                ax.marker_active = None

    def set_all_animated(self, state):
        for ax in self.fig.axes:
            for m in ax.markers:
                m.set_animated(state)
            for l_ax in ax.marker_linked_axes:
                for m in l_ax.markers:
                    m.set_animated(state)

    def set_active_animated(self):
        for ax in self.fig.axes:
            if ax.marker_active != None:
                ax.marker_active.set_animated(True)
            for l_ax in ax.marker_linked_axes:
                if l_ax.marker_active != None:
                    l_ax.marker_active.set_animated(True)

    def clear_saved_background(self):
        for ax in self.fig.axes:
            ax._draw_background = None
            for l_ax in ax.marker_linked_axes:
                l_ax._draw_background = None

    def draw_active_marker(self, axes):
        if axes._draw_background == None:
            self.draw_all(animated=True)

        ## set active marker on each axes to animated
        axes.figure.canvas.restore_region(axes._draw_background)
        if axes.marker_active != None:
            axes.marker_active.draw()
        for ax in axes.marker_linked_axes:
            ax.figure.canvas.restore_region(ax._draw_background)
            if ax.marker_active != None:
                ax.marker_active.draw()

    def get_event_marker(self, axes, event):
        for m in axes.markers:
            if m.contains_event(event):
                return m
        return None

    def get_event_axes(self, event):
        plt.figure(self.fig.number)
        if plt.get_current_fig_manager().toolbar.mode != '':
            self.zoom = True
        else:
            self.zoom = False

        if self.zoom:
            return None

        axes = event.inaxes
        if axes in self.fig.axes:
            for ax in axes.get_shared_x_axes().get_siblings(axes):
                if (ax in self.top_axes):
                    return ax
            return axes
        else:
            return None

    def onkey_release(self, event):
        axes = self.get_event_axes(event)

        if event.key == 'shift':
            self.shift_is_held = False

    def onkey_press(self, event):
        axes = self.get_event_axes(event)
        if axes == None:
            return

        if axes.marker_active == None:
            return
        elif event.key == 'shift':
            self.shift_is_held = True
        elif(event.key == 'left'):
            self.shift_linked(axes, -1)
            self.draw_active_marker(axes)
        elif(event.key == 'right'):
            self.shift_linked(axes, 1)
            self.draw_active_marker(axes)
        elif(event.key == 'delete'):
            self.delete_linked(axes)
            self.draw_all()

    def onmotion(self, event):
        x = event.x
        y = event.y
        axes = self.get_event_axes(event)

        if axes == None:
            return 

        if axes != self.move or axes.marker_active == None:
            return
        
        self.move_linked(axes, x, y)
        self.draw_active_marker(axes)

    def onclick(self, event):
        axes = self.get_event_axes(event)
        self.move = axes
        if self.move == None:
            return
        m = self.get_event_marker(axes, event)
        if (m != None and axes.marker_active != m): 
            self.make_linked_active(axes, m)
            self.draw_all()

    def onrelease(self, event):
        x = event.x
        y = event.y
        axes = self.get_event_axes(event)

        self.move = None

        if (axes == None):
            return

        m = self.get_event_marker(axes, event)
        active_marker = axes.marker_active

        if (m == None and (active_marker == None or self.shift_is_held == True)):
            self.add_linked(axes, x, y)
            self.draw_all()
        elif (m != None): 
            self.make_linked_active(axes, m)
            self.draw_all()
        elif (active_marker != None):
            self.move_linked(axes, x, y)
            self.draw_all()
        else:
            return
        
        return

    def draw_all(self, animated=True):
        self.set_all_animated(False)
        if animated:
            self.set_active_animated()

        self.canvas_draw_disconnect()
        self.fig.canvas.draw()

        drawn = [self.fig]
        for ax in self.fig.axes:
            for l_ax in ax.marker_linked_axes:
                fig = l_ax.figure
                if fig not in drawn:
                    fig._eventmanager.canvas_draw_disconnect()
                    fig.canvas.draw()
                    drawn.append(fig)

        if animated:
            self.update_canvas()
            for ax in self.fig.axes:
                self.draw_active_marker(ax)
        else:
            self.clear_saved_background()

        for fig in drawn:
            fig._eventmanager.canvas_draw_connect()

        self.set_active_animated()

    def update_canvas(self):
        for ax in self.fig.axes:
            ax._draw_background = ax.figure.canvas.copy_from_bbox(ax.bbox)
            for l_ax in ax.marker_linked_axes:
                fig = l_ax.figure
                l_ax._draw_background = fig.canvas.copy_from_bbox(l_ax.bbox)

    def canvas_draw_disconnect(self):
        self.fig.canvas.mpl_disconnect(self.ciddraw)

    def canvas_draw_connect(self):
        self.ciddraw = self.fig.canvas.mpl_connect('draw_event', self.on_draw)

    def update_all(self):
        ##TODO: update display for twinx axes
        for ax in self.fig.axes:
            for m in ax.markers:
                m.update_marker()
            for l_ax in ax.marker_linked_axes:
                for m in l_ax.markers:
                    m.update_marker()

    def on_draw(self, event):
        self.update_all()
        self.draw_all(animated=False)


