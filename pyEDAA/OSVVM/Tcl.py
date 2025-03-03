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

from pyTooling.Decorators import readonly

from pyEDAA.OSVVM.Environment import Context, osvvmContext
from pyEDAA.OSVVM.Procedures import noop
from pyEDAA.OSVVM.Procedures import FileExists, DirectoryExists, FindOsvvmSettingsDirectory
from pyEDAA.OSVVM.Procedures import build, include, library, analyze, simulate, generic
from pyEDAA.OSVVM.Procedures import TestSuite, RunTest
from pyEDAA.OSVVM.Procedures import ChangeWorkingDirectory, CreateOsvvmScriptSettingsPkg
from pyEDAA.OSVVM.Procedures import SetCoverageAnalyzeEnable, SetCoverageSimulateEnable


class TclEnvironment:
	_tcl: Tk
	_procedures: Dict[str, Callable]
	_context: Context

	def __init__(self, context: Context) -> None:
		self._context = context
		context._tcl = self

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

	def LoadProFile(self, path: Path) -> None:
		includeFile = self._context.IncludeFile(path)

		self.EvaluateProFile(includeFile)

	def EvaluateProFile(self, path: Path) -> None:
		try:
			self._tcl.evalfile(str(path))
		except TclError as ex:
			# breakpoint()
			print(f"{'-' * 30}")
			print(f"Exception from TCL:")
			print(f"  {ex}")

	def __setitem__(self, tclVariableName: str, value: Any) -> None:
		self._tcl.setvar(tclVariableName, value)

	def __getitem__(self, tclVariableName: str) -> None:
		return self._tcl.getvar(tclVariableName)

	def __delitem__(self, tclVariableName: str) -> None:
		self._tcl.unsetvar(tclVariableName)


class OsvvmVariables:
	_toolName: str

	def __init__(
		self,
		toolName: Nullable[str] = None
	) -> None:
		self._toolName = toolName if toolName is not None else "pyEDAA.ProjectModel"

	@readonly
	def ToolName(self) -> str:
		return self._toolName


class OsvvmProFileProcessor(TclEnvironment):
	def __init__(
		self,
		# defaultsFile: Path,
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
		code = dedent(f"""\
			namespace eval ::osvvm {{
			  variable VhdlVersion     2019
			  variable ToolVendor      "???"
			  variable ToolName        "{osvvmVariables.ToolName}"
			  variable ToolNameVersion "???"
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
			raise Exception() from ex

	def OverwriteTclProcedures(self) -> None:
		self.RegisterPythonFunctionAsTclProcedure(noop, "puts")

	def RegisterTclProcedures(self) -> None:
		self.RegisterPythonFunctionAsTclProcedure(build)
		self.RegisterPythonFunctionAsTclProcedure(include)
		self.RegisterPythonFunctionAsTclProcedure(library)
		self.RegisterPythonFunctionAsTclProcedure(analyze)
		self.RegisterPythonFunctionAsTclProcedure(simulate)
		self.RegisterPythonFunctionAsTclProcedure(generic)

		self.RegisterPythonFunctionAsTclProcedure(TestSuite)
		self.RegisterPythonFunctionAsTclProcedure(RunTest)

		self.RegisterPythonFunctionAsTclProcedure(SetCoverageAnalyzeEnable)
		self.RegisterPythonFunctionAsTclProcedure(SetCoverageSimulateEnable)

		self.RegisterPythonFunctionAsTclProcedure(FileExists)
		self.RegisterPythonFunctionAsTclProcedure(DirectoryExists)
		self.RegisterPythonFunctionAsTclProcedure(ChangeWorkingDirectory)

		self.RegisterPythonFunctionAsTclProcedure(FindOsvvmSettingsDirectory)
		self.RegisterPythonFunctionAsTclProcedure(CreateOsvvmScriptSettingsPkg)
