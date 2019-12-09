
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import markerplot

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig, ax = plt.subplots(1, 1, constrained_layout=True, figsize=(10,5))
fig.marker_enable()

x = np.linspace(-2*np.pi, 2*np.pi, 100)

ax.plot(x, np.sin(x), label='sin(x)')
ax.plot(x, np.cos(x), label='cox(x)')

## or place static markers:
ax.marker_add(x=0)

plt.legend()
plt.show()