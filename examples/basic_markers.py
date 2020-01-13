
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
#from fig2pptx import fig2pptx

import markerplot

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,5), constrained_layout=False)
ax1.grid(linewidth=0.5, linestyle='-')
ax2.grid(linewidth=0.5, linestyle='-')

fig.marker_enable(show_xline=True, show_xlabel=True, wrap=True)

## link all markers between ax1 and ax2 (interactive only)
ax1.marker_link(ax2)

x1 = np.linspace(-2*np.pi, 2*np.pi, 100)
x2 = np.linspace(-6*np.pi, 6*np.pi, 100)

ax1.plot(x1, np.sin(x1), label='sin(x)')
ax1.plot(x2, np.sin(x1), label='sin(x)_2')
ax2.plot(x1, np.sin(x1), label='cos(x)')

ax1.legend()
ax2.legend()
ax1.marker_add(xd=2)
ax2.marker_add(xd=2)

plt.tight_layout()
fig.savefig(dir_/ 'test.png', dpi=330)
#fig2pptx(dir_ / r'test.pptx', close_plots=False)
## place static markers



plt.show()