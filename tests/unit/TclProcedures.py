# ==================================================================================================================== #
#              _____ ____    _        _      ___  ______     ____     ____  __                                         #
#  _ __  _   _| ____|  _ \  / \      / \    / _ \/ ___\ \   / /\ \   / /  \/  |                                        #
# | '_ \| | | |  _| | | | |/ _ \    / _ \  | | | \___ \\ \ / /  \ \ / /| |\/| |                                        #
# | |_) | |_| | |___| |_| / ___ \  / ___ \ | |_| |___) |\ V /    \ V / | |  | |                                        #
# | .__/ \__, |_____|____/_/   \_\/_/   \_(_)___/|____/  \_/      \_/  |_|  |_|                                        #
# |_|    |___/                                                                                                         #
# ==================================================================================================================== #
# Authors:                                                                                                             #
#   Patrick Lehmann                                                                                                    #
#                                                                                                                      #
# License:                                                                                                             #
# ==================================================================================================================== #
# Copyright 2025-2025 Patrick Lehmann - Boetzingen, Germany                                                            #
#                                                                                                                      #
# Licensed under the Apache License, Version 2.0 (the "License");                                                      #
# you may not use this file except in compliance with the License.                                                     #
# You may obtain a copy of the License at                                                                              #
#                                                                                                                      #
#   http://www.apache.org/licenses/LICENSE-2.0                                                                         #
#                                                                                                                      #
# Unless required by applicable law or agreed to in writing, software                                                  #
# distributed under the License is distributed on an "AS IS" BASIS,                                                    #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                             #
# See the License for the specific language governing permissions and                                                  #
# limitations under the License.                                                                                       #
#                                                                                                                      #
# SPDX-License-Identifier: Apache-2.0                                                                                  #
# ==================================================================================================================== #
#
"""Tcl procedure tests."""
from pathlib  import Path
from textwrap import dedent
from tkinter import TclError
from unittest import TestCase as TestCase

from pyVHDLModel import VHDLVersion

from pyEDAA.OSVVM.Environment import Library, VHDLSourceFile, GenericValue, Testcase, Testsuite, Context
from pyEDAA.OSVVM.Tcl import OsvvmProFileProcessor

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


class BasicProcedures(TestCase):
	def test_Analyze(self) -> None:
		print()
		processor = OsvvmProFileProcessor()

		file1 = Path("tests/examples/simple/lib1_file1.vhdl")
		file2 = Path("tests/examples/simple/lib1_file2.vhdl")

		code = dedent(f"""\
			analyze {file1.as_posix()}
			analyze {file2.as_posix()}
			""")

		try:
			processor._tcl.eval(code)
		except TclError as ex:
			print(f"TCL Error: {ex}")
		context = processor.Context

		self.assertEqual(1, len(context.Libraries))
		self.assertEqual("default", context.Library.Name)
		self.assertEqual(context.Library, context.Libraries["default"])

		library = context.Library
		self.assertEqual(2, len(library.Files))
		self.assertEqual(file1, library.Files[0].Path)
		self.assertEqual(file2, library.Files[1].Path)
