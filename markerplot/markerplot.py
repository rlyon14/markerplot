
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from time import time
from threading import Timer, Semaphore


class Marker(object):
    
    def __init__(self, axes, xd, yd):
        
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

        ## draw box for each dot, ytext, xline and xlabel
        self.draw_box_xline = None
        self.draw_box_xtext = None
        self.draw_box_ydot = [None]*len(self.lines)
        self.draw_box_ytext = [None]*len(self.lines)

        if (len(self.lines) < 1):
            raise RuntimeError('Markers cannot be added to axes without data lines.')

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
        #self.draw_box_xline = self.axes.figure.canvas.copy_from_bbox(self.xline.axes.bbox)

        ## x label
        self.xtext = self.axes.text(0, 0, '', color='white', transform=self.axes.transAxes, fontsize=8, verticalalignment='center', bbox=boxparams)
        #self.draw_box_xtext = self.axes.figure.canvas.copy_from_bbox(self.xtext.axes.bbox)

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

            #self.draw_box_ydot[i] = ax.figure.canvas.copy_from_bbox(self.ydot.axes.bbox)
            #self.draw_box_ytext[i] = ax.figure.canvas.copy_from_bbox(self.ytext.axes.bbox)

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

    ## TODO: space over x and y dimensions
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

        self.draw_box_xline = self.axes.figure.canvas.copy_from_bbox(self.xline.axes.bbox)
        self.draw_box_xtext = self.axes.figure.canvas.copy_from_bbox(self.xtext.axes.bbox)

        for i, (ax,l) in enumerate(self.lines):
            self.draw_box_ydot[i] = ax.figure.canvas.copy_from_bbox(self.ydot[i].axes.bbox)
            self.draw_box_ytext[i] = ax.figure.canvas.copy_from_bbox(self.ytext[i].axes.bbox)
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
            self.ytext[i].set_visible(True)
            self.ydot[i].set_visible(True)

            ## turn off ylabel and dot if ypoint is out of bounds
            if (self.xdpoint > self.line_xbounds[i][1]) or (self.xdpoint < self.line_xbounds[i][0]):
                self.ytext[i].set_visible(False)
                self.ydot[i].set_visible(False)

            ## ylabel and dot position
            xd, yd = l.get_xdata()[self.xidx[i]], l.get_ydata()[self.xidx[i]]

            xa, ya = self.data2axes(ax, (xd, yd))
            xloc.append(xa)
            self.yloc.append(ya)

            if (not np.isfinite(yd)):
                self.ytext[i].set_visible(False)
                self.ydot[i].set_visible(False)

            else:
                self.ytext[i].set_position((xa+self.ylabel_gap, ya))
                self.ydot[i].set_data([xd], [yd])

                ## ylabel text
                if ax.marker_params['yformat'] != None:
                    txt = ax.marker_params['yformat'](xd, yd)
                else:
                    txt = '{:0.3f}'.format(yd)

                self.ytext[i].set_text(txt)
        
        self.space_ylabels(xloc)

        ## save drawing boxes where marker will move to
        #self.draw_box_xline = self.axes.figure.canvas.copy_from_bbox(self.xline.axes.bbox)
        #self.draw_box_xtext = self.axes.figure.canvas.copy_from_bbox(self.xtext.axes.bbox)


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

    def draw(self):


        
        #self.axes.figure.canvas.blit(self.axes.bbox)

        #working
        self.axes.figure.draw_artist(self.xline)
        self.axes.figure.draw_artist(self.xtext)
        for i, (ax,l) in enumerate(self.lines):
            self.ydot[i].axes.draw_artist(self.ydot[i])
            self.ytext[i].axes.draw_artist(self.ytext[i])

        self.axes.figure.canvas.blit(self.axes.bbox)
        self.axes.figure.canvas.restore_region(self.draw_box_xtext)
        self.axes.figure.canvas.restore_region(self.draw_box_xline)

        for i, (ax,l) in enumerate(self.lines):
            self.axes.figure.canvas.restore_region(self.draw_box_ydot[i])
            self.axes.figure.canvas.restore_region(self.draw_box_ydot[i])
        

        # #working
        # self.axes.figure.draw_artist(self.xtext)
        # self.axes.figure.canvas.blit(self.axes.bbox)
        # self.axes.figure.canvas.restore_region(self.draw_box_xtext)

        #self.xline.axes.figure.canvas.blit(self.draw_box_xline)
        
        

        
        # self.axes.figure.canvas.restore_region(self.draw_box_xtext)
        # self.xtext.axes.draw_artist(self.xtext)
        # self.xtext.axes.figure.canvas.blit(self.xtext.axes.bbox)

        #self.xline.axes.figure.canvas.blit(self.xline.axes.bbox)
        #self.xtext.axes.figure.canvas.blit(self.xtext.axes.bbox)


        # for i, (ax,l) in enumerate(self.lines):


        #     ax.figure.canvas.restore_region(self.draw_box_ydot[i])
        #     ax.figure.canvas.restore_region(self.draw_box_ytext[i])

        #self.xline.axes.draw_artist(self.xline)
        #self.xtext.axes.draw_artist(self.xtext)



        # for i, (ax,l) in enumerate(self.lines):
        #     self.ydot[i].axes.draw_artist(self.ydot[i])
        #     self.ytext[i].axes.draw_artist(self.ytext[i])

        #     self.ydot[i].axes.figure.canvas.blit(self.ydot[i].axes.bbox)
        #     self.ytext[i].axes.figure.canvas.blit(self.ytext[i].axes.bbox)


        



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
        self.last_release = [None, 0]
        self.last_press = [None, 0]
        self.valid_press = False

        self.press_max_seconds = 0.005
        self.key_released_timer = None
        self.key_pressed = False
        self.sem = Semaphore()

        self.cidclick = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.cidpress = self.fig.canvas.mpl_connect('key_press_event', self.onkey_press)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('key_release_event', self.onkey_release_debounce)
        self.cidmotion = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)
        self.cidbtnrelease = self.fig.canvas.mpl_connect('button_release_event', self.onrelease)

    def axes_to_top(self, axes):
        max_zorder = 0
        for ax in axes.get_shared_x_axes().get_siblings(axes):
            if ax.get_zorder() > max_zorder:
                max_zorder = ax.get_zorder()
        axes.set_zorder(max_zorder+1)
        axes.patch.set_visible(False)
        
    def move_linked(self, axes, xd, yd):
        axes.marker_active.move_to_point(xd, yd)
        for ax in axes.marker_linked_axes:
            ax.marker_active.move_to_point(xd, yd)
        #self.draw_linked(axes)

    def add_linked(self, axes, xd, yd):
        axes.marker_active = axes.marker_add(xd, yd)  
        for ax in axes.marker_linked_axes:
            ax.marker_active = ax.marker_add(xd, yd)  
        #self.draw_all()

    def shift_linked(self, axes, direction):
        axes.marker_active.shift(direction)
        for ax in axes.marker_linked_axes:
            ax.marker_active.shift(direction)
        #self.draw_linked(axes)
        
    def delete_linked(self, axes):
        axes.marker_active = axes.marker_delete(axes.marker_active)
        for ax in axes.marker_linked_axes:
            ax.marker_active = ax.marker_delete(ax.marker_active)
        #self.draw_all()

    def make_linked_active(self, axes, marker):
        axes.marker_active = marker
        idx = axes.markers.index(marker)
        for ax in axes.marker_linked_axes:
            ax.marker_active = ax.markers[idx]
        #self.draw_all()

    def draw_all(self):
        #print('test')
        self.fig.canvas.draw()
        drawn = [self.fig]
        for ax in self.fig.axes:
            for l_ax in ax.marker_linked_axes:
                fig = l_ax.figure
                if fig not in drawn:
                    fig.canvas.draw()
                    drawn.append(fig)

    def draw_linked(self, axes):
        axes.marker_active.draw()
        for ax in axes.marker_linked_axes:
            ax.marker_active.draw()


    def get_event_marker(self, axes, event):
        for m in axes.markers:
            if m.contains_event(event):
                return m
        return None

    def get_event_axes(self, event):
        plt.figure(self.fig.number)
        if plt.get_current_fig_manager().toolbar.mode != '':
            return None

        axes = event.inaxes
        if axes in self.fig.axes:
            for ax in axes.get_shared_x_axes().get_siblings(axes):
                if (ax in self.top_axes):
                    return ax
            return axes
        else:
            return None

    def onkey_release_debounce(self, event):
        if self.key_pressed:
            self.key_released_timer = Timer(self.press_max_seconds, self.onkey_release, [event])
            self.key_released_timer.start()

    def onkey_release(self, event):
        self.sem.acquire()
        print('release')

        
        self.key_pressed = False
        axes = self.get_event_axes(event)

        if event.key == 'shift':
            self.shift_is_held = False
        self.draw_all()
        self.sem.release()
        print('relase done')

    def onkey_press(self, event):
        self.sem.acquire()
        print('press')
        
        if self.key_released_timer:
            self.key_released_timer.cancel()
            self.key_released_timer = None

        self.key_pressed = True

        axes = self.get_event_axes(event)
        if axes == None:
            return

        if axes.marker_active == None:
            return
        elif event.key == 'shift':
            self.shift_is_held = True
        elif(event.key == 'left'):
            self.shift_linked(axes, -1)
            self.draw_linked(axes)
        elif(event.key == 'right'):
            self.shift_linked(axes, 1)
            self.draw_linked(axes)
        elif(event.key == 'delete'):
            self.delete_linked(axes)
            #self.draw_all()

        self.sem.release()
        print('press done')
        #self.draw_linked(axes)

    def onmotion(self, event):
        xd = event.xdata
        yd = event.ydata
        axes = self.get_event_axes(event)

        if axes == None:
            return 

        if axes != self.move or axes.marker_active == None:
            return
        
        self.move_linked(axes, xd, yd)
        self.draw_linked(axes)

    def onclick(self, event):
        self.move = self.get_event_axes(event)

    def onrelease(self, event):
        xd = event.xdata
        yd = event.ydata
        axes = self.get_event_axes(event)

        if (axes == None):
            return
        self.move = None

        m = self.get_event_marker(axes, event)
        active_marker = axes.marker_active

        if (m == None and (active_marker == None or self.shift_is_held == True)):
            self.add_linked(axes, xd, yd)
        elif (m != None): 
            self.make_linked_active(axes, m)
        elif (active_marker != None):
            self.move_linked(axes, xd, yd)
        else:
            return
        
        self.draw_all()
        return
