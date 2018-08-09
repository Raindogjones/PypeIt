# Module to run tests on PypeItPar classes
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import numpy

import pytest

from pypeit.spectrographs.opticalmodel import DetectorMap
from pypeit.spectrographs.keck_deimos import DEIMOSCameraDistortion, KeckDEIMOSSpectrograph

# These tests are not run on Travis
if os.getenv('PYPEIT_DEV') is None:
    skip_test=True
else:
    skip_test=False

def test_detectormap():
    d = DetectorMap()
    xpix = numpy.array([[24,20],[24,20]])
    ypix = numpy.array([[1000,996],[1000,996]])
    ximg, yimg = d.image_coordinates(xpix, ypix)
    assert ximg.shape == yimg.shape, 'Did not return correct shape.'
    det, _xpix, _ypix = d.ccd_coordinates(ximg, yimg)
    assert numpy.all(numpy.isclose(_xpix, xpix) & numpy.isclose(_ypix, ypix)), 'I/O mismatch'

def test_deimos_distortion():
    c = DEIMOSCameraDistortion()
    assert abs(c.apply_distortion(c.remove_distortion(0.5)) - 0.5) < 1e-5, \
        'Failed distortion recovery'

def test_deimos_mask_coordinates():
    if skip_test:
        return
    f = os.path.join(os.environ['PYPEIT_DEV'], 'RAW_DATA', 'Keck_DEIMOS', '830G_M',
                     'DE.20100913.22358.fits.gz')
    spec = KeckDEIMOSSpectrograph()
    spec.get_grating(f)
    assert numpy.isclose(spec.grating.central_wave, 8500.0078125), 'Incorrect grating setup'
    # Get the chip and pixel coordinates (1-indexed!) at the central
    # wavelength
    ccd, xpix, ypix = spec.mask_to_pixel_coordinates(x=-127.15775, y=20.0565)
    assert ccd == 6, 'Incorrect chip selected'
    assert numpy.isclose(xpix, 528.54329982), 'Incorrect x coordinate'
    assert numpy.isclose(ypix, 487.64455754), 'Incorrect y coordinate'

