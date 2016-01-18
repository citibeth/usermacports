"""
EasyBuild support for using (already installed/existing) tree off
software instead of a full install via EasyBuild.

@author Elizabeth Fischer (Columbia University, USA)
"""
import os
import re
import stat

from easybuild.easyblocks.generic.cmakemake import CMakeMake
from easybuild.tools.environment import setvar
from easybuild.tools.run import run_cmd
import easybuild.tools.environment as env

def is_exe(fpath):
	return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

def which(program):
	for path in os.getenv("PATH").split(os.pathsep):
		path = path.strip('"')
		exe_file = os.path.join(path, program)
		if is_exe(exe_file):
			return exe_file

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

	def make_installdir(self, dontcreate=None):
		"""Custom implementation of make installdir: do nothing, do
		not touch system compiler directories and files."""
		pass


	def configure_step(self, srcdir=None, builddir=None):
		"""Configure build using cmake"""

		if builddir is not None:
			self.log.nosupport("CMakeMake.configure_step: named argument 'builddir' (should be 'srcdir')", "2.0")

		default_srcdir = '.'

		# if separate_build_dir...
		objdir = os.path.join(self.builddir, 'build')
		configme_sh = os.path.join(self.builddir, 'ebconfig.py')
		configme_out = open(configme_sh, 'w')
		configme_out.write(
r"""#!/usr/bin/env python
#

import sys
import os
import subprocess

def cmdlist(str):
	return list(x.strip().replace("'",'') for x in str.split('\n') if x)

env = dict(PATH=os.getenv('PATH'))
""")

		self.log.info("Creating CMake build dir %s" % objdir)
		try:
			os.mkdir(objdir)
		except OSError, err:
			pass

		try:
			os.chdir(objdir)
		except OSError, err:
			raise EasyBuildError("Failed to cd to separate build dir %s in %s: %s", objdir, os.getcwd(), err)
		default_srcdir = self.cfg['start_dir']

		if srcdir is None:
			if self.cfg.get('srcdir', None) is not None:
				srcdir = self.cfg['srcdir']
			else:
				srcdir = default_srcdir
		# -----------------

		# Set the search paths for CMake
		include_paths = os.pathsep.join(self.toolchain.get_variable("CPPFLAGS", list))
		library_paths = os.pathsep.join(self.toolchain.get_variable("LDFLAGS", list))
#		setvar("CMAKE_INCLUDE_PATH", include_paths)
#		setvar("CMAKE_LIBRARY_PATH", library_paths)
		setvar("CMAKE_INCLUDE_PATH", os.getenv('CFLAGS'))
		setvar("CMAKE_LIBRARY_PATH", os.getenv('LD_LIBRARY_PATH'))

		# ---------------------------------------------------------
		configme_out.write("env['EB_INCLUDE_PATH'] = ';'.join(cmdlist(")
		configme_out.write('"""\n')
		# Get transitive paths as loaded by module command
		for path in os.getenv('CPATH').split(os.pathsep):
			configme_out.write("    %s\n" % path)
		configme_out.write('"""')
		configme_out.write("))\n\n")

		# ---------------------------------------------------------
		configme_out.write("env['CMAKE_INCLUDE_PATH'] = os.pathsep.join(cmdlist(")
		configme_out.write('"""\n')
		for path in self.toolchain.get_variable("CPPFLAGS", list):
			configme_out.write("    %s\n" % path)
		configme_out.write('"""')
		configme_out.write("))\n\n")

		configme_out.write("env['CMAKE_LIBRARY_PATH'] = os.pathsep.join(cmdlist(")
		configme_out.write('"""\n')
		for path in self.toolchain.get_variable("LDFLAGS", list):
			configme_out.write("    %s\n" % path)
		configme_out.write('"""')
		configme_out.write("))\n\n")
		# ---------------------------------------------------------


#		configme_out.write("export CMAKE_INCLUDE_PATH='%s'\n" % include_paths)
#		configme_out.write("export CMAKE_LIBRARY_PATH='%s'\n" % library_paths)

		options = ['-DCMAKE_INSTALL_PREFIX=%s' % self.installdir]

		tcvar = self.toolchain.get_variable
		options.append('-DCMAKE_C_COMPILER=%s'       % which(tcvar('CC')))
		options.append('-DCMAKE_C_FLAGS=%s'          % tcvar('CFLAGS'))
		options.append('-DCMAKE_CXX_COMPILER=%s'     % which(tcvar('CXX')))
		options.append('-DCMAKE_CXX_FLAGS=%s'        % tcvar('CXXFLAGS'))
		options.append('-DCMAKE_Fortran_COMPILER=%s' % which(tcvar('F90')))
		options.append('-DCMAKE_Fortran_FLAGS=%s'    % tcvar('F90FLAGS'))


#		env_to_options = {
#			'CC': 'CMAKE_C_COMPILER',
#			'CFLAGS': 'CMAKE_C_FLAGS',
#			'CXX': 'CMAKE_CXX_COMPILER',
#			'CXXFLAGS': 'CMAKE_CXX_FLAGS',
#			'F90': 'CMAKE_Fortran_COMPILER',
#			'FFLAGS': 'CMAKE_Fortran_FLAGS',
#		}
#		for env_name, option in env_to_options.items():
#			value = os.getenv(env_name)
#			if value is not None:
#				options.append("-D%s='%s'" % (option, value))


		# show what CMake is doing by default
#		options.append("-DCMAKE_VERBOSE_MAKEFILE=ON")

		options_string = " ".join(options)

		configme_out.write('cmd = cmdlist("""\n')
		configme_out.write('%s\n' % which('cmake'))
		configme_out.write('    %s\n' % srcdir)
		for opt in options:
			configme_out.write('    %s\n' % opt)
		configme_out.write('""") + sys.argv[1:]\n\n')
		configme_out.write
		configme_out.write("proc = subprocess.Popen(cmd, env=env, cwd=%s)\n" % repr(objdir))
		configme_out.write("proc.wait()\n")

		configme_out.close()
		os.chmod(configme_sh, os.stat(configme_sh).st_mode | stat.S_IEXEC)



		command = "%s cmake %s %s %s" % (self.cfg['preconfigopts'], srcdir, options_string, self.cfg['configopts'])
		self.log.info('CWD = %s' % os.getcwd())
		self.log.info('Running cmd: %s' % command)


#		(out, _) = run_cmd(command, log_all=True, simple=False)
#		return out
		return 0

	def buid_step(self, *args, **kwargs):
		pass

	def cleanup_step(self):
		"""Do NOT remove the build directory, under any circumstances!"""
		env.restore_env_vars(self.cfg['unwanted_env_vars'])

