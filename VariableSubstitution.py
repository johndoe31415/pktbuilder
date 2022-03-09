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

class VariableSubstitution():
	def __init__(self, variables):
		self._vars = variables

	@staticmethod
	def __substitute(text, vardict):
		for (srch, repl) in vardict.items():
			src = "${" + srch + "}"
			text = text.replace(src, repl)
		return text

	def substitute(self, text, extra = None):
		text = self.__substitute(text, self._vars)
		if extra is not None:
			text = self.__substitute(text, extra)
		return text
