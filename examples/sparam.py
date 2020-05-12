
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
    s = Sparam(str(p))
    
    plotted_names = [sp.name for (sp, ax, lines)  in plotted_sp]
    print(plotted_names, s.name)
    if s.name not in plotted_names:
        ax, lines = s.plot(axes=ax1, label=p.stem)
        plotted_sp.append((s, ax, lines))

format_options = {"Magnitude (dB)":'db', "Phase (deg)":'ang'}
def set_data_format(axes, value):
    for (sp, ax, lines) in plotted_sp:
        sp.plot(label=sp.name, outf=value, lines=lines)

fig.app.add_drop_event_handler(drop_event_handler)
fig.app.add_data_format_handler(set_data_format, format_options, initial='db')

s = Sparam(dir_ / 'TGA2598-SM.s2p')

ax, lines = s.plot(axes=ax1)
plotted_sp.append((s, ax, lines))
plt.show()
