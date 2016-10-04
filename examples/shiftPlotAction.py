# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2004-2016 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""This script is a simple (trivial) example of how to create a PlotWindow,
create a custom :class:`PlotAction` and add it to the toolbar.

The action simply shifts the selected curve up by 1 unit by adding 1 to each
value of y.
"""

__authors__ = ["P. Knobel"]
__license__ = "MIT"
__date__ = "20/09/2016"

from silx.gui import qt
from silx.gui.plot import PlotWindow
from silx.gui.plot.PlotActions import PlotAction


class ShiftUpAction(PlotAction):
    """QAction shifting up a curve by one unit

    :param plot: :class:`.PlotWidget` instance on which to operate
    :param parent: See :class:`QAction`
    """
    def __init__(self, plot, parent=None):
        PlotAction.__init__(self,
                            plot,
                            icon='shape-circle',
                            text='Shift up',
                            tooltip='Shift active curve up by one unit',
                            triggered=self.shiftActiveCurveUp,
                            parent=parent)

    def shiftActiveCurveUp(self):
        """Get the active curve, add 1 to all y values, use this new y
        array to replace the original curve"""
        # By inheriting from PlotAction, we get access to attribute self.plot
        # which is a reference to the PlotWindow
        activeCurve = self.plot.getActiveCurve()

        if activeCurve is not None:
            # Unpack curve data.
            # Each curve is represented by a tuple of 5 variables:
            #  - x and y are the array of abscissa and ordinate values
            #  - legend is a unique text identifying a curve
            #  - info and params are dictionaries of additional data
            #    (user defined, curve style and color...)
            x0, y0, legend, info, params = activeCurve

            # Add 1 to all values in the y array
            # and assign the result to a new array y1
            # (do not modify y0 if you want to preserve the original curve)
            y1 = y0 + 1.0

            # Re-using the same legend causes the original curve
            # to be replaced
            self.plot.addCurve(x0, y1, legend=legend,
                               info=info)


# creating QApplication is mandatory in order to use qt widget
app = qt.QApplication([])

# create a PlotWindow
plotwin = PlotWindow()
# Add a new toolbar
toolbar = qt.QToolBar("My toolbar")
plotwin.addToolBar(toolbar)
# Get a reference to the PlotWindow's menu bar, add a menu
menubar = plotwin.menuBar()
actions_menu = menubar.addMenu("Custom actions")

# Initialize our action, give it plotwin as a parameter
myaction = ShiftUpAction(plotwin)
# Add action to the menubar and toolbar
toolbar.addAction(myaction)
actions_menu.addAction(myaction)

# Plot a couple of curves with synthetic data
x = [0, 1, 2, 3, 4, 5, 6]
y1 = [0, 1, 0, 1, 0, 1, 0]
y2 = [0, 1, 2, 3, 4, 5, 6]
plotwin.addCurve(x, y1, legend="triangle shaped curve")
plotwin.addCurve(x, y2, legend="oblique line")

plotwin.show()
app.exec_()
