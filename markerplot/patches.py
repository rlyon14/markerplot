
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

def marker_add(self, xd=None, idx=None, disp=None):
    """ add new marker at a given x data value, index value or display coordinate, and set as the
        axes active marker

        Parameters
        ----------
            xd: (float, list) x-value in data coordinates
            idx: (int, list) index of x-data (ignored if axes data lines have unequal xdata arrays)
            disp: (tuple) x,y value in axes display cordinates
    """
    if isinstance(xd, (list, tuple, np.ndarray)):
        for x in xd:
            self.markers.append(Marker(self.axes, xd=x))
    
    elif isinstance(idx, (list, tuple, np.ndarray)):
        for i in idx:
            self.markers.append(Marker(self.axes, idx=i))
    else:
        self.markers.append(Marker(self.axes, xd=xd, idx=idx, disp=disp))

    self.marker_active = self.markers[-1]
    return self.marker_active

def marker_delete(self, marker):
    """ remove marker from axes
    """
    idx = self.markers.index(marker)
    marker.remove()
    self.markers.pop(idx)
    return self.markers[-1] if len(self.markers) > 0 else None

def marker_set_params(self, **kwargs):
    """ allows for updates to axes marker parameters if axes requires unique parameters
    """
    self.marker_params.update(dict(**kwargs))

def marker_ignore(self, *lines):
    """ flags lines that should not accept markers (i.e. smithchart lines)
    """
    lines = list(lines)
    self.marker_ignorelines += lines

def marker_link(self, *axes, byindex=False):
    """ --interactive only--
        links axes together so that any interactive change to markers on axes one is reflected in the other

        Parameters
        ----------
            axes: (Axes object) axes that will be linked to current axes (self)
            byindex: (bool) if True, each marker will be linked by xdata index rather than xdata value
                     This will force each axes into index mode, meaning every data line must have identical xdata lengths.

        Warning: 
        If manual markers are placed in linked axes with axes.marker_add(), interactive markers will fail if the 
        number of markers are not kept equal between linked axes.
    """
    axes = list(axes)
    self._force_index_mode = byindex
    for ax in axes:
        if ax in self.marker_linked_axes or ax == self:
            continue
        self.marker_linked_axes.append(ax)
        ax.marker_linked_axes.append(self)
        ax._force_index_mode = byindex

def _marker_yformat(self, xd, yd, idx=None):
    yformatter = self.yaxis.get_major_formatter()

    if not isinstance(yformatter, ticker.ScalarFormatter) and self.marker_params['inherit_ticker']:
        return yformatter(yd)
    else:
        return self.marker_params['yformat'](xd, yd, idx=idx)


def _marker_xformat(self, xd):
    xformatter = self.xaxis.get_major_formatter()

    if not isinstance(xformatter, ticker.ScalarFormatter) and self.marker_params['inherit_ticker']:
        return xformatter(xd)
    else:
        return self.marker_params['xformat'](xd)

##############
############## 


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
        self._eventmanager = MarkerManager(self, top_axes=top_axes)

    default_params = dict(
        show_xline=True,
        show_dot=True,
        yformat= lambda x, y, idx: '{:.3f}'.format(y),
        xformat= lambda x: '{:.3f}'.format(x),
        show_xlabel=False,
        xreversed=False, 
        alpha=0.7,
        wrap = False,
        xlabel_pad = 6,
        ylabel_xpad = 10,
        ylabel_ypad = 4,
        inherit_ticker = True
    )

    default_params.update(dict(**marker_params))

    for ax in self.axes:
        ax.markers = []
        ax.marker_params = dict(**default_params)
        ax.marker_ignorelines = []
        ax.marker_active = None
        ax.marker_linked_axes = []
        ax._draw_background = None
        ax._force_index_mode = False
        
        if not hasattr(ax.__class__, 'marker_add'):
            patch = gorilla.Patch(ax.__class__, 'marker_add', marker_add)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_delete', marker_delete)
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


    ## link all axes together in figure
    if link_all: 
        for ax in self.axes:
            ax.marker_link(*self.axes)

##############
##############


## add marker_enable() to Figure class
patch = gorilla.Patch(matplotlib.figure.Figure, 'marker_enable', marker_enable)
gorilla.apply(patch)

