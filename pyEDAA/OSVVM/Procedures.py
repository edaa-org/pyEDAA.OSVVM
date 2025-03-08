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
from typing  import Optional as Nullable, Tuple

from pyTooling.Decorators     import export
from pyVHDLModel              import VHDLVersion

from pyEDAA.OSVVM             import OSVVMException
from pyEDAA.OSVVM.Environment import osvvmContext, VHDLSourceFile, GenericValue


@export
def build(file: str) -> None:
	include(file)


@export
def include(file: str) -> None:
	currentDirectory = osvvmContext._currentDirectory

	includeFile = osvvmContext.IncludeFile(Path(file))
	osvvmContext.EvaluateFile(includeFile)

	osvvmContext._currentDirectory = currentDirectory


@export
def library(libraryName: str, libraryPath: Nullable[str] = None) -> None:
	osvvmContext.SetLibrary(libraryName)


@export
def analyze(file: str) -> None:
	file = Path(file)
	fullPath = (osvvmContext._currentDirectory / file).resolve()

	if not fullPath.exists():
		print(f"[analyze] Path '{fullPath}' doesn't exist.")
		ex = OSVVMException(f"Path '{fullPath}' can't be analyzed.")
		ex.__cause__ = FileNotFoundError(fullPath)
		osvvmContext.LastException = ex
		raise ex

	if fullPath.suffix in (".vhd", ".vhdl"):
		vhdlFile = VHDLSourceFile(fullPath.relative_to(osvvmContext._workingDirectory, walk_up=True))
		osvvmContext.AddVHDLFile(vhdlFile)
	else:
		print(f"[analyze] Unknown file type for '{fullPath}'.")
		ex = OSVVMException(f"Path '{fullPath}' is no VHDL file.")
		osvvmContext.LastException = ex
		raise ex


@export
def simulate(toplevelName: str, *options: Tuple[int]) -> None:
	testcase = osvvmContext.SetTestcaseToplevel(toplevelName)
	for optionID in options:
		try:
			option = osvvmContext._options[int(optionID)]
		except KeyError as ex2:
			ex = OSVVMException(f"Option {optionID} not found in option dictionary.")
			ex.__cause__ = ex2
			osvvmContext.LastException = ex
			raise ex

		if isinstance(option, GenericValue):
			testcase.AddGeneric(option)
		else:
			ex = OSVVMException(f"Option {optionID} is not a GenericValue.")
			ex.__cause__ = TypeError()
			osvvmContext.LastException = ex
			raise ex

	# osvvmContext._testcase = None


@export
def generic(name: str, value: str) -> GenericValue:
	genericValue = GenericValue(name, value)
	optionID = osvvmContext.AddOption(genericValue)

	return optionID


@export
def TestSuite(name: str) -> None:
	osvvmContext.SetTestsuite(name)


@export
def TestName(name: str) -> None:
	osvvmContext.AddTestcase(name)


@export
def RunTest(file: str, *options: Tuple[int]) -> None:
	file = Path(file)
	vhdlFile = VHDLSourceFile(file)
	testName = file.stem
	testcase = osvvmContext.AddTestcase(testName)
	osvvmContext.AddVHDLFile(vhdlFile)
	testcase.SetToplevel(testName)
	for optionID in options:
		try:
			option = osvvmContext._options[int(optionID)]
		except KeyError as ex2:
			ex = OSVVMException(f"Option {optionID} not found in option dictionary.")
			ex.__cause__ = ex2
			osvvmContext.LastException = ex
			raise ex

		if isinstance(option, GenericValue):
			testcase.AddGeneric(option)
		else:
			ex = OSVVMException(f"Option {optionID} is not a GenericValue.")
			ex.__cause__ = TypeError()
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
	print(f"[SetVHDLVersion] {value}:{value.__class__.__name__}")
	try:
		value = int(value)
	except ValueError as e:
		ex = OSVVMException(f"Unsupported VHDL version '{value}'.")
		ex.__cause__ = e
		osvvmContext.LastException = ex
		raise ex

	match value:
		case 1993:
			osvvmContext.VHDLVersion = VHDLVersion.VHDL93
		case 2001:
			osvvmContext.VHDLVersion = VHDLVersion.VHDL2002
		case 2008:
			osvvmContext.VHDLVersion = VHDLVersion.VHDL2008
		case 2019:
			osvvmContext.VHDLVersion = VHDLVersion.VHDL2019
		case _:
			ex = OSVVMException(f"Unsupported VHDL version '{value}'.")
			osvvmContext.LastException = ex
			raise ex


@export
def GetVHDLVersion() -> int:
	if osvvmContext.VHDLVersion is VHDLVersion.VHDL93:
		return 1993
	elif osvvmContext.VHDLVersion is VHDLVersion.VHDL2002:
		return 2002
	elif osvvmContext.VHDLVersion is VHDLVersion.VHDL2008:
		return 2008
	elif osvvmContext.VHDLVersion is VHDLVersion.VHDL2019:
		return 2019
	else:
		ex = OSVVMException(f"Potentially unsupported VHDL version '{osvvmContext.VHDLVersion}'.")
		osvvmContext.LastException = ex
		raise ex


@export
def SetCoverageAnalyzeEnable(value: bool) -> None:
	print(f"[SetCoverageAnalyzeEnable] {value}")


@export
def SetCoverageSimulateEnable(value: bool) -> None:
	print(f"[SetCoverageSimulateEnable] {value}")


@export
def FileExists(file: str) -> bool:
	return (osvvmContext._currentDirectory / file).is_file()


@export
def DirectoryExists(directory: str) -> bool:
	return (osvvmContext._currentDirectory / directory).is_dir()


@export
def ChangeWorkingDirectory(directory: str) -> None:
	osvvmContext._currentDirectory = (newDirectory := osvvmContext._currentDirectory / directory)
	if not newDirectory.is_dir():
		print(f"[ChangeWorkingDirectory] Directory {newDirectory} doesn't exist.")


@export
def FindOsvvmSettingsDirectory(*args):
	pass


@export
def CreateOsvvmScriptSettingsPkg(*args):
	pass


@export
def noop(*args):
	pass
