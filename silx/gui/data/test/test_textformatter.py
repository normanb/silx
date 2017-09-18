# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2017 European Synchrotron Radiation Facility
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
__authors__ = ["V. Valls"]
__license__ = "MIT"
__date__ = "18/09/2017"

import unittest
import shutil
import tempfile
import numpy

from silx.gui.test.utils import TestCaseQt
from silx.gui.test.utils import SignalListener
from ..TextFormatter import TextFormatter
from silx.third_party import six

try:
    import h5py
except ImportError:
    h5py = None


class TestTextFormatter(TestCaseQt):

    def test_copy(self):
        formatter = TextFormatter()
        copy = TextFormatter(formatter=formatter)
        self.assertIsNot(formatter, copy)
        copy.setFloatFormat("%.3f")
        self.assertEquals(formatter.integerFormat(), copy.integerFormat())
        self.assertNotEquals(formatter.floatFormat(), copy.floatFormat())
        self.assertEquals(formatter.useQuoteForText(), copy.useQuoteForText())
        self.assertEquals(formatter.imaginaryUnit(), copy.imaginaryUnit())

    def test_event(self):
        listener = SignalListener()
        formatter = TextFormatter()
        formatter.formatChanged.connect(listener)
        formatter.setFloatFormat("%.3f")
        formatter.setIntegerFormat("%03i")
        formatter.setUseQuoteForText(False)
        formatter.setImaginaryUnit("z")
        self.assertEquals(listener.callCount(), 4)

    def test_int(self):
        formatter = TextFormatter()
        formatter.setIntegerFormat("%05i")
        result = formatter.toString(512)
        self.assertEquals(result, "00512")

    def test_float(self):
        formatter = TextFormatter()
        formatter.setFloatFormat("%.3f")
        result = formatter.toString(1.3)
        self.assertEquals(result, "1.300")

    def test_complex(self):
        formatter = TextFormatter()
        formatter.setFloatFormat("%.1f")
        formatter.setImaginaryUnit("i")
        result = formatter.toString(1.0 + 5j)
        result = result.replace(" ", "")
        self.assertEquals(result, "1.0+5.0i")

    def test_string(self):
        formatter = TextFormatter()
        formatter.setIntegerFormat("%.1f")
        formatter.setImaginaryUnit("z")
        result = formatter.toString("toto")
        self.assertEquals(result, '"toto"')


class TestTextFormatterWithH5py(TestCaseQt):

    @classmethod
    def setUpClass(cls):
        super(TestTextFormatterWithH5py, cls).setUpClass()
        if h5py is None:
            raise unittest.SkipTest("h5py is not available")

        cls.tmpDirectory = tempfile.mkdtemp()
        cls.h5File = h5py.File("%s/formatter.h5" % cls.tmpDirectory, mode="w")
        cls.formatter = TextFormatter()

    @classmethod
    def tearDownClass(cls):
        super(TestTextFormatterWithH5py, cls).tearDownClass()
        cls.h5File.close()
        cls.h5File = None
        shutil.rmtree(cls.tmpDirectory)

    def create_dataset(self, data, dtype=None):
        testName = "%s" % self.id()
        dataset = self.h5File.create_dataset(testName, data=data, dtype=dtype)
        return dataset

    def testAscii(self):
        d = self.create_dataset(data=b"abc")
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, '"abc"')

    def testUnicode(self):
        d = self.create_dataset(data=u"i\u2661cookies")
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(len(result), 11)
        self.assertEquals(result, u'"i\u2661cookies"')

    def testBadAscii(self):
        d = self.create_dataset(data=b"\xF0\x9F\x92\x94")
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, 'ENCODING_ERROR:0xf09f9294')

    def testVoid(self):
        d = self.create_dataset(data=numpy.void(b"abc\xF0"))
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, '0x616263f0')

    def testEnum(self):
        dtype = h5py.special_dtype(enum=('i', {"RED": 0, "GREEN": 1, "BLUE": 42}))
        d = numpy.array(42, dtype=dtype)
        d = self.create_dataset(data=d)
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, 'BLUE(42)')

    def testRef(self):
        dtype = h5py.special_dtype(ref=h5py.Reference)
        d = numpy.array(self.h5File.ref, dtype=dtype)
        d = self.create_dataset(data=d)
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, 'REF')

    def testArrayAscii(self):
        d = self.create_dataset(data=[b"abc"])
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, '["abc"]')

    def testArrayUnicode(self):
        dtype = h5py.special_dtype(vlen=six.text_type)
        d = numpy.array([u"i\u2661cookies"], dtype=dtype)
        d = self.create_dataset(data=d)
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(len(result), 13)
        self.assertEquals(result, u'["i\u2661cookies"]')

    def testArrayBadAscii(self):
        d = self.create_dataset(data=[b"\xF0\x9F\x92\x94"])
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, '[ENCODING_ERROR:0xf09f9294]')

    def testArrayVoid(self):
        d = self.create_dataset(data=numpy.void([b"abc\xF0"]))
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, '[0x616263f0]')

    def testArrayEnum(self):
        dtype = h5py.special_dtype(enum=('i', {"RED": 0, "GREEN": 1, "BLUE": 42}))
        d = numpy.array([42, 1, 100], dtype=dtype)
        d = self.create_dataset(data=d)
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, '[BLUE(42) GREEN(1) 100]')

    def testArrayRef(self):
        dtype = h5py.special_dtype(ref=h5py.Reference)
        d = numpy.array([self.h5File.ref, None], dtype=dtype)
        d = self.create_dataset(data=d)
        result = self.formatter.toString(d[()], dtype=d.dtype)
        self.assertEquals(result, '[REF NULL_REF]')


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    test_suite = unittest.TestSuite()
    test_suite.addTest(loadTests(TestTextFormatter))
    test_suite.addTest(loadTests(TestTextFormatterWithH5py))
    return test_suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
