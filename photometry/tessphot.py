#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. codeauthor:: Rasmus Handberg <rasmush@phys.au.dk>
"""

import logging
import traceback
from . import STATUS, AperturePhotometry, PSFPhotometry, LinPSFPhotometry, HaloPhotometry

#------------------------------------------------------------------------------
class _PhotErrorDummy(object):
	def __init__(self, traceback, *args, **kwargs):
		self.status = STATUS.ERROR
		self._details = {'errors': traceback} if traceback else {}

#------------------------------------------------------------------------------
def _try_photometry(PhotClass, *args, **kwargs):
	logger = logging.getLogger(__name__)
	tbcollect = []
	try:
		with PhotClass(*args, **kwargs) as pho:
			pho.photometry()

			if pho.status in (STATUS.OK, STATUS.WARNING):
				pho.save_lightcurve()

	except (KeyboardInterrupt, SystemExit):
		logger.info("Stopped by user or system")
		try:
			pho._status = STATUS.ABORT
		except:
			pass

	except:
		logger.exception("Something happened")
		tb = traceback.format_exc().strip()
		try:
			pho._status = STATUS.ERROR
			pho.report_details(error=tb)
		except:
			tbcollect.append(tb)

	try:
		return pho
	except UnboundLocalError:
		return _PhotErrorDummy(tbcollect, *args, **kwargs)

#------------------------------------------------------------------------------
def tessphot(method=None, *args, **kwargs):
	"""
	Run the photometry pipeline on a single star.

	This function will run the specified photometry or perform the dynamical
	scheme of trying simple aperture photometry, evaluating its performance
	and if nessacery try another algorithm.

	Parameters:
		method (string or None): Type of photometry to run. Can be ``'aperture'``, ``'halo'``, ``'psf'``, ``'linpsf'`` or ``None``.
		*args: Arguments passed on to the photometry class init-function.
		**kwargs: Keyword-arguments passed on to the photometry class init-function.

	Returns:
		:py:class:`photometry.BasePhotometry`: Photometry object that inherits from :py:class:`photometry.BasePhotometry`.
	"""

	logger = logging.getLogger(__name__)

	if method is None:
		pho = _try_photometry(AperturePhotometry, *args, **kwargs)

		if pho.status == STATUS.WARNING:
			logger.warning("Try something else?")
			# TODO: If too crowded:
			# pho = _try_photometry(PSFPhotometry, starid, input_folder, output_folder, datasource, plot)

	elif method == 'aperture':
		pho = _try_photometry(AperturePhotometry, *args, **kwargs)

	elif method == 'psf':
		pho = _try_photometry(PSFPhotometry, *args, **kwargs)

	elif method == 'linpsf':
		pho = _try_photometry(LinPSFPhotometry, *args, **kwargs)

	elif method == 'halo':
		pho = _try_photometry(HaloPhotometry, *args, **kwargs)

	else:
		raise ValueError("Invalid method: '{0}'".format(method))

	logger.info("Done")
	return pho
