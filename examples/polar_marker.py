
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
#from fig2pptx import fig2pptx


from markerplot import interactive_subplots

dir_ = Path(__file__).parent

#matplotlib.use('Qt4Agg') 

def xdata_to_theta(x, y, **kwargs):
    return '{:.3f}\n$\\theta$={:.3f}'.format(y, x* (180/np.pi))

fig, axes = interactive_subplots(1,1, subplot_kw=dict(polar=True), show_xlabel=True, yformat=xdata_to_theta, wrap=True, show_xline=True)

axes.set_thetamin(-180)
axes.set_thetamax(180)
axes.set_theta_direction(-1)
axes.set_theta_zero_location("N")
axes.set_thetagrids(np.hstack((np.arange(0, 180 + 30, 30), (np.arange(30, 180, 30) * -1)[::-1])), fontsize='small')

# print(axes.InvertedPolarTransform(axes).transform)
# print(axes.transData.transform((0,1.5)))
#print(axes.__dict__)
#print(axes.transAxes.transform)





## link all markers between ax1 and ax2 (interactive only)
#ax1.marker_link(ax2)

x1 = np.arange(-180, 180, 1)
y1 = np.sin(x1* (np.pi/180))
y2 = np.cos(x1* (np.pi/180))

r = np.arange(0, 2, 0.01)
theta = 2 * np.pi * r

#axes.plot(theta, r)
axes.plot(x1 * (np.pi/180), y2, label='test')
#axes.plot(x1 * (np.pi/180), y2, label='test')

axes.marker_add(0)
fig.savefig(dir_/ 'test.png', dpi=330)
#fig2pptx(dir_ / r'test.pptx', close_plots=False)

#axes.axvline(np.pi, linewidth=0.5, color='r')
#axes.grid(True)

plt.show()