
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from . markerplot import MarkerManager, Marker

import gorilla
import matplotlib

def marker_add(self, x, y=None):
    params = self.marker_params
    new_marker = Marker(self.axes, x, y, **params)
    
    self.markers.append(new_marker)
    return new_marker

def marker_delete(self, marker):
    idx = self.markers.index(marker)
    marker.remove()
    self.markers.pop(idx)
    return self.markers[-1] if len(self.markers) > 0 else None

def marker_set_params(self, **kwargs):
    self.marker_params.update(dict(**kwargs))
    
def marker_enable(self,  **kwargs):
    self._eventmanager = MarkerManager(self)
    for ax in self.axes:
        ax.grid(linewidth=0.5, linestyle='-')
        ax.markers =[]
        ax.marker_params = dict(**kwargs)
        ax.marker_ignorelines = []
        
        if not hasattr(ax.__class__, 'marker_add'):
            patch = gorilla.Patch(ax.__class__, 'marker_add', marker_add)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_delete', marker_delete)
            gorilla.apply(patch)

            patch = gorilla.Patch(ax.__class__, 'marker_set_params', marker_set_params)
            gorilla.apply(patch)

patch = gorilla.Patch(matplotlib.figure.Figure, 'marker_enable', marker_enable)
gorilla.apply(patch)

