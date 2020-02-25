from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QGridLayout, QLabel,
                             QLabel, QSizePolicy, QSlider, QSpacerItem, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget, QStyleFactory, QGroupBox, QCheckBox)

from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np

from pathlib import Path
import sys

from time import time
import matplotlib.pyplot as plt
import markerplot
import matplotlib

import sys
import time
from pathlib import Path

import numpy as np
# from fbs_runtime.application_context.PyQt5 import ApplicationContext
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5

from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

from matplotlib.figure import Figure
import matplotlib.pyplot as plt

dir_ = Path(__file__).parent

class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self, nrows=1, ncols=1, figsize=(5,3), constrained_layout=False, **kwargs):
        self.qapp = QtWidgets.QApplication(sys.argv)
        
        super().__init__()
        #self.setAutoFillBackground(True)
        
        self._main = QtWidgets.QWidget()
        self.setWindowTitle('title')
        self.setStyle(QStyleFactory.create('Fusion'))

        self.setCentralWidget(self._main)
        self.layout = QGridLayout(self._main)

        self.fig = Figure(figsize=figsize, constrained_layout=constrained_layout)
        self.ax = self.fig.subplots(nrows, ncols, **kwargs)
        self.nrows = nrows
        self.ncols = ncols

        if not isinstance(self.ax, np.ndarray):
            self.ax = np.array([self.ax])

        for ax in self.ax.flatten():
            ax.grid()

        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas, 0,0, (self.nrows*self.ncols)+1, 1)

        toolbar = self.build_toolbar()
        self.addToolBar(toolbar)
        self.canvas.setFocusPolicy( QtCore.Qt.ClickFocus )
        self.canvas.setFocus()

    def build_toolbar(self):
        toolbar = NavigationToolbar(self.canvas, self)
        #toolbar.removeAction(toolbar._actions['forward'])
        #toolbar.removeAction(toolbar._actions['back'])
        toolbar.removeAction(toolbar._actions['configure_subplots'])
        icon = QtGui.QPixmap(str(dir_  / 'icons/subplots_large.png'))

        icon.setDevicePixelRatio(self.canvas._dpi_ratio)

        # print(matplotlib.rcParams['datapath'])
        a = toolbar.addAction(QtGui.QIcon(icon),
                    'Customize', self.set_tight_layout)
        a.setToolTip('Apply Tight Layout')

        toolbar.coordinates = False
        return toolbar
        #layout.addWidget(toolbar)

        # self.locLabel = QLabel("", toolbar)
        # self.locLabel.setAlignment(
        #         QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        # self.locLabel.setSizePolicy(
        #     QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                             QtWidgets.QSizePolicy.Ignored))
        # toolbar.addWidget(self.locLabel)
            
    def createCheckBox(self, label):
        

    def createTracesGroup(self):
        self.traces = [QGroupBox("Traces{}".format(i)) for i in range(self.nrows * self.ncols)]
        #self.traces = np.array(self.traces).reshape(self.ax.shape)
        #self.traces_flat = self.traces.flatten()

        self.traces_cb = [[]]*(self.nrows * self.ncols)
        
        for i, ax in enumerate(self.ax.flatten()):
            print(ax, i)
            layout = QVBoxLayout()
            for ax_shared in ax.get_shared_x_axes().get_siblings(ax):
                # if ax_shared == ax:
                #     continue
                for l in ax_shared.lines:

            #for ii, l in enumerate(ax.lines):
                    label = l.get_label()
                    if label == '' or label[0] == '_':
                        continue

                    #label = plt.text(0.4,0.4,'$%s$' %label,size=50)
                    cb = QCheckBox(label)
                    self.traces_cb[i].append((cb, l, label))
                    cb.stateChanged.connect(self.state_changed)
                    cb.setChecked(True)

                    layout.addWidget(cb)

            self.traces[i].setLayout(layout)  
        # self.menu_scroll = QScrollArea(widgetResizable=False)
        # self.menu_scroll.setWidget(self.traces)

    def state_changed(self):
        for i, ax in enumerate(self.ax.flatten()):
            for ii, (cb, l, label) in enumerate(self.traces_cb[i]):
                state = cb.isChecked()
                l.set_visible(state)
                if state:
                    l.set_label(label)
                else:
                    l.set_label('')
            ax.legend(fontsize='small')
        self.canvas.draw()
    
    def set_tight_layout(self):
        self.fig.tight_layout()
        self.canvas.draw()

    def show(self):
        self.createTracesGroup()
        added_traces = False
        for i, tr in enumerate(self.traces):
            if len(self.traces_cb[i]) > 1:
                added_traces = True
                self.layout.addWidget(self.traces[i], i, 1)
        
        if added_traces:
            self.layout.addWidget(QGroupBox(), i+1,1)
            self.layout.setColumnStretch(0, 1)
            self.layout.setRowStretch(i+1, 1)

        super().show()
        self.qapp.exec_()

def interactive_subplots(nrows=1, ncols=1, figsize=(5,3), constrained_layout=True, **kwargs):
    app = PlotWindow(nrows, ncols, figsize=figsize, constrained_layout=True, **kwargs)
    fig, ax = app.fig, app.ax
    return app, fig, ax

if __name__ == "__main__":

    app, fig, ax = interactive_subplots(1,2)
    t = np.linspace(0, 10, 101)
    ax[0].plot(t, np.sin(t), label='sin')
    ax[1].plot(t, np.cos(t), label='cos')
    
    fig.marker_enable(link_all=True, show_xlabel=True)
    app.show()
