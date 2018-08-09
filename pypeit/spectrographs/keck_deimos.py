'''
Implements DEIMOS-specific functions, including reading in slitmask design files.
'''
from __future__ import absolute_import, division, print_function

import glob
import re
import numpy as np

from scipy import interpolate

from astropy.io import fits

from pypeit import msgs
from pypeit.core import parse
from pypeit.par.pypeitpar import DetectorPar
from pypeit.spectrographs import spectrograph
from pypeit import telescopes
from pypeit.core import fsort
from pypeit.par import pypeitpar

from pypeit.spectrographs.slitmask import SlitMask
from pypeit.spectrographs.opticalmodel import ReflectionGrating, OpticalModel, DetectorMap

from pypeit import debugger

class KeckDEIMOSSpectrograph(spectrograph.Spectrograph):
    """
    Child to handle Keck/DEIMOS specific code
    """
    def __init__(self):
        # Get it started
        super(KeckDEIMOSSpectrograph, self).__init__()
        self.spectrograph = 'keck_deimos'
        self.telescope = telescopes.KeckTelescopePar()
        self.camera = 'DEIMOS'
        self.detector = [
                # Detector 1
                DetectorPar(dataext         = 1,
                            dispaxis        = 0,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            platescale      = 0.1185,
                            darkcurr        = 4.19,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 1.226,
                            ronoise         = 2.570,
                            datasec         = '',       # These are provided by read_deimos
                            oscansec        = '',
                            suffix          = '_01'

                            ),
                # Detector 2
                DetectorPar(dataext         = 2,
                            dispaxis        = 0,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            platescale      = 0.1185,
                            darkcurr        = 3.46,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 1.188,
                            ronoise         = 2.491,
                            datasec         = '',       # These are provided by read_deimos
                            oscansec        = '',
                            suffix          = '_02'
                            ),
                # Detector 3
                DetectorPar(dataext         = 3,
                            dispaxis        = 0,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            platescale      = 0.1185,
                            darkcurr        = 4.03,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 1.248,
                            ronoise         = 2.618,
                            datasec         = '',       # These are provided by read_deimos
                            oscansec        = '',
                            suffix          = '_03'
                            ),
                # Detector 4
                DetectorPar(dataext         = 4,
                            dispaxis        = 0,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            platescale      = 0.1185,
                            darkcurr        = 3.80,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 1.220,
                            ronoise         = 2.557,
                            datasec         = '',       # These are provided by read_deimos
                            oscansec        = '',
                            suffix          = '_04'
                            ),
                # Detector 5
                DetectorPar(dataext         = 5,
                            dispaxis        = 0,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            platescale      = 0.1185,
                            darkcurr        = 4.71,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 1.184,
                            ronoise         = 2.482,
                            datasec         = '',       # These are provided by read_deimos
                            oscansec        = '',
                            suffix          = '_05'
                            ),
                # Detector 6
                DetectorPar(dataext         = 6,
                            dispaxis        = 0,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            platescale      = 0.1185,
                            darkcurr        = 4.28,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 1.177,
                            ronoise         = 2.469,
                            datasec         = '',       # These are provided by read_deimos
                            oscansec        = '',
                            suffix          = '_06'
                            ),
                # Detector 7
                DetectorPar(dataext         = 7,
                            dispaxis        = 0,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            platescale      = 0.1185,
                            darkcurr        = 3.33,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 1.201,
                            ronoise         = 2.518,
                            datasec         = '',       # These are provided by read_deimos
                            oscansec        = '',
                            suffix          = '_07'),
                # Detector 8
                DetectorPar(dataext         = 8,
                            dispaxis        = 0,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1., 
                            platescale      = 0.1185,
                            darkcurr        = 3.69,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 1.230,
                            ronoise         = 2.580,
                            datasec         = '',       # These are provided by read_deimos
                            oscansec        = '',
                            suffix          = '_08'
                            )
            ]
        self.numhead = 9
        # Uses default timeunit
        # Uses default primary_hdrext
        # self.sky_file ?

        # Don't instantiate these until they're needed
        self.slitmask = None
        self.grating = None
        self.optical_model = None
        self.detector_map = None

    @staticmethod
    def default_pypeit_par():
        """
        Set default parameters for Keck LRISb reductions.
        """
        par = pypeitpar.PypeItPar()
        par['rdx']['spectrograph'] = 'keck_deimos'

        # Use the ARMS pipeline
        par['rdx']['pipeline'] = 'ARMS'

        # Set wave tilts order
        par['calibrations']['slits']['sigdetect'] = 50.
        par['calibrations']['slits']['polyorder'] = 3
        par['calibrations']['slits']['fracignore'] = 0.02
        par['calibrations']['slits']['pcapar'] = [3,2,1,0]

        # Overscan subtract the images
        par['calibrations']['biasframe']['useframe'] = 'overscan'

        # Alter the method used to combine pixel flats
        par['calibrations']['pixelflatframe']['process']['combine'] = 'median'
        par['calibrations']['pixelflatframe']['process']['sig_lohi'] = [10.,10.]

        # Always sky subtract, starting with default parameters
        par['skysubtract'] = pypeitpar.SkySubtractionPar()
        # Always flux calibrate, starting with default parameters
        par['fluxcalib'] = None  #  pypeitpar.FluxCalibrationPar()
        # Always correct for flexure, starting with default parameters
        par['flexure'] = pypeitpar.FlexurePar()
        return par

    def header_keys(self):
        def_keys = self.default_header_keys()

        def_keys[0]['target'] = 'TARGNAME'
        def_keys[0]['exptime'] = 'ELAPTIME'
        def_keys[0]['hatch'] = 'HATCHPOS'
        def_keys[0]['lamps'] = 'LAMPS'
        def_keys[0]['detrot'] = 'ROTATVAL'
        def_keys[0]['decker'] = 'SLMSKNAM'
        def_keys[0]['filter1'] = 'DWFILNAM'
        def_keys[0]['dispname'] = 'GRATENAM'

        def_keys[0]['gratepos'] = 'GRATEPOS'
        def_keys[0]['g3tltwav'] = 'G3TLTWAV'
        def_keys[0]['g4tltwav'] = 'G4TLTWAV'
        def_keys[0]['dispangle'] = 'G3TLTWAV'
        return def_keys

    def add_to_fitstbl(self, fitstbl):
        for gval in [3,4]:
            gmt = fitstbl['gratepos'] == gval
            fitstbl['dispangle'][gmt] = fitstbl['g3tltwav'][gmt]
        return

    def cond_dict(self, ftype):
        cond_dict = {}

        if ftype == 'science':
            cond_dict['condition1'] = 'lamps=Off'
            cond_dict['condition2'] = 'hatch=open'
            cond_dict['condition3'] = 'exptime>30'
        elif ftype == 'bias':
            cond_dict['condition1'] = 'exptime<2'
            cond_dict['condition2'] = 'lamps=Off'
            cond_dict['condition3'] = 'hatch=closed'
        elif ftype == 'pixelflat':
            cond_dict['condition1'] = 'lamps=Qz'
            cond_dict['condition2'] = 'exptime<30'
            cond_dict['condition3'] = 'hatch=closed'
        elif ftype == 'pinhole':
            cond_dict['condition1'] = 'exptime>99999999'
        elif ftype == 'trace':
            cond_dict['condition1'] = 'lamps=Qz'
            cond_dict['condition2'] = 'exptime<30'
            cond_dict['condition3'] = 'hatch=closed'
        elif ftype == 'arc':
            cond_dict['condition1'] = 'lamps=Kr_Xe_Ar_Ne'
            cond_dict['condition2'] = 'hatch=closed'
        else:
            pass

        return cond_dict

    def load_raw_img_head(self, raw_file, det=None, **null_kwargs):
        """
        Wrapper to the raw image reader for DEIMOS

        Args:
            raw_file:  str, filename
            det: int, REQUIRED
              Desired detector
            **null_kwargs:
              Captured and never used

        Returns:
            raw_img: ndarray
              Raw image;  likely unsigned int
            head0: Header

        """
        raw_img, head0, _ = read_deimos(raw_file, det=det)

        return raw_img, head0

    def get_match_criteria(self):
        match_criteria = {}
        for key in fsort.ftype_list:
            match_criteria[key] = {}

        # Standard
        # Can be over-ruled by flux calibrate = False
        # match_criteria['standard']['number'] = 1
        match_criteria['standard']['match'] = {}
        match_criteria['standard']['match']['decker'] = ''
        match_criteria['standard']['match']['binning'] = ''
        match_criteria['standard']['match']['filter1'] = ''
        # Bias
        match_criteria['bias']['match'] = {}
        match_criteria['bias']['match']['binning'] = ''
        # Pixelflat
        match_criteria['pixelflat']['match'] = match_criteria['standard']['match'].copy()
        # Traceflat
        match_criteria['trace']['match'] = match_criteria['standard']['match'].copy()
        # Arc
        match_criteria['arc']['match'] = match_criteria['standard']['match'].copy()

        # Return
        return match_criteria

    def get_image_section(self, filename, det, section='datasec'):
        """
        Return a string representation of a slice defining a section of
        the detector image.

        Overwrites base class function to use :func:`read_deimos` to get
        the image sections.

        .. todo::
            - It feels really ineffiecient to just get the image section
              using the full :func:`read_deimos`.  Can we parse that
              function into something that can give you the image
              section directly?

        This is done separately for the data section and the overscan
        section in case one is defined as a header keyword and the other
        is defined directly.
        
        Args:
            filename (str):
                data filename
            det (int):
                Detector number
            section (:obj:`str`, optional):
                The section to return.  Should be either datasec or
                oscansec, according to the :class:`DetectorPar`
                keywords.

        Returns:
            list, bool: A list of string representations for the image
            sections, one string per amplifier, followed by three
            booleans: if the slices are one indexed, if the slices
            should include the last pixel, and if the slice should have
            their order transposed.
        """
        # Read the file
        temp, head0, secs = read_deimos(filename, det)
        if section == 'datasec':
            return secs[0], False, False, False
        elif section == 'oscansec':
            return secs[1], False, False, False
        else:
            raise ValueError('Unrecognized keyword: {0}'.format(section))

    # WARNING: Uses Spectrograph default get_image_shape.  If no file
    # provided it will fail.  Provide a function like in keck_lris.py
    # that forces a file to be provided?

    def bpm(self, filename=None, det=None, **null_kwargs):
        """
        Override parent bpm function with BPM specific to DEIMOS.

        .. todo::
            Allow for binning changes.

        Parameters
        ----------
        det : int, REQUIRED
        **null_kwargs:
            Captured and never used

        Returns
        -------
        bpix : ndarray
          0 = ok; 1 = Mask

        """
        self.empty_bpm(filename=filename, det=det)
        if det == 1:
            self.bpm_img[:,1052:1054] = 1
        elif det == 2:
            self.bpm_img[:,0:4] = 1
            self.bpm_img[:,376:380] = 1
            self.bpm_img[:,2047] = 1
        elif det == 3:
            self.bpm_img[:,851] = 1
        elif det == 4:
            self.bpm_img[:,0:4] = 1
            self.bpm_img[:,997:998] = 1
        elif det == 5:
            self.bpm_img[:,129] = 1
        elif det == 7:
            self.bpm_img[:,426:428] = 1
        elif det == 8:
            self.bpm_img[:,931] = 1
            self.bpm_img[:,933] = 1

        return self.bpm_img

    def setup_arcparam(self, arcparam, disperser=None, fitstbl=None, arc_idx=None,
                       msarc_shape=None, **null_kwargs):
        """

        Args:
            arcparam:
            disperser:
            fitstbl:
            arc_idx:
            msarc_shape:
            binspectral:
            **null_kwargs:

        Returns:

        """
        arcparam['wv_cen'] = fitstbl['dispangle'][arc_idx]
        # TODO -- Should set according to the lamps that were on
        arcparam['lamps'] = ['ArI','NeI','KrI','XeI']
        if disperser == '830G': # Blaze 8640
            arcparam['n_first']=2 # Too much curvature for 1st order
            arcparam['disp']=0.47 # Ang per pixel (unbinned)
            arcparam['b1']= 1./arcparam['disp']/msarc_shape[0]
            arcparam['wvmnx'][0] = 550.
            arcparam['wvmnx'][1] = 11000.
            arcparam['min_ampl'] = 3000.  # Lines tend to be very strong
        elif disperser == '1200G': # Blaze 7760
            arcparam['n_first']=2 # Too much curvature for 1st order
            arcparam['disp']=0.32 # Ang per pixel (unbinned)
            arcparam['b1']= 1./arcparam['disp']/msarc_shape[0]
            arcparam['wvmnx'][0] = 550.
            arcparam['wvmnx'][1] = 11000.
            arcparam['min_ampl'] = 2000.  # Lines tend to be very strong
        else:
            msgs.error('Not ready for this disperser {:s}!'.format(disperser))

    def get_slitmask(self, filename):
        hdu = fits.open(filename)
        corners = np.array([hdu['BluSlits'].data['slitX1'],
                            hdu['BluSlits'].data['slitY1'],
                            hdu['BluSlits'].data['slitX2'],
                            hdu['BluSlits'].data['slitY2'],
                            hdu['BluSlits'].data['slitX3'],
                            hdu['BluSlits'].data['slitY3'],
                            hdu['BluSlits'].data['slitX4'],
                            hdu['BluSlits'].data['slitY4']]).T.reshape(-1,4,2)
        self.slitmask = SlitMask(corners, slitid=hdu['BluSlits'].data['dSlitId'])
        return self.slitmask

    def get_grating(self, filename):
        """
        Take from xidl/DEEP2/spec2d/pro/deimos_omodel.pro and
        xidl/DEEP2/spec2d/pro/deimos_grating.pro
        """
        hdu = fits.open(filename)

        # Grating slider
        slider = hdu[0].header['GRATEPOS']
        # TODO: Add test for slider

        # Central wavelength, grating angle, and tilt position
        if slider == 3:
            central_wave = hdu[0].header['G3TLTWAV']
            # Not used
            #angle = (hdu[0].header['G3TLTRAW'] + 29094)/2500
            tilt = hdu[0].header['G3TLTVAL']
        else:
            # Slider is 2 or 4
            central_wave = hdu[0].header['G4TLTWAV']
            # Not used
            #angle = (hdu[0].header['G4TLTRAW'] + 40934)/2500
            tilt = hdu[0].header['G4TLTVAL']

        # Ruling
        name = hdu[0].header['GRATENAM']
        if 'Mirror' in name:
            ruling = 0
        else:
            # Remove all non-numeric characters from the name and
            # convert to a floating point number
            ruling = float(re.sub('[^0-9]', '', name))
            # Adjust
            if abs(ruling-1200) < 0.5:
                ruling = 1200.06
            elif abs(ruling-831) <  2:
                ruling = 831.90

        # Get the orientation of the grating
        roll, yaw, tilt = KeckDEIMOSSpectrograph._grating_orientation(slider, ruling, tilt)

        self.grating = None if ruling == 0 else ReflectionGrating(ruling, tilt, roll, yaw,
                                                                  central_wave=central_wave)
        return self.grating

    @staticmethod
    def _grating_orientation(slider, ruling, tilt):
        """
        Return the roll, yaw, and tilt of the grating.

        Numbers are hardwired.

        From xidl/DEEP2/spec2d/pro/omodel_params.pro
        """
        if slider == 2 and int(ruling) == 0:
            # Mirror in place of the grating
            return 0., 0., -19.423

        if slider == 2:
            raise ValueError('Ruling should be 0 if slider in position 2.')

        # Use the calibrated coefficients
        _ruling = int(ruling) if int(ruling) in [600, 831, 900, 1200] else 'other'
        orientation_coeffs = {3: {    600: [ 0.145, -0.008, 5.6e-4, -0.182],
                                      831: [ 0.143,  0.000, 5.6e-4, -0.182],
                                      900: [ 0.141,  0.000, 5.6e-4, -0.134],
                                     1200: [ 0.145,  0.055, 5.6e-4, -0.181],
                                  'other': [ 0.145,  0.000, 5.6e-4, -0.182] },
                              4: {    600: [-0.065,  0.063, 6.9e-4, -0.298],
                                      831: [-0.034,  0.060, 6.9e-4, -0.196],
                                      900: [-0.064,  0.083, 6.9e-4, -0.277],
                                     1200: [-0.052,  0.122, 6.9e-4, -0.294],
                                  'other': [-0.050,  0.080, 6.9e-4, -0.250] } }

        # Return calbirated roll, yaw, and tilt
        return orientation_coeffs[slider][_ruling][0], \
                orientation_coeffs[slider][_ruling][1], \
                tilt*(1-orientation_coeffs[slider][_ruling][2]) \
                    + orientation_coeffs[slider][_ruling][3]

    def mask_to_pixel_coordinates(self, x=None, y=None, wave=None, order=1, filename=None):

        if x is None and y is not None or x is not None and y is None:
            raise ValueError('Must provide both x and y or neither to use slit mask.')

        if filename is not None:
            if x is None and y is None:
                # Reset the slit mask
                self.get_slitmask(filename)
            # Reset the grating
            self.get_grating(filename)

        if x is None and y is None and self.slitmask is None:
            raise ValueError('No coordinates; Provide them directly or instantiate slit mask.')

        _x = self.slitmask.center[:,0] if x is None else x
        _y = self.slitmask.center[:,1] if y is None else y

        if self.grating is None:
            raise ValueError('Must define a grating first; provide a file or use get_grating()')

        if self.optical_model is None:
            self.optical_model = DEIMOSOpticalModel(self.grating)
        else:
            self.optical_model.reset_grating(self.grating)

        if self.detector_map is None:
            self.detector_map = DEIMOSDetectorMap()

        x_img, y_img = self.optical_model.mask_to_imaging_coordinates(_x, _y, wave=wave,
                                                                      order=order)
        return self.detector_map.ccd_coordinates(x_img, y_img)


class DEIMOSOpticalModel(OpticalModel):
    # TODO: Are focal_r_surface (!R_IMSURF) and focal_r_curvature
    # (!R_CURV) supposed to be the same?  If so, consolodate these into
    # a single number.
    def __init__(self, grating):
        super(DEIMOSOpticalModel, self).__init__(
                    20018.4,                # Pupil distance in mm (!PPLDIST, !D_1)
                    2133.6,                 # Radius of the image surface in mm (!R_IMSURF)
                    2124.71,                # Focal-plane radius of curvature in mm (!R_CURV)
                    2120.9,                 # Mask radius of curvature in mm (!M_RCURV)
                    np.radians(6.),         # Mask tilt angle in radians (!M_ANGLE)
                    128.803,                # Mask y zero point in mm (!ZPT_YM)
                    3.378,                  # Mask z zero-point in mm (!MASK_HT0)
                    2197.1,                 # Collimator distance in mm (sys.COL_DST)
                    4394.2,                 # Collimator radius of curvature in mm (!R_COLL)
                    -0.75,                  # Collimator curvature constant (!K_COLL)
                    np.radians(0.002),      # Collimator tilt error in radians (sys.COL_ERR)
                    0.0,                    # Collimator tilt phi angle in radians (sys.COL_PHI)
                    grating,                # DEIMOS grating object
                    np.radians(2.752),      # Camera angle in radians (sys.CAM_ANG)
                    np.pi/2,                # Camera tilt phi angle in radians (sys.CAM_PHI)
                    382.0,                  # Camera focal length in mm (sys.CAM_FOC)
                    DEIMOSCameraDistortion(),   # Object used to apply/remove camera distortions
                    np.radians(0.021),      # ICS rotation in radians (sys.MOS_ROT)
                    [-0.234, -3.822])       # Camera optical axis center in mm (sys.X_OPT,sys.Y_OPT)

        # Include tent mirror
        self.tent_theta = np.radians(71.5-0.5)  # Tent mirror theta angle (sys.TNT_ANG)
        self.tent_phi = np.radians(90.+0.081)   # Tent mirror phi angle (sys.TNT_PHI)

        #TENT MIRROR: this mirror is OK to leave in del-theta,phi
        self.tent_reflection \
                = OpticalModel.get_reflection_transform(self.tent_theta, self.tent_phi)

    def reset_grating(self, grating):
        self.grating = grating

    def mask_coo_to_grating_input_vectors(self, x, y):
        """
        Propagate rays from the mask plane to the grating.

        Taken from xidl/DEEP2/spec2d/pro/model/pre_grating.pro

        Need to override parent class to add tent mirror reflection.
        """
        r = super(DEIMOSOpticalModel, self).mask_coo_to_grating_input_vectors(x, y)
        # Reflect off the tent mirror and return
        return OpticalModel.reflect(r, self.tent_reflection)


class DEIMOSCameraDistortion:
    """Class to remove or apply DEIMOS camera distortion."""
    def __init__(self):
        self.c0 = 1.
        self.c2 = 0.0457563
        self.c4 = -0.3088123
        self.c6 = -14.917
    
        x = np.linspace(-0.6, 0.6, 1000)
        y = self.remove_distortion(x)
        self.interpolator = interpolate.interp1d(y, x)

    def remove_distortion(self, x):
        x2 = np.square(x)
        return x / (self.c0 + x2 * (self.c2 + x2 * (self.c4 + x2 * self.c6)))

    def apply_distortion(self, y):
        indx = (y > self.interpolator.x[0]) & (y < self.interpolator.x[-1])
        if not np.all(indx):
            warnings.warn('Some input angles outside of valid distortion interval!')
        x = np.zeros_like(y)
        x[indx] = self.interpolator(y[indx])
        return x


class DEIMOSDetectorMap(DetectorMap):
    """
    A map of the center coordinates and rotation of each CCD in DEIMOS.

    !! PIXEL COORDINATES ARE 1-INDEXED !!
    """
    def __init__(self):
        # Number of chips
        self.nccd = 8

        # Number of pixels for each chip in each dimension
        self.npix = np.array([2048, 4096])

        # The size of the CCD pixels in mm
        self.pixel_size = 0.015

        # Nominal gap between each CCD in each dimension in mm
        self.ccd_gap = np.array([1, 0.1])

        # Width of the CCD edge in each dimension in mm
        self.ccd_edge = np.array([0.154, 0.070])

        # Effective size of each chip in each dimension in pixels
        self.ccd_size = self.npix + (2*self.ccd_edge + self.ccd_gap)/self.pixel_size

        # Center coordinates
        origin = np.array([[-1.5,-0.5], [-0.5,-0.5], [ 0.5,-0.5], [ 1.5,-0.5],
                           [-1.5, 0.5], [-0.5, 0.5], [ 0.5, 0.5], [ 1.5, 0.5]])
        offset = np.array([[-20.05, 14.12], [-12.64, 7.25], [0.00, 0.00], [-1.34, -19.92],
                           [-19.02, 16.46], [ -9.65, 8.95], [1.88, 1.02], [ 4.81, -24.01]])
        self.ccd_center = origin * self.ccd_size[None,:] + offset
        
        # Construct the rotation matrix
        self.rotation = np.radians([-0.082, 0.030, 0.0, -0.1206, 0.136, -0.06, -0.019, -0.082])
        cosa = np.cos(self.rotation)
        sina = np.sin(self.rotation)
        self.rot_matrix = np.array([cosa, -sina, sina, cosa]).T.reshape(self.nccd,2,2)

        # ccd_geom.pro has offsets by sys.CN_XERR, but these are all 0.
   

def read_deimos(raw_file, det=None):
    """
    Read a raw DEIMOS data frame (one or more detectors)
    Packed in a multi-extension HDU
    Based on pypeit.arlris.read_lris...
       Based on readmhdufits.pro

    Parameters
    ----------
    raw_file : str
      Filename

    Returns
    -------
    array : ndarray
      Combined image
    header : FITS header
    sections : tuple
      List of datasec, oscansec sections
    """

    # Check for file; allow for extra .gz, etc. suffix
    fil = glob.glob(raw_file + '*')
    if len(fil) != 1:
        msgs.error('Found {0} files matching {1}'.format(len(fil), raw_file + '*'))
    # Read
    try:
        msgs.info("Reading DEIMOS file: {:s}".format(fil[0]))
    except AttributeError:
        print("Reading DEIMOS file: {:s}".format(fil[0]))

    hdu = fits.open(fil[0])
    head0 = hdu[0].header

    # Get post, pre-pix values
    precol = head0['PRECOL']
    postpix = head0['POSTPIX']
    preline = head0['PRELINE']
    postline = head0['POSTLINE']
    detlsize = head0['DETLSIZE']
    x0, x_npix, y0, y_npix = np.array(parse.load_sections(detlsize)).flatten()

    # Create final image
    if det is None:
        image = np.zeros((x_npix,y_npix+4*postpix))

    # Setup for datasec, oscansec
    dsec = []
    osec = []

    # get the x and y binning factors...
    binning = head0['BINNING']
    if binning != '1,1':
        msgs.error("This binning for DEIMOS might not work.  But it might..")

    xbin, ybin = [int(ibin) for ibin in binning.split(',')]

    # DEIMOS detectors
    nchip = 8


    if det is None:
        chips = range(nchip)
    else:
        chips = [det-1] # Indexing starts at 0 here
    # Loop
    for tt in chips:
        data, oscan = deimos_read_1chip(hdu, tt+1)


        #if n_elements(nobias) eq 0 then nobias = 0


        # One detector??
        if det is not None:
            image = np.zeros((data.shape[0],data.shape[1]+oscan.shape[1]))

        # Indexing
        x1, x2, y1, y2, o_x1, o_x2, o_y1, o_y2 = indexing(tt, postpix, det=det)

        # Fill
        image[y1:y2, x1:x2] = data
        image[o_y1:o_y2, o_x1:o_x2] = oscan

        # Sections
        idsec = '[{:d}:{:d},{:d}:{:d}]'.format(y1, y2, x1, x2)
        iosec = '[{:d}:{:d},{:d}:{:d}]'.format(o_y1, o_y2, o_x1, o_x2)
        dsec.append(idsec)
        osec.append(iosec)
    # Return
    return image, head0, (dsec,osec)


def indexing(itt, postpix, det=None):
    """
    Some annoying book-keeping for instrument placement.

    Parameters
    ----------
    itt : int
    postpix : int
    det : int, optional

    Returns
    -------

    """
    # Deal with single chip
    if det is not None:
        tt = 0
    else:
        tt = itt
    ii = 2048
    jj = 4096
    # y indices
    if tt < 4:
        y1, y2 = 0, jj
    else:
        y1, y2 = jj, 2*jj
    o_y1, o_y2 = y1, y2

    # x
    x1, x2 = (tt%4)*ii, (tt%4 + 1)*ii
    if det is None:
        o_x1 = 4*ii + (tt%4)*postpix
    else:
        o_x1 = ii + (tt%4)*postpix
    o_x2 = o_x1 + postpix

    # Return
    return x1, x2, y1, y2, o_x1, o_x2, o_y1, o_y2

def deimos_read_1chip(hdu,chipno):
    """ Read one of the DEIMOS detectors

    Parameters
    ----------
    hdu : HDUList
    chipno : int

    Returns
    -------
    data : ndarray
    oscan : ndarray
    """

    # Extract datasec from header
    datsec = hdu[chipno].header['DATASEC']
    detsec = hdu[chipno].header['DETSEC']
    postpix = hdu[0].header['POSTPIX']
    precol = hdu[0].header['PRECOL']

    x1_dat, x2_dat, y1_dat, y2_dat = np.array(parse.load_sections(datsec)).flatten()
    x1_det, x2_det, y1_det, y2_det = np.array(parse.load_sections(detsec)).flatten()

    # This rotates the image to be increasing wavelength to the top
    #data = np.rot90((hdu[chipno].data).T, k=2)
    #nx=data.shape[0]
    #ny=data.shape[1]


    # Science data
    fullimage = hdu[chipno].data
    data = fullimage[x1_dat:x2_dat,y1_dat:y2_dat]

    # Overscan
    oscan = fullimage[:,y2_dat:]

    # Flip as needed
    if x1_det > x2_det:
        data = np.flipud(data)
        oscan = np.flipud(oscan)
    if y1_det > y2_det:
        data = np.fliplr(data)
        oscan = np.fliplr(oscan)

    # Return
    return data, oscan


