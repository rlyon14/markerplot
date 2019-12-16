
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from . markerplot import MarkerManager, Marker

import gorilla
import matplotlib

def marker_add(self, x, y=None):
    new_marker = Marker(self.axes, x, y)
    
    self.markers.append(new_marker)
    return new_marker

def marker_delete(self, marker):
    idx = self.markers.index(marker)
    marker.remove()
    self.markers.pop(idx)
    return self.markers[-1] if len(self.markers) > 0 else None

def marker_set_params(self, **kwargs):
    self.marker_params.update(dict(**kwargs))

def marker_ignore(self, *lines):
    lines = list(lines)
    self.marker_ignorelines += lines

def marker_link(self, *axes):
    axes = list(axes)
    for ax in axes:
        if ax in self.marker_linked_axes:
            continue
        self.marker_linked_axes.append(ax)
        ax.marker_linked_axes.append(self)
    
def marker_enable(self, interactive=True, top_axes=None, **kwargs):
    if interactive:
        self._eventmanager = MarkerManager(self, top_axes=top_axes)

    default_params = dict(
        xmode=True,
        show_xline=True,
        show_dot=True,
        yformat=None,
        xformat=None,
        show_xlabel=True,
        xreversed=False, 
        alpha=0.7
    )

    default_params.update(dict(**kwargs))

    for ax in self.axes:
        ax.markers =[]
        ax.marker_params = dict(**default_params)
        ax.marker_ignorelines = []
        ax.marker_active = None
        ax.marker_linked_axes = []
        
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

patch = gorilla.Patch(matplotlib.figure.Figure, 'marker_enable', marker_enable)
gorilla.apply(patch)

