
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from . markers import MarkerManager, Marker
from matplotlib import ticker

import gorilla
import matplotlib

####################
## Axes Patches ##
####################

def marker_add(self, xd=None, idx=None, disp=None, lines=None):
    """ add new marker at a given x data value, index value or display coordinate, and set as the
        axes active marker

        Parameters
        ----------
            xd: (float, list) x-value in data coordinates
            idx: (int, list) index of x-data (ignored if axes data lines have unequal xdata arrays)
            disp: (tuple) x,y value in axes display cordinates
            lines: (list, tuple, np.ndarray) lines to place markers on
                    if lines is not provided, markers will be placed on all lines on the axes
    """
    if isinstance(xd, (list, tuple, np.ndarray)):
        for x in xd:
            self.markers.append(Marker(self.axes, xd=x, lines=lines))
    
    elif isinstance(idx, (list, tuple, np.ndarray)):
        for i in idx:
            self.markers.append(Marker(self.axes, idx=i, lines=lines))
    else:
        self.markers.append(Marker(self.axes, xd=xd, idx=idx, disp=disp, lines=lines))

    self.marker_active = self.markers[-1]
    return self.marker_active

def marker_delete(self, marker):
    """ remove marker from axes
    """
    idx = self.markers.index(marker)
    marker.remove()
    self.markers.pop(idx)
    return self.markers[-1] if len(self.markers) > 0 else None

def marker_delete_all(self):
    """ remove all markers from axes
    """
    for m in self.markers:
        m.remove()

    self.marker_active = None
    self.markers = []

def marker_set_params(self, **kwargs):
    """ allows for updates to axes marker parameters if axes requires unique parameters
    """
    self.marker_params.update(dict(**kwargs))

def marker_ignore(self, *lines):
    """ flags lines that should not accept markers (i.e. smithchart lines)
    """
    lines = list(lines)
    self.marker_ignorelines += lines

def marker_link(self, *axes):
    """ --interactive only--
        links axes together so that any interactive change to markers on axes one is reflected in the other

        Parameters
        ----------
            axes: (Axes object) axes that will be linked to current axes (self)

        Warning: 
        If manual markers are placed in linked axes with axes.marker_add(), interactive markers will fail if the 
        number of markers are not kept equal between linked axes.
    """
    axes = list(axes)
    for ax in axes:
        if ax in self.marker_linked_axes or ax == self:
            continue
        self.marker_linked_axes.append(ax)
        ax.marker_linked_axes.append(self)

def _marker_yformat(self, xd, yd, mxd=None):
    yformatter = self.yaxis.get_major_formatter()
    if self.marker_params['yformat'] != None:
        return self.marker_params['yformat'](xd, yd, mxd=mxd)

    elif not isinstance(yformatter, (ticker.ScalarFormatter, ticker.FixedFormatter)) and self.marker_params['inherit_ticker']:
        return yformatter(yd)

    else:
        return '{:.3f}'.format(yd)


def _marker_xformat(self, xd):
    xformatter = self.xaxis.get_major_formatter()
    if self.marker_params['xformat'] != None:
        return self.marker_params['xformat'](xd)
    elif not isinstance(xformatter, (ticker.ScalarFormatter, ticker.FixedFormatter)) and self.marker_params['inherit_ticker']:
        return xformatter(xd)
    else:
        return '{:.3f}'.format(xd)

def plot(self, *args, **kwargs):
    mxd = kwargs.pop('marker_xd', None)

    ## change default linewidth to 1
    lw = kwargs.pop('linewidth', 1)

    original = gorilla.get_original_attribute(self, 'plot')
    lines = original(*args, linewidth=lw, **kwargs)

    if np.any(mxd):
        for l in lines:
            l._marker_xdata = mxd

    return lines

def clear(self, *args, **kwargs):

    original = gorilla.get_original_attribute(self, 'clear')
    ret = original(*args, **kwargs)

    self.marker_delete_all()
    self.marker_ignorelines = []
    self._active_background = None

    return ret

def draw_lines_markers(self, blit=True):

    self.figure.canvas.restore_region(self._all_background)

    for ax in self.axes.get_shared_x_axes().get_siblings(self):
        for l in ax.lines:
            if l not in ax.marker_ignorelines:# and l.get_visible():
                ax.draw_artist(l)
    # for (ax, l) in lines:
    #     ## if the line is not visible, draw artist will not draw it
    #     ax.draw_artist(l)
    
    for m in self.markers:
        m.update_marker()
        if m != self.marker_active:
            m.draw()

    if blit:
        #self.figure.canvas.blit(self.bbox)

        #self.figure.c
        #self.figure.draw_artist(self.yaxis)
        # self.yaxis.remove()
        self.figure.canvas.blit(self.bbox)
        #print(self.xaxis)
        self._active_background = self.figure.canvas.copy_from_bbox(self.bbox)

        if self.marker_active != None:
            self.marker_active.draw()

        self.figure.canvas.blit(self.bbox)
    else:
        if self.marker_active != None:
            self.marker_active.draw()
        self._active_background = None


##############
############## 

marker_default_params = dict(
        show_xline=True,
        show_yline = False,
        yformat= None,
        xformat= None,
        show_xlabel=False,
        show_ylabel=True,
        xreversed=False, 
        alpha=0.7,
        wrap = False,
        xlabel_pad = 6,
        ylabel_xpad = 10,
        ylabel_ypad = 4,
        inherit_ticker = True,
    )

####################
## Figure Patches ##
####################

def marker_enable(self, interactive=True, link_all=False, **marker_params):
    """ enable markers on all child axes of figure

        Parameters
        ----------
            interactive: (bool) if True, an event manager will be added to the figure object and allow interactive 
                         markers to be placed on any child axes.
            
            top_axes: (list of Axes) only used for shared axes created by plt.twinx().
                      axes in this list will be flagged as the interactive axes, any shared axes behind these will be non-interactive
            
            marker_params:  marker parameters to attach to all child axes, if parameters other than the defaults are needed.
                            If an axes needs unique parameters, use axes.marker_set_params() 

                    show_xline: (bool) show vertical line (for rectlinear) or radial line (for polar) at each marker.
                                also affects how interactive marker placement is handled 

                    show_dot: (bool) show marker dot on each data line

                    yformat: function with parameters: (xd, yd, idx)
                                returns string to place in marker label text box

                    xformat: function with parameters: (xd)
                                returns string to place in xlabel text box (if shown)
                                
                    show_xlabel: (bool) show xdata text box at bottom of rectlinear markers

                    alpha: (float, 0-1) alpha value to apply to marker label text boxes

                    wrap: (bool) allow markers to wrap to other side of data array when using arrow keys
    """
    if interactive:
        ## this will overwrite the reference to a previously defined event manager.
        ## as long as the user didn't store the old reference, the previous event bindings will be disconnected
        self._eventmanager = MarkerManager(self)

    default_inst = dict(**marker_default_params)
    default_inst.update(dict(**marker_params))

    for ax in self.axes:
        ax.markers = []
        ax.marker_params = dict(**default_inst)
        ax.marker_ignorelines = []
        ax.marker_active = None
        ax.marker_linked_axes = []
        ax._active_background = None
        ax._all_background = None
        ax._top_axes = ax
        
        if not hasattr(ax.__class__, 'marker_add'):
            patch = gorilla.Patch(ax.__class__, 'marker_add', marker_add)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_delete', marker_delete)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_delete_all', marker_delete_all)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_set_params', marker_set_params)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_ignore', marker_ignore)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_link', marker_link)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, '_marker_xformat', _marker_xformat)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, '_marker_yformat', _marker_yformat)
            gorilla.apply(patch)

            settings = gorilla.Settings(allow_hit=True, store_hit=True)
            patch = gorilla.Patch(ax.__class__, 'plot', plot, settings=settings)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'clear', clear, settings=settings)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'draw_lines_markers', draw_lines_markers)
            gorilla.apply(patch)

    self._top_axes = []
    sub_axes = []
    for ax in self.axes:
        if ax not in sub_axes:
            self._top_axes.append(ax)
        else:
            continue
        ## loop through list of shared axes, included this axes
        for ax_s in ax.get_shared_x_axes().get_siblings(ax):
            
            if ax_s != ax:
                sub_axes.append(ax_s)
                ax_s._top_axes = ax
    
    for ax in self.axes:
        if ax._top_axes != ax:
            continue

        zorder = []
        for ax_s in ax.get_shared_x_axes().get_siblings(ax):
            if ax_s != ax:
                ax_s.patch.set_visible(False)
            zorder.append(ax_s.get_zorder())
        if len(zorder) > 1:
            ax.set_zorder(np.max(zorder)+1)

    if link_all: 
        for ax in self._top_axes:
            ax.marker_link(*self._top_axes)

##############
##############


## add marker_enable() to Figure class
patch = gorilla.Patch(matplotlib.figure.Figure, 'marker_enable', marker_enable)
gorilla.apply(patch)


