""" Object to hold + process a single image"""

import inspect

import os
import numpy as np

from pypeit import msgs

from pypeit.core import procimg
from pypeit.core import combine
from pypeit.par import pypeitpar

from pypeit.images import pypeitimage
from pypeit.images import processimage

from IPython import embed

# REMOVE THIS
from importlib import reload
reload(procimg)


class CombinedImage(pypeitimage.PypeItImage):

    def __init__(self, spectrograph, det, proc_par, files=None, frametype=None):

        # Init me
        pypeitimage.PypeItImage.__init__(self, spectrograph, det)

        # Assign the internal list of files
        self._set_files(files)

        # Required parameters
        if not isinstance(proc_par, pypeitpar.ProcessImagesPar):
            msgs.error('Provided ParSet for must be type ProcessImagesPar.')
        self.proc_par = proc_par  # This musts be named this way as it is frequently a child

        # Optional parameters
        self.frametype = frametype

        # Internal images
        self.images = []
        self.combined = None

        # All possible processing steps
        #  Note these have to match the method names below
        self.steps = dict()

    @property
    def nimages(self):
        return len(self.images)

    def _set_files(self, files, check=False):
        """
        Assign the provided files to :attr:`files`.

        Args:
            files (None, :obj:`str`, :obj:`list`):
                The files to process.
            check (:obj:`bool`, optional):
                Check that the files exist on disk.

        Raises:
            PypeItError:
                Raised if the input objects have the wrong type.
        """
        if files is None:
            self.files = []
        elif isinstance(files, str):
            self.files = [files]
        elif isinstance(files, list):
            if not np.all([isinstance(f, str) for f in files]):
                msgs.error('File list elements must be strings.')
            self.files = files
        else:
            msgs.error('Provides files must be None, a string name, or a list of strings.')

        if check:
            self._check_files()

    def _check_files(self):
        """
        Check that files in :attr:`files` exist.

        Raises:
            PypeItError:
                Raised if any of the files don't exist.
        """
        for f in self.files:
            if not os.path.isfile(f):
                msgs.error('{0} does not exist!'.format(f))

    def combine(self):
        if self.nimages == 1:
            self.combined = self.images[0].image
        else:
            #
            saturation = self.spectrograph.detector[self.det-1]['saturation']
            # Build the image stack
            image_arr = np.zeros((self.images[0].image.shape[0],
                                         self.images[0].image.shape[1],
                                         self.nimages))
            for kk,iimage in enumerate(self.images):
                image_arr[:,:,kk] = iimage.image

            # Do it
            self.combined = combine.comb_frames(image_arr,
                                                frametype=self.frametype,
                                             saturation=saturation,
                                             method=self.proc_par['combine'],
                                             satpix=self.proc_par['satpix'],
                                             cosmics=self.proc_par['sigrej'],
                                             n_lohi=self.proc_par['n_lohi'],
                                             sig_lohi=self.proc_par['sig_lohi'],
                                             replace=self.proc_par['replace'])
        # Return
        return self.combined.copy()

    def load_images(self, reload=False):
        if (not reload) and (self.nimages > 0):
            msgs.warn("Images already loaded.  Use reload if you wish")
            return
        for file in self.files:
            processImage = processimage.ProcessImage(file, self.spectrograph, self.det, self.proc_par)
            processImage.load_image(file)
            self.images.append(processImage)

    def process_images(self, process_steps, pixel_flat=None, illum_flat=None,
                       bias=None, bpm=None):

        for image in self.images:
            # Standard order
            #   -- May need to allow for other order some day..
            if 'subtract_bias' in process_steps:
                image.subtract_bias(bias)
            if 'subtract_overscan' in process_steps:
                image.subtract_overscan()
            if 'trim' in process_steps:
                image.trim()
            if 'apply_gain' in process_steps:
                image.apply_gain()
            # Always orient
            image.orient()
            # Flat field
            if 'flatten' in process_steps:
                image.flatten(pixel_flat, illum_flat=illum_flat, bpm=bpm)






