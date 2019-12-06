
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from . markerplot import MarkerManager, Marker

import gorilla
import matplotlib

def add_marker(self, x, y=None):
    ## get axes marker settings
    params = self.marker_params
    new_marker = Marker(self.axes, x, y, **params)#, smithchart=self.smithchart, xdisplay=self.xDisplay, show_xlabel=self.show_xlabel)
    self.markers.append(new_marker)
    return new_marker

def delete_marker(self, marker):
    idx = self.markers.index(marker)
    marker.remove()
    self.markers.pop(idx)
    return self.markers[-1] if len(self.markers) > 0 else None

def set_marker_params(self, **kwargs):
    self.marker_params.update(**kwargs)
    
def enable_dynamic_markers(self, **kwargs):
    self._eventmanager = MarkerManager(self)
    for ax in self.axes:
        ax.grid(linewidth=0.5, linestyle='-')
        ax.markers =[]
        ax.marker_params = dict(**kwargs)
        ax.marker_ignorelines = []
    
        patch = gorilla.Patch(ax.__class__, 'add_marker', add_marker)
        gorilla.apply(patch)

        patch = gorilla.Patch(ax.__class__, 'delete_marker', delete_marker)
        gorilla.apply(patch)

        patch = gorilla.Patch(ax.__class__, 'set_marker_params', set_marker_params)
        gorilla.apply(patch)

patch = gorilla.Patch(matplotlib.figure.Figure, 'enable_dynamic_markers', enable_dynamic_markers)
gorilla.apply(patch)

