
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import markerplot

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig, ax = plt.subplots(1, 1, constrained_layout=True, figsize=(10,5))

## make sure any axes you want the markers on have already been added to fig before this call
fig.marker_enable(show_xline=False, show_xlabel=False)

x1 = np.linspace(-2*np.pi, 2*np.pi, 100)
x2 = np.linspace(-6*np.pi, 6*np.pi, 100)

ax.plot(x1, np.sin(x1), label='sin(x)')
ax.plot(x2, np.cos(x2), label='cox(x)')

## place static markers
ax.marker_add(x=0)

plt.legend()
plt.show()