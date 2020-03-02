
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
#from fig2pptx import fig2pptx
#import rftools
import markerplot
from matplotlib import ticker

dir_ = Path(__file__).parent

matplotlib.use('Qt4Agg') 

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10,5), constrained_layout=True, dpi=100)
ax1.grid(linewidth=0.5, linestyle='-')
ax2.grid(linewidth=0.5, linestyle='-')
ax3.grid(linewidth=0.5, linestyle='-')

fig.marker_enable(show_xline=True, show_xlabel=True, wrap=True, inherit_ticker=True, link_all=True)

x1 = np.linspace(-2*np.pi, 2*np.pi, 100)

l1 = ax1.plot(x1, np.sin(x1))
ax1.plot(x1, np.cos(x1))
print(l1)
ax2.plot(x1, np.sin(x1))
ax3.plot(x1, np.cos(x1))

# ax1.marker_add(xd=2, lines=l1)
# ax2.marker_add(xd=2)
# ax3.marker_add(xd=2)

ax1.xaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))
ax2.yaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))

fig.savefig(dir_/ 'test.png', dpi=330)

plt.show()
