
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from time import time, sleep
from threading import Timer, Semaphore
##

class Marker(object):
    
    def __init__(self, axes, xd=None, idx=None, disp=None, lines=None):
        """ create marker on axes at a given x data value, data index value or display coordinate

            Parameters
            ----------
                xd: (float) x-value in data coordinates
                disp: (tuple) x,y value in axes display cordinates
                idx: (int) index of x-data (ignored if axes data lines have unequal xdata arrays)
        """
        self.axes = axes 
        ## marker will inherit these parameters from axes, ignoring params from linked axes
        self.show_xline = axes.marker_params['show_xline']
        self.show_yline = axes.marker_params['show_yline']
        self.show_xlabel = axes.marker_params['show_xlabel'] if self.axes.name != 'polar' else False
        self.show_ylabel = axes.marker_params['show_ylabel']
        self.xreversed = axes.marker_params['xreversed']
        self.wrap = axes.marker_params['wrap']
        self.xlabel_pad = axes.marker_params['xlabel_pad']
        self.ylabel_xpad = axes.marker_params['ylabel_xpad']
        self.ylabel_ypad = axes.marker_params['ylabel_ypad']

        self.ylabel_xpad *= (self.axes.figure.dpi/100)
        self.ylabel_ypad *= (self.axes.figure.dpi/100)
        self.xlabel_pad *= (self.axes.figure.dpi/100)

        def data2display(ax, point):
            return ax.transData.transform(point)

        self.data2display = data2display
        self.axes2display = self.axes.transAxes.transform
        self.display2data = self.axes.transData.inverted().transform

        self.base_origin = list(self.display2data((0,0)))
        self.lines = []

        if np.any(lines):
            ## use lines if provided
            if not isinstance(lines, (tuple, list, np.ndarray)):
                lines = [lines]
            for l in lines:
                self.lines.append((l.axes, l))

        else:
            ## get lines from any shared axes
            for ax in self.axes.get_shared_x_axes().get_siblings(self.axes):
                for l in ax.lines:
                    if (l not in ax.marker_ignorelines) and (l not in self.axes.marker_ignorelines):
                        self.lines.append((ax,l))
        
        self.ydot = [None]*len(self.lines)
        self.yline = [None]*len(self.lines)
        self.ytext = [None]*len(self.lines)
        self.xdpoint = None
        self.xidx = [0]*len(self.lines)
        self.renderer = self.axes.figure.canvas.get_renderer()
        self.line_xbounds = [None]*len(self.lines)
        self._hidden_markers = []

        if (len(self.lines) < 1):
            raise RuntimeError('Markers cannot be added to axes without data lines.')

        ## turn on index mode if all lines have identical x-data
        monotonic_flag = True
        xcheck = np.zeros(shape=(len(self.lines), 3))
        for i, (ax,l) in enumerate(self.lines):

            if not hasattr(l, '_marker_xdata'):
                l._marker_xdata = l.get_xdata()
            
            if monotonic_flag:
                diff = np.diff(l.get_xdata())
                monotonic_flag = np.all(diff > 0) or np.all(diff < 0)

            xcheck[i] = l._marker_xdata[0], l._marker_xdata[-1], len(l._marker_xdata)

            l.xy = self.data2display(ax, l.get_xydata())

        for ax in self.axes.marker_linked_axes:
            for l in ax.lines:
                if (l in ax.marker_ignorelines or l in self.axes.marker_ignorelines):
                    continue

                if not hasattr(l, '_marker_xdata'):
                    l._marker_xdata = l.get_xdata()

                xdata = l._marker_xdata
                xcheck = np.append(xcheck, [[xdata[0], xdata[-1], len(xdata)]], axis=0)

        self.index_mode = np.all(xcheck == xcheck[0,:]) 

        if not monotonic_flag:
            self.index_mode = False
            self.show_xline = False
            self.show_xlabel = False

        self.create(xd, idx=idx, disp=disp)

    def update_params(self):
        self.show_xline = axes.marker_params['show_xline']
        self.show_yline = axes.marker_params['show_yline']
        self.show_xlabel = axes.marker_params['show_xlabel'] if self.axes.name != 'polar' else False
        self.show_ylabel = axes.marker_params['show_ylabel']
        self.xreversed = axes.marker_params['xreversed']
        self.wrap = axes.marker_params['wrap']
        self.xlabel_pad = axes.marker_params['xlabel_pad']
        self.ylabel_xpad = axes.marker_params['ylabel_xpad']
        self.ylabel_ypad = axes.marker_params['ylabel_ypad']
        self.update_marker(move=True)

    def update_marker(self, move=True):
        """ updates marker (without drawing on canvas) if the dpi or figure size changes
        """
        self.renderer = self.axes.figure.canvas.get_renderer()

        self.xlabel_pad = self.axes.marker_params['xlabel_pad']
        self.ylabel_xpad = self.axes.marker_params['ylabel_xpad']
        self.ylabel_ypad = self.axes.marker_params['ylabel_ypad']

        self.ylabel_xpad *= (self.axes.figure.dpi/100)
        self.ylabel_ypad *= (self.axes.figure.dpi/100)
        self.xlabel_pad *= (self.axes.figure.dpi/100)

        self.display2data = self.axes.transData.inverted().transform

        for i, (ax,l) in enumerate(self.lines):
            l.xy = self.data2display(ax, l.get_xydata())

        self.base_origin = list(self.display2data((0,0)))

        if move:
            self.move_to_point(self.xdpoint, idx=self.xidx[0])

        return self.base_origin

    def find_nearest_xdpoint(self, xd=None, disp=None):
        mline, xdpoint, mdist = None, 0, np.inf

        if disp != None:
            x, y = disp
            
        for ax, l in self.lines:
            if self.show_xline:
                if disp != None:
                    xd, yd = self.display2data(disp)
                xl = l._marker_xdata
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
                    xl = l._marker_xdata
                    dist = np.abs(xl - xd)

                xidx_l, mdist_l = np.argmin(dist), np.min(dist)  
            
            if mdist_l < mdist:
                mline, xdpoint, mdist  = l, l._marker_xdata[int(xidx_l)], mdist_l

        return mline, xdpoint

    def create(self, xd=None, disp=None, idx=None):

        if not self.index_mode:
            if xd == None and disp == None:
                raise RuntimeError('xdata or display cordinates must be provided if not in index mode')
            mline, self.xdpoint = self.find_nearest_xdpoint(xd, disp=disp)
        else:
            if idx != None:
                self.xdpoint = self.lines[0][1]._marker_xdata[idx]
            else:
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
            self.yline[i] = Line2D([0], [0], linewidth=0.5, color='r')
            self.ydot[i].set_marker('.')
            self.ydot[i].set_linestyle(':')
            ax.add_line(self.ydot[i])
            ax.add_line(self.yline[i])
            self.axes.marker_ignorelines.append(self.ydot[i])
            self.axes.marker_ignorelines.append(self.yline[i])
            ax.marker_ignorelines.append(self.ydot[i])
            ax.marker_ignorelines.append(self.yline[i])
            
            self.line_xbounds[i] = np.min(l._marker_xdata), np.max(l._marker_xdata)

        ## move objects to current point
        self.move_to_point(xd, disp=disp, idx=idx)
        self.set_visible(False)

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

        ## make the marker visible so get_window_extent works properly
        self.set_visible(True)

        xmin, ymin = self.axes2display((0,0))
        xmax, ymax = self.axes2display((1,1))

        ## variables for the axes boundaries
        ymax -= self.ylabel_ypad
        ymin += self.ylabel_ypad
        xmax -= self.ylabel_xpad
        xmin += self.ylabel_xpad

        xl, yl = self.data2display(self.axes, (self.xdpoint, 0))
        xlabel_dim = self.xtext.get_window_extent(self.renderer)

        x1, y1 = xlabel_dim.x0, xlabel_dim.y0
        x2, y2 = xlabel_dim.x1, xlabel_dim.y1
        xlen = x2-x1

        ypos = ymin + (y2-y1)/2 + self.xlabel_pad - self.ylabel_ypad
        self.xtext.set_position((xl-xlen/2, ypos))
        xlabel_dim = self.xtext.get_window_extent(self.renderer)

        if self.show_xlabel:
            ymin = xlabel_dim.y1 + self.ylabel_ypad

        if xlabel_dim.x0 < xmin:
            #ypos = (xlabel_dim.y1 + xlabel_dim.y0)/2
            xpos = xmin
            self.xtext.set_position((xpos, ypos))

        if xlabel_dim.x1 > xmax:
            #ypos = (xlabel_dim.y1 + xlabel_dim.y0)/2
            xpos = xmax - (xlabel_dim.x1 - xlabel_dim.x0)
            self.xtext.set_position((xpos, ypos))


        ## generate list of ylabel locations
        dims = []
        ylocs = []
        ylabels = []
        for i, ytext in enumerate(self.ytext):
            if (i not in self._hidden_markers) and (self.lines[i][1].get_visible()):
                dim = ytext.get_window_extent(self.renderer)
                dims.append(dim)
                ylocs.append((dim.y1 + dim.y0)/2)
                ylabels.append(ytext)

        self.set_visible(False)
        if len(ylabels) < 1:
            return

        ## sort ylabels by their positions on the axes
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

            ## force inside axes bounds
            ovl = dims[i].x1 - xmax
            if ovl > 0:
                ## flip label to left side of dot
                shift = (dims[i].x1 - dims[i].x0) + self.ylabel_xpad*2
                xloc -= shift
                ovl = ovl - shift
                if ovl > 0:
                    xloc -= ovl

            ovl = xmin - dims[i].x0
            if ovl > 0:
                xloc += ovl

            ## set position
            ytext.set_position((xloc, yloc))
        

    def move_to_point(self, xd=None, disp=None, idx=None):
        
        origin = list(self.axes.transData.inverted().transform((0,0)))

        if not np.all(origin == self.base_origin):
            self.update_marker(move=False)

        if not self.index_mode:
            mline, self.xdpoint = self.find_nearest_xdpoint(xd, disp=disp)

            for i, (ax,l) in enumerate(self.lines):
                self.xidx[i] = np.argmin(np.abs(l._marker_xdata-self.xdpoint))
        else:
            if idx == None:
                mline, self.xdpoint = self.find_nearest_xdpoint(xd, disp=disp)
                idx = np.argmin(np.abs(mline._marker_xdata-self.xdpoint))
            for i, (ax,l) in enumerate(self.lines):
                self.xidx[i] = idx
            self.xdpoint = self.lines[0][1]._marker_xdata[self.xidx[0]]
        
        ## vertical line placement
        self.xline.set_xdata([self.xdpoint, self.xdpoint])

        xl, yl = self.data2display(self.axes, (self.xdpoint, 0))

        ## xlabel text
        txt = self.axes._marker_xformat(self.xdpoint)
        self.xtext.set_text(txt)


        xloc = []
        yloc = []
        for i, (ax,l) in enumerate(self.lines):
            xlim = ax.get_xlim()
            self.set_show(i)


            if not self.index_mode:
                ## turn off ylabel and dot if ypoint is out of bounds
                if (self.xdpoint > self.line_xbounds[i][1]) or (self.xdpoint < self.line_xbounds[i][0]):
                    self.set_hidden(i)

            ## ylabel and dot position
            xd, yd = l.get_xdata()[self.xidx[i]], l.get_ydata()[self.xidx[i]]
            xl, yl = self.data2display(ax, (np.real(xd), np.real(yd)))

            if (not np.isfinite(yd)):
                self.set_hidden(i)
            else:
                xpos = xl+self.ylabel_xpad if not self.show_yline else self.ylabel_xpad
                self.ytext[i].set_position((xpos, yl))
                self.ydot[i].set_data([xd], [yd])
                self.yline[i].set_data(xlim, [yd, yd])

                ## ylabel text
                mxd = l._marker_xdata[self.xidx[i]]
                txt = ax._marker_yformat(xd, yd, mxd=mxd)

                self.ytext[i].set_text(txt)
        
        self.space_labels()

    def shift(self, direction):
        direction = -direction if self.xreversed else direction
        xmax, xmin = -np.inf, np.inf

        if self.index_mode:
            xlen = len(self.lines[0][1]._marker_xdata)
            nxidx = self.xidx[0] -1 if direction < 0 else self.xidx[0] +1
            if (nxidx >= xlen):
                nxidx = 0 if self.wrap else xlen-1
            elif (nxidx <= 0):
                nxidx = xlen-1 if self.wrap else 0
            self.move_to_point(self.lines[0][1]._marker_xdata[nxidx])
            return

        line = None
        step_sizes = np.array([0.0]*len(self.lines), dtype='float64')
        if direction > 0:
            xloc = np.array([np.inf]*len(self.lines))
        else:
            xloc = np.array([-np.inf]*len(self.lines))

        for i, (ax,l) in enumerate(self.lines):
            xdata = l._marker_xdata

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
                new_xpoint = self.lines[l_idx][1]._marker_xdata[self.xidx[l_idx]] + step_size
                self.move_to_point(new_xpoint)
        else:
            l_idx = np.argmax(xloc)
            if np.max(xloc) > -np.inf:
                new_xpoint = self.lines[l_idx][1]._marker_xdata[self.xidx[l_idx]] - step_size
                self.move_to_point(new_xpoint)

    def remove(self):
        if self.xline in self.axes.lines:
            idx = self.axes.lines.index(self.xline)
            self.axes.lines.pop(idx)

        for i, (ax,l) in enumerate(self.lines):	
            if self.ydot[i] in ax.lines:
                idx = ax.lines.index(self.ydot[i])
                ax.lines.pop(idx)
                idx = ax.lines.index(self.yline[i])
                ax.lines.pop(idx)

    def set_visible(self, state):
        self.xtext.set_visible(self.show_xlabel and state)
        self.xline.set_visible(self.show_xline and state)

        for i, (ax,l) in enumerate(self.lines):	
            vis = l.get_visible() and i not in self._hidden_markers
            self.ytext[i].set_visible(self.show_ylabel and state and vis)
            self.ydot[i].set_visible(self.show_ylabel and state and vis)
            self.yline[i].set_visible(self.show_yline and state and vis)

    def contains_event(self, event):
        contains, attrd = self.xtext.contains(event)
        if (contains):
            return True
            
        for ym in self.ytext:
            contains, attrd = ym.contains(event)
            if (contains):
                return True
        return False

    def set_hidden(self, idx):
        if idx not in self._hidden_markers:
            self._hidden_markers.append(idx)

    def set_show(self, idx):
        if idx in self._hidden_markers:
            self._hidden_markers.remove(idx)

    def draw(self):
        """ Draws each artist associated with marker."""
        
        self.set_visible(True)

        self.axes.draw_artist(self.xline)
        for i, (ax,l) in enumerate(self.lines):
            self.yline[i].axes.draw_artist(self.yline[i])
            self.ydot[i].axes.draw_artist(self.ydot[i])
            self.ytext[i].axes.draw_artist(self.ytext[i])
            
        self.axes.draw_artist(self.xtext)

        self.set_visible(False)

class MarkerManager(object):
    def __init__(self, fig, top_axes=None):
        self.fig = fig
        self.toolbar = self.fig.canvas.toolbar

        self.move = None
        self.shift_is_held = False 

        self.zoom = False

        self.cidclick = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.cidpress = self.fig.canvas.mpl_connect('key_press_event', self.onkey_press)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('key_release_event', self.onkey_release)
        self.cidmotion = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('button_release_event', self.onrelease)
        self.ciddraw = self.fig.canvas.mpl_connect('draw_event', self.on_draw)
        
    def move_linked(self, axes, x, y):
        axes.marker_active.move_to_point(disp=(x,y))
        for ax in axes.marker_linked_axes:
            ax.marker_active.move_to_point(xd=axes.marker_active.xdpoint)

    def add_linked(self, axes, x, y):
        marker = axes.marker_add(disp=(x,y))  
        for ax in axes.marker_linked_axes:
            ax.marker_add(xd=axes.marker_active.xdpoint)

        self.make_linked_active(axes, marker)

    def shift_linked(self, axes, direction):
        axes.marker_active.shift(direction)
        for ax in axes.marker_linked_axes:
            ax.marker_active.move_to_point(xd=axes.marker_active.xdpoint)
        
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

    def draw_active_marker(self, axes):
        active_background_none = False

        if axes._active_background == None:
            active_background_none = True
        
        else:
            for ax in axes.marker_linked_axes:
                if ax._active_background == None:
                    active_background_none = True
                    break

        if active_background_none:
            self.draw_lm(axes)
            return

        axes.figure.canvas.restore_region(axes._active_background)
        if axes.marker_active != None:
            axes.marker_active.draw()
            axes.figure.canvas.blit(axes.bbox)
        
        for ax in axes.marker_linked_axes:
            ax.figure.canvas.restore_region(ax._active_background)
            if ax.marker_active != None:
                ax.marker_active.draw()
                ax.figure.canvas.blit(ax.bbox)


    def get_event_marker(self, axes, event):
        for m in axes.markers:
            m.set_visible(True)
            contains = m.contains_event(event)
            m.set_visible(False)
            if contains:
                return m
        return None

    def get_event_axes(self, event):
        tmode = self.toolbar.mode
        if tmode != '':
            return None

        axes = event.inaxes
        if axes in self.fig.axes:
            return axes._top_axes
        else:
            return None

    def onkey_release(self, event):
        axes = self.get_event_axes(event)

        if event.key == 'shift':
            self.shift_is_held = False

    def onkey_press(self, event):
        axes = self.get_event_axes(event)
        if(event.key == 'escape'):
            if self.toolbar.mode == 'pan/zoom':
                self.toolbar.pan()
            elif self.toolbar.mode == 'zoom rect':
                self.toolbar.zoom()

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
            self.draw_lm(axes)
        elif(event.key == 'f5'):
            self.update_all()
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
            self.draw_lm(axes)

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
            self.draw_lm(axes)
        elif (m != None): 
            self.make_linked_active(axes, m)
            self.draw_lm(axes)
        elif (active_marker != None):
            self.move_linked(axes, x, y)
            self.draw_active_marker(axes)
        else:
            return
        
        return

    def update_background(self):
        """ generates a blank background image for each axes
        """
        self.canvas_draw_disconnect()

        vis = []
        for ax in self.fig.axes:
            for l in ax.lines:
                if l not in ax.marker_ignorelines and l.get_visible():
                    l.set_visible(False)
                    vis.append(l)

        self.fig.canvas.draw()

        for ax in self.fig.axes:

            ax._all_background =  self.fig.canvas.copy_from_bbox(ax.bbox)
            ax._active_background = None

        for l in vis:
            l.set_visible(True)

        self.canvas_draw_connect()

    def draw_all(self, blit=True):
        self.update_background()

        if blit:
            for ax in self.fig._top_axes:
                ax.draw_lines_markers()
                    
    def draw_lm(self, axes):
        axes.draw_lines_markers()
        for ax in axes.marker_linked_axes:
            ax.draw_lines_markers()

    def canvas_draw_disconnect(self):
        self.fig.canvas.mpl_disconnect(self.ciddraw)

    def canvas_draw_connect(self):
        self.ciddraw = self.fig.canvas.mpl_connect('draw_event', self.on_draw)

    def update_all(self):
        error_threshold = 1
        old_origins = np.zeros(shape=(1,2))
        
        for ax in self.fig._top_axes:
            for m in ax.markers:
                old_origins = np.append(old_origins, [m.base_origin], axis=0)

        new_origins = np.zeros(shape=(1,2))
        for ax in self.fig._top_axes:
            for m in ax.markers:
                new_origins = np.append(new_origins, [m.update_marker()], axis=0)
            for l_ax in ax.marker_linked_axes:
                for m in l_ax.markers:
                    m.update_marker()

        diff = np.max(np.abs(old_origins - new_origins))
        return diff < error_threshold

    def on_draw(self, event):
        ## if constrained_layout or automatic tight_layout is on, the axes may automatically move/resize 
        ## during the screen update and invalidate the text label positions
        
        ## draw until axes origin stops moving
        max_draw = 10
        identical = False
        draw = 0
        while not identical:
            identical = self.update_all()
            self.draw_all(blit=False)
            
            draw += 1
            if draw > max_draw:
                break
        
        self.update_all()
        for ax in self.fig._top_axes:
            ax.draw_lines_markers(blit=False)



