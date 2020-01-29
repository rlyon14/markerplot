
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from fig2pptx import fig2pptx
#import rftools
import markerplot
from matplotlib import ticker

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10,5), constrained_layout=True, dpi=100)
ax1.grid(linewidth=0.5, linestyle='-')
ax2.grid(linewidth=0.5, linestyle='-')

fig.marker_enable(show_xline=True, show_xlabel=True, wrap=True, ignore_axis_formatter=False)

## link all markers between ax1 and ax2 (interactive only)
#ax1.marker_link(ax2)

x1 = np.linspace(-2*np.pi, 2*np.pi, 100)
x2 = np.linspace(-6*np.pi, 6*np.pi, 100)

ax1.plot(x1, np.sin(x1), label='sin(x)')
ax2.plot(x1, np.sin(x1), label='sin(x)_2')
ax3.plot(x1, np.cos(x1), label='cos(x)')

ax1.xaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))
ax2.yaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))

ax1.legend()
ax2.legend()
ax1.marker_add(xd=2)
ax2.marker_add(xd=2)
ax3.marker_add(xd=2)

#plt.tight_layout()
fig.savefig(dir_/ 'test.png', dpi=330)
#fig2pptx(dir_ / r'test.pptx', close_plots=False)
## place static markers


plt.show()