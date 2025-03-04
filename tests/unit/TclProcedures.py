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
from tkinter  import TclError
from unittest import TestCase as TestCase

from pyTooling.Common import firstPair, firstValue, firstItem
from pyVHDLModel      import VHDLVersion

from pyEDAA.OSVVM.Environment import Library, VHDLSourceFile, GenericValue, Testcase, Testsuite, Context
from pyEDAA.OSVVM.Tcl         import OsvvmProFileProcessor, getException

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


class BasicProcedures(TestCase):
	def setUp(self):
		from pyEDAA.OSVVM.Environment import osvvmContext

		osvvmContext.Clear()

	def test_Library(self) -> None:
		print()
		processor = OsvvmProFileProcessor()

		code = dedent(f"""\
			library lib
			""")

		try:
			processor._tcl.eval(code)
		except TclError as ex:
			raise getException(ex, processor.Context)

		context = processor.Context

		self.assertEqual(1, len(context.Libraries))
		libraryName, library = firstPair(context.Libraries)
		self.assertEqual(library, context.Library)
		self.assertEqual("lib", libraryName)
		self.assertEqual("lib", library.Name)
		self.assertEqual(0, len(library.Files))

	def test_Analyze1(self) -> None:
		print()
		processor = OsvvmProFileProcessor()

		file1 = Path("tests/examples/simple/lib1_file1.vhdl")

		code = dedent(f"""\
			analyze {file1.as_posix()}
			""")

		try:
			processor._tcl.eval(code)
		except TclError as ex:
			raise getException(ex, processor.Context)

		context = processor.Context

		self.assertEqual(1, len(context.Libraries))
		self.assertEqual("default", context.Library.Name)
		self.assertEqual(context.Library, context.Libraries["default"])

		library = context.Library
		self.assertEqual(1, len(library.Files))
		vhdlFile = library.Files[0]
		self.assertEqual(file1, vhdlFile.Path)
		self.assertEqual(VHDLVersion.VHDL2008, vhdlFile.VHDLVersion)

	def test_Analyze2(self) -> None:
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
			raise getException(ex, processor.Context)

		context = processor.Context

		self.assertEqual(1, len(context.Libraries))
		self.assertEqual("default", context.Library.Name)
		self.assertEqual(context.Library, context.Libraries["default"])

		library = context.Library
		self.assertEqual(2, len(library.Files))
		self.assertEqual(file1, library.Files[0].Path)
		self.assertEqual(file2, library.Files[1].Path)

	def test_Library1_Analyze1(self) -> None:
		print()
		processor = OsvvmProFileProcessor()

		file1 = Path("tests/examples/simple/lib1_file1.vhdl")

		code = dedent(f"""\
			library lib
			analyze {file1.as_posix()}
			""")

		try:
			processor._tcl.eval(code)
		except TclError as ex:
			raise getException(ex, processor.Context)

		context = processor.Context

		self.assertEqual(1, len(context.Libraries))
		libraryName, library = firstPair(context.Libraries)
		self.assertEqual(library, context.Library)
		self.assertEqual("lib", libraryName)
		self.assertEqual("lib", library.Name)

		self.assertEqual(1, len(library.Files))
		vhdlFile = library.Files[0]
		self.assertEqual(file1, vhdlFile.Path)
		self.assertEqual(VHDLVersion.VHDL2008, vhdlFile.VHDLVersion)

	def test_Library2_Analyze3(self) -> None:
		print()
		processor = OsvvmProFileProcessor()

		file1_1 = Path("tests/examples/simple/lib1_file1.vhdl")
		file2_1 = Path("tests/examples/simple/lib2_file1.vhdl")
		file1_2 = Path("tests/examples/simple/lib1_file2.vhdl")

		code = dedent(f"""\
			library lib1
			analyze {file1_1.as_posix()}

			library lib2
			analyze {file2_1.as_posix()}

			library lib1
			analyze {file1_2.as_posix()}
			""")

		try:
			processor._tcl.eval(code)
		except TclError as ex:
			raise getException(ex, processor.Context)

		context = processor.Context

		self.assertEqual(2, len(context.Libraries))
		libraryName, library = firstPair(context.Libraries)
		self.assertEqual(library, context.Library)
		self.assertEqual("lib1", libraryName)
		self.assertEqual("lib1", library.Name)

		self.assertEqual(2, len(library.Files))
		self.assertEqual(file1_1, library.Files[0].Path)
		self.assertEqual(file1_2, library.Files[1].Path)

		library = context.Libraries["lib2"]
		self.assertEqual("lib2", library.Name)
		self.assertEqual(1, len(library.Files))
		self.assertEqual(file2_1, library.Files[0].Path)

	def test_Testsuite(self) -> None:
		print()
		processor = OsvvmProFileProcessor()

		code = dedent(f"""\
			TestSuite ts
			""")

		try:
			processor._tcl.eval(code)
		except TclError as ex:
			raise getException(ex, processor.Context)

		context = processor.Context

		self.assertEqual(1, len(context.Testsuites))
		testsuiteName, testsuite = firstPair(context.Testsuites)
		self.assertEqual("ts", testsuiteName)
		self.assertEqual("ts", testsuite.Name)
		self.assertEqual(testsuite, context.Testsuite)
		self.assertEqual(0, len(testsuite.Testcases))

	def test_TestName(self) -> None:
		print()
		processor = OsvvmProFileProcessor()

		code = dedent(f"""\
			TestName tn
			""")

		try:
			processor._tcl.eval(code)
		except TclError as ex:
			raise getException(ex, processor.Context)

		context = processor.Context

		self.assertEqual(1, len(context.Testsuites))
		testsuiteName, testsuite = firstPair(context.Testsuites)
		self.assertEqual("default", testsuiteName)
		self.assertEqual("default", testsuite.Name)
		self.assertEqual(testsuite, context.Testsuite)

		self.assertEqual(1, len(testsuite.Testcases))
		testcaseName, testcase = firstPair(testsuite.Testcases)
		self.assertEqual("tn", testcaseName)
		self.assertEqual("tn", testcase.Name)
		self.assertEqual(testcase, context.TestCase)
		self.assertEqual(0, len(testcase.Generics))

	# def test_Simulate(self) -> None:
	# 	print()
	# 	processor = OsvvmProFileProcessor()
	#
	# 	code = dedent(f"""\
	# 		simulate tb
	# 		""")
	#
	# 	try:
	# 		processor._tcl.eval(code)
	# 	except TclError as ex:
	# 		if str(ex) == "":
	# 			ex = processor.Context.LastException
	# 		raise ex
	#
	# 	context = processor.Context
	#
	# 	self.assertEqual(1, len(context.Libraries))

	def test_RunTest(self) -> None:
		print()
		processor = OsvvmProFileProcessor()

		file1 = Path("tests/examples/simple/lib1_file1.vhdl")

		code = dedent(f"""\
			RunTest {file1.as_posix()}
			""")

		try:
			processor._tcl.eval(code)
		except TclError as ex:
			raise getException(ex, processor.Context)

		context = processor.Context

		self.assertEqual(1, len(context.Libraries))
		library = firstValue(context.Libraries)
		self.assertEqual("default", library.Name)

		self.assertEqual(1, len(library.Files))
		vhdlFile = firstItem(library.Files)
		self.assertEqual(file1, vhdlFile.Path)

		self.assertEqual(1, len(context.Testsuites))
		testsuite = firstValue(context.Testsuites)
		self.assertEqual("default", testsuite.Name)

		self.assertEqual(1, len(testsuite.Testcases))
		testcase = firstValue(testsuite.Testcases)
		self.assertEqual("lib1_file1", testcase.Name)
		self.assertEqual(0, len(testcase.Generics))


class NoOperation(TestCase):
	def setUp(self):
		from pyEDAA.OSVVM.Environment import osvvmContext

		osvvmContext.Clear()

	def test_Puts(self) -> None:
		print()
		processor = OsvvmProFileProcessor()

		code = dedent(f"""\
			puts {{Hello World}}
			""")

		try:
			processor._tcl.eval(code)
		except TclError as ex:
			raise getException(ex, processor.Context)

		context = processor.Context
