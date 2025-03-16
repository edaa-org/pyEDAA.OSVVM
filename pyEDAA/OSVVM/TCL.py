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
from pathlib  import Path
from textwrap import dedent
from tkinter  import Tk, Tcl, TclError
from typing   import Any, Dict, Callable, Optional as Nullable

from pyTooling.Decorators     import readonly, export
from pyVHDLModel              import VHDLVersion

from pyEDAA.OSVVM             import OSVVMException
from pyEDAA.OSVVM.Environment import Context, osvvmContext, Build, Project
from pyEDAA.OSVVM.Procedures  import noop, NoNullRangeWarning
from pyEDAA.OSVVM.Procedures  import FileExists, DirectoryExists, FindOsvvmSettingsDirectory
from pyEDAA.OSVVM.Procedures  import build, BuildName, include, library, analyze, simulate, generic
from pyEDAA.OSVVM.Procedures  import TestSuite, TestName, RunTest
from pyEDAA.OSVVM.Procedures  import ChangeWorkingDirectory, CreateOsvvmScriptSettingsPkg
from pyEDAA.OSVVM.Procedures  import SetVHDLVersion, GetVHDLVersion
from pyEDAA.OSVVM.Procedures  import SetCoverageAnalyzeEnable, SetCoverageSimulateEnable


@export
class TclEnvironment:
	_tcl: Tk
	_procedures: Dict[str, Callable]
	_context: Context

	def __init__(self, context: Context) -> None:
		self._context = context
		context._processor = self

		self._tcl = Tcl()
		self._procedures = {}

	@readonly
	def TCL(self) -> Tk:
		return self._tcl

	@readonly
	def Procedures(self) -> Dict[str, Callable]:
		return self._procedures

	@readonly
	def Context(self) -> Context:
		return self._context

	def RegisterPythonFunctionAsTclProcedure(self, pythonFunction: Callable, tclProcedureName: Nullable[str] = None):
		if tclProcedureName is None:
			tclProcedureName = pythonFunction.__name__

		self._tcl.createcommand(tclProcedureName, pythonFunction)
		self._procedures[tclProcedureName] = pythonFunction

	def EvaluateTclCode(self, tclCode: str) -> None:
		try:
			self._tcl.eval(tclCode)
		except TclError as e:
			e = getException(e, self._context)
			ex = OSVVMException(f"Caught TclError while evaluating TCL code.")
			ex.add_note(tclCode)
			raise ex from e

	def EvaluateProFile(self, path: Path) -> None:
		try:
			self._tcl.evalfile(str(path))
		except TclError as e:
			ex = getException(e, self._context)
			raise OSVVMException(f"Caught TclError while processing '{path}'.") from ex

	def __setitem__(self, tclVariableName: str, value: Any) -> None:
		self._tcl.setvar(tclVariableName, value)

	def __getitem__(self, tclVariableName: str) -> None:
		return self._tcl.getvar(tclVariableName)

	def __delitem__(self, tclVariableName: str) -> None:
		self._tcl.unsetvar(tclVariableName)


@export
class OsvvmVariables:
	_vhdlVersion: VHDLVersion
	_toolVendor:  str
	_toolName:    str
	_toolVersion: str

	def __init__(
		self,
		vhdlVersion: Nullable[VHDLVersion] = None,
		toolVendor:  Nullable[str] = None,
		toolName:    Nullable[str] = None,
		toolVersion: Nullable[str] = None
	) -> None:
		self._vhdlVersion = vhdlVersion if vhdlVersion is not None else VHDLVersion.VHDL2008
		self._toolVendor =  toolVendor  if toolVendor  is not None else "EDA²"
		self._toolName =    toolName    if toolName    is not None else "pyEDAA.ProjectModel"
		self._toolVersion = toolVersion if toolVersion is not None else "0.1"

	@readonly
	def VHDlversion(self) -> VHDLVersion:
		return self._vhdlVersion

	@readonly
	def ToolVendor(self) -> str:
		return self._toolVendor

	@readonly
	def ToolName(self) -> str:
		return self._toolName

	@readonly
	def ToolVersion(self) -> str:
		return self._toolVersion


@export
class OsvvmProFileProcessor(TclEnvironment):
	def __init__(
		self,
		context: Nullable[Context] = None,
		osvvmVariables: Nullable[OsvvmVariables] = None
	) -> None:
		if context is None:
			context = osvvmContext

		super().__init__(context)

		if osvvmVariables is None:
			osvvmVariables = OsvvmVariables()

		self.LoadOsvvmDefaults(osvvmVariables)
		self.OverwriteTclProcedures()
		self.RegisterTclProcedures()

	def LoadOsvvmDefaults(self, osvvmVariables: OsvvmVariables) -> None:
		match osvvmVariables.VHDlversion:
			case VHDLVersion.VHDL2002:
				version = "2002"
			case VHDLVersion.VHDL2008:
				version = "2008"
			case VHDLVersion.VHDL2019:
				version = "2019"
			case _:
				version = "unsupported"

		code = dedent(f"""\
			namespace eval ::osvvm {{
			  variable VhdlVersion     {version}
			  variable ToolVendor      "{osvvmVariables.ToolVendor}"
			  variable ToolName        "{osvvmVariables.ToolName}"
			  variable ToolNameVersion "{osvvmVariables.ToolVersion}"
			  variable ToolSupportsDeferredConstants           1
			  variable ToolSupportsGenericPackages             1
			  variable FunctionalCoverageIntegratedInSimulator "default"
			  variable Support2019FilePath                     1

			  variable ClockResetVersion                       0
			}}
			""")

		try:
			self._tcl.eval(code)
		except TclError as ex:
			raise OSVVMException(f"TCL error occurred, when initializing OSVVM variables.") from ex

	def OverwriteTclProcedures(self) -> None:
		self.RegisterPythonFunctionAsTclProcedure(noop, "puts")

	def RegisterTclProcedures(self) -> None:
		self.RegisterPythonFunctionAsTclProcedure(build)
		self.RegisterPythonFunctionAsTclProcedure(include)
		self.RegisterPythonFunctionAsTclProcedure(library)
		self.RegisterPythonFunctionAsTclProcedure(analyze)
		self.RegisterPythonFunctionAsTclProcedure(simulate)
		self.RegisterPythonFunctionAsTclProcedure(generic)

		self.RegisterPythonFunctionAsTclProcedure(BuildName)
		self.RegisterPythonFunctionAsTclProcedure(NoNullRangeWarning)

		self.RegisterPythonFunctionAsTclProcedure(TestSuite)
		self.RegisterPythonFunctionAsTclProcedure(TestName)
		self.RegisterPythonFunctionAsTclProcedure(RunTest)

		self.RegisterPythonFunctionAsTclProcedure(SetVHDLVersion)
		self.RegisterPythonFunctionAsTclProcedure(GetVHDLVersion)
		self.RegisterPythonFunctionAsTclProcedure(SetCoverageAnalyzeEnable)
		self.RegisterPythonFunctionAsTclProcedure(SetCoverageSimulateEnable)

		self.RegisterPythonFunctionAsTclProcedure(FileExists)
		self.RegisterPythonFunctionAsTclProcedure(DirectoryExists)
		self.RegisterPythonFunctionAsTclProcedure(ChangeWorkingDirectory)

		self.RegisterPythonFunctionAsTclProcedure(FindOsvvmSettingsDirectory)
		self.RegisterPythonFunctionAsTclProcedure(CreateOsvvmScriptSettingsPkg)

	def LoadIncludeFile(self, path: Path) -> None:
		includeFile = self._context.IncludeFile(path)

		self.EvaluateProFile(includeFile)

	def LoadBuildFile(self, buildFile: Path, buildName: Nullable[str] = None) -> Build:
		if buildName is None:
			buildName = buildFile.stem

		self._context.BeginBuild(buildName)
		includeFile = self._context.IncludeFile(buildFile)
		self.EvaluateProFile(includeFile)

		return self._context.EndBuild()

	def LoadRegressionFile(self, regressionFile: Path, projectName: Nullable[str] = None) -> Project:
		if projectName is None:
			projectName = regressionFile.stem

		self.EvaluateProFile(regressionFile)

		return self._context.ToProject(projectName)


@export
def getException(ex: Exception, context: Context) -> Exception:
	if str(ex) == "":
		if (lastException := context.LastException) is not None:
			return lastException

	return ex
