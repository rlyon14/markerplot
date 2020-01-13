
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from . markerplot import MarkerManager, Marker

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
            xd: (float) x-value in data coordinates
            disp: (tuple) x,y tuple of display cordinates
            idx: (int) index of x-data (only for index mode)
    """
    new_marker = Marker(self.axes, xd=xd, idx=idx, disp=disp)
    
    self.markers.append(new_marker)
    self.marker_active = new_marker
    return new_marker

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
    """ links axes together so that any change to markers on one is reflected in the other
        Parameters
        ----------
            axes: (Axes object) axes that will be linked to current axes (self)
            byindex: (bool) if True, each marker will be linked by xdata index rather than xdata value
                     (assumes each line on axes have identical xdata lengths)
    """
    axes = list(axes)
    self._force_index_mode = byindex
    for ax in axes:
        if ax in self.marker_linked_axes:
            continue
        self.marker_linked_axes.append(ax)
        ax.marker_linked_axes.append(self)
        ax._force_index_mode = byindex

##############
############## 


####################
## Figure Patches ##
####################
def marker_enable(self, interactive=True, top_axes=None, **marker_params):
    """ enable markers on all child axes of figure

        Parameters
        ----------
            interactive: (bool) if True, an event manager will be added to the figure object and allow interactive 
                         markers to be placed on any child axes.
            
            top_axes: (list of Axes) only used for shared axes created by plt.twinx().
                      axes in this list will be flagged as the interactive axes, any shared axes behind these will be non-interactive
            
            marker_params:  marker parameters to attach to all child axes, if parameters other than the defaults are needed.
                            if an axes needs unique parameters, use axes.marker_set_params() after fig.marker_enable() is called

                show_xline: (bool) show vertical line (for rectlinear) or radial line (for polar) at each marker.
                            also affects how interactive marker placement is handled 

                show_dot: (bool) show marker dot on each data line

                yformat: function with parameters: (xd, yd, idx)
                            returns string to place in marker label text box

                xformat: function with parameters: (xd)
                            returns string to place in xlabel text box (if shown)
                            
                show_xlabel: (bool) show xdata text box at bottom of rectlinear plots

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
    )

    default_params.update(dict(**marker_params))

    for ax in self.axes:
        ax.markers =[]
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

##############
##############


## add marker_enable() to Figure class
patch = gorilla.Patch(matplotlib.figure.Figure, 'marker_enable', marker_enable)
gorilla.apply(patch)

