
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from fig2pptx import fig2pptx

import markerplot

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig, ax1 = plt.subplots(1, 1, figsize=(10,5), constrained_layout=True)
#ax1.grid(linewidth=0.5, linestyle='-')
#ax2.grid(linewidth=0.5, linestyle='-')

fig.marker_enable(show_xline=True, show_xlabel=True, wrap=True)

## link all markers between ax1 and ax2 (interactive only)
#ax1.marker_link(ax2)

x1 = np.linspace(-2*np.pi, 2*np.pi, 100)
x2 = np.linspace(-6*np.pi, 6*np.pi, 100)

ax1.plot(x1, np.sin(x1), label='sin(x)')
ax1.plot(x1, np.sin(x1), label='sin(x)_2')


ax1.legend()
ax1.marker_add(3,6)
#ax1.marker_add(x=3)
print(fig.dpi)

#plt.tight_layout()
# fig.savefig(dir_/ 'test.png', dpi=330)
fig2pptx(dir_ / r'test.pptx', close_plots=False)
## place static markers



plt.show()