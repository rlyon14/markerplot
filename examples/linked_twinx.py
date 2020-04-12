
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np


from markerplot import interactive_subplots

dir_ = Path(__file__).parent

fig, (ax1, ax2) = interactive_subplots(2, 1, constrained_layout=True, figsize=(10,5))
ax1.grid(linewidth=0.5, linestyle='-')
ax2.grid(linewidth=0.5, linestyle='-')
par1 = ax1.twinx()
par2 = ax2.twinx()

fig.marker_enable(show_xline=True, show_xlabel=False, link_all=True)





x1 = np.linspace(-2*np.pi, 2*np.pi, 100)
x2 = np.linspace(-6*np.pi, 6*np.pi, 100)

ax1.plot(x1, np.sin(x1), label='sin(x)')
par1.plot(x1, np.cos(x1), label='cos(x)')
ax2.plot(x1, np.sin(x1), label='sin(x)')
par2.plot(x1, np.cos(x1), label='cos(x)')


plt.show()