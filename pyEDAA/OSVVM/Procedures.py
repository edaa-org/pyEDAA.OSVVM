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
"""
This module implements OSVVM's TCL procedures (used in OSVVM's ``*.pro`` files) as Python functions.

These functions are then registered at the :class:`TCL processor <pyEDAA.OSVVM.TCL.OsvvmProFileProcessor>`, so procedure
calls within TCL code get "redirected" to these Python functions. Each function has access to a global variable
:data:`~pyEDAA.OSVVM.Environment.osvvmContext` to preserve its state or modify the context.
"""
from pathlib import Path
from typing  import Optional as Nullable, Tuple

from pyTooling.Decorators     import export
from pyVHDLModel              import VHDLVersion

from pyEDAA.OSVVM             import OSVVMException
from pyEDAA.OSVVM.Environment import osvvmContext, VHDLSourceFile, GenericValue
from pyEDAA.OSVVM.Environment import BuildName as OSVVM_BuildName, NoNullRangeWarning as OSVVM_NoNullRangeWarning


@export
def BuildName(name: str) -> int:
	try:
		buildName = OSVVM_BuildName(name)
		optionID = osvvmContext.AddOption(buildName)
	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex

	return optionID

@export
def build(file: str, *options: int) -> None:
	"""
	This function implements the behavior of OSVVM's ``build`` procedure.

	The current directory of the currently active context is preserved	while the referenced ``*.pro`` file is processed.
	After processing that file, the context's current directory is restored.

	The referenced file gets appended to a list of included files maintained by the context.

	:underline:`pro-file discovery algorithm:`

	1. If the path explicitly references a ``*.pro`` file, this file is used.
	2. If the path references a directory, it checks implicitly for a ``build.pro`` file, otherwise
	3. it checks implicitly for a ``<path>.pro`` file, named like the directories name.

	:param file:            Explicit path to a ``*.pro`` file or a directory containing an implicitly searched ``*.pro`` file.
	:param options:         Optional list of option IDs.
	:raises TypeError:      If parameter proFileOrBuildDirectory is not a Path.
	:raises OSVVMException: If parameter proFileOrBuildDirectory is an absolute path.
	:raises OSVVMException: If parameter proFileOrBuildDirectory is not a *.pro file or build directory.
	:raises OSVVMException: If a TclError was caught while processing a *.pro file.

	.. seealso::

	   * :func:`BuildName`
	   * :func:`include`
	   * :func:`ChangeWorkingDirectory`
	"""
	try:
		file = Path(file)
		buildName = None

		# Preserve current directory
		currentDirectory = osvvmContext._currentDirectory

		for optionID in options:
			try:
				option = osvvmContext._options[int(optionID)]
			except KeyError as e:  # pragma: no cover
				ex = OSVVMException(f"Option {optionID} not found in option dictionary.")
				ex.__cause__ = e
				osvvmContext.LastException = ex
				raise ex

			if isinstance(option, OSVVM_BuildName):
				buildName = option.Name
			else:  # pragma: no cover
				ex = OSVVMException(f"Option {optionID} is not a BuildName.")
				ex.__cause__ = TypeError()
				osvvmContext.LastException = ex
				raise ex

		# If no build name was specified, derive a name from *.pro file.
		if buildName is None:
			buildName = file.stem

		osvvmContext.BeginBuild(buildName)
		includeFile = osvvmContext.IncludeFile(file)
		osvvmContext.EvaluateFile(includeFile)
		osvvmContext.EndBuild()

		# Restore current directory after recursively evaluating *.pro files.
		osvvmContext._currentDirectory = currentDirectory

	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex


@export
def include(file: str) -> None:
	"""
	This function implements the behavior of OSVVM's ``include`` procedure.

	The current directory of the currently active context is preserved	while the referenced ``*.pro`` file is processed.
	After processing that file, the context's current directory is restored.

	The referenced file gets appended to a list of included files maintained by the context.

	:underline:`pro-file discovery algorithm:`

	1. If the path explicitly references a ``*.pro`` file, this file is used.
	2. If the path references a directory, it checks implicitly for a ``build.pro`` file, otherwise
	3. it checks implicitly for a ``<path>.pro`` file, named like the directories name.

	:param file:            Explicit path to a ``*.pro`` file or a directory containing an implicitly searched ``*.pro`` file.
	:raises TypeError:      If parameter proFileOrBuildDirectory is not a Path.
	:raises OSVVMException: If parameter proFileOrBuildDirectory is an absolute path.
	:raises OSVVMException: If parameter proFileOrBuildDirectory is not a *.pro file or build directory.
	:raises OSVVMException: If a TclError was caught while processing a *.pro file.

	.. seealso::

	   * :func:`build`
	   * :func:`ChangeWorkingDirectory`
	"""
	try:
		# Preserve current directory
		currentDirectory = osvvmContext._currentDirectory

		includeFile = osvvmContext.IncludeFile(Path(file))
		osvvmContext.EvaluateFile(includeFile)

		# Restore current directory after recursively evaluating *.pro files.
		osvvmContext._currentDirectory = currentDirectory

	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex


@export
def library(libraryName: str, libraryPath: Nullable[str] = None) -> None:
	"""
	This function implements the behavior of OSVVM's ``library`` procedure.

	It sets the currently active VHDL library to the specified VHDL library. If no VHDL library with that name exist, a
	new VHDL library is created and set as active VHDL library.

	.. hint:: All following ``analyze`` calls will use this library as the VHDL file's VHDL library.

	.. caution:: Parameter `libraryPath` is not yet implemented.

	:param libraryName: Name of the VHDL library.
	:param libraryPath: Optional: Path where to create that VHDL library.

	.. seealso::

	   * :func:`LinkLibrary`
	   * :func:`LinkLibraryDirectory`
	"""
	try:
		if libraryPath is not None:
			ex = NotImplementedError(f"Optional parameter 'libraryPath' not yet supported.")
			osvvmContext.LastException = ex
			raise ex

		osvvmContext.SetLibrary(libraryName)

	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex


@export
def NoNullRangeWarning() -> int:
	try:
		option = OSVVM_NoNullRangeWarning()
		optionID = osvvmContext.AddOption(option)
	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex

	return optionID


@export
def analyze(file: str, *options: int) -> None:
	try:
		file = Path(file)
		fullPath = (osvvmContext._currentDirectory / file).resolve()

		noNullRangeWarning = None
		for optionID in options:
			try:
				option = osvvmContext._options[int(optionID)]
			except KeyError as e:  # pragma: no cover
				ex = OSVVMException(f"Option {optionID} not found in option dictionary.")
				ex.__cause__ = e
				osvvmContext.LastException = ex
				raise ex

			if isinstance(option, OSVVM_NoNullRangeWarning):
				noNullRangeWarning = True
			else:  # pragma: no cover
				ex = OSVVMException(f"Option {optionID} is not a NoNullRangeWarning.")
				ex.__cause__ = TypeError()
				osvvmContext.LastException = ex
				raise ex

		if not fullPath.exists():  # pragma: no cover
			ex = OSVVMException(f"Path '{fullPath}' can't be analyzed.")
			ex.__cause__ = FileNotFoundError(fullPath)
			osvvmContext.LastException = ex
			raise ex

		if fullPath.suffix in (".vhd", ".vhdl"):
			vhdlFile = VHDLSourceFile(
				fullPath.relative_to(osvvmContext._workingDirectory, walk_up=True),
				noNullRangeWarning=noNullRangeWarning
			)
			osvvmContext.AddVHDLFile(vhdlFile)
		else:  # pragma: no cover
			ex = OSVVMException(f"Path '{fullPath}' is no VHDL file.")
			osvvmContext.LastException = ex
			raise ex

	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex


@export
def simulate(toplevelName: str, *options: int) -> None:
	try:
		testcase = osvvmContext.SetTestcaseToplevel(toplevelName)
		for optionID in options:
			try:
				option = osvvmContext._options[int(optionID)]
			except KeyError as e:  # pragma: no cover
				ex = OSVVMException(f"Option {optionID} not found in option dictionary.")
				ex.__cause__ = e
				osvvmContext.LastException = ex
				raise ex

			if isinstance(option, GenericValue):
				testcase.AddGeneric(option)
			else:  # pragma: no cover
				ex = OSVVMException(f"Option {optionID} is not a GenericValue.")
				ex.__cause__ = TypeError()
				osvvmContext.LastException = ex
				raise ex

	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex
	# osvvmContext._testcase = None


@export
def generic(name: str, value: str) -> int:
	try:
		genericValue = GenericValue(name, value)
		optionID = osvvmContext.AddOption(genericValue)
	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex

	return optionID


@export
def TestSuite(name: str) -> None:
	try:
		osvvmContext.SetTestsuite(name)
	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex


@export
def TestName(name: str) -> None:
	try:
		osvvmContext.AddTestcase(name)
	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex


@export
def RunTest(file: str, *options: int) -> None:
	try:
		file = Path(file)
		testName = file.stem

		# Analyze file
		fullPath = (osvvmContext._currentDirectory / file).resolve()

		if not fullPath.exists():  # pragma: no cover
			ex = OSVVMException(f"Path '{fullPath}' can't be analyzed.")
			ex.__cause__ = FileNotFoundError(fullPath)
			osvvmContext.LastException = ex
			raise ex

		if fullPath.suffix in (".vhd", ".vhdl"):
			vhdlFile = VHDLSourceFile(fullPath.relative_to(osvvmContext._workingDirectory, walk_up=True))
			osvvmContext.AddVHDLFile(vhdlFile)
		else:  # pragma: no cover
			ex = OSVVMException(f"Path '{fullPath}' is no VHDL file.")
			osvvmContext.LastException = ex
			raise ex

		# Add testcase
		testcase = osvvmContext.AddTestcase(testName)
		testcase.SetToplevel(testName)
		for optionID in options:
			try:
				option = osvvmContext._options[int(optionID)]
			except KeyError as e:  # pragma: no cover
				ex = OSVVMException(f"Option {optionID} not found in option dictionary.")
				ex.__cause__ = e
				osvvmContext.LastException = ex
				raise ex

			if isinstance(option, GenericValue):
				testcase.AddGeneric(option)
			else:  # pragma: no cover
				ex = OSVVMException(f"Option {optionID} is not a GenericValue.")
				ex.__cause__ = TypeError()
				osvvmContext.LastException = ex
				raise ex

	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex
	# osvvmContext._testcase = None


@export
def LinkLibrary(libraryName: str, libraryPath: Nullable[str] = None):
	print(f"[LinkLibrary] {libraryPath}")


@export
def LinkLibraryDirectory(libraryDirectory: str):
	print(f"[LinkLibraryDirectory] {libraryDirectory}")


@export
def SetVHDLVersion(value: str) -> None:
	try:
		try:
			value = int(value)
		except ValueError as e:  # pragma: no cover
			ex = OSVVMException(f"Unsupported VHDL version '{value}'.")
			ex.__cause__ = e
			osvvmContext.LastException = ex
			raise ex

		match value:
			case 1987:
				osvvmContext.VHDLVersion = VHDLVersion.VHDL87
			case 1993:
				osvvmContext.VHDLVersion = VHDLVersion.VHDL93
			case 2002:
				osvvmContext.VHDLVersion = VHDLVersion.VHDL2002
			case 2008:
				osvvmContext.VHDLVersion = VHDLVersion.VHDL2008
			case 2019:
				osvvmContext.VHDLVersion = VHDLVersion.VHDL2019
			case _:  # pragma: no cover
				ex = OSVVMException(f"Unsupported VHDL version '{value}'.")
				osvvmContext.LastException = ex
				raise ex

	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex

@export
def GetVHDLVersion() -> int:
	try:
		if osvvmContext.VHDLVersion is VHDLVersion.VHDL87:
			return 1987
		elif osvvmContext.VHDLVersion is VHDLVersion.VHDL93:
			return 1993
		elif osvvmContext.VHDLVersion is VHDLVersion.VHDL2002:
			return 2002
		elif osvvmContext.VHDLVersion is VHDLVersion.VHDL2008:
			return 2008
		elif osvvmContext.VHDLVersion is VHDLVersion.VHDL2019:
			return 2019
		else:  # pragma: no cover
			ex = OSVVMException(f"Unsupported VHDL version '{osvvmContext.VHDLVersion}'.")
			osvvmContext.LastException = ex
			raise ex
	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex


@export
def SetCoverageAnalyzeEnable(value: bool) -> None:
	print(f"[SetCoverageAnalyzeEnable] {value}:{value.__class__.__name__}")


@export
def SetCoverageSimulateEnable(value: bool) -> None:
	print(f"[SetCoverageSimulateEnable] {value}")


@export
def FileExists(file: str) -> bool:
	try:
		return (osvvmContext._currentDirectory / file).is_file()
	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex

@export
def DirectoryExists(directory: str) -> bool:
	try:
		return (osvvmContext._currentDirectory / directory).is_dir()
	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex

@export
def ChangeWorkingDirectory(directory: str) -> None:
	try:
		osvvmContext._currentDirectory = (newDirectory := osvvmContext._currentDirectory / directory)
		if not newDirectory.is_dir():  # pragma: no cover
			ex = OSVVMException(f"Directory '{newDirectory}' doesn't exist.")
			ex.__cause__ = NotADirectoryError(newDirectory)
			osvvmContext.LastException = ex
			raise ex
	except Exception as ex:  # pragma: no cover
		osvvmContext.LastException = ex
		raise ex


@export
def FindOsvvmSettingsDirectory(*args):
	pass


@export
def CreateOsvvmScriptSettingsPkg(*args):
	pass


@export
def noop(*args):
	pass
