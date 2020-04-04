
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

    original = gorilla.get_original_attribute(self, 'plot')
    lines = original(*args, **kwargs)

    if np.any(mxd):
        for l in lines:
            l._marker_xdata = mxd

    return lines

def clear(self, *args, **kwargs):

    original = gorilla.get_original_attribute(self, 'clear')
    ret = original(*args, **kwargs)

    self.marker_delete_all()
    self.marker_ignorelines = []
    self._draw_background = None

    return ret

def draw_lines_markers(self):
    for ax in self.fig.axes:
        for l_ax in ax.marker_linked_axes:

def update_background(self):
    if ax.marker_active != None:
        ax.marker_active.set_animated(True)
    
    self._draw_background = None

##############
############## 

marker_default_params = dict(
        show_xline=True,
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
def marker_enable(self, interactive=True, top_axes=None, link_all=False, **marker_params):
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
        self._eventmanager = MarkerManager(self, top_axes=top_axes)

    default_inst = dict(**marker_default_params)
    default_inst.update(dict(**marker_params))

    for ax in self.axes:
        ax.markers = []
        ax.marker_params = dict(**default_inst)
        ax.marker_ignorelines = []
        ax.marker_active = None
        ax.marker_linked_axes = []
        ax._draw_background = None
        
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


    ## link all axes together in figure
    if link_all: 
        for ax in self.axes:
            ax.marker_link(*self.axes)

##############
##############


## add marker_enable() to Figure class
patch = gorilla.Patch(matplotlib.figure.Figure, 'marker_enable', marker_enable)
gorilla.apply(patch)

