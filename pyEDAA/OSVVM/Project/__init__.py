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
from typing import Optional as Nullable, List, Dict, Mapping, Iterable, TypeVar, Generic, Generator

from pyTooling.Common      import getFullyQualifiedName
from pyTooling.Decorators  import readonly, export
from pyTooling.MetaClasses import ExtendedType
from pyVHDLModel           import VHDLVersion

from pyEDAA.OSVVM          import OSVVMException


__all__ = ["osvvmContext"]


_ParentType = TypeVar("_ParentType", bound="Base")


@export
class Base(Generic[_ParentType], metaclass=ExtendedType, slots=True):
	_parent: Nullable[_ParentType]

	def __init__(self, parent: Nullable[_ParentType] = None):
		self._parent = parent

	@readonly
	def Parent(self) -> _ParentType:
		return self._parent


@export
class Named(Base[_ParentType], Generic[_ParentType]):
	_name:  str

	def __init__(
		self,
		name:   str,
		parent: Nullable[_ParentType] = None
	) -> None:
		super().__init__(parent)

		if not isinstance(name, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'name' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex

		self._name = name

	@readonly
	def Name(self) -> str:
		return self._name

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}: {self._name}"


@export
class Option(metaclass=ExtendedType, slots=True):
	pass


@export
class NoNullRangeWarning(Option):
	def __init__(self) -> None:
		super().__init__()

	def __repr__(self) -> str:
		return "NoNullRangeWarning"


@export
class SourceFile(Base[_ParentType], Generic[_ParentType]):
	"""A base-class describing any source file (VHDL, Verilog, ...) supported by OSVVM Scripts."""

	_path: Path

	def __init__(
		self,
		path:   Path,
		parent: Nullable[Base] = None
	) -> None:
		super().__init__(parent)

		if not isinstance(path, Path):  # pragma: no cover
			ex = TypeError(f"Parameter 'path' is not a Path.")
			ex.add_note(f"Got type '{getFullyQualifiedName(path)}'.")
			raise ex

		self._path = path

	@readonly
	def Path(self) -> Path:
		return self._path

	def __repr__(self) -> str:
		return f"SourceFile: {self._path}"


@export
class VHDLSourceFile(SourceFile["VHDLLibrary"]):
	_vhdlVersion:        VHDLVersion
	_noNullRangeWarning: Nullable[bool]

	def __init__(
		self,
		path: Path,
		vhdlVersion:        VHDLVersion = VHDLVersion.VHDL2008,
		vhdlLibrary:        Nullable["VHDLLibrary"] = None,
		noNullRangeWarning: Nullable[bool] = None
	):
		if vhdlLibrary is None:
			super().__init__(path, None)
		elif isinstance(vhdlLibrary, VHDLLibrary):
			super().__init__(path, vhdlLibrary)
			vhdlLibrary._files.append(self)
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'vhdlLibrary' is not a Library.")
			ex.add_note(f"Got type '{getFullyQualifiedName(vhdlLibrary)}'.")
			raise ex

		if not isinstance(vhdlVersion, VHDLVersion):  # pragma: no cover
			ex = TypeError(f"Parameter 'vhdlVersion' is not a VHDLVersion.")
			ex.add_note(f"Got type '{getFullyQualifiedName(vhdlVersion)}'.")
			raise ex

		self._vhdlVersion = vhdlVersion

		if noNullRangeWarning is not None and not isinstance(noNullRangeWarning, bool):
			ex = TypeError(f"Parameter 'noNullRangeWarning' is not a boolean.")
			ex.add_note(f"Got type '{getFullyQualifiedName(noNullRangeWarning)}'.")
			raise ex

		self._noNullRangeWarning = noNullRangeWarning

	@readonly
	def VHDLLibrary(self) -> Nullable["VHDLLibrary"]:
		return self._parent

	@property
	def VHDLVersion(self) -> VHDLVersion:
		return self._vhdlVersion

	@VHDLVersion.setter
	def VHDLVersion(self, value: VHDLVersion) -> None:
		if not isinstance(value, VHDLVersion):
			ex = TypeError(f"Parameter 'value' is not a VHDLVersion.")
			ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
			raise ex

		self._vhdlVersion = value

	@property
	def NoNullRangeWarning(self) -> bool:
		return self._noNullRangeWarning

	@NoNullRangeWarning.setter
	def NoNullRangeWarning(self, value: bool) -> None:
		if value is not None and not isinstance(value, bool):
			ex = TypeError(f"Parameter 'value' is not a boolean.")
			ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
			raise ex

		self._noNullRangeWarning = value

	def __repr__(self) -> str:
		options = ""
		if self._noNullRangeWarning is not None:
			options += f", NoNullRangeWarning"
		return f"VHDLSourceFile: {self._path} ({self._vhdlVersion}{options})"

@export
class VHDLLibrary(Named["Build"]):
	"""A VHDL library collecting multiple VHDL files containing VHDL design units."""

	_files: List[VHDLSourceFile]

	def __init__(
		self,
		name:      str,
		vhdlFiles: Nullable[Iterable[VHDLSourceFile]] = None,
		build:     Nullable["Build"] = None
	) -> None:
		if build is None:
			super().__init__(name, None)
		elif isinstance(build, Build):
			super().__init__(name, build)
			build._vhdlLibraries[name] = self
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'build' is not a Build.")
			ex.add_note(f"Got type '{getFullyQualifiedName(build)}'.")
			raise ex

		self._files = []
		if vhdlFiles is None:
			pass
		elif isinstance(vhdlFiles, Iterable):
			for vhdlFile in vhdlFiles:
				vhdlFile._parent = self
				self._files.append(vhdlFile)
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'vhdlFiles' is not an iterable of VHDLSourceFile.")
			ex.add_note(f"Got type '{getFullyQualifiedName(vhdlFiles)}'.")
			raise ex

	@readonly
	def Build(self) -> Nullable["Build"]:
		return self._parent

	@readonly
	def Files(self) -> List[SourceFile]:
		return self._files

	def AddFile(self, file: VHDLSourceFile) -> None:
		if not isinstance(file, VHDLSourceFile):  # pragma: no cover
			ex = TypeError(f"Parameter 'file' is not a VHDLSourceFile.")
			ex.add_note(f"Got type '{getFullyQualifiedName(file)}'.")
			raise ex

		file._parent = self
		self._files.append(file)

	def __repr__(self) -> str:
		return f"VHDLLibrary: {self._name}"


@export
class GenericValue(Option):
	_name:  str
	_value: str

	def __init__(
		self,
		name:   str,
		value:  str
	) -> None:
		super().__init__()

		if not isinstance(name, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'name' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex

		self._name = name

		if not isinstance(value, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'value' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
			raise ex

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
class Testcase(Named["Testsuite"]):
	_toplevelName: Nullable[str]
	_generics:     Dict[str, str]

	def __init__(
		self,
		name:         str,
		toplevelName: Nullable[str] = None,
		generics:     Nullable[Iterable[GenericValue] | Mapping[str, str]] = None,
		testsuite:    Nullable["Testsuite"] = None
	) -> None:
		if testsuite is None:
			super().__init__(name, None)
		elif isinstance(testsuite, Testsuite):
			super().__init__(name, testsuite)
			testsuite._testcases[name] = self
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'testsuite' is not a Testsuite.")
			ex.add_note(f"Got type '{getFullyQualifiedName(testsuite)}'.")
			raise ex

		if not (toplevelName is None or isinstance(toplevelName, str)):  # pragma: no cover
			ex = TypeError(f"Parameter 'toplevelName' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(toplevelName)}'.")
			raise ex

		self._toplevelName = toplevelName

		self._generics = {}
		if generics is None:
			pass
		elif isinstance(generics, Mapping):
			for key, value in generics.items():
				self._generics[key] = value
		elif isinstance(generics, Iterable):
			for item in generics:
				self._generics[item._name] = item._value
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'generics' is not an iterable of GenericValue nor a dictionary of strings.")
			ex.add_note(f"Got type '{getFullyQualifiedName(generics)}'.")
			raise ex

	@readonly
	def Testsuite(self) -> "Testsuite":
		return self._parent

	@readonly
	def ToplevelName(self) -> str:
		return self._toplevelName

	@readonly
	def Generics(self) -> Dict[str, str]:
		return self._generics

	def SetToplevel(self, toplevelName: str) -> None:
		if not isinstance(toplevelName, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'toplevelName' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(toplevelName)}'.")
			raise ex

		self._toplevelName = toplevelName

	def AddGeneric(self, genericValue: GenericValue):
		if not isinstance(genericValue, GenericValue):  # pragma: no cover
			ex = TypeError(f"Parameter 'genericValue' is not a GenericValue.")
			ex.add_note(f"Got type '{getFullyQualifiedName(genericValue)}'.")
			raise ex

		self._generics[genericValue._name] = genericValue._value

	def __repr__(self) -> str:
		generics = f" - [{', '.join([f'{n}={v}' for n,v in self._generics.items()])}]" if len(self._generics) > 0 else ""
		return f"Testcase: {self._name}{generics}"


@export
class Testsuite(Named["Build"]):
	_testcases: Dict[str, Testcase]

	def __init__(
		self,
		name: str,
		testcases: Nullable[Iterable[Testcase] | Mapping[str, Testcase]] = None,
		build:     Nullable["Build"] = None
	) -> None:
		if build is None:
			super().__init__(name, None)
		elif isinstance(build, Build):
			super().__init__(name, build)
			build._testsuites[name] = self
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'build' is not a Build.")
			ex.add_note(f"Got type '{getFullyQualifiedName(build)}'.")
			raise ex

		self._testcases = {}
		if testcases is None:
			pass
		elif isinstance(testcases, Mapping):
			for key, value in testcases.items():
				value._parent = self
				self._testcases[key] = value
		elif isinstance(testcases, Iterable):
			for item in testcases:
				item._parent = self
				self._testcases[item._name] = item
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'testcases' is not an iterable of Testcase nor a mapping of Testcase.")
			ex.add_note(f"Got type '{getFullyQualifiedName(testcases)}'.")
			raise ex

	@readonly
	def Build(self) -> Nullable["Build"]:
		return self._parent

	@readonly
	def Testcases(self) -> Dict[str, Testcase]:
		return self._testcases

	def AddTestcase(self, testcase: Testcase) -> None:
		if not isinstance(testcase, Testcase):  # pragma: no cover
			ex = TypeError(f"Parameter 'testcase' is not a Testcase.")
			ex.add_note(f"Got type '{getFullyQualifiedName(testcase)}'.")
			raise ex

		testcase._parent = self
		self._testcases[testcase._name] = testcase

	def __repr__(self) -> str:
		return f"Testsuite: {self._name}"


@export
class BuildName(Option):
	_name: str

	def __init__(
		self,
		name: str,
	) -> None:
		super().__init__()

		if not isinstance(name, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'name' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex

		self._name = name

	@readonly
	def Name(self) -> str:
		return self._name

	def __repr__(self) -> str:
		return f"BuildName: {self._name}"


@export
class Build(Named["Project"]):
	_includedFiles: List[Path]
	_vhdlLibraries: Dict[str, VHDLLibrary]
	_testsuites:    Dict[str, Testsuite]

	def __init__(
		self,
		name:          str,
		vhdlLibraries: Nullable[Iterable[VHDLLibrary] | Mapping[str, VHDLLibrary]] = None,
		testsuites:    Nullable[Iterable[Testsuite] | Mapping[str, Testsuite]] = None,
		project:       Nullable[Base] = None
	) -> None:
		if project is None:
			super().__init__(name, None)
		elif isinstance(project, Project):
			super().__init__(name, project)
			project._builds[name] = self
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'project' is not a Project.")
			ex.add_note(f"Got type '{getFullyQualifiedName(project)}'.")
			raise ex

		self._includedFiles = []
		self._vhdlLibraries = {}
		if vhdlLibraries is None:
			pass
		elif isinstance(vhdlLibraries, Mapping):
			for key, value in vhdlLibraries.items():
				value._parent = self
				self._vhdlLibraries[key] = value
		elif isinstance(vhdlLibraries, Iterable):
			for item in vhdlLibraries:
				item._parent = self
				self._vhdlLibraries[item._name] = item
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'libraries' is not an iterable of VHDLLibrary nor a mapping of VHDLLibrary.")
			ex.add_note(f"Got type '{getFullyQualifiedName(vhdlLibraries)}'.")
			raise ex

		self._testsuites = {}
		if testsuites is None:
			pass
		elif isinstance(testsuites, Mapping):
			for key, value in testsuites.items():
				value._parent = self
				self._testsuites[key] = value
		elif isinstance(testsuites, Iterable):
			for item in testsuites:
				item._parent = self
				self._testsuites[item._name] = item
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'testsuites' is not an iterable of Testsuite nor a mapping of Testsuite.")
			ex.add_note(f"Got type '{getFullyQualifiedName(testsuites)}'.")
			raise ex

	@readonly
	def Project(self) -> Nullable["Project"]:
		return self._parent

	@readonly
	def IncludedFiles(self) -> Generator[Path, None, None]:
		return (file for file in self._includedFiles)

	@readonly
	def VHDLLibraries(self) -> Dict[str, VHDLLibrary]:
		return self._vhdlLibraries

	@readonly
	def Testsuites(self) -> Dict[str, Testsuite]:
		return self._testsuites

	def AddVHDLLibrary(self, vhdlLibrary: VHDLLibrary) -> None:
		if not isinstance(vhdlLibrary, VHDLLibrary):  # pragma: no cover
			ex = TypeError(f"Parameter 'vhdlLibrary' is not a VHDLLibrary.")
			ex.add_note(f"Got type '{getFullyQualifiedName(vhdlLibrary)}'.")
			raise ex

		vhdlLibrary._parent = self
		self._vhdlLibraries[vhdlLibrary._name] = vhdlLibrary

	def AddTestsuite(self, testsuite: Testsuite) -> None:
		if not isinstance(testsuite, Testsuite):  # pragma: no cover
			ex = TypeError(f"Parameter 'testsuite' is not a Testsuite.")
			ex.add_note(f"Got type '{getFullyQualifiedName(testsuite)}'.")
			raise ex

		testsuite._parent = self
		self._testsuites[testsuite._name] = testsuite

	def __repr__(self) -> str:
		return f"Build: {self._name}"


@export
class Project(Named[None]):
	_builds: Dict[str, Build]

	def __init__(
		self,
		name:   str,
		builds: Nullable[Iterable[Build] | Mapping[str, Build]] = None
	) -> None:
		super().__init__(name, None)

		self._builds = {}
		if builds is None:
			pass
		elif isinstance(builds, Mapping):
			for key, value in builds.items():
				value._parent = self
				self._builds[key] = value
		elif isinstance(builds, Iterable):
			for item in builds:
				item._parent = self
				self._builds[item._name] = item
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'builds' is not an iterable of Build nor a mapping of Build.")
			ex.add_note(f"Got type '{getFullyQualifiedName(builds)}'.")
			raise ex

	@readonly
	def Builds(self) -> Dict[str, Build]:
		return self._builds

	@readonly
	def IncludedFiles(self) -> Generator[Path, None, None]:
		for build in self._builds.values():
			yield from build.IncludedFiles

	def AddBuild(self, build: Build) -> None:
		if not isinstance(build, Build):  # pragma: no cover
			ex = TypeError(f"Parameter 'build' is not a Build.")
			ex.add_note(f"Got type '{getFullyQualifiedName(build)}'.")
			raise ex

		build._parent = self
		self._builds[build._name] = build

	def __repr__(self) -> str:
		return f"Project: {self._name}"

@export
class Context(Base):
	# _tcl:              TclEnvironment

	_processor:        "OsvvmProFileProcessor"
	_lastException:    Exception

	_workingDirectory: Path
	_currentDirectory: Path
	_includedFiles:    List[Path]

	_vhdlversion:      VHDLVersion

	_vhdlLibraries:    Dict[str, VHDLLibrary]
	_vhdlLibrary:      Nullable[VHDLLibrary]

	_testsuites:       Dict[str, Testsuite]
	_testsuite:        Nullable[Testsuite]
	_testcase:         Nullable[Testcase]
	_options:          Dict[int, Option]

	_builds:           Dict[str, Build]
	_build:            Nullable[Build]

	def __init__(self) -> None:
		super().__init__()

		self._processor =        None
		self._lastException =    None

		self._workingDirectory = Path.cwd()
		self._currentDirectory = self._workingDirectory
		self._includedFiles =    []

		self._vhdlversion =      VHDLVersion.VHDL2008

		self._vhdlLibrary =      None
		self._vhdlLibraries =    {}

		self._testcase =         None
		self._testsuite =        None
		self._testsuites =       {}
		self._options =          {}

		self._build =            None
		self._builds =           {}

	def Clear(self) -> None:
		self._processor =        None
		self._lastException =    None

		self._workingDirectory = Path.cwd()
		self._currentDirectory = self._workingDirectory
		self._includedFiles =    []

		self._vhdlversion =      VHDLVersion.VHDL2008

		self._vhdlLibrary =      None
		self._vhdlLibraries =    {}

		self._testcase =         None
		self._testsuite =        None
		self._testsuites =       {}
		self._options =          {}

		self._build =            None
		self._builds =           {}

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
	def VHDLLibraries(self) -> Dict[str, VHDLLibrary]:
		return self._vhdlLibraries

	@readonly
	def VHDLLibrary(self) -> VHDLLibrary:
		return self._vhdlLibrary

	@readonly
	def Testsuites(self) -> Dict[str, Testsuite]:
		return self._testsuites

	@readonly
	def Testsuite(self) -> Testsuite:
		return self._testsuite

	@readonly
	def TestCase(self) -> Testcase:
		return self._testcase

	@readonly
	def Build(self) -> Build:
		return self._build

	@readonly
	def Builds(self) -> Dict[str, Build]:
		return self._builds

	def ToProject(self, projectName: str) -> Project:
		project = Project(projectName, self._builds)

		return project

	def BeginBuild(self, buildName: str) -> Build:
		if len(self._vhdlLibraries) > 0:
			raise OSVVMException(f"VHDL libraries have been created outside of an OSVVM build script.")
		if len(self._testsuites) > 0:
			raise OSVVMException(f"Testsuites have been created outside of an OSVVM build script.")

		build = Build(buildName)
		build._vhdlLibraries = self._vhdlLibraries
		build._testsuites = self._testsuites

		self._build = build
		self._builds[buildName] = build

		return build

	def EndBuild(self) -> Build:
		build = self._build

		self._vhdlLibrary = None
		self._vhdlLibraries = {}
		self._testcase = None
		self._testsuite = None
		self._testsuites = {}
		self._build = None

		return build

	def IncludeFile(self, proFileOrBuildDirectory: Path) -> Path:
		if not isinstance(proFileOrBuildDirectory, Path):  # pragma: no cover
			ex = TypeError(f"Parameter 'proFileOrBuildDirectory' is not a Path.")
			ex.add_note(f"Got type '{getFullyQualifiedName(proFileOrBuildDirectory)}'.")
			self._lastException = ex
			raise ex

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
				if not proFile.exists():  # pragma: no cover
					ex = OSVVMException(f"Path '{proFileOrBuildDirectory}' is not a build directory.")
					ex.__cause__ = FileNotFoundError(path / "build.pro")
					self._lastException = ex
					raise ex
		else:  # pragma: no cover
			ex = OSVVMException(f"Path '{proFileOrBuildDirectory}' is not a *.pro file or build directory.")
			self._lastException = ex
			raise ex

		self._includedFiles.append(proFile)
		return proFile

	def EvaluateFile(self, proFile: Path) -> None:
		self._processor.EvaluateProFile(proFile)

	def SetLibrary(self, name: str):
		try:
			self._vhdlLibrary = self._vhdlLibraries[name]
		except KeyError:
			self._vhdlLibrary = VHDLLibrary(name, build=self._build)
			self._vhdlLibraries[name] = self._vhdlLibrary

	def AddVHDLFile(self, vhdlFile: VHDLSourceFile) -> None:
		if self._vhdlLibrary is None:
			self.SetLibrary("default")

		vhdlFile.VHDLVersion = self._vhdlversion
		self._vhdlLibrary.AddFile(vhdlFile)

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
			ex = OSVVMException("Can't set testcase toplevel, because no testcase was setup.")
			self._lastException = ex
			raise ex

		self._testcase.SetToplevel(toplevel)

		return self._testcase

	def AddOption(self, option: Option) -> int:
		optionID = id(option)
		self._options[optionID] = option

		return optionID


osvvmContext: Context = Context()
"""
Global OSVVM processing context.

:type: Context
"""
