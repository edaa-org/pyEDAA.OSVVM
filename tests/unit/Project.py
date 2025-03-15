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

from pyTooling.Common import firstPair
from pyVHDLModel      import VHDLVersion

from pyEDAA.OSVVM.Environment import VHDLSourceFile, VHDLLibrary
from pyEDAA.OSVVM.Environment import GenericValue, Testcase, Testsuite
from pyEDAA.OSVVM.Environment import Context, Project, Build


if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


class Instantiate(TestCase):
	def test_VHDLSourceFile(self) -> None:
		path = Path("source.vhdl")
		vhdlFile = VHDLSourceFile(path, VHDLVersion.VHDL2008)

		self.assertIsNone(vhdlFile.Parent)
		self.assertIsNone(vhdlFile.VHDLLibrary)
		self.assertEqual(path, vhdlFile.Path)
		self.assertEqual(VHDLVersion.VHDL2008, vhdlFile.VHDLVersion)

	def test_VHDLSourceFile_Library(self) -> None:
		library = VHDLLibrary("library")

		path = Path("source.vhdl")
		vhdlFile = VHDLSourceFile(path, VHDLVersion.VHDL2008, library)

		self.assertIs(library, vhdlFile.Parent)
		self.assertIs(library, vhdlFile.VHDLLibrary)
		self.assertEqual(path, vhdlFile.Path)
		self.assertEqual(VHDLVersion.VHDL2008, vhdlFile.VHDLVersion)
		self.assertEqual(f"VHDLSourceFile: source.vhdl", repr(vhdlFile))

	def test_Library(self) -> None:
		library = VHDLLibrary("library")

		self.assertEqual("library", library.Name)
		self.assertIsNone(library.Parent)
		self.assertIsNone(library.Build)
		self.assertEqual(0, len(library.Files))
		self.assertEqual(f"VHDLLibrary: library", repr(library))

	def test_Library_VHDLSourceFiles(self) -> None:
		path1 = Path("source1.vhdl")
		path2 = Path("source2.vhdl")
		paths = (path1, path2)
		vhdlFile1 = VHDLSourceFile(path1, VHDLVersion.VHDL2008)
		vhdlFile2 = VHDLSourceFile(path2, VHDLVersion.VHDL2008)
		vhdlFiles = (vhdlFile1, vhdlFile2)

		library = VHDLLibrary("library", vhdlFiles)

		self.assertEqual("library", library.Name)
		self.assertIsNone(library.Parent)
		self.assertIsNone(library.Build)
		self.assertEqual(2, len(library.Files))
		for i, vhdlFile in enumerate(library.Files):
			self.assertIs(library, vhdlFile.VHDLLibrary)
			self.assertEqual(vhdlFiles[i], vhdlFile)
			self.assertEqual(paths[i], vhdlFile.Path)

	def test_Library_Build(self) -> None:
		build = Build("build")
		library = VHDLLibrary("library", build=build)

		self.assertEqual("library", library.Name)
		self.assertIs(build, library.Parent)
		self.assertIs(build, library.Build)
		self.assertEqual(0, len(library.Files))

	def test_GenericValue(self) -> None:
		generic = GenericValue("generic", "value")

		self.assertEqual("generic", generic.Name)
		self.assertEqual("value", generic.Value)

	def test_Testcase(self) -> None:
		tc = Testcase("tc")

		self.assertEqual("tc", tc.Name)
		self.assertIsNone(tc.Parent)
		self.assertIsNone(tc.Testsuite)
		self.assertIsNone(tc.ToplevelName)
		self.assertEqual(0, len(tc.Generics))
		self.assertEqual(f"Testcase: tc", repr(tc))

	def test_Testcase_Testsuite(self) -> None:
		ts = Testsuite("ts")
		tc = Testcase("tc", testsuite=ts)

		self.assertEqual("tc", tc.Name)
		self.assertIs(ts, tc.Parent)
		self.assertIs(ts, tc.Testsuite)
		self.assertIsNone(tc.ToplevelName)
		self.assertEqual(0, len(tc.Generics))
		self.assertEqual(f"Testcase: tc", repr(tc))

	def test_Testcase_GenericsList(self) -> None:
		generic1 = GenericValue("param1", "value1")
		generic2 = GenericValue("param2", "value2")
		generics = (generic1, generic2)
		tc = Testcase("tc", generics=generics)

		self.assertEqual("tc", tc.Name)
		self.assertIsNone(tc.Parent)
		self.assertIsNone(tc.Testsuite)
		self.assertIsNone(tc.ToplevelName)
		self.assertEqual(2, len(tc.Generics))
		for i, (genericName, genericValue) in enumerate(tc.Generics.items(), start=1):
			self.assertEqual(f"param{i}", genericName)
			self.assertEqual(f"value{i}", genericValue)
		self.assertEqual(f"Testcase: tc - [param1=value1, param2=value2]", repr(tc))

	def test_Testcase_GenericsDict(self) -> None:
		generics = {
			"param1": "value1",
			"param2": "value2",
		}
		tc = Testcase("tc", generics=generics)

		self.assertEqual("tc", tc.Name)
		self.assertIsNone(tc.Parent)
		self.assertIsNone(tc.Testsuite)
		self.assertIsNone(tc.ToplevelName)
		self.assertEqual(2, len(tc.Generics))
		for i, (genericName, genericValue) in enumerate(tc.Generics.items(), start=1):
			self.assertEqual(f"param{i}", genericName)
			self.assertEqual(f"value{i}", genericValue)
		self.assertEqual(f"Testcase: tc - [param1=value1, param2=value2]", repr(tc))

	def test_Testsuite(self) -> None:
		ts = Testsuite("ts")

		self.assertEqual("ts", ts.Name)
		self.assertIsNone(ts.Parent)
		self.assertIsNone(ts.Build)
		self.assertEqual(0, len(ts.Testcases))
		self.assertEqual(f"Testsuite: ts", repr(ts))

	def test_Testsuite_Build(self) -> None:
		build = Build("build")
		ts = Testsuite("ts", build=build)

		self.assertEqual("ts", ts.Name)
		self.assertIs(build, ts.Parent)
		self.assertIs(build, ts.Build)
		self.assertEqual(0, len(ts.Testcases))
		self.assertEqual(f"Testsuite: ts", repr(ts))

	def test_Testsuite_TestcasesList(self) -> None:
		tc1 = Testcase("tc1")
		tc2 = Testcase("tc2")
		testcases = (tc1, tc2)
		ts = Testsuite("ts", testcases)

		self.assertEqual("ts", ts.Name)
		self.assertIsNone(ts.Parent)
		self.assertIsNone(ts.Build)
		self.assertEqual(2, len(ts.Testcases))
		for i, (testcaseName, testcase) in enumerate(ts.Testcases.items()):
			self.assertIs(ts, testcase.Testsuite)
			self.assertEqual(f"tc{i+1}", testcaseName)
			self.assertEqual(testcases[i], testcase)
		self.assertEqual(f"Testsuite: ts", repr(ts))

	def test_Testsuite_TestcasesDict(self) -> None:
		testcases = {
			"tc1": Testcase("tc1"),
			"tc2": Testcase("tc2")
		}
		ts = Testsuite("ts", testcases)

		self.assertEqual("ts", ts.Name)
		self.assertIsNone(ts.Parent)
		self.assertIsNone(ts.Build)
		self.assertEqual(2, len(ts.Testcases))
		for i, (testcaseName, testcase) in enumerate(ts.Testcases.items()):
			self.assertIs(ts, testcase.Testsuite)
			self.assertEqual(f"tc{i+1}", testcaseName)
			self.assertEqual(testcases[testcaseName], testcase)
		self.assertEqual(f"Testsuite: ts", repr(ts))

	def test_Build(self) -> None:
		build = Build("build")

		self.assertEqual("build", build.Name)
		self.assertIsNone(build.Parent)
		self.assertIsNone(build.Project)
		self.assertEqual(0, len(build.VHDLLibraries))
		self.assertEqual(0, len(build.Testsuites))
		self.assertEqual(f"Build: build", repr(build))

	def test_Build_Project(self) -> None:
		project = Project("project")
		build = Build("build", project=project)

		self.assertEqual("build", build.Name)
		self.assertIs(project, build.Parent)
		self.assertIs(project, build.Project)
		self.assertEqual(0, len(build.VHDLLibraries))
		self.assertEqual(0, len(build.Testsuites))
		self.assertEqual(f"Build: build", repr(build))

	def test_Build_LibrariesList(self) -> None:
		library1 = VHDLLibrary("lib1")
		library2 = VHDLLibrary("lib2")
		libraries = (library1, library2)
		build = Build("build", vhdlLibraries=libraries)

		self.assertEqual("build", build.Name)
		self.assertIsNone(build.Parent)
		self.assertIsNone(build.Project)
		self.assertEqual(2, len(build.VHDLLibraries))
		for i, (libraryName, library) in enumerate(build.VHDLLibraries.items()):
			self.assertIs(build, library.Build)
			self.assertEqual(f"lib{i+1}", libraryName)
			self.assertEqual(libraries[i], library)
		self.assertEqual(0, len(build.Testsuites))
		self.assertEqual(f"Build: build", repr(build))

	def test_Build_LibrariesDict(self) -> None:
		libraries = {
			"lib1": VHDLLibrary("lib1"),
			"lib2": VHDLLibrary("lib2")
		}
		build = Build("build", vhdlLibraries=libraries)

		self.assertEqual("build", build.Name)
		self.assertIsNone(build.Parent)
		self.assertIsNone(build.Project)
		self.assertEqual(2, len(build.VHDLLibraries))
		for i, (libraryName, library) in enumerate(build.VHDLLibraries.items()):
			self.assertIs(build, library.Build)
			self.assertEqual(f"lib{i+1}", libraryName)
			self.assertEqual(libraries[libraryName], library)
		self.assertEqual(0, len(build.Testsuites))
		self.assertEqual(f"Build: build", repr(build))

	def test_Build_TestsuitesList(self) -> None:
		ts1 = Testsuite("ts1")
		ts2 = Testsuite("ts2")
		testsuites = (ts1, ts2)
		build = Build("build", testsuites=testsuites)

		self.assertEqual("build", build.Name)
		self.assertIsNone(build.Parent)
		self.assertIsNone(build.Project)
		self.assertEqual(0, len(build.VHDLLibraries))
		self.assertEqual(2, len(build.Testsuites))
		for i, (testsuiteName, testsuite) in enumerate(build.Testsuites.items()):
			self.assertIs(build, testsuite.Build)
			self.assertEqual(f"ts{i+1}", testsuiteName)
			self.assertEqual(testsuites[i], testsuite)
		self.assertEqual(f"Build: build", repr(build))

	def test_Build_TestsuitesDict(self) -> None:
		testsuites = {
			"ts1": Testsuite("ts1"),
			"ts2": Testsuite("ts2")
		}
		build = Build("build", testsuites=testsuites)

		self.assertEqual("build", build.Name)
		self.assertIsNone(build.Parent)
		self.assertIsNone(build.Project)
		self.assertEqual(0, len(build.VHDLLibraries))
		self.assertEqual(2, len(build.Testsuites))
		for i, (testsuiteName, testsuite) in enumerate(build.Testsuites.items()):
			self.assertIs(build, testsuite.Build)
			self.assertEqual(f"ts{i+1}", testsuiteName)
			self.assertEqual(testsuites[testsuiteName], testsuite)
		self.assertEqual(f"Build: build", repr(build))

	def test_Project(self) -> None:
		project = Project("project")

		self.assertEqual("project", project.Name)
		self.assertIsNone(project.Parent)
		self.assertEqual(0, len(project.Builds))
		self.assertEqual(f"Project: project", repr(project))

	def test_Project_BuildsList(self) -> None:
		build1 = Build("build1")
		build2 = Build("build2")
		builds = (build1, build2)
		project = Project("project", builds)

		self.assertEqual("project", project.Name)
		self.assertIsNone(project.Parent)
		self.assertEqual(2, len(project.Builds))
		for i, (buildName, build) in enumerate(project.Builds.items()):
			self.assertIs(project, build.Project)
			self.assertEqual(f"build{i+1}", buildName)
			self.assertEqual(builds[i], build)
		self.assertEqual(f"Project: project", repr(project))

	def test_Project_BuildsDict(self) -> None:
		builds = {
			"build1": Build("build1"),
			"build2": Build("build2")
		}
		project = Project("project", builds)

		self.assertEqual("project", project.Name)
		self.assertIsNone(project.Parent)
		self.assertEqual(2, len(project.Builds))
		for i, (buildName, build) in enumerate(project.Builds.items()):
			self.assertIs(project, build.Project)
			self.assertEqual(f"build{i+1}", buildName)
			self.assertEqual(builds[buildName], build)
		self.assertEqual(f"Project: project", repr(project))

	def test_Context(self) -> None:
		context = Context()

		cwd = Path.cwd()
		self.assertEqual(cwd, context.WorkingDirectory)
		self.assertEqual(cwd, context.CurrentDirectory)
		self.assertIsNone(context.VHDLLibrary)
		self.assertIsNone(context.TestCase)
		self.assertIsNone(context.Testsuite)
		self.assertEqual(0, len(context.IncludedFiles))
		self.assertEqual(0, len(context.VHDLLibraries))
		self.assertEqual(0, len(context.Testsuites))


class Operations(TestCase):
	def test_Testsuite_AddTestcase(self) -> None:
		tc = Testcase("tc")
		ts = Testsuite("ts")
		ts.AddTestcase(tc)

		self.assertEqual(1, len(ts.Testcases))

		testcaseName, testcase = firstPair(ts.Testcases)
		self.assertIs(tc, testcase)
		self.assertIs(ts, testcase.Testsuite)
		self.assertEqual("tc", testcaseName)

	def test_Build_AddLibrary(self) -> None:
		lib = VHDLLibrary("lib")
		build = Build("build")
		build.AddVHDLLibrary(lib)

		self.assertEqual(1, len(build.VHDLLibraries))

		libraryName, library = firstPair(build.VHDLLibraries)
		self.assertIs(lib, library)
		self.assertIs(build, library.Build)
		self.assertEqual("lib", libraryName)

	def test_Build_AddTestsuite(self) -> None:
		ts = Testsuite("ts")
		build = Build("build")
		build.AddTestsuite(ts)

		self.assertEqual(1, len(build.Testsuites))

		testsuiteName, testsuite = firstPair(build.Testsuites)
		self.assertIs(ts, testsuite)
		self.assertIs(build, testsuite.Build)
		self.assertEqual("ts", testsuiteName)

	def test_Project_AddBuild(self) -> None:
		bld = Build("build")
		project = Project("project")
		project.AddBuild(bld)

		self.assertEqual(1, len(project.Builds))

		buildName, build = firstPair(project.Builds)
		self.assertIs(bld, build)
		self.assertIs(project, build.Project)
		self.assertEqual("build", buildName)
