from rfnetwork import *
from markerplot import MarkerPlot
from pathlib import Path
import matplotlib

dir_ = Path(__file__).parent
matplotlib.use('Qt4Agg')

n = Network(2e9,6e9,10e6, allow_internal=False, nf_flag=True)
s = Sparam(dir_.joinpath(r'QPL9057.s2p'))

s.plot(21, outf='db')
s.smithchart(1,2)


plt.show()