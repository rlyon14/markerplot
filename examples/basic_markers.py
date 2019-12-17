
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import markerplot

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig, (ax1, ax2) = plt.subplots(2, 1, constrained_layout=True, figsize=(10,5))
ax1.grid(linewidth=0.5, linestyle='-')
ax2.grid(linewidth=0.5, linestyle='-')

fig.marker_enable(show_xline=True, show_xlabel=True)

## link all markers between ax1 and ax2 (interactive only)
#ax1.marker_link(ax2)

x1 = np.linspace(-2*np.pi, 2*np.pi, 100)
x2 = np.linspace(-6*np.pi, 6*np.pi, 100)

ax1.plot(x1, np.sin(x1), label='sin(x)')
ax2.plot(x1, np.cos(x1), label='cos(x)')

## place static markers
#ax.marker_add(x=0)

ax1.legend()
ax2.legend()
plt.show()