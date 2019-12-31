
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import markerplot

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig1, ax1 = plt.subplots(1, 1, constrained_layout=True, figsize=(10,5))
ax1.grid(linewidth=0.5, linestyle='-')

fig2, ax2 = plt.subplots(1, 1, constrained_layout=True, figsize=(10,5))
ax2.grid(linewidth=0.5, linestyle='-')
par1 = ax1.twinx()

## bring ax1 to top instead of par1
fig1.marker_enable(show_xline=True, show_xlabel=False, top_axes=ax1)
fig2.marker_enable(show_xline=True, show_xlabel=False)

## link all markers between ax1 and ax2 (interactive only)
ax1.marker_link(ax2)

x1 = np.linspace(-2*np.pi, 2*np.pi, 100)
x2 = np.linspace(-6*np.pi, 6*np.pi, 100)

ax1.plot(x1, np.sin(x1), label='sin(x)')
ax2.plot(x1, np.cos(x1), label='cos(x)')


plt.legend()
plt.show()