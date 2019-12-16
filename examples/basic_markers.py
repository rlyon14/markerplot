
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import markerplot

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig, ax = plt.subplots(2, 1, constrained_layout=True, figsize=(10,5))
ax[0].grid(linewidth=0.5, linestyle='-')
ax[1].grid(linewidth=0.5, linestyle='-')

## make sure any axes you want the markers on have already been added to fig before this call
fig.marker_enable(show_xline=True, show_xlabel=False, top_axes=None) #, linked_axes=[ax[1]])

ax[0].marker_link(ax[1])
x1 = np.linspace(-2*np.pi, 2*np.pi, 100)
x2 = np.linspace(-6*np.pi, 6*np.pi, 100)

ax[0].plot(x1, np.sin(x1), label='sin(x)')
ax[1].plot(x1, np.cos(x1), label='cox(x)')

## place static markers
#ax.marker_add(x=0)

plt.legend()
plt.show()