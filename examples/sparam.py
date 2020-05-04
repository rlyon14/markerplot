
from pathlib import Path, PurePath
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
#from fig2pptx import fig2pptx
#import rftools
import markerplot
from markerplot import interactive_subplots, hide_lines
from matplotlib import ticker
from rfnetwork import Sparam

dir_ = Path(__file__).parent 



fig, (ax1) = interactive_subplots(1, 1, figsize=(10,5), constrained_layout=True)
ax1.grid(linewidth=0.5, linestyle='-')
splots = []
names = []
g_outf = 'db'

def drop_event_handler(text):
    p = Path(text)
    p = p.relative_to(r"file:\\")
    print(p)
    splots.append(Sparam(str(p)))
    names.append(p.stem)
    print(g_outf, id(g_outf))
    ax, lines = splots[-1].plot(axes=ax1, label=p.stem, outf=g_outf)
    fig.app.remove_all()
    hide_lines(*lines, state=True)
    fig.app.update_traces_group()
    fig.canvas.draw()



fig.app.add_drop_event_handler(drop_event_handler)

splots.append(Sparam(dir_ / 'TGA2598-SM.s2p'))

def set_data_format(axes, outf):
    g_outf = {"Magnitude (dB)":'db', "Phase (deg)":'ang', "VSWR":'vswr', "Unwrapped Phase (deg)":'ang_unwrap'}[outf]
    print(g_outf, id(g_outf))
    for i, sp in enumerate(splots):
        ax, lines = sp.plot(axes=axes, outf=g_outf, label=names[i])
        hide_lines(*lines, state=(i>0))

    fig.app.update_traces_group()
    fig.canvas.draw()

fig.app.add_data_format_handler(set_data_format)
splots[-1].plot(axes=ax1)
names.append(None)
plt.show()
