
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib

class Marker(object):
    def __init__(self, axes, xd, yd, show_xline=True, show_dot=True, xdisplay=None, smithchart=False, show_xlabel=True, xreversed=False):
        
        self.axes = axes
        self.xreversed = xreversed
        self.smithchart = smithchart
        self.show_xlabel = show_xlabel
        self.show_xline = False if smithchart else show_xline
        self.show_dot = show_dot
        self.xline = None
        self.xdisplay = xdisplay if isinstance(xdisplay, (list, np.ndarray)) else []

        #self.data2display = self.axes.transData.transform
        #self.display2data = self.axes.transData.inverted().transform
        #self.data2axes = self.axes.transLimits.transform
        #self.axes2data = self.axes.transLimits.inverted().transform

        scale_func = {'log': np.log10, 'linear': lambda x: x}

        def data2axes(p):
            xscale = self.axes.get_xscale()
            yscale = self.axes.get_yscale()

            xd = scale_func[xscale](p[0])
            yd = scale_func[yscale](p[1])

            return self.axes.transLimits.transform((xd,yd))

        self.data2axes = data2axes
        self.axes2display = self.axes.transAxes.transform
        self.display2axes = self.axes.transAxes.inverted().transform

        self.lines = []
        
        for l in self.axes.lines:
            if (l not in self.axes.marker_ignorelines):
                self.lines.append(l)
                
        self.ydot = [None]*len(self.lines)
        self.ytext = [None]*len(self.lines)
        self.xdpoint = []
        self.xidx = [0]*len(self.lines)
        self.renderer = self.axes.figure.canvas.get_renderer()

        if (len(self.lines) < 1):
            raise RuntimeError('Markers cannot be added to axes with no data lines.')

        self.create(xd, yd)

    def find_nearest_xdpoint(self, xd, yd=None):
        mline, xdpoint, mdist = None, 0, np.inf

        for l in self.lines:
            xl, yl = l.get_xdata(), l.get_ydata()

            if yd==None:
                dist = (xl - xd)**2
            else:
                dist = (xl - xd)**2 + (yl-yd)**2	## array of distances (squared) of every point on the line from the point xd, yd
            xidx_l, mdist_l = np.argmin(dist), np.min(dist)   ## index and distance of the point on the line with the closest distance to xd, yd
            
            if mdist_l < mdist:
                mline, xdpoint, mdist  = l, l.get_xdata()[xidx_l], mdist_l
        return xdpoint

    def create(self, xd, yd=None):
        self.xdpoint = self.find_nearest_xdpoint(xd, yd)
        xa, ya = self.data2axes((self.xdpoint, 0))


        if self.show_xline:
            boxparams = dict(boxstyle='round', facecolor='black', edgecolor='black', alpha=0.7)
            self.xline = self.axes.axvline(self.xdpoint, linewidth=0.5, color='r')
            self.axes.marker_ignorelines.append(self.xline)

            xidx = np.argmin(np.abs(self.lines[0].get_xdata()-self.xdpoint))
            txt = self.xdisplay[xidx] if len(self.xdisplay) > 0  else '{:.3f}'.format(self.xdpoint) 
            if (self.show_xlabel):
                self.xtext = self.axes.text(xa, 0, txt, color='white', transform=self.axes.transAxes, fontsize=8, verticalalignment='center', bbox=boxparams)
                xtext_dim = self.xtext.get_window_extent(self.renderer)

                x1 = self.display2axes((xtext_dim.x0, xtext_dim.y0))[0]
                x2 = self.display2axes((xtext_dim.x1, xtext_dim.y1))[0]

                xlen = (x2-x1)/2
                self.xtext.set_position((xa-xlen, 0))
        
        self.yloc =[]
        xloc = []
        for i, l in enumerate(self.lines):
            xd = self.xdpoint
            self.xidx[i] = np.argmin(np.abs(l.get_xdata()-xd))
            xidx = self.xidx[i]
            yd = l.get_ydata()
            xd, yd = l.get_xdata()[xidx], l.get_ydata()[xidx]	
            xa, ya = self.data2axes((xd, yd))
            boxparams = dict(facecolor='black', edgecolor=l.get_color(), linewidth=1.6, boxstyle='round', alpha=0.7)
            
            if self.smithchart and len(self.xdisplay) > 0:
                label = '{:0.3f}'.format(self.xdisplay[xidx]) if isinstance(self.xdisplay[xidx], float) else self.xdisplay[xidx]
            else:
                label = '{:0.3f}'.format(yd) #if self.labels[i] != None else '{:0.3f}'.format(yd)
            self.ytext[i] = self.axes.text(xa+0.01, ya, label ,color='white', fontsize=8, transform = self.axes.transAxes, verticalalignment='center', bbox=boxparams)
            ytext_dim = self.ytext[i].get_window_extent(self.renderer)
            y1 = self.display2axes((ytext_dim.x0, ytext_dim.y0))[1]
            y2 = self.display2axes((ytext_dim.x1, ytext_dim.y1))[1]
            self.ylen = (y2-y1)*1.8

            if self.xdpoint > l.get_xdata()[-1] or self.xdpoint < l.get_xdata()[0]:
                self.ytext[i].set_visible(False)

            #print(ytext_dim)
            self.yloc.append(ya)

            if self.show_dot:
                self.ydot[i] = Line2D([xd], [yd], linewidth=10, color=l.get_color(), markersize=10)
                self.ydot[i].set_marker('.')
                self.ydot[i].set_linestyle(':')
                self.axes.add_line(self.ydot[i])
                self.axes.marker_ignorelines.append(self.ydot[i])
                if self.xdpoint > l.get_xdata()[-1] or self.xdpoint < l.get_xdata()[0]:
                    self.ydot[i].set_visible(False)

            xloc.append(xa)
        self.space_ylabels(xloc)

    def space_ylabels(self, xa):
        ylabels = list(self.ytext)
        zipped = zip(self.yloc, ylabels, xa)
        zipped_sorted  = sorted(zipped, key=lambda x: x[0])
        yloc, ylabels, xa = zip(*zipped_sorted)

        yloc = list(yloc)
        for i, y in enumerate(yloc):
            if i >= len(yloc) -1:
                break
            ovl = (yloc[i+1] - self.ylen/2) - (y + self.ylen/2)

            if ovl < 0:
                yloc[i] -= abs(ovl)/2
                yloc[i+1] += abs(ovl)/2
                for j in range(i-1, -1, -1):
                    ovl = (yloc[j+1] - self.ylen/2) - (yloc[j] + self.ylen/2)
                    if ovl < 0:
                        yloc[j] -= abs(ovl)

        for i, y in enumerate(yloc):
            ylabels[i].set_position((xa[i]+0.01, y))
        self.yloc = yloc


    def move_to_point(self, xd, yd=None):
        self.xdpoint = self.find_nearest_xdpoint(xd, yd)
        for i, l in enumerate(self.lines):
            self.xidx[i] = np.argmin(np.abs(l.get_xdata()-self.xdpoint))
        #self._move_to_xindex(self.xidx)
        
        xd = self.xdpoint
        xa, ya = self.data2axes((xd, 0))
        if self.show_xline:
            self.xline.set_xdata([xd, xd])
            if self.show_xlabel:
                txt = self.xdisplay[self.xidx[0]] if len(self.xdisplay) > 0  else '{:.3f}'.format(xd) 
                self.xtext.set_text(txt)

                xtext_dim = self.xtext.get_window_extent(self.renderer)

                x1 = self.display2axes((xtext_dim.x0, xtext_dim.y0))[0]
                x2 = self.display2axes((xtext_dim.x1, xtext_dim.y1))[0]

                xlen = (x2-x1)/2

                self.xtext.set_position((xa-xlen, 0))

        ## TODO: create all objects regardless of settings, set visibility
        xloc =[]
        self.yloc = []
        for i, l in enumerate(self.lines):
            if self.xdpoint > l.get_xdata()[-1] or self.xdpoint < l.get_xdata()[0]:
                self.ytext[i].set_visible(False)
                self.ydot[i].set_visible(False)
            else:
                self.ytext[i].set_visible(True)
                self.ydot[i].set_visible(True)

            xd, yd = l.get_xdata()[self.xidx[i]], l.get_ydata()[self.xidx[i]]	

            xa, ya = self.data2axes((xd, yd))
            self.ytext[i].set_position((xa+0.01, ya))
            if self.smithchart and len(self.xdisplay) > 0:
                label = '{:0.3f}'.format(self.xdisplay[self.xidx[i]]) if isinstance(self.xdisplay[self.xidx[i]], float) else self.xdisplay[self.xidx[i]]
            else:
                label = '{:0.3f}'.format(yd) 
            self.yloc.append(ya)
            self.ytext[i].set_text(label)
            
            if self.show_dot:
                self.ydot[i].set_data([xd], [yd])
            dim = self.ytext[i].get_window_extent(renderer=self.renderer)
            xloc.append(xa)
        
        self.space_ylabels(xloc)


    def shift(self, direction):
        direction = -direction if self.xreversed else direction
        xmax, xmin = -np.inf, np.inf
        line = None

        for i, l in enumerate(self.lines):
            
            
            if direction > 0:
                ## find line with point furthest to the left
                temp_x = -np.inf
                if (self.xidx[i] +1) >= 0 and self.xidx[i] != 0:
                    temp_x = l.get_xdata()[self.xidx[i] +1] 

                if temp_x > xmax:
                    xmax = temp_x
                    line_idx = i
            else:
                if (self.xidx[i] +1) < len(l.get_xdata()):
                    temp_x = l.get_xdata()[self.xidx[i] +1] 

                if temp_x < xmin:
                    xmin = temp_x
                    line_idx = i
        

        xdata = self.lines[line_idx].get_xdata()
        new_xpoint = xdata[self.xidx[line_idx]]
        if direction < 0:
            if (self.xidx[line_idx] -1) >= 0:
                new_xpoint = xdata[self.xidx[line_idx] -1]
        else:
            if (self.xidx[line_idx] +1) < (len(xdata)):
                new_xpoint = xdata[self.xidx[line_idx] +1]

        self.move_to_point(new_xpoint)

    def remove(self):
        if self.show_xline:
            if self.show_xlabel:
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

