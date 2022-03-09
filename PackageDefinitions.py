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

import json
import re
import os

class PackageDefinitions():
	def __init__(self, filename, variables):
		with open(filename) as f:
			self._defs = json.load(f)
		self._variables = variables

	def _substitute(self, value, extra = None):
		for (srch, repl) in self._variables.items():
			src = "${" + srch + "}"
			value = value.replace(src, repl)
		if extra is not None:
			for (srch, repl) in extra.items():
				src = "${" + srch + "}"
				value = value.replace(src, repl)
		return value

	def _parse_opts(self, opts, arch, flags):
		result = [ ]
		for opt in opts:
			if isinstance(opt, str):
				result.append(self._substitute(opt))
			else:
				(condition, value) = opt
				if condition.startswith("arch="):
					if re.fullmatch(condition[5:], arch):
						result.append(self._substitute(value))
				elif condition.startswith("flag="):
					flagname = condition[5:]
					if flagname in flags:
						result.append(self._substitute(value))
				else:
					raise NotImplementedError("Unknown condition: %s" % (condition))
		return result

	def get_version(self, name, version, arch, flags):
		if name not in self._defs:
			raise Exception("No such package: %s" % (name))
		definition = dict(self._defs[name])
		definition["name"] = name
		definition["version"] = version
		definition["src"] = next(item for item in definition["src"] if (item["version"] == version))
		definition["src"]["uri"] = definition["src"]["uri"].replace("${version}", definition["src"]["version"])
		definition["opts"] = { name: self._parse_opts(opt, arch, flags) for (name, opt) in definition.get("opts", { }).items() }
		if "env" in definition:
			for varname in definition["env"]:
				extra = { varname: os.environ.get(varname, "") }
				definition["env"][varname] = self._substitute(definition["env"][varname], extra)

		return definition

	def get(self, name, arch, flags):
		if name in self._defs:
			latest_version = self._defs[name]["src"][-1]["version"]
			return self.get_version(name, latest_version, arch, flags)
		raise Exception("No such package: %s" % (name))
