"""
EasyBuild support for using (already installed/existing) tree off
software instead of a full install via EasyBuild.

@author Elizabeth Fischer (Columbia University, USA)
"""
import os
import re

from easybuild.easyblocks.generic.cmakemake import CMakeMake
from easybuild.tools.environment import setvar
from easybuild.tools.run import run_cmd
import easybuild.tools.environment as env

class CmakeDev(CMakeMake):
	"""
	Support for generating a module file for some existing pre-installed tree of software
	(eg: a MacPorts installation).
	"""

	def __init__(self, *args, **kwargs):
		"""Extra initialization: determine system compiler version and prefix."""
		super(CmakeDev, self).__init__(*args, **kwargs)


	# ================================================
	def fetch_step(self, skip_checksums=False):
		"""Fetch source files and patches (incl. extensions)."""
		# User should have put project dir as sources[0]
		pass

	def checksum_step(self):
		"""Verify checksum of sources and patches, if a checksum is available."""
		pass

	def extract_step(self):
		"""
		Unpack the source files.
		"""
#		for src in self.src:
#			self.src[self.src.index(src)]['finalpath'] = src['path']
#			# I think this would work too:
#			# src['finalpath'] = src['path']

		self.builddir = self.cfg['sources'][0]
		self.log.info("Changing Build dir to %s" % self.builddir)


	def patch_step(self, beginpath=None):
		"""
		Apply the patches
		"""
		pass


	def prepare_step(self, *args, **kwargs):
		"""
		Pre-configure step. Set's up the builddir just before starting configure
		"""
		super(CmakeDev, self).prepare_step(*args, **kwargs)


#	def configure_step(self, *args, **kwargs):
#		self.builddir = self.src[0]['path']


	def make_installdir(self, dontcreate=None):
		"""Custom implementation of make installdir: do nothing, do
		not touch system compiler directories and files."""
		pass


	def configure_step(self, srcdir=None, builddir=None):
		"""Configure build using cmake"""

		if builddir is not None:
			self.log.nosupport("CMakeMake.configure_step: named argument 'builddir' (should be 'srcdir')", "2.0")

		# Set the search paths for CMake
		include_paths = os.pathsep.join(self.toolchain.get_variable("CPPFLAGS", list))
		library_paths = os.pathsep.join(self.toolchain.get_variable("LDFLAGS", list))
		setvar("CMAKE_INCLUDE_PATH", include_paths)
		setvar("CMAKE_LIBRARY_PATH", library_paths)

		default_srcdir = '.'
		if self.cfg.get('separate_build_dir', False):
			objdir = os.path.join(self.builddir, 'build')
			try:
				os.mkdir(objdir)
			except OSError, err:
				pass

			try:
				os.chdir(objdir)
			except OSError, err:
				raise EasyBuildError("Failed to create separate build dir %s in %s: %s", objdir, os.getcwd(), err)
			default_srcdir = self.cfg['start_dir']

		if srcdir is None:
			if self.cfg.get('srcdir', None) is not None:
				srcdir = self.cfg['srcdir']
			else:
				srcdir = default_srcdir

		options = ['-DCMAKE_INSTALL_PREFIX=%s' % self.installdir]
		env_to_options = {
			'CC': 'CMAKE_C_COMPILER',
			'CFLAGS': 'CMAKE_C_FLAGS',
			'CXX': 'CMAKE_CXX_COMPILER',
			'CXXFLAGS': 'CMAKE_CXX_FLAGS',
			'F90': 'CMAKE_Fortran_COMPILER',
			'FFLAGS': 'CMAKE_Fortran_FLAGS',
		}
		for env_name, option in env_to_options.items():
			value = os.getenv(env_name)
			if value is not None:
				options.append("-D%s='%s'" % (option, value))

		# show what CMake is doing by default
		options.append("-DCMAKE_VERBOSE_MAKEFILE=ON")

		options_string = " ".join(options)

		command = "%s cmake %s %s %s" % (self.cfg['preconfigopts'], srcdir, options_string, self.cfg['configopts'])
		(out, _) = run_cmd(command, log_all=True, simple=False)

		return out


	def cleanup_step(self):
		"""Do NOT remove the build directory, under any circumstances!"""
		env.restore_env_vars(self.cfg['unwanted_env_vars'])

