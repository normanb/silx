# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2004-2018 European Synchrotron Radiation Facility
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
"""Widget displaying a symbol (marker symbol, line style and color) to identify
an item displayed by a plot.
"""

__authors__ = ["V.A. Sole", "T. Rueter", "T. Vincent"]
__license__ = "MIT"
__data__ = "11/11/2019"


import logging

import numpy

from .. import qt, colors


_logger = logging.getLogger(__name__)


# Build all symbols
# Courtesy of the pyqtgraph project

_Symbols = dict([(name, qt.QPainterPath())
                for name in ['o', 's', 't', 'd', '+', 'x', '.', ',']])
_Symbols['o'].addEllipse(qt.QRectF(.1, .1, .8, .8))
_Symbols['.'].addEllipse(qt.QRectF(.3, .3, .4, .4))
_Symbols[','].addEllipse(qt.QRectF(.4, .4, .2, .2))
_Symbols['s'].addRect(qt.QRectF(.1, .1, .8, .8))

coords = {
    't': [(0.5, 0.), (.1, .8), (.9, .8)],
    'd': [(0.1, 0.5), (0.5, 0.), (0.9, 0.5), (0.5, 1.)],
    '+': [(0.0, 0.40), (0.40, 0.40), (0.40, 0.), (0.60, 0.),
          (0.60, 0.40), (1., 0.40), (1., 0.60), (0.60, 0.60),
          (0.60, 1.), (0.40, 1.), (0.40, 0.60), (0., 0.60)],
    'x': [(0.0, 0.40), (0.40, 0.40), (0.40, 0.), (0.60, 0.),
          (0.60, 0.40), (1., 0.40), (1., 0.60), (0.60, 0.60),
          (0.60, 1.), (0.40, 1.), (0.40, 0.60), (0., 0.60)]
}
for s, c in coords.items():
    _Symbols[s].moveTo(*c[0])
    for x, y in c[1:]:
        _Symbols[s].lineTo(x, y)
    _Symbols[s].closeSubpath()
tr = qt.QTransform()
tr.rotate(45)
_Symbols['x'].translate(qt.QPointF(-0.5, -0.5))
_Symbols['x'] = tr.map(_Symbols['x'])
_Symbols['x'].translate(qt.QPointF(0.5, 0.5))

_NoSymbols = (None, 'None', 'none', '', ' ')
"""List of values resulting in no symbol being displayed for a curve"""


_LineStyles = {
    None: qt.Qt.NoPen,
    'None': qt.Qt.NoPen,
    'none': qt.Qt.NoPen,
    '': qt.Qt.NoPen,
    ' ': qt.Qt.NoPen,
    '-': qt.Qt.SolidLine,
    '--': qt.Qt.DashLine,
    ':': qt.Qt.DotLine,
    '-.': qt.Qt.DashDotLine
}
"""Conversion from matplotlib-like linestyle to Qt"""

_NoLineStyle = (None, 'None', 'none', '', ' ')
"""List of style values resulting in no line being displayed for a curve"""


_colormapImage = {}
"""Store cached pixmap"""
# FIXME: Could be better to use a LRU dictionary

_COLORMAP_PIXMAP_SIZE = 32
"""Size of the cached pixmaps for the colormaps"""


class LegendIconWidget(qt.QWidget):
    """Object displaying linestyle and symbol of plots.

    :param QWidget parent: See :class:`QWidget`
    """

    def __init__(self, parent=None):
        super(LegendIconWidget, self).__init__(parent)

        # Visibilities
        self.showLine = True
        self.showSymbol = True
        self.showColormap = True

        # Line attributes
        self.lineStyle = qt.Qt.NoPen
        self.lineWidth = 1.
        self.lineColor = qt.Qt.green

        self.symbol = ''
        # Symbol attributes
        self.symbolStyle = qt.Qt.SolidPattern
        self.symbolColor = qt.Qt.green
        self.symbolOutlineBrush = qt.QBrush(qt.Qt.white)

        self.colormap = None
        """Name or array of colors"""

        # Control widget size: sizeHint "is the only acceptable
        # alternative, so the widget can never grow or shrink"
        # (c.f. Qt Doc, enum QSizePolicy::Policy)
        self.setSizePolicy(qt.QSizePolicy.Fixed,
                           qt.QSizePolicy.Fixed)

    def sizeHint(self):
        return qt.QSize(50, 15)

    def setSymbol(self, symbol):
        """Set the symbol"""
        symbol = str(symbol)
        if symbol not in _NoSymbols:
            if symbol not in _Symbols:
                raise ValueError("Unknown symbol: <%s>" % symbol)
        self.symbol = symbol
        # self.update() after set...?
        # Does not seem necessary

    def setSymbolColor(self, color):
        """
        :param color: determines the symbol color
        :type style: qt.QColor
        """
        self.symbolColor = qt.QColor(color)

    # Modify Line

    def setLineColor(self, color):
        self.lineColor = qt.QColor(color)

    def setLineWidth(self, width):
        self.lineWidth = float(width)

    def setLineStyle(self, style):
        """Set the linestyle.

        Possible line styles:

        - '', ' ', 'None': No line
        - '-': solid
        - '--': dashed
        - ':': dotted
        - '-.': dash and dot

        :param str style: The linestyle to use
        """
        if style not in _LineStyles:
            raise ValueError('Unknown style: %s', style)
        self.lineStyle = _LineStyles[style]

    def setColormap(self, colormap):
        """Set the colormap to display

        If the argument is a `Colormap` object, only the current state will be
        displayed. The object itself will not be stored, and further changes
        of this `Colormap` will not update this widget.

        :param Union[str,numpy.ndarray,Colormap] colormap: The colormap to
            display
        """
        if isinstance(colormap, colors.Colormap):
            # Helper to allow to support Colormap objects
            c = colormap.getName()
            if c is None:
                c = colormap.getNColors()
            colormap = c

        if colormap is None:
            self.colormap = None
            return

        if numpy.array_equal(self.colormap, colormap):
            # This also works with strings
            return

        self.colormap = colormap
        if isinstance(colormap, numpy.ndarray):
            name = None
            colorArray = colormap
        else:
            name = colormap
            colorArray = None

    def getColormap(self):
        """Returns the used colormap.

        If the argument was set with a `Colormap` object, this function will
        returns the LUT, represented by a string name or by an array or colors.

        :returns: Union[None,str,numpy.ndarray,Colormap]
        """
        return self.colormap

    # Paint

    def paintEvent(self, event):
        """
        :param event: event
        :type event: QPaintEvent
        """
        painter = qt.QPainter(self)
        self.paint(painter, event.rect(), self.palette())

    def paint(self, painter, rect, palette):
        painter.save()
        painter.setRenderHint(qt.QPainter.Antialiasing)
        # Scale painter to the icon height
        # current -> width = 2.5, height = 1.0
        scale = float(self.height())
        ratio = float(self.width()) / scale
        symbolOffset = qt.QPointF(.5 * (ratio - 1.), 0.)
        # Determine and scale offset
        offset = qt.QPointF(float(rect.left()) / scale, float(rect.top()) / scale)

        # Override color when disabled
        if self.isEnabled():
            overrideColor = None
        else:
            overrideColor = palette.color(qt.QPalette.Disabled,
                                          qt.QPalette.WindowText)

        # Draw BG rectangle (for debugging)
        # bottomRight = qt.QPointF(
        #    float(rect.right())/scale,
        #    float(rect.bottom())/scale)
        # painter.fillRect(qt.QRectF(offset, bottomRight),
        #                 qt.QBrush(qt.Qt.green))

        isSymbol = (self.showSymbol and
                    len(self.symbol) and
                    self.symbol not in _NoSymbols)
        isColormap = self.colormap is not None
        isSymbolColormap = isSymbol and isColormap
        if isSymbolColormap:
            isSymbol = False
            isColormap = False

        if self.showColormap:
            if isColormap:
                if self.isEnabled():
                    image = self.getColormapImage(self.colormap)
                else:
                    image = self.getGrayedColormapImage(self.colormap)
                pixmapRect = qt.QRect(0, 0, _COLORMAP_PIXMAP_SIZE, 1)
                widthMargin = 0
                halfHeight = 4
                dest = qt.QRect(
                    rect.left() + widthMargin,
                    rect.center().y() - halfHeight + 1,
                    rect.width() - widthMargin * 2,
                    halfHeight * 2,
                )
                painter.drawImage(dest, image, pixmapRect)

        painter.scale(scale, scale)

        llist = []
        if self.showLine:
            linePath = qt.QPainterPath()
            linePath.moveTo(0., 0.5)
            linePath.lineTo(ratio, 0.5)
            # linePath.lineTo(2.5, 0.5)
            lineBrush = qt.QBrush(
                self.lineColor if overrideColor is None else overrideColor)
            linePen = qt.QPen(
                lineBrush,
                (self.lineWidth / self.height()),
                self.lineStyle,
                qt.Qt.FlatCap
            )
            llist.append((linePath, linePen, lineBrush))
        if isSymbol:
            # PITFALL ahead: Let this be a warning to others
            # symbolPath = Symbols[self.symbol]
            # Copy before translate! Dict is a mutable type
            symbolPath = qt.QPainterPath(_Symbols[self.symbol])
            symbolPath.translate(symbolOffset)
            symbolBrush = qt.QBrush(
                self.symbolColor if overrideColor is None else overrideColor,
                self.symbolStyle)
            symbolPen = qt.QPen(
                self.symbolOutlineBrush,  # Brush
                1. / self.height(),       # Width
                qt.Qt.SolidLine           # Style
            )
            llist.append((symbolPath,
                          symbolPen,
                          symbolBrush))

        if isSymbolColormap:
            nbSymbols = int(ratio + 2)
            for i in range(nbSymbols):
                if self.isEnabled():
                    image = self.getColormapImage(self.colormap)
                else:
                    image = self.getGrayedColormapImage(self.colormap)
                pos = int((_COLORMAP_PIXMAP_SIZE / nbSymbols) * i)
                pos = numpy.clip(pos, 0, _COLORMAP_PIXMAP_SIZE-1)
                color = image.pixelColor(pos, 0)
                delta = qt.QPointF(ratio * ((i - (nbSymbols-1)/2) / nbSymbols), 0)

                symbolPath = qt.QPainterPath(_Symbols[self.symbol])
                symbolPath.translate(symbolOffset + delta)
                symbolBrush = qt.QBrush(color, self.symbolStyle)
                symbolPen = qt.QPen(
                    self.symbolOutlineBrush,  # Brush
                    1. / self.height(),       # Width
                    qt.Qt.SolidLine           # Style
                )
                llist.append((symbolPath,
                              symbolPen,
                              symbolBrush))

        # Draw
        for path, pen, brush in llist:
            path.translate(offset)
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawPath(path)

        painter.restore()

    # Helpers

    @staticmethod
    def isEmptySymbol(symbol):
        """Returns True if this symbol description will result in an empty
        symbol."""
        return symbol in _NoSymbols

    @staticmethod
    def isEmptyLineStyle(lineStyle):
        """Returns True if this line style description will result in an empty
        line."""
        return lineStyle in _NoLineStyle

    @staticmethod
    def _getColormapKey(colormap):
        """
        Returns the key used to store the image in the data storage
        """
        if isinstance(colormap, numpy.ndarray):
            key = tuple(colormap)
        else:
            key = colormap
        return key

    @staticmethod
    def getGrayedColormapImage(colormap):
        """Return a grayed version image preview from a LUT name.

        This images are cached into a global structure.

        :param Union[str,numpy.ndarray] colormap: Description of the LUT
        :rtype: qt.QImage
        """
        key = LegendIconWidget._getColormapKey(colormap)
        grayKey = (key, "gray")
        image = _colormapImage.get(grayKey, None)
        if image is None:
            image = LegendIconWidget.getColormapImage(colormap)
            image = image.convertToFormat(qt.QImage.Format_Grayscale8)
            _colormapImage[grayKey] = image
        return image

    @staticmethod
    def getColormapImage(colormap):
        """Return an image preview from a LUT name.

        This images are cached into a global structure.

        :param Union[str,numpy.ndarray] colormap: Description of the LUT
        :rtype: qt.QImage
        """
        key = LegendIconWidget._getColormapKey(colormap)
        image = _colormapImage.get(key, None)
        if image is None:
            image = LegendIconWidget.createColormapImage(colormap)
            _colormapImage[key] = image
        return image

    @staticmethod
    def createColormapImage(colormap):
        """Create and return an icon preview from a LUT name.

        This icons are cached into a global structure.

        :param Union[str,numpy.ndarray] colormap: Description of the LUT
        :rtype: qt.QImage
        """
        size = _COLORMAP_PIXMAP_SIZE
        if isinstance(colormap, numpy.ndarray):
            lut = colormap
            if len(lut) > size:
                # Down sample
                step = int(len(lut) / size)
                lut = lut[::step]
            elif len(lut) < size:
                # Over sample
                indexes = numpy.arange(size) / float(size) * (len(lut) - 1)
                indexes = indexes.astype("int")
                lut = lut[indexes]
        else:
            colormap = colors.Colormap(colormap)
            lut = colormap.getNColors(size)

        if lut is None or len(lut) == 0:
            return qt.QIcon()

        pixmap = qt.QPixmap(size, 1)
        painter = qt.QPainter(pixmap)
        for i in range(size):
            rgb = lut[i]
            r, g, b = rgb[0], rgb[1], rgb[2]
            painter.setPen(qt.QColor(r, g, b))
            painter.drawPoint(qt.QPoint(i, 0))
        painter.end()
        return pixmap.toImage()
