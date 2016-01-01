"""
EasyBuild support for using (already installed/existing) tree off
software instead of a full install via EasyBuild.

@author Elizabeth Fischer (Columbia University, USA)
"""
import os
import re

from easybuild.easyblocks.generic.bundle import Bundle

class Tree(Bundle):
	"""
	Support for generating a module file for some existing pre-installed tree of software
	(eg: a MacPorts installation).
	"""

	def __init__(self, *args, **kwargs):
		"""Extra initialization: determine system compiler version and prefix."""
		super(Tree, self).__init__(*args, **kwargs)

	def make_installdir(self, dontcreate=None):
		"""Custom implementation of make installdir: do nothing, do
		not touch system compiler directories and files."""
		pass



	def make_module_step(self, fake=False):

		"""Custom module step for Tree: make 'EBROOT' and 'EBVERSION'
		reflect actual system compiler version and install path."""

		# For module file generation: temporarly set version and
		# installdir to system compiler values


		orig_installdir = self.installdir
		self.installdir = self.cfg['sanity_check_paths']['dirs'][0]

		# Generate module
		res = super(Tree, self).make_module_step(fake=fake)

		# Reset version and installdir to EasyBuild values
		self.installdir = orig_installdir

		return res

#	def permissions_step(self):
#		"""Override: https://github.com/hpcugent/easybuild-framework/blob/541556488193cc917c2478f2134ae1e51bbde7d4/easybuild/framework/easyblock.py"""
#		pass
