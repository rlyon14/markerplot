
from pathlib import Path, PurePath
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
#from fig2pptx import fig2pptx
#import rftools
import markerplot
from markerplot import interactive_subplots
from matplotlib import ticker
from rfnetwork import Sparam

dir_ = Path(__file__).parent 



fig, (ax1) = interactive_subplots(1, 1, figsize=(10,5), constrained_layout=True)
ax1.grid(linewidth=0.5, linestyle='-')

plotted_sp = []

def drop_event_handler(text):
    p = Path(text)
    p = p.relative_to(r"file:\\")
    print(p)
    s = Sparam(str(p))
    plotted_sp.append(s)
    s.plot(axes=ax1, label=p.stem)
    fig.app.update_traces_group()
    fig.canvas.draw()

def set_data_format(axes, value):
    outf = {"Magnitude (dB)":'db', "Phase (deg)":'ang', "VSWR":'vswr'}[value]
    for sp in plotted_sp:
        sp.plot(axes=axes, label=sp.name, outf=outf)

fig.app.add_drop_event_handler(drop_event_handler)
fig.app.add_data_format_handler(set_data_format)

s = Sparam(dir_ / 'TGA2598-SM.s2p')
plotted_sp.append(s)
s.plot(axes=ax1)
plt.show()
