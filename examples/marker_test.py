from markerplot import MarkerPlot
from pathlib import Path
import matplotlib
import numpy as np

dir_ = Path(__file__).parent
matplotlib.use('Qt4Agg')

p = MarkerPlot()

x = np.linspace(-2*np.pi, 2*np.pi, 100)

p.plot(x, np.sin(x), label='sin(x)')
p.plot(x, np.cos(x), label='cox(x)')
p.show()