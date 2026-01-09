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
# Copyright 2025-2026 Patrick Lehmann - Boetzingen, Germany                                                            #
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
A TCL execution environment for OSVVM's ``*.pro`` files.
"""
from pathlib                         import Path
from textwrap                        import dedent
from tkinter                         import Tk, Tcl, TclError
from typing                          import Any, Dict, Callable, Optional as Nullable

from pyTooling.Decorators            import export, readonly
from pyTooling.MetaClasses           import ExtendedType
from pyVHDLModel                     import VHDLVersion

from pyEDAA.OSVVM                    import OSVVMException
from pyEDAA.OSVVM.Project            import Context, osvvmContext, Build, Project
from pyEDAA.OSVVM.Project.Procedures import noop, NoNullRangeWarning
from pyEDAA.OSVVM.Project.Procedures import FileExists, DirectoryExists, FindOsvvmSettingsDirectory
from pyEDAA.OSVVM.Project.Procedures import build, BuildName, include, library, analyze, simulate, generic
from pyEDAA.OSVVM.Project.Procedures import TestSuite, TestName, RunTest
from pyEDAA.OSVVM.Project.Procedures import ChangeWorkingDirectory, CreateOsvvmScriptSettingsPkg
from pyEDAA.OSVVM.Project.Procedures import SetVHDLVersion, GetVHDLVersion
from pyEDAA.OSVVM.Project.Procedures import SetCoverageAnalyzeEnable, SetCoverageSimulateEnable
from pyEDAA.OSVVM.Project.Procedures import ConstraintFile, ScopeToRef, ScopeToCell


@export
class TclEnvironment(metaclass=ExtendedType, slots=True):
	"""
	A TCL execution environment wrapping an embedded TCL interpreter based on :class:`tkinter.Tcl`.
	"""
	_tcl:        Tk                   #: The embedded TCL interpreter instance.
	_procedures: Dict[str, Callable]  #: A dictionary of registered TCL procedures implemented by Python functions.
	_context:    Context              #: The TCL execution context.

	def __init__(self, context: Context) -> None:
		"""
		Initialize a TCL execution environment.

		:param context: The TCL execution context.
		"""
		self._context = context
		context._processor = self

		self._tcl = Tcl()
		self._procedures = {}

	@readonly
	def TCL(self) -> Tk:
		"""
		Read-only property to access the embedded TCL interpreter instance (:attr:`_tcl`).

		:returns: TCL interpreter instance.
		"""
		return self._tcl

	@readonly
	def Procedures(self) -> Dict[str, Callable]:
		"""
		Read-only property to access the dictionary of registered TCL procedures implemented by Python functions (:attr:`_procedures`).

		:returns: The dictionary of registered procedures.
		"""
		return self._procedures

	@readonly
	def Context(self) -> Context:
		"""
		Read-only property to access the TCL execution context (:attr:`_context`).

		:returns: The TCL execution context.
		"""
		return self._context

	def RegisterPythonFunctionAsTclProcedure(self, pythonFunction: Callable, tclProcedureName: Nullable[str] = None) -> None:
		"""
		Register a Python function as TCL procedure.

		:param pythonFunction:   The Python function to be registered.
		:param tclProcedureName: Optional, name of the TCl procedure. |br|
		                         Default: derived the TCL procedure name from Python function name.
		"""
		if tclProcedureName is None:
			tclProcedureName = pythonFunction.__name__

		self._tcl.createcommand(tclProcedureName, pythonFunction)
		self._procedures[tclProcedureName] = pythonFunction

	def EvaluateTclCode(self, tclCode: str) -> None:
		"""
		Evaluate TCL source code.

		:param tclCode:         TCL source code to evaluate.
		:raises OSVVMException: When a :exc:`~tkinter.TclError` is caught while executing the TCL source code. |br|
		                        In case the error is unspecific, :func:`~pyEDAA.OSVVM.Project.TCL.getException` is used to
		                        look up and restore an exception, potentially coming from Python code called within TCL
		                        code.
		"""
		try:
			self._tcl.eval(tclCode)
		except TclError as e:
			e = getException(e, self._context)
			ex = OSVVMException(f"Caught TclError while evaluating TCL code.")
			ex.add_note(tclCode)
			raise ex from e

	def EvaluateProFile(self, path: Path) -> None:
		"""
		Evaluate TCL source file.

		:param path:            Path to a TCL source file for evaluation.
		:raises OSVVMException: When a :exc:`~tkinter.TclError` is caught while executing the TCL source code. |br|
		                        In case the error is unspecific, :func:`~pyEDAA.OSVVM.Project.TCL.getException` is used to
		                        look up and restore an exception, potentially coming from Python code called within TCL
		                        code.
		"""
		try:
			self._tcl.evalfile(str(path))
		except TclError as e:
			ex = getException(e, self._context)
			raise OSVVMException(f"Caught TclError while processing '{path}'.") from ex

	def __setitem__(self, tclVariableName: str, value: Any) -> None:
		"""
		Set a TCL variable to a specific value.

		:param tclVariableName: Name of the TCL variable.
		:param value:           Value to be set.
		"""
		self._tcl.setvar(tclVariableName, value)

	def __getitem__(self, tclVariableName: str) -> None:
		"""
		Return a TCL variable's value.

		:param tclVariableName: Name of the TCL variable.
		:returns:               TCL variable's value.
		"""
		return self._tcl.getvar(tclVariableName)

	def __delitem__(self, tclVariableName: str) -> None:
		"""
		Unset a TCL variable.

		:param tclVariableName: Name of the TCL variable.
		"""
		self._tcl.unsetvar(tclVariableName)


@export
class OsvvmVariables(metaclass=ExtendedType, slots=True):
	"""
	A class representing OSVVM's setting variables.
	"""
	_vhdlVersion: VHDLVersion  #: Default VHDL language revision.
	_toolVendor:  str          #: Name of the tool vendor.
	_toolName:    str          #: Name of the tool.
	_toolVersion: str          #: Version of the tool.

	def __init__(
		self,
		vhdlVersion: Nullable[VHDLVersion] = None,
		toolVendor:  Nullable[str] = None,
		toolName:    Nullable[str] = None,
		toolVersion: Nullable[str] = None
	) -> None:
		"""
		Initialize OSVVM's setting variables.

		:param vhdlVersion: Optional, default VHDL language revision.
		:param toolVendor:  Optional, name of the tool vendor.
		:param toolName:    Optional, name of the tool.
		:param toolVersion: Optional, version of the tool.

		.. note::

		   If not specified, the following values are used:

		   * VHDL version = :pycode:`VHDLVersion.VHDL2008`
		   * Tool vendor = :pycode:`"EDA²"`
		   * Tool name = :pycode:`"pyEDAA.ProjectModel"`
		   * Tool version = :pycode:`"0.1"`
		"""
		self._vhdlVersion = vhdlVersion if vhdlVersion is not None else VHDLVersion.VHDL2008
		self._toolVendor =  toolVendor  if toolVendor  is not None else "EDA²"
		self._toolName =    toolName    if toolName    is not None else "pyEDAA.ProjectModel"
		self._toolVersion = toolVersion if toolVersion is not None else "0.1"

	@readonly
	def VHDLVersion(self) -> VHDLVersion:
		"""
		Read-only property to access the default VHDL language revision (:attr:`_vhdlVersion`).

		:returns: The default VHDL language revision.
		"""
		return self._vhdlVersion

	@readonly
	def ToolVendor(self) -> str:
		"""
		Read-only property to access the tool vendor name (:attr:`_toolVendor`).

		:returns: The tool vendor name.
		"""
		return self._toolVendor

	@readonly
	def ToolName(self) -> str:
		"""
		Read-only property to access the tool's' name (:attr:`_toolName`).

		:returns: The tool's name.
		"""
		return self._toolName

	@readonly
	def ToolVersion(self) -> str:
		"""
		Read-only property to access the tool's version (:attr:`_toolVersion`).

		:returns: The tool's version.
		"""
		return self._toolVersion


@export
class OsvvmProFileProcessor(TclEnvironment):
	"""
	An OSVVM-specific TCL execution environment for ``*.pro`` files.
	"""

	def __init__(
		self,
		context: Nullable[Context] = None,
		osvvmVariables: Nullable[OsvvmVariables] = None
	) -> None:
		"""
		Initialize an OSVVM-specific TCL execution environment.

		:param context:        The TCL execution context.
		:param osvvmVariables: OSVVM default settings.

		.. rubric:: Initialization steps:

		1. Initialize base-class.
		2. Load OSVVM default value into ``::osvvm::`` namespace variables.
		3. Overwrite predefined TCL procedures. |br|
		   Avoid harmful or disturbing actions caused by these procedures.
		4. Register Python functions as TCL procedures.
		"""
		if context is None:
			context = osvvmContext

		super().__init__(context)

		if osvvmVariables is None:
			osvvmVariables = OsvvmVariables()

		self.LoadOsvvmDefaults(osvvmVariables)
		self.OverwriteTclProcedures()
		self.RegisterTclProcedures()

	def LoadOsvvmDefaults(self, osvvmVariables: OsvvmVariables) -> None:
		"""
		Create an OSVVM namespace and declare variables with default values.

		:param osvvmVariables: OSVVM settings object.

		.. code-block:: TCL

		   namespace eval ::osvvm {
		     variable VhdlVersion                             <Version>
		     variable ToolVendor                              "<ToolVendor>"
		     variable ToolName                                "<ToolName>"
		     variable ToolNameVersion                         "<ToolVersion>"
		     variable ToolSupportsDeferredConstants           1
		     variable ToolSupportsGenericPackages             1
		     variable FunctionalCoverageIntegratedInSimulator "default"
		     variable Support2019FilePath                     1

		     variable ClockResetVersion                       0
		   }
		"""
		match osvvmVariables.VHDLVersion:
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
		"""
		Overwrite predefined TCL procedures.

		.. rubric:: List of overwritten procedures:

		* `puts` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.noop`
		"""
		self.RegisterPythonFunctionAsTclProcedure(noop, "puts")

	def RegisterTclProcedures(self) -> None:
		"""
		Register Python functions as TCL procedures.

		.. rubric:: List of registered procedures:

		* ``build`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.build`
		* ``include`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.include`
		* ``library`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.library`
		* ``analyze`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.analyze`
		* ``simulate`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.simulate`
		* ``generic`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.generic`
		* ``BuildName`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.BuildName`
		* ``NoNullRangeWarning`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.NoNullRangeWarning`
		* ``TestSuite`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.TestSuite`
		* ``TestName`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.TestName`
		* ``RunTest`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.RunTest`
		* ``SetVHDLVersion`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.SetVHDLVersion`
		* ``GetVHDLVersion`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.GetVHDLVersion`
		* ``SetCoverageAnalyzeEnable`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.SetCoverageAnalyzeEnable`
		* ``SetCoverageSimulateEnable`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.SetCoverageSimulateEnable`
		* ``FileExists`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.FileExists`
		* ``DirectoryExists`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.DirectoryExists`
		* ``ChangeWorkingDirectory`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.ChangeWorkingDirectory`
		* ``FindOsvvmSettingsDirectory`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.FindOsvvmSettingsDirectory`
		* ``CreateOsvvmScriptSettingsPkg`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.CreateOsvvmScriptSettingsPkg`
		* ``ConstraintFile`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.ConstraintFile`
		* ``ScopeToRef`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.ScopeToRef`
		* ``ScopeToCell`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.ScopeToCell`
		* ``OpenBuildHtml`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.noop`
		* ``SetTranscriptType`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.noop`
		* ``GetTranscriptType`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.noop`
		* ``SetSimulatorResolution`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.noop`
		* ``GetSimulatorResolution`` |rarr| :func:`~pyEDAA.OSVVM.Project.Procedures.noop`
		"""
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

		self.RegisterPythonFunctionAsTclProcedure(ConstraintFile)
		self.RegisterPythonFunctionAsTclProcedure(ScopeToRef)
		self.RegisterPythonFunctionAsTclProcedure(ScopeToCell)

		self.RegisterPythonFunctionAsTclProcedure(noop, "OpenBuildHtml")
		self.RegisterPythonFunctionAsTclProcedure(noop, "SetTranscriptType")
		self.RegisterPythonFunctionAsTclProcedure(noop, "GetTranscriptType")
		self.RegisterPythonFunctionAsTclProcedure(noop, "SetSimulatorResolution")
		self.RegisterPythonFunctionAsTclProcedure(noop, "GetSimulatorResolution")

	def LoadIncludeFile(self, path: Path) -> None:
		"""
		Load an OSVVM ``*.pro`` file for inclusion (not as a root level build, see :meth:`LoadBuildFile`).

		:param path: Path to the ``*.pro`` file.

		.. seealso::

		   * :meth:`LoadBuildFile`
		"""
		# TODO: should a context be used with _context to restore _currentDirectory?
		includeFile = self._context.IncludeFile(path)
		self.EvaluateProFile(includeFile)

	def LoadBuildFile(self, buildFile: Path, buildName: Nullable[str] = None) -> Build:
		"""
		Load an OSVVM ``*.pro`` file as build creating a new build context.

		.. rubric:: inferring the build name:

		1. From optional parameter ``buildName``.
		2. From ``*.pro`` file's filename.

		:param path: Path to the ``*.pro`` file.
		:returns:    The created build object.

		.. seealso::

		   * :meth:`LoadIncludeFile`
		"""
		if buildName is None:
			buildName = buildFile.stem

		self._context.BeginBuild(buildName)
		includeFile = self._context.IncludeFile(buildFile)
		self.EvaluateProFile(includeFile)

		# TODO: should a context be used with _context to restore _currentDirectory?
		return self._context.EndBuild()

	def LoadRegressionFile(self, regressionFile: Path, projectName: Nullable[str] = None) -> Project:
		"""
		Load a TCL file as a regression file and create a project from it.

		.. rubric:: inferring the project name:

		1. From optional parameter ``projectName``.
		2. From ``*.pro`` file's filename.

		:param regressionFile:
		:param projectName:
		:return:
		"""
		if projectName is None:
			projectName = regressionFile.stem

		self.EvaluateProFile(regressionFile)

		return self._context.ToProject(projectName)


@export
def getException(ex: Exception, context: Context) -> Exception:
	"""
	Restore Python exceptions if known by the execution context.

	:param ex:      Original exception (usually a :exc:`~tkinter.TclError`).
	:param context: The TCL execution context.
	:returns:       The original Python exception, if the context preserved an exception, otherwise the given TCLError.

	.. note::

	   When executing Python code within TCL, where TCL again is run within Python, TCL doesn't forward Python exceptions
	   through the TCL layer back into Python. Therefore, last seen Python exceptions are caught in the Python-TCL
	   interfacing procedures and preserved in the TCL execution context.

	   This helper function restores these preserved exception objects.
	"""
	if str(ex) == "":
		if (lastException := context.LastException) is not None:
			return lastException

	return ex
