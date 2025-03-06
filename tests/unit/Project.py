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
"""Instantiation tests for the project model."""
from pathlib  import Path
from unittest import TestCase as TestCase

from pyVHDLModel import VHDLVersion

from pyEDAA.OSVVM.Environment import VHDLLibrary, VHDLSourceFile, GenericValue, Testcase, Testsuite, Context

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


class Instantiate(TestCase):
	def test_VHDLSourceFile(self) -> None:
		path = Path("source.vhdl")
		vhdlFile = VHDLSourceFile(path, VHDLVersion.VHDL2008)

		self.assertEqual(path, vhdlFile.Path)
		self.assertEqual(VHDLVersion.VHDL2008, vhdlFile.VHDLVersion)

	def test_Library(self) -> None:
		library = VHDLLibrary("library")

		self.assertEqual("library", library.Name)
		self.assertEqual(0, len(library.Files))

	def test_GenericValue(self) -> None:
		generic = GenericValue("generic", "value")

		self.assertEqual("generic", generic.Name)
		self.assertEqual("value", generic.Value)

	def test_Testcase(self) -> None:
		tc = Testcase("tc")

		self.assertEqual("tc", tc.Name)
		self.assertIsNone(tc.ToplevelName)
		self.assertEqual(0, len(tc.Generics))

	def test_Testsuite(self) -> None:
		ts = Testsuite("ts")

		self.assertEqual("ts", ts.Name)
		self.assertEqual(0, len(ts.Testcases))

	def test_Context(self) -> None:
		context = Context()

		cwd = Path.cwd()
		self.assertEqual(cwd, context.WorkingDirectory)
		self.assertEqual(cwd, context.CurrentDirectory)
		self.assertIsNone(context.Library)
		self.assertIsNone(context.TestCase)
		self.assertIsNone(context.Testsuite)
		self.assertEqual(0, len(context.IncludedFiles))
		self.assertEqual(0, len(context.Libraries))
		self.assertEqual(0, len(context.Testsuites))
