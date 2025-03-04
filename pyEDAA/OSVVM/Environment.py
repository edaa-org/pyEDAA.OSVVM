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
from pathlib import Path
from typing  import Optional as Nullable, List, Dict

from pyTooling.Decorators  import readonly, export
from pyTooling.MetaClasses import ExtendedType
from pyVHDLModel           import VHDLVersion

from pyEDAA.OSVVM          import OSVVMException


__all__ = ["osvvmContext"]


@export
class Base(metaclass=ExtendedType):
	pass


@export
class SourceFile(Base):
	"""A base-class describing any source file (VHDL, Verilog, ...) supported by OSVVM Scripts."""

	_path: Path

	def __init__(self, path: Path) -> None:
		self._path = path

	@readonly
	def Path(self) -> Path:
		return self._path


@export
class VHDLSourceFile(SourceFile):
	_vhdlVersion: VHDLVersion

	def __init__(self, path: Path, vhdlVersion: Nullable[VHDLVersion] = None):
		super().__init__(path)

		self._vhdlVersion = vhdlVersion

	@property
	def VHDLVersion(self) -> VHDLVersion:
		return self._vhdlVersion

	@VHDLVersion.setter
	def VHDLVersion(self, value: VHDLVersion) -> None:
		self._vhdlVersion = value


@export
class Library(Base):
	"""A VHDL library collecting multiple VHDL files containing VHDL design units."""

	_name: str
	_files: List[VHDLSourceFile]

	def __init__(self, name: str) -> None:
		self._name = name
		self._files = []

	@readonly
	def Name(self) -> str:
		return self._name

	@readonly
	def Files(self) -> List[SourceFile]:
		return self._files

	def AddFile(self, file: VHDLSourceFile) -> None:
		self._files.append(file)

	def __repr__(self) -> str:
		return f"VHDLLibrary: {self._name}"


@export
class GenericValue(Base):
	_name: str
	_value: str

	def __init__(self, name: str, value: str) -> None:
		self._name = name
		self._value = value

	@readonly
	def Name(self) -> str:
		return self._name

	@readonly
	def Value(self) -> str:
		return self._value

	def __repr__(self) -> str:
		return f"{self._name} = {self._value}"


@export
class Testcase(Base):
	_name: str
	_toplevelName: Nullable[str]
	_generics: Dict[str, str]

	def __init__(self, name: str) -> None:
		self._name = name
		self._toplevelName = None
		self._generics = {}

	@readonly
	def Name(self) -> str:
		return self._name

	@readonly
	def ToplevelName(self) -> str:
		return self._toplevelName

	@readonly
	def Generics(self) -> Dict[str, str]:
		return self._generics

	def SetToplevel(self, toplevelName: str) -> None:
		self._toplevelName = toplevelName

	def AddGeneric(self, genericValue: GenericValue):
		self._generics[genericValue._name] = genericValue._value

	def __repr__(self) -> str:
		return f"Testcase: {self._name} - [{', '.join([f'{n}={v}' for n,v in self._generics.items()])}]"


@export
class Testsuite(Base):
	_name:      str
	_testcases: Dict[str, Testcase]

	def __init__(self, name: str) -> None:
		self._name = name
		self._testcases = {}

	@readonly
	def Name(self) -> str:
		return self._name

	@readonly
	def Testcases(self) -> Dict[str, Testcase]:
		return self._testcases

	def AddTestcase(self, testcase: Testcase) -> None:
		self._testcases[testcase._name] = testcase

	def __repr__(self) -> str:
		return f"Testsuite: {self._name}"


@export
class Context(Base):
	# _tcl:              TclEnvironment

	_lastException:    Exception

	_workingDirectory: Path
	_currentDirectory: Path
	_includedFiles:    List[Path]

	_vhdlversion:      VHDLVersion

	_libraries:        Dict[str, Library]
	_library:          Nullable[Library]

	_testsuites:       Dict[str, Testsuite]
	_testsuite:        Nullable[Testsuite]
	_testcase:         Nullable[Testcase]
	_options:          Dict[int, GenericValue]

	def __init__(self) -> None:
		self._processor =        None
		self._lastException =    None

		self._workingDirectory = Path.cwd()
		self._currentDirectory = self._workingDirectory
		self._includedFiles =    []

		self._vhdlversion = VHDLVersion.VHDL2008

		self._library =    None
		self._libraries =  {}

		self._testcase =   None
		self._testsuite =  None
		self._testsuites = {}
		self._options =    {}

	def Clear(self) -> None:
		self._processor =        None
		self._lastException =    None

		self._workingDirectory = Path.cwd()
		self._currentDirectory = self._workingDirectory
		self._includedFiles =    []

		self._vhdlversion = VHDLVersion.VHDL2008

		self._library =    None
		self._libraries =  {}

		self._testcase =   None
		self._testsuite =  None
		self._testsuites = {}
		self._options =    {}

	@readonly
	def Processor(self):  # -> "Tk":
		return self._processor

	@property
	def LastException(self) -> Exception:
		lastException = self._lastException
		self._lastException = None
		return lastException

	@LastException.setter
	def LastException(self, value: Exception) -> None:
		self._lastException = value

	@readonly
	def WorkingDirectory(self) -> Path:
		return self._workingDirectory

	@readonly
	def CurrentDirectory(self) -> Path:
		return self._currentDirectory

	@property
	def VHDLVersion(self) -> VHDLVersion:
		return self._vhdlversion

	@VHDLVersion.setter
	def VHDLVersion(self, value: VHDLVersion) -> None:
		self._vhdlversion = value

	@readonly
	def IncludedFiles(self) -> List[Path]:
		return self._includedFiles

	@readonly
	def Libraries(self) -> Dict[str, Library]:
		return self._libraries

	@readonly
	def Library(self) -> Library:
		return self._library

	@readonly
	def Testsuites(self) -> Dict[str, Testsuite]:
		return self._testsuites

	@readonly
	def Testsuite(self) -> Testsuite:
		return self._testsuite

	@readonly
	def TestCase(self) -> Testcase:
		return self._testcase

	def IncludeFile(self, proFileOrBuildDirectory: Path) -> Path:
		if proFileOrBuildDirectory.is_absolute():
			ex = OSVVMException(f"Absolute path '{proFileOrBuildDirectory}' not supported.")
			self._lastException = ex
			raise ex

		path = (self._currentDirectory / proFileOrBuildDirectory).resolve()
		if path.is_file():
			if path.suffix == ".pro":
				self._currentDirectory = path.parent.relative_to(self._workingDirectory, walk_up=True)
				proFile = self._currentDirectory / path.name
			else:
				ex = OSVVMException(f"Path '{proFileOrBuildDirectory}' is not a *.pro file.")
				self._lastException = ex
				raise ex
		elif path.is_dir():
			self._currentDirectory = path
			proFile = path / "build.pro"
			if not proFile.exists():
				proFile = path / f"{path.name}.pro"
				if not proFile.exists():
					ex = OSVVMException(f"Path '{proFileOrBuildDirectory}' is not a build directory.")
					ex.__cause__ = FileNotFoundError(path / "build.pro")
					self._lastException = ex
					raise ex
		else:
			ex = OSVVMException(f"Path '{proFileOrBuildDirectory}' is not a *.pro file or build directory.")
			self._lastException = ex
			raise ex

		self._includedFiles.append(proFile)
		return proFile

	def EvaluateFile(self, proFile: Path) -> None:
		self._processor.EvaluateProFile(proFile)

	def SetLibrary(self, name: str):
		try:
			self._library = self._libraries[name]
		except KeyError:
			self._library = Library(name)
			self._libraries[name] = self._library

	def AddVHDLFile(self, vhdlFile: VHDLSourceFile) -> None:
		if self._library is None:
			self.SetLibrary("default")

		vhdlFile.VHDLVersion = self._vhdlversion
		self._library.AddFile(vhdlFile)

	def SetTestsuite(self, testsuiteName: str):
		try:
			self._testsuite = self._testsuites[testsuiteName]
		except KeyError:
			self._testsuite = Testsuite(testsuiteName)
			self._testsuites[testsuiteName] = self._testsuite

	def AddTestcase(self, testName: str) -> TestCase:
		if self._testsuite is None:
			self.SetTestsuite("default")

		self._testcase = Testcase(testName)
		self._testsuite._testcases[testName] = self._testcase

		return self._testcase

	def SetTestcaseToplevel(self, toplevel: str) -> TestCase:
		if self._testcase is None:
			ex = OSVVMException("Can't set testcase toplevel, because no testcase setup.")
			self._lastException = ex
			raise ex

		self._testcase.SetToplevel(toplevel)

		return self._testcase

	def AddOption(self, genericValue: GenericValue):
		optionID = id(genericValue)
		self._options[optionID] = genericValue

		return optionID


osvvmContext: Context = Context()
