
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import markerplot

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig, ax = plt.subplots(1, 1, constrained_layout=True, figsize=(10,5))
print(fig.__class__)
fig.marker_enable()

x1 = np.linspace(-2*np.pi, 2*np.pi, 100)
x2 = np.linspace(-6*np.pi, 6*np.pi, 100)

ax.plot(x2, np.sin(x2), label='sin(x)')
ax.plot(x1, np.cos(x1), label='cox(x)')

## or place static markers:
ax.marker_add(x=0)

plt.legend()
plt.show()