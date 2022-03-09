#	pktbuilder - Build gcc embedded toolchains and more
#	Copyright (C) 2022-2022 Johannes Bauer
#
#	This file is part of pktbuilder.
#
#	pktbuilder is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	pktbuilder is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with pktbuilder; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import requests
import tempfile
import subprocess
import logging
import shutil
import contextlib
import multiprocessing
from Tools import ExecTools
from CmdlineEscape import CmdlineEscape
from WorkDir import WorkDir

_log = logging.getLogger("pktbuilder.RecipeBuilder")

class RecipeBuilder():
	def __init__(self, args, pkg_defs, recipe, variables):
		self._args = args
		self._pkg_defs = pkg_defs
		self._recipe = recipe
		self._variables = variables
		self._pkg_dir = os.path.realpath(self._args.download_directory)
		self._log_dir = os.path.realpath(self._args.log_directory)
		with contextlib.suppress(FileExistsError):
			os.makedirs(self._log_dir)

	def _next_logfile(self):
		i = 1
		while True:
			filename = "%s/%04d.txt" % (self._log_dir, i)
			if not os.path.exists(filename):
				return filename
			i += 1

	def _get_source(self, uri):
		basename = os.path.basename(uri)
		local_name = self._pkg_dir + "/" + basename
		if not os.path.exists(local_name):
			dl_bytes = 0
			with requests.get(uri) as response, open(local_name, "wb") as f:
				response.raise_for_status()
				for chunk in response.iter_content(chunk_size = 1024 * 1024):
					dl_bytes += len(chunk)
					f.write(chunk)
					_log.debug("%s: %.1f MiB downloaded" % (uri, dl_bytes / 1024 / 1024))
		return local_name

	def _execute(self, cmd, env = None):
		logfile = self._next_logfile()
		all_env = dict(os.environ)
		if env is not None:
			all_env.update(env)
		_log.debug("Running: %s log %s", CmdlineEscape().cmdline(cmd), os.path.basename(logfile))
		with open(logfile, "wb") as f:
			f.write(("Running: %s\n" % (CmdlineEscape().cmdline(cmd, env = env))).encode())
			f.write(("CWD:     %s\n" % (os.getcwd())).encode())
			f.write(b"\n\n\n")
			f.flush()
			subprocess.check_call(cmd, env = all_env, stdout = f, stderr = subprocess.STDOUT)

	def _extract(self, src_filename, dirname):
		if src_filename.endswith(".tar.gz"):
			_log.info("Extracting .tar.gz image %s to %s", src_filename, dirname)
			ExecTools.pipe_exec([
				[ "pigz", "-d", "-c", src_filename ],
				[ "tar", "-C", dirname, "-x" ],
			])
		else:
			raise NotImplementedError("Do not know how to extract: %s" % (src_filename))

	def _build(self, ingredient_no, dirname, pkg, ingredient):
		ruleset = pkg.get("ruleset", "configure/make")
		_log.info("Ingredient %d: Building %s-%s according to %s ruleset", ingredient_no, pkg["name"], pkg["version"], ruleset)
		if ruleset == "configure/make":
			with WorkDir(dirname):
				os.mkdir("build")
				os.chdir("build")
				cmd = [ "../configure" ] + pkg["opts"]["configure"]
				self._execute(cmd, env = pkg.get("env", { }))

				self._execute([ "make", "-j%d" % (multiprocessing.cpu_count()) ], env = pkg.get("env", { }))
				self._execute([ "make", "install" ], env = pkg.get("env", { }))
		else:
			raise NotImplementedError(ruleset)

	def _run_build_ingredient(self, ingredient, ingredient_no):
		pkg = self._pkg_defs.get(ingredient["name"], self._recipe.arch, flags = ingredient.get("flags", [ ]))
		source = self._get_source(pkg["src"]["uri"])
		tmpdir = tempfile.mkdtemp(prefix = "pktbuilder_")
		try:
			self._extract(source, tmpdir)
			if "subdir" in pkg["src"]:
				subdir = tmpdir + "/" + pkg["src"]["subdir"]
			else:
				subdir = tmpdir + "/" + ingredient["name"] + "-" + pkg["src"]["version"]
			if not os.path.isdir(subdir):
				raise Exception("Subdir does not exist after extraction: %s" % (subdir))
			self._build(ingredient_no, subdir, pkg, ingredient)
		finally:
			if not self._args.preserve_tempfiles:
				shutil.rmtree(tmpdir)

	def _run_writefile_ingredient(self, ingredient, ingredient_no):
		filename = self._variables.substitute(ingredient["filename"])
		with contextlib.suppress(FileExistsError):
			os.makedirs(os.path.dirname(filename))
		with open(filename, "w") as f:
			f.write(self._variables.substitute(ingredient["content"]))

	def run(self):
		for (ingredient_no, ingredient) in enumerate(self._recipe, 1):
			if ingredient_no < self._args.start_at:
				continue
			ingredient_type = ingredient.get("type", "build")
			if ingredient_type == "build":
				self._run_build_ingredient(ingredient, ingredient_no)
			elif ingredient_type == "writefile":
				self._run_writefile_ingredient(ingredient, ingredient_no)
			else:
				raise NotImplementedError(ingredient_type)
			if self._args.one_pkg_only:
				_log.info("Breaking off after one package.")
				break
