
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

##TODO: fix this
def marker_add_ignoreline(self, *lines):
    lines = list(lines)
    self.marker_ignorelines += lines
    
def marker_enable(self, interactive=True, linked_axes=None, **kwargs):
    if interactive:
        self._eventmanager = MarkerManager(self, linked_axes)

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

    default_params.update(kwargs)

    for ax in self.axes:
        ax.markers =[]
        ax.marker_params = default_params
        ax.marker_ignorelines = []
        
        if not hasattr(ax.__class__, 'marker_add'):
            patch = gorilla.Patch(ax.__class__, 'marker_add', marker_add)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_delete', marker_delete)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_set_params', marker_set_params)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_add_ignoreline', marker_add_ignoreline)
            gorilla.apply(patch)

patch = gorilla.Patch(matplotlib.figure.Figure, 'marker_enable', marker_enable)
gorilla.apply(patch)

