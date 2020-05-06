
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

def drop_event_handler(text):
    p = Path(text)
    p = p.relative_to(r"file:\\")
    print(p)
    s = Sparam(str(p))
    s.plot(axes=ax1, label='test')
    fig.app.update_traces_group()
    fig.canvas.draw()

fig.app.add_drop_event_handler(drop_event_handler)

s = Sparam(dir_ / 'TGA2598-SM.s2p')
s.plot(axes=ax1)
plt.show()
