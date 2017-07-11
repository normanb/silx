# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2017 European Synchrotron Radiation Facility
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
"""This module provides the class for axes of the :class:`Plot`.
"""

__authors__ = ["V. Valls"]
__license__ = "MIT"
__date__ = "27/06/2017"

import logging
from ... import qt

_logger = logging.getLogger(__name__)


class Axis(qt.QObject):
    """This class describes and controls a plot axis.

    Note: This is an abstract class.
    """
    # States are half-stored on the backend of the plot, and half-stored on this
    # object.
    # TODO It would be good to store all the states of an axis in this object.
    #      i.e. vmin and vmax

    LINEAR = "linear"
    """Constant defining a linear scale"""

    LOGARITHMIC = "log"
    """Constant defining a logarithmic scale"""

    _SCALES = set([LINEAR, LOGARITHMIC])

    sigInvertedChanged = qt.Signal(bool)
    """Signal emitted when axis orientation has changed"""

    sigScaleChanged = qt.Signal(str)
    """Signal emitted when axis scale has changed"""

    _sigLogarithmicChanged = qt.Signal(bool)
    """Signal emitted when axis scale has changed to or from logarithmic"""

    sigAutoScaleChanged = qt.Signal(bool)
    """Signal emitted when axis autoscale has changed"""

    sigLimitsChanged = qt.Signal(float, float)
    """Signal emitted when axis autoscale has changed"""

    def __init__(self, plot):
        """Constructor

        :param silx.gui.plot.PlotWidget.PlotWidget plot: Parent plot of this
            axis
        """
        qt.QObject.__init__(self, parent=plot)
        self._scale = self.LINEAR
        self._isAutoScale = True
        # Store default labels provided to setGraph[X|Y]Label
        self._defaultLabel = ''
        # Store currently displayed labels
        # Current label can differ from input one with active curve handling
        self._currentLabel = ''
        self._plot = plot

    def getLimits(self):
        """Get the limits of this axis.

        :return: Minimum and maximum values of this axis as tuple
        """
        return self._internalGetLimits()

    def setLimits(self, vmin, vmax):
        """Set this axis limits.

        :param float vmin: minimum axis value
        :param float vmax: maximum axis value
        """
        vmin, vmax = self._checkLimits(vmin, vmax)

        self._internalSetLimits(vmin, vmax)
        self._plot._setDirtyPlot()

        self.sigLimitsChanged.emit(vmin, vmax)
        self._plot._notifyLimitsChanged(emitSignal=False)

    def _checkLimits(self, vmin, vmax):
        """Makes sure axis range is not empty

        :param float vmin: Min axis value
        :param float vmax: Max axis value
        :return: (min, max) making sure min < max
        :rtype: 2-tuple of float
        """
        if vmax < vmin:
            _logger.debug('%s axis: max < min, inverting limits.', self._defaultLabel)
            vmin, vmax = vmax, vmin
        elif vmax == vmin:
            _logger.debug('%s axis: max == min, expanding limits.', self._defaultLabel)
            if vmin == 0.:
                vmin, vmax = -0.1, 0.1
            elif vmin < 0:
                vmin, vmax = vmin * 1.1, vmin * 0.9
            else:  # xmin > 0
                vmin, vmax = vmin * 0.9, vmin * 1.1

        return vmin, vmax

    def isInverted(self):
        """Return True if the axis is inverted (top to bottom for the y-axis),
        False otherwise. It is always False for the X axis.

        :rtype: bool
        """
        return False

    def setInverted(self, isInverted):
        """Set the axis orientation.

        This is only available for the Y axis.

        :param bool flag: True for Y axis going from top to bottom,
                          False for Y axis going from bottom to top
        """
        raise NotImplementedError()

    def getLabel(self):
        """Return the current displayed label of this axis.

        :param str axis: The Y axis for which to get the label (left or right)
        :rtype: str
        """
        return self._currentLabel

    def setLabel(self, label):
        """Set the label displayed on the plot for this axis.

        The provided label can be temporarily replaced by the label of the
        active curve if any.

        :param str label: The axis label
        """
        self._defaultLabel = label
        self._setCurrentLabel(label)
        self._plot._setDirtyPlot()

    def _setCurrentLabel(self, label):
        """Define the label currently displayed.

        If the label is None or empty the default label is used.

        :param str label: Currently displayed label
        """
        if label is None or label == '':
            label = self._defaultLabel
        if label is None:
            label = ''
        self._currentLabel = label
        self._internalSetCurrentLabel(label)

    def getScale(self):
        """Return the name of the scale used by this axis.

        :rtype: str
        """
        return self._scale

    def setScale(self, scale):
        """Set the scale to be used by this axis.

        :param str scale: Name of the scale ("log", or "linear")
        """
        assert(scale in self._SCALES)
        if self._scale == scale:
            return

        # For the backward compatibility signal
        emitLog = self._scale == self.LOGARITHMIC or scale == self.LOGARITHMIC

        if scale == self.LOGARITHMIC:
            self._internalSetLogarithmic(True)
        elif scale == self.LINEAR:
            self._internalSetLogarithmic(False)
        else:
            raise ValueError("Scale %s unsupported" % scale)

        self._scale = scale

        # TODO hackish way of forcing update of curves and images
        for item in self._plot._getItems(withhidden=True):
            item._updated()
        self._plot._invalidateDataRange()
        self._plot.resetZoom()

        self.sigScaleChanged.emit(self._scale)
        if emitLog:
            self._sigLogarithmicChanged.emit(self._scale == self.LOGARITHMIC)

    def _isLogarithmic(self):
        """Return True if this axis scale is logarithmic, False if linear.

        :rtype: bool
        """
        return self._scale == self.LOGARITHMIC

    def _setLogarithmic(self, flag):
        """Set the scale of this axes (either linear or logarithmic).

        :param bool flag: True to use a logarithmic scale, False for linear.
        """
        flag = bool(flag)
        self.setScale(self.LOGARITHMIC if flag else self.LINEAR)

    def isAutoScale(self):
        """Return True if axis is automatically adjusting its limits.

        :rtype: bool
        """
        return self._isAutoScale

    def setAutoScale(self, flag=True):
        """Set the axis limits adjusting behavior of :meth:`resetZoom`.

        :param bool flag: True to resize limits automatically,
                          False to disable it.
        """
        self._isAutoScale = bool(flag)
        self.sigAutoScaleChanged.emit(self._isAutoScale)


class XAxis(Axis):
    """Axis class defining primitives for the X axis"""

    # TODO With some changes on the backend, it will be able to remove all this
    #      specialised implementations (prefixel by '_internal')

    def _internalSetCurrentLabel(self, label):
        self._plot._backend.setGraphXLabel(label)

    def _internalGetLimits(self):
        return self._plot._backend.getGraphXLimits()

    def _internalSetLimits(self, xmin, xmax):
        self._plot._backend.setGraphXLimits(xmin, xmax)

    def _internalSetLogarithmic(self, flag):
        self._plot._backend.setXAxisLogarithmic(flag)


class YAxis(Axis):
    """Axis class defining primitives for the Y axis"""

    # TODO With some changes on the backend, it will be able to remove all this
    #      specialised implementations (prefixel by '_internal')

    def _internalSetCurrentLabel(self, label):
        self._plot._backend.setGraphYLabel(label, axis='left')

    def _internalGetLimits(self):
        return self._plot._backend.getGraphYLimits(axis='left')

    def _internalSetLimits(self, ymin, ymax):
        self._plot._backend.setGraphYLimits(ymin, ymax, axis='left')

    def _internalSetLogarithmic(self, flag):
        self._plot._backend.setYAxisLogarithmic(flag)

    def setInverted(self, flag=True):
        """Set the axis orientation.

        This is only available for the Y axis.

        :param bool flag: True for Y axis going from top to bottom,
                          False for Y axis going from bottom to top
        """
        flag = bool(flag)
        self._plot._backend.setYAxisInverted(flag)
        self._plot._setDirtyPlot()
        self.sigInvertedChanged.emit(flag)

    def isInverted(self):
        """Return True if the axis is inverted (top to bottom for the y-axis),
        False otherwise. It is always False for the X axis.

        :rtype: bool
        """
        return self._plot._backend.isYAxisInverted()


class YRightAxis(Axis):
    """Proxy axis for the secondary Y axes. It manages it own label and limit
    but share the some state like scale and direction with the main axis."""

    # TODO With some changes on the backend, it will be able to remove all this
    #      specialised implementations (prefixel by '_internal')

    def __init__(self, plot, mainAxis):
        """Constructor

        :param silx.gui.plot.PlotWidget.PlotWidget plot: Parent plot of this
            axis
        :param Axis mainAxis: Axis which sharing state with this axis
        """
        Axis.__init__(self, plot)
        self.__mainAxis = mainAxis

    @property
    def sigInvertedChanged(self):
        """Signal emitted when axis orientation has changed"""
        return self.__mainAxis.sigInvertedChanged

    @property
    def sigScaleChanged(self):
        """Signal emitted when axis scale has changed"""
        return self.__mainAxis.sigScaleChanged

    @property
    def _sigLogarithmicChanged(self):
        """Signal emitted when axis scale has changed to or from logarithmic"""
        return self.__mainAxis._sigLogarithmicChanged

    @property
    def sigAutoScaleChanged(self):
        """Signal emitted when axis autoscale has changed"""
        return self.__mainAxis.sigAutoScaleChanged

    def _internalSetCurrentLabel(self, label):
        self._plot._backend.setGraphYLabel(label, axis='right')

    def _internalGetLimits(self):
        return self._plot._backend.getGraphYLimits(axis='right')

    def _internalSetLimits(self, ymin, ymax):
        self._plot._backend.setGraphYLimits(ymin, ymax, axis='right')

    def setInverted(self, flag=True):
        """Set the Y axis orientation.

        :param bool flag: True for Y axis going from top to bottom,
                          False for Y axis going from bottom to top
        """
        return self.__mainAxis.setInverted(flag)

    def isInverted(self):
        """Return True if Y axis goes from top to bottom, False otherwise."""
        return self.__mainAxis.isInverted()

    def getScale(self):
        """Return the name of the scale used by this axis.

        :rtype: str
        """
        return self.__mainAxis.getScale()

    def setScale(self, scale):
        """Set the scale to be used by this axis.

        :param str scale: Name of the scale ("log", or "linear")
        """
        self.__mainAxis.setScale(scale)

    def _isLogarithmic(self):
        """Return True if Y axis scale is logarithmic, False if linear."""
        return self.__mainAxis._isLogarithmic()

    def _setLogarithmic(self, flag):
        """Set the Y axes scale (either linear or logarithmic).

        :param bool flag: True to use a logarithmic scale, False for linear.
        """
        return self.__mainAxis._setLogarithmic(flag)

    def isAutoScale(self):
        """Return True if Y axes are automatically adjusting its limits."""
        return self.__mainAxis.isAutoScale()

    def setAutoScale(self, flag=True):
        """Set the Y axis limits adjusting behavior of :meth:`resetZoom`.

        :param bool flag: True to resize limits automatically,
                          False to disable it.
        """
        return self.__mainAxis.setAutoScale(flag)
