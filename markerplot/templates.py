import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes._axes import Axes
from matplotlib.axes._subplots import SubplotBase
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
from datetime import datetime
from matplotlib.figure import Figure
import sys
import tkinter
from tkinter import *
import matplotlib

def smithcircles(values, npoints = 5001):
    np.seterr(divide='ignore', invalid='ignore')
    values = np.array(values)
    lines =  [Line2D([0]*npoints,[np.nan]*npoints) for i in range(4)]
    xdat = np.linspace(0, 2*np.pi, npoints, endpoint=True)
    xcenter = np.zeros((4, len(values)))
    ycenter = np.zeros((4, len(values)))
    radius  = np.zeros((4, len(values)))

    #real z lines
    lines[0].set_alpha(0.2)
    lines[0].set_color("gray")
    lines[0].set_data(np.array([np.nan]), np.array([np.nan]))
    xcenter[0] = values/(1+values)
    ycenter[0] = [0]*len(values)
    radius[0] = 1/(1+values)

    #reactive z lines
    lines[1].set_alpha(0.2)
    lines[1].set_color("gray")
    lines[1].set_data(np.array([np.nan]), np.array([np.nan]))
    xcenter[1] = [1]*len(values)
    ycenter[1] = 1/values
    radius[1] = 1/values

    #real y lines
    lines[2].set_alpha(0.1)
    lines[2].set_color("red")
    lines[2].set_data(np.array([np.nan]), np.array([np.nan]))
    xcenter[2] = -(values/(1+values))
    ycenter[2] = 0
    radius[2] = 1/(1+values)

    #reactive y lines
    lines[3].set_alpha(0.1)
    lines[3].set_color("red")
    lines[3].set_data(np.array([np.nan]), np.array([np.nan]))
    xcenter[3] = -1
    ycenter[3] = -1/values
    radius[3] = 1/values

    #generate lines
    for i in range(4):
        for v in range(len(values)):
            ydat = radius[i,v]*np.exp(1j*xdat)
            yreal = np.real(ydat)+xcenter[i,v]
            yimag = np.imag(ydat)+ycenter[i,v]
            yimag2 = np.imag(ydat)-ycenter[i,v]

            for j in range(len(yimag)):
                if yimag[j]**2+yreal[j]**2 > 1:
                    yimag[j]=np.nan
                if yimag2[j]**2+yreal[j]**2 > 1:
                    yimag2[j]=np.nan

            if (i == 1 or i == 3):
                lines[i].set_xdata(np.concatenate((lines[i].get_xdata(), [np.nan], yreal, [np.nan], yreal)))
                lines[i].set_ydata(np.concatenate((lines[i].get_ydata(), [np.nan], yimag, [np.nan], yimag2)))
            else:
                lines[i].set_xdata(np.concatenate((lines[i].get_xdata(), [np.nan], yreal)))
                lines[i].set_ydata(np.concatenate((lines[i].get_ydata(), [np.nan], yimag)))

    np.seterr(divide='warn', invalid='warn')
    return lines

def format_smithchart(axes, lines=None, admittance=False):
    if lines == None:
        lines = [2, 1, 0.5, 0.2, 0]

    plt.sca(axes)
    axes.set_aspect('equal')
    axes.spines['right'].set_color('none')
    axes.spines['top'].set_color('none')
    axes.xaxis.set_ticks_position('bottom')
    axes.spines['bottom'].set_position(('data',0))
    axes.yaxis.set_ticks_position('left')
    axes.spines['left'].set_position(('data',0))
    axes.set_ylim(-1, 1)
    axes.set_xlim(-1, 1)
    lines = smithcircles(lines) 
    plt.xticks([],fontsize=7)
    plt.yticks([], fontsize=7)
    axes.set_title('', fontsize=7)
    #plt.tight_layout()
    axes.add_line(lines[0])
    axes.add_line(lines[1])
    axes.marker_ignorelines.append(lines[0])
    axes.marker_ignorelines.append(lines[1])
    if admittance:
        axes.add_line(lines[2])
        axes.add_line(lines[3])
        axes.marker_ignorelines.append(lines[2])
        axes.marker_ignorelines.append(lines[3])
    return axes
