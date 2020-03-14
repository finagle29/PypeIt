"""
Module for guiding Bias subtraction including generating a Bias image as desired

.. include common links, assuming primary doc root is up one directory
.. include:: ../links.rst
"""
import numpy as np
import os
from IPython import embed

from pypeit import msgs
from pypeit import masterframe
from pypeit.par import pypeitpar
from pypeit.images import calibrationimage
from pypeit.images import pypeitimage


class BiasImage(calibrationimage.CalibrationImage):
    # Set the version of this class
    version = '1.0.0'

    # Output to disk
    output_to_disk = ('BIAS_IMAGE',)
    hdu_prefix = 'BIAS_'
    master_type = 'Bias'
    frametype = 'bias'


class BiasFrame(calibrationimage.BuildCalibrationImage):
    """
    Class to generate/load the Bias image or instructions on how to deal
    with the bias.

    This class is primarily designed to generate a Bias frame for bias
    subtraction.  It also contains I/O methods for the Master frames of
    PypeIt.  The build_master() method will return a simple command
    (str) if that is the specified parameter (`par['useframe']`).

    Args:
        spectrograph (:class:`pypeit.spectrographs.spectrograph.Spectrograph`):
            Spectrograph used to take the data.

        files (:obj:`list`, optional):
            List of filenames to process.
        det (:obj:`int`, optional):
            The 1-indexed detector number to process.
        par (:class:`pypeit.par.pypeitpar.FrameGroupPar`, optional):
            The parameters used to process the frames.  If None, set
            to::
                
                pypeitpar.FrameGroupPar('bias')

        master_key (:obj:`str`, optional):
            The string identifier for the instrument configuration.  See
            :class:`pypeit.masterframe.MasterFrame`.
        master_dir (:obj:`str`, optional):
            Path to master frames
        reuse_masters (:obj:`bool`, optional):
            Load from disk if possible
    """

    # Frame type is a class attribute
    #frametype = 'bias'
    #master_type = 'Bias'
    #master_version = '1.0.0'

    image_type = BiasImage

    postbias_process_steps = ['trim']
    postbias_process_steps += ['orient']

    def __init__(self, spectrograph, par, det, files=None):

        self.par = par

        # Start us up
        calibrationimage.BuildCalibrationImage.__init__(self, spectrograph, det,
                                                        self.par['process'], files,
                                                        bias=None)

    def build_image(self, overwrite=False, trim=True):
        """
        Grab the bias files (as needed) and then process the input bias
        frames with :func:`pypeit.processimages.ProcessImages.process`.

        Args:
            overwrite: (:obj: `bool`, optional):
                Regenerate the combined image
            trim (:obj:`bool`, optional):
                If True, trim the image

        Returns:
            `numpy.ndarray`_: Combined, processed image.
        """
        # Nothing?
        if self.par['useframe'].lower() == 'none':
            msgs.info("Bias image subtraction not activated.")
            return None
        if self.nfiles == 0:
            msgs.info("No bias frames provided.  No bias image will be generated or used")
            return None
        # Build
        pypeitimage = super(BiasFrame, self).build_image(ignore_saturation=True)
        biasImage = BiasImage.from_pypeitimage(pypeitimage)
        # Return
        return biasImage


    def load(self, ifile, reuse_masters=False):
        """
        Load the bias frame according to how par['useframe'] is set.
        
        Args:
            ifile (:obj:`str`):
                Name of the master frame file.

        Returns:
            Returns either the `numpy.ndarray`_ with the bias image
            or None if no bias is to be subtracted.
        """
        # How are we treating biases?
        # 1) No bias subtraction
        if self.par['useframe'].lower() == 'none':
            msgs.info("Will not perform bias/dark subtraction")
            return None

        # 2) Use overscan
        if self.par['useframe'] == 'overscan':
            msgs.error("useframe=overscan was Deprecated. Remove it from your pypeit file")

        # 3) User wants bias subtractions
        if self.par['useframe'] in ['bias', 'dark']:
            # Check on whether to reuse and whether the file exists
            if os.path.isfile(ifile) and reuse_masters:
                self.pypeitImage = BiasImage.from_file(ifile, hdu_prefix='BIAS_')
                return self.pypeitImage
            else:
                return None

