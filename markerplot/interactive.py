from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QGridLayout, QLabel,
                             QLabel, QSizePolicy, QSlider, QSpacerItem, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget, QStyleFactory, QGroupBox, QCheckBox)

from PyQt5 import QtWidgets, QtCore, QtGui
#from PyQt5.Qtgui import QImage
import numpy as np

from pathlib import Path
import sys

from time import time
import matplotlib.pyplot as plt
import markerplot
import matplotlib
import io

import sys
import time
from pathlib import Path
import win32clipboard
from PIL import Image

import numpy as np
# from fbs_runtime.application_context.PyQt5 import ApplicationContext
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5

from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

from matplotlib.figure import Figure
import matplotlib.pyplot as plt

dir_ = Path(__file__).parent

class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self, nrows=1, ncols=1, figsize=(5,3), constrained_layout=False, title=None, **kwargs):
        self.qapp = QtWidgets.QApplication(sys.argv)
        
        super().__init__()
        
        #self.setAutoFillBackground(True)
        title = 'Figure' if title == None else title
        self._main = QtWidgets.QWidget()
        self.setWindowTitle(title)
        self.setStyle(QStyleFactory.create('Fusion'))

        self.setCentralWidget(self._main)
        self.layout = QGridLayout(self._main)

        #self.fig = Figure(figsize=figsize, constrained_layout=constrained_layout)
        self.fig = plt.figure(figsize=figsize, constrained_layout=constrained_layout)
        
        self.ax = self.fig.subplots(nrows, ncols, **kwargs)
        
        #plt.close(self.fig)
        
        self.nrows = nrows
        self.ncols = ncols

        if not isinstance(self.ax, np.ndarray):
            self.ax = np.array([self.ax])

        for ax in self.ax.flatten():
            ax.grid()

        print('c', id(self.fig.canvas))
        self._old_canvas = self.fig.canvas
        #self.canvas = FigureCanvas(self.fig)
        self.canvas = self.fig.canvas
        print('c', id(self.fig.canvas), id(self.canvas))

        
        print('t')
        self._old_canvas_mn_show = self.canvas.manager.show
        print('p', id(self._old_canvas_mn_show))
        self.canvas.manager.show = self.show
        print('p', id(self._old_canvas_mn_show))
        self.layout.addWidget(self.canvas, 0,0, (self.nrows*self.ncols)+1, 1)
        

        toolbar = self.build_toolbar()
        self.addToolBar(toolbar)
        self.canvas.setFocusPolicy( QtCore.Qt.ClickFocus )
        self.canvas.setFocus()

        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)
        

    def build_toolbar(self):
        toolbar = NavigationToolbar(self.canvas, self, coordinates=False)
        #toolbar.removeAction(toolbar._actions['forward'])
        #toolbar.removeAction(toolbar._actions['back'])
        toolbar.removeAction(toolbar._actions['configure_subplots'])
        icon = QtGui.QPixmap(str(dir_  / 'icons/layout_large.png'))

        icon.setDevicePixelRatio(self.canvas._dpi_ratio)

        # print(matplotlib.rcParams['datapath'])
        a = toolbar.addAction(QtGui.QIcon(icon),
                    'Customize', self.set_tight_layout)
        a.setToolTip('Apply Tight Layout')

        ## Copy
        icon = QtGui.QPixmap(str(dir_  / 'icons/copy_large.png'))

        icon.setDevicePixelRatio(self.canvas._dpi_ratio)

        # print(matplotlib.rcParams['datapath'])
        a = toolbar.addAction(QtGui.QIcon(icon),
                    'Customize', self.copy_figure)
        a.setToolTip('Copy To Clipboard')


        toolbar.coordinates = False
        
        #layout.addWidget(toolbar)

        locLabel = QLabel("", toolbar)
        locLabel.setAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        locLabel.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                    QtWidgets.QSizePolicy.Ignored))
        toolbar.addWidget(locLabel)
        return toolbar
            
    def createCheckBoxLabel(self, label, size=14):
        r,g,b,a=self.palette().base().color().getRgbF()

        _figure=Figure(edgecolor=(r,g,b), facecolor=(r,g,b), dpi=100)

        _canvas=FigureCanvas(_figure)
        #l.addWidget(self._canvas)
        _figure.clear()
        text=_figure.suptitle(
            label,
            x=0.0,
            y=1.0,
            horizontalalignment='left',
            verticalalignment='top',
            size='small'
        )
        _canvas.draw()

        (x0,y0),(x1,y1)=text.get_window_extent().get_points()
        w=x1-x0; h=y1-y0
        

       # _figure.set_size_inches(w, h)
        _canvas.setFixedSize(w,h)
        #self.setFixedSize(w,h)
        return _canvas

    def createTracesGroup(self):
        self.traces = [QGroupBox("Traces{}".format(i)) for i in range(self.nrows * self.ncols)]
        #self.traces = np.array(self.traces).reshape(self.ax.shape)
        #self.traces_flat = self.traces.flatten()

        self.traces_cb = [[]]*(self.nrows * self.ncols)
        
        for i, ax in enumerate(self.ax.flatten()):
            #print(ax, i)
            row = 0
            layout = QGridLayout()
            for ax_shared in ax.get_shared_x_axes().get_siblings(ax):
                # if ax_shared == ax:
                #     continue
                for l in ax_shared.lines:

            #for ii, l in enumerate(ax.lines):
                    label = l.get_label()
                    if label == '' or label[0] == '_':
                        continue

                    #label = plt.text(0.4,0.4,'$%s$' %label,size=50)
                    cb = QCheckBox('')
                    self.traces_cb[i].append((cb, l, label))
                    cb.stateChanged.connect(self.state_changed)
                    cb.setChecked(True)
                    qlabel = self.createCheckBoxLabel(label, size=14)
                    
                    layout.addWidget(cb, row, 0)
                    layout.addWidget(qlabel, row, 1, alignment=Qt.AlignLeft)
                    
                    row += 1

            layout.setAlignment(Qt.AlignLeft)
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

    def copy_figure(self):

        buf = io.BytesIO()
        self.fig.savefig(buf)
        data = buf.getvalue()[14:]

        image = Image.open(buf)
        #print(image)
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        buf.close()



        # #clipboard = win32clipboard
        # #clipboard = QApplication.clipboard()
        # #clipboard.setImage(QtGui.QImage.fromData(buf.getvalue()),  mode=clipboard.Clipboard)
        # win32clipboard.OpenClipboard()
        # win32clipboard.SetClipboardData(0, bytes(buf))
        # buf.close()
        

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

        #self.fig.canvas = self._old_canvas
        
        #self.canvas.destroy()
        super().show()
        
        self.qapp.exec_()
        #self.canvas.manager.show = self._old_canvas_mn_show
        plt.close(self.fig)
        self._old_canvas_mn_show()
        #plt.close(self.fig)
        #self.qapp.quit()
        print(id(plt.gcf()), id(self.fig))
        #plt.close('all')
        print(id(plt.gcf()), id(self.fig))
        print(id(plt.gcf()), id(self.fig))
        
        print('close')

class CanvasManager(object):
    def __init__(self, show_func):
        self._show = show_func
    def show(self):
        return self._show()


def interactive_subplots(nrows=1, ncols=1, figsize=(5,3), constrained_layout=True, title=None, **kwargs):
    app = PlotWindow(nrows, ncols, figsize=figsize, constrained_layout=True, title=title, **kwargs)
    fig, ax = app.fig, app.ax
    return app, fig, ax

if __name__ == "__main__":
    matplotlib.use('Qt5Agg')
    #print(id(plt.gcf()))
    app, fig, ax = interactive_subplots(1,2)
    print('hello')
    #fig, ax = plt.subplots(1,2)
    t = np.linspace(0, 10, 101)
    ax[0].plot(t, np.sin(t), label='sin')
    ax[1].plot(t, np.cos(t), label='cos')
    
    fig.marker_enable(link_all=True, show_xlabel=True)
    plt.show(block=True)
