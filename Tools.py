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

import subprocess

class ExecTools():
	@classmethod
	def pipe_exec(cls, cmds, output_file = None):
		proc = None
		f = None

		for (index, cmd) in enumerate(cmds):
			is_last_cmd = (index == len(cmds) - 1)
			if not is_last_cmd:
				proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, stdin = proc.stdout if (proc is not None) else subprocess.DEVNULL)
			else:
				if output_file is None:
					proc = subprocess.Popen(cmd, stdout = subprocess.DEVNULL, stdin = proc.stdout if (proc is not None) else subprocess.DEVNULL)
				else:
					f = open(output_file, "wb")
					proc = subprocess.Popen(cmd, stdout = f, stdin = proc.stdout if (proc is not None) else subprocess.DEVNULL)
		returncode = proc.wait()
		if f is not None:
			f.close()
		if returncode != 0:
			raise Exception("Returned %d: %s" % (returncode, str(cmds)))
