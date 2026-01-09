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
This module implements OSVVM's TCL procedures (used in OSVVM's ``*.pro`` files) as Python functions.

These functions are then registered at the :class:`TCL processor <pyEDAA.OSVVM.Project.TCL.OsvvmProFileProcessor>`, so
procedure calls within TCL code get "redirected" to these Python functions. Each Python function has access to a global
variable :data:`~pyEDAA.OSVVM.Project.osvvmContext` to preserve its state or modify the context.

.. important::

   For passing Python exceptions through the TCL layer back into Python, every function in the module MUST follow the
   following scheme:

   .. code-block:: Python

      def myTclProcedure(....) -> ...:
        try:
          # do something

        except OSVVMException as ex:  # pragma: no cover
          raise ex
        except Exception as ex:       # pragma: no cover
          osvvmContext.RaiseException(ex)
"""
from pathlib               import Path
from typing                import Optional as Nullable

from pyTooling.Decorators  import export
from pyTooling.Common      import getFullyQualifiedName
from pyVHDLModel           import VHDLVersion

from pyEDAA.OSVVM          import OSVVMException
from pyEDAA.OSVVM.Project  import osvvmContext, VHDLSourceFile, GenericValue, ConstraintFile as OSVVM_ConstraintFile
from pyEDAA.OSVVM.Project  import XDCConstraintFile, ScopeToRef as OSVVM_ScopeToRef, ScopeToCell as OSVVM_ScopeToCell
from pyEDAA.OSVVM.Project  import BuildName as OSVVM_BuildName, NoNullRangeWarning as OSVVM_NoNullRangeWarning


@export
def BuildName(name: str) -> int:
	"""
	This function implements the behavior of OSVVM's ``BuildName`` procedure.

	Create and register a :class:`~pyEDAA.OSVVM.Project.BuildName` option and return the options unique ID.

	:param name: Name of the build.
	:returns:    The option's unique ID.
	"""
	try:
		buildName = OSVVM_BuildName(name)
		return osvvmContext.AddOption(buildName)
	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def build(file: str, *options: int) -> None:
	"""
	This function implements the behavior of OSVVM's ``build`` procedure.

	The current directory of the currently active context is preserved	while the referenced ``*.pro`` file is processed.
	After processing that file, the context's current directory is restored.

	The referenced file gets appended to a list of included files maintained by the context.

	.. rubric:: pro-file discovery algorithm:

	1. If the path explicitly references a ``*.pro`` file, this file is used.
	2. If the path references a directory, it checks implicitly for a ``build.pro`` file, otherwise
	3. it checks implicitly for a ``<path>.pro`` file, named like the directories name.

	.. rubric:: inferring the build name:

	1. The option :class:`~pyEDAA.OSVVM.Project.BuildName` was gives (indirectly via option ID) as parameter.
	2. It's derived from the current directory name.

	:param file:            Explicit path to a ``*.pro`` file or a directory containing an implicitly searched ``*.pro``
	                        file.
	:param options:         Optional, list of option IDs.
	:raises OSVVMException: If parameter 'options' contains unknown option IDS.
	:raises OSVVMException: If parameter 'options' contains an option not of type :class:`~pyEDAA.OSVVM.Project.BuildName`.

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
				osvvmContext.RaiseException(ex)

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

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def include(file: str) -> None:
	"""
	This function implements the behavior of OSVVM's ``include`` procedure.

	The current directory of the currently active context is preserved	while the referenced ``*.pro`` file is processed.
	After processing that file, the context's current directory is restored.

	The referenced file gets appended to a list of included files maintained by the context.

	.. rubric:: pro-file discovery algorithm:

	1. If the path explicitly references a ``*.pro`` file, this file is used.
	2. If the path references a directory, it checks implicitly for a ``build.pro`` file, otherwise
	3. it checks implicitly for a ``<path>.pro`` file, named like the directories name.

	:param file:            Explicit path to a ``*.pro`` file or a directory containing an implicitly searched ``*.pro``
	                        file.

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

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def library(libraryName: str, libraryPath: Nullable[str] = None) -> None:
	"""
	This function implements the behavior of OSVVM's ``library`` procedure.

	It sets the currently active VHDL library to the specified VHDL library. If no VHDL library with that name exist, a
	new VHDL library is created and set as active VHDL library.

	.. hint::

	   All following ``analyze`` calls will use this library as the VHDL source file's VHDL library.

	.. caution::

	   Parameter `libraryPath` is not yet implemented.

	:param libraryName:          Name of the VHDL library.
	:param libraryPath:          Optional, path where to create that VHDL library.
	:raises NotImplementedError: When parameter 'libraryPath' is not None.

	.. seealso::

	   * :func:`LinkLibrary`
	   * :func:`LinkLibraryDirectory`
	"""
	try:
		if libraryPath is not None:
			raise NotImplementedError(f"Optional parameter 'libraryPath' not yet supported.")

		osvvmContext.SetLibrary(libraryName)

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def NoNullRangeWarning() -> int:
	"""
	This function implements the behavior of OSVVM's ``NoNullRangeWarning`` procedure.

	Create and register a :class:`~pyEDAA.OSVVM.Project.NoNullRangeWarning` option and return the options unique ID.

	:returns: The option's unique ID.
	"""
	try:
		option = OSVVM_NoNullRangeWarning()
		return osvvmContext.AddOption(option)
	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def analyze(file: str, *options: int) -> None:
	"""
	This function implements the behavior of OSVVM's ``analyze`` procedure.

	Analyze an HDL source file.

  .. rubric:: Supported options:

  * :func:`NoNullRangeWarning` - disable null-range warnings when analyzing.
  * :func:`ConstraintFile` - associated constraint file

	:param file:            Path of the VHDL source file.
	:param options:         Optional, list of option IDs.
	:raises OSVVMException: When the referenced source file doesn't exist.
	:raises OSVVMException: When the referenced source file isn't an ``*.vhd`` or ``*.vhdl`` file.
	:raises OSVVMException: When parameter 'options' contains an unknown option ID.
	:raises OSVVMException: When referenced option is not a :class:`~pyEDAA.OSVVM.Project.NoNullRangeWarning` or
	                        :class:`~pyEDAA.OSVVM.Project.ConstraintFile`.

	.. seealso::

	   * :func:`NoNullRangeWarning`
	   * :func:`SetCoverageAnalyzeEnable`
	   * :func:`ConstraintFile`
	"""
	try:
		file = Path(file)
		fullPath = (osvvmContext._currentDirectory / file).resolve()

		noNullRangeWarning = None
		associatedConstraintFiles = []
		for optionID in options:
			try:
				option = osvvmContext._options[int(optionID)]
			except KeyError as ex:  # pragma: no cover
				osvvmContext.RaiseException(OSVVMException(f"Option {optionID} not found in option dictionary."), ex)

			if isinstance(option, OSVVM_NoNullRangeWarning):
				noNullRangeWarning = True
			elif isinstance(option, OSVVM_ConstraintFile):
				associatedConstraintFiles.append(XDCConstraintFile(
					option.Path,
					option.ScopeToRef,
					option.ScopeToCell
				))
			else:  # pragma: no cover
				ex = TypeError(f"Option {optionID} is not a NoNullRangeWarning or ConstraintFile.")
				ex.add_note(f"Got type '{getFullyQualifiedName(option)}'.")
				osvvmContext.RaiseException(OSVVMException(f"Dereferenced option ID is not a NoNullRangeWarning or ConstraintFile object"), ex)

		if not fullPath.exists():  # pragma: no cover
			osvvmContext.RaiseException(OSVVMException(f"Path '{fullPath}' can't be analyzed."), FileNotFoundError(fullPath))

		if fullPath.suffix in (".vhd", ".vhdl"):
			vhdlFile = VHDLSourceFile(
				fullPath.relative_to(osvvmContext._workingDirectory, walk_up=True),
				noNullRangeWarning=noNullRangeWarning,
				associatedFiles=associatedConstraintFiles
			)
			osvvmContext.AddVHDLFile(vhdlFile)
		else:  # pragma: no cover
			osvvmContext.RaiseException(OSVVMException(f"Path '{fullPath}' is no VHDL file (*.vhd, *.vhdl)."))

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def simulate(toplevelName: str, *options: int) -> None:
	"""
	This function implements the behavior of OSVVM's ``simulate`` procedure.

	Simulate a given toplevel entity or configuration name.

  .. rubric:: Supported options:

  * :func:`generic` - specify generic values.

	:param toplevelName:    Name of the toplevel.
	:param options:         Optional, list of option IDs.
	:raises ValueError:     When parameter 'toplevelName' is empty.
	:raises OSVVMException: When parameter 'options' contains an unknown option ID.
	:raises OSVVMException: When referenced option is not a :class:`~pyEDAA.OSVVM.Project.GenericValue`.

	.. seealso::

	   * :func:`generic`
	   * :func:`RunTest`
	"""
	try:
		if toplevelName == "":
			raise ValueError(f"Parameter 'toplevelName' is empty.")

		testcase = osvvmContext.SetTestcaseToplevel(toplevelName)
		for optionID in options:
			try:
				option = osvvmContext._options[int(optionID)]
			except KeyError as ex:  # pragma: no cover
				osvvmContext.RaiseException(OSVVMException(f"Option {optionID} not found in option dictionary."), ex)

			if isinstance(option, GenericValue):
				testcase.AddGeneric(option)
			else:  # pragma: no cover
				ex = TypeError(f"Option {optionID} is not a GenericValue.")
				ex.add_note(f"Got type '{getFullyQualifiedName(option)}'.")
				osvvmContext.RaiseException(OSVVMException(f"Dereferenced option ID is not a GenericValue object"), ex)

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def generic(name: str, value: str) -> int:
	"""
	This function implements the behavior of OSVVM's ``generic`` procedure.

	Create and register a :class:`~pyEDAA.OSVVM.Project.GenericValue` option and return the options unique ID.

	:param name:  Name of the generic.
	:param value: Value of the generic.
	:returns:     The option's unique ID.
	"""
	try:
		genericValue = GenericValue(name, value)
		return osvvmContext.AddOption(genericValue)
	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def TestSuite(name: str) -> None:
	"""
	This function implements the behavior of OSVVM's ``TestSuite`` procedure.

	Set or create the currently active :class:`~pyEDAA.OSVVM.Project.Testsuite`.

	:param name: Name of the OSVVM testsuite.
	"""
	try:
		osvvmContext.SetTestsuite(name)
	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def TestName(name: str) -> None:
	"""
	This function implements the behavior of OSVVM's ``TestName`` procedure.

	Create a new :class:`~pyEDAA.OSVVM.Project.Testcase`.

	:param name: Name of the OSVVM testcase.
	"""
	try:
		osvvmContext.AddTestcase(name)
	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def RunTest(file: str, *options: int) -> None:
	"""
	This function implements the behavior of OSVVM's ``RunTest`` procedure.

	Simulate a given toplevel entity or configuration name. Infer testcase name from filename.

  .. rubric:: Supported options:

  * :func:`generic` - specify generic values.

	:param file:            Path of the VHDL source file containing the toplevel.
	:param options:         Optional, list of option IDs.
	:raises OSVVMException: When the referenced source file doesn't exist.
	:raises OSVVMException: When the referenced source file isn't an ``*.vhd`` or ``*.vhdl`` file.
	:raises OSVVMException: When parameter 'options' contains an unknown option ID.
	:raises OSVVMException: When referenced option is not a :class:`~pyEDAA.OSVVM.Project.GenericValue`.

	.. seealso::

	   * :func:`generic`
	   * :func:`simulate`
	"""
	try:
		file = Path(file)
		testName = file.stem

		# Analyze file
		fullPath = (osvvmContext._currentDirectory / file).resolve()

		if not fullPath.exists():  # pragma: no cover
			osvvmContext.RaiseException(OSVVMException(f"Path '{fullPath}' can't be analyzed."), FileNotFoundError(fullPath))

		if fullPath.suffix in (".vhd", ".vhdl"):
			vhdlFile = VHDLSourceFile(fullPath.relative_to(osvvmContext._workingDirectory, walk_up=True))
			osvvmContext.AddVHDLFile(vhdlFile)
		else:  # pragma: no cover
			osvvmContext.RaiseException(OSVVMException(f"Path '{fullPath}' is no VHDL file (*.vhd, *.vhdl)."))

		# Add testcase
		testcase = osvvmContext.AddTestcase(testName)
		testcase.SetToplevel(testName)
		for optionID in options:
			try:
				option = osvvmContext._options[int(optionID)]
			except KeyError as ex:  # pragma: no cover
				osvvmContext.RaiseException(OSVVMException(f"Option {optionID} not found in option dictionary."), ex)

			if isinstance(option, GenericValue):
				testcase.AddGeneric(option)
			else:  # pragma: no cover
				ex = TypeError(f"Option {optionID} is not a GenericValue.")
				ex.add_note(f"Got type '{getFullyQualifiedName(option)}'.")
				osvvmContext.RaiseException(OSVVMException(f"Dereferenced option ID is not a GenericValue object"), ex)

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def LinkLibrary(libraryName: str, libraryPath: Nullable[str] = None):
	"""
	Not implemented by pyEDAA.OSVVM.
	"""
	osvvmContext.RaiseException(NotImplementedError(f"Procedure 'LinkLibrary' is not implemented."))


@export
def LinkLibraryDirectory(libraryDirectory: str):
	"""
	Not implemented by pyEDAA.OSVVM.
	"""
	osvvmContext.RaiseException(NotImplementedError(f"Procedure 'LinkLibraryDirectory' is not implemented."))


@export
def SetVHDLVersion(value: str) -> None:
	"""
	This function implements the behavior of OSVVM's ``SetVHDLVersion`` procedure.

	Set the used VHDL language revision.

	.. hint::

	   All following ``analyze`` calls will use this VHDL revision.

	:param value:           The VHDL language revision's release year.
	:raises ValueError:     When parameter 'value' is not an integer value.
	:raises OSVVMException: When parameter 'value' is not a known VHDL revision's release year.

	.. seealso::

	   * :func:`GetVHDLVersion`
	"""
	try:
		try:
			value = int(value)
		except ValueError as e:  # pragma: no cover
			ex = ValueError(f"Parameter 'value' is not an integer value.")
			ex.add_note(f"Got '{value}'.")
			osvvmContext.RaiseException(ex, e)

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
				osvvmContext.RaiseException(OSVVMException(f"Unsupported VHDL version '{value}'."))

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def GetVHDLVersion() -> int:
	"""
	This function implements the behavior of OSVVM's ``GetVHDLVersion`` procedure.

	Returns the currently set VHDL language revision.

	:returns:               The VHDL language revision's release year.
	:raises OSVVMException: When the currently set VHDL language revision is unknown in this decoding function.

	.. seealso::

	   * :func:`SetVHDLVersion`
	"""
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
			osvvmContext.RaiseException(OSVVMException(f"Unsupported VHDL version '{osvvmContext.VHDLVersion}'."))

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def SetCoverageAnalyzeEnable(value: bool) -> None:
	"""
	Not implemented by pyEDAA.OSVVM.
	"""
	osvvmContext.RaiseException(NotImplementedError(f"Procedure 'SetCoverageAnalyzeEnable' is not implemented."))


@export
def SetCoverageSimulateEnable(value: bool) -> None:
	"""
	Not implemented by pyEDAA.OSVVM.
	"""
	osvvmContext.RaiseException(NotImplementedError(f"Procedure 'SetCoverageSimulateEnable' is not implemented."))


@export
def FileExists(file: str) -> bool:
	"""
	This function implements the behavior of OSVVM's ``FileExists`` procedure.

	Check if the given file exists.

	:param file:        File name.
	:returns:           True, if file exists, otherwise False.
	:raises ValueError: When parameter 'file' is empty.

	.. seealso::

	   * :func:`DirectoryExists`
	"""
	try:
		if file == "":
			raise ValueError(f"Parameter 'file' is empty.")

		return (osvvmContext._currentDirectory / file).is_file()

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def DirectoryExists(directory: str) -> bool:
	"""
	This function implements the behavior of OSVVM's ``DirectoryExists`` procedure.

	Check if the given directory exists.

	:param directory:   Directory name.
	:returns:           True, if directory exists, otherwise False.
	:raises ValueError: When parameter 'directory' is empty.

	.. seealso::

	   * :func:`FileExists`
	"""
	try:
		if directory == "":
			raise ValueError(f"Parameter 'directory' is empty.")

		return (osvvmContext._currentDirectory / directory).is_dir()

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def ChangeWorkingDirectory(directory: str) -> None:
	"""
	This function implements the behavior of OSVVM's ``ChangeWorkingDirectory`` procedure.

	Change the current directory (virtual working directory) to the given directory.

	:param directory:       Directory name.
	:raises ValueError:     When parameter 'directory' is empty.
	:raises OSVVMException: When the referenced directory doesn't exist.

	.. seealso::

	   * :func:`build`
	   * :func:`include`
	"""
	try:
		if directory == "":
			raise ValueError(f"Parameter 'directory' is empty.")

		osvvmContext._currentDirectory = (newDirectory := osvvmContext._currentDirectory / directory)
		if not newDirectory.is_dir():  # pragma: no cover
			osvvmContext.RaiseException(OSVVMException(f"Directory '{newDirectory}' doesn't exist."), NotADirectoryError(newDirectory))

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def FindOsvvmSettingsDirectory(*args) -> None:
	"""
	Not implemented by pyEDAA.OSVVM.
	"""
	osvvmContext.RaiseException(NotImplementedError(f"Procedure 'FindOsvvmSettingsDirectory' is not implemented."))


@export
def CreateOsvvmScriptSettingsPkg(*args) -> None:
	"""
	Not implemented by pyEDAA.OSVVM.
	"""
	osvvmContext.RaiseException(NotImplementedError(f"Procedure 'CreateOsvvmScriptSettingsPkg' is not implemented."))


@export
def noop(*args) -> None:
	"""
	A no-operation dummy procedure accepting any positional arguments.

	:param args: Any arguments
	"""


@export
def ConstraintFile(file: str, *options: int) -> int:
	"""
	This function implements the behavior of pyEDAA's ``ConstraintFile`` procedure.

	Create and register a :class:`~pyEDAA.OSVVM.Project.ConstraintFile` option and return the options unique ID.

	:param file:            Path to the constraint file.
	:param options:         Optional, list of option IDs.
	:returns:               The option's unique ID.
	:raises OSVVMException: When parameter 'options' contains an unknown option ID.
	:raises OSVVMException: When referenced option is not a :class:`~pyEDAA.OSVVM.Project.ScopeToRef` or
	                        :class:`~pyEDAA.OSVVM.Project.ScopeToCell`.
	:raises OSVVMException: When the referenced constraint file doesn't exist.
	:raises OSVVMException: When the referenced constraint file isn't an ``*.sdc`` or ``*.xdc`` file.
	"""
	try:
		file = Path(file)
		fullPath = (osvvmContext._currentDirectory / file).resolve()

		properties = {}
		for optionID in options:
			try:
				option = osvvmContext._options[int(optionID)]
			except KeyError as ex:  # pragma: no cover
				osvvmContext.RaiseException(OSVVMException(f"Option {optionID} not found in option dictionary."), ex)

			if isinstance(option, OSVVM_ScopeToRef):
				properties["scopeToRef"] = option.Reference
			elif isinstance(option, OSVVM_ScopeToCell):
				properties["scopeToCell"] = option.Cell
			else:  # pragma: no cover
				ex = TypeError(f"Option {optionID} is not a ScopeToRef or ScopeToCell.")
				ex.add_note(f"Got type '{getFullyQualifiedName(option)}'.")
				osvvmContext.RaiseException(OSVVMException(f"Dereferenced option ID is not a ScopeToRef or ScopeToCell object"), ex)

		if not fullPath.exists():  # pragma: no cover
			osvvmContext.RaiseException(OSVVMException(f"Constraint file '{fullPath}' can't be found."), FileNotFoundError(fullPath))

		if not fullPath.suffix in (".sdc", ".xdc"):
			osvvmContext.RaiseException(OSVVMException(f"Path '{fullPath}' is no constraint file (*.sdc, *.xdc)."))

		constraint = OSVVM_ConstraintFile(Path(file), **properties)
		return osvvmContext.AddOption(constraint)

	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def ScopeToRef(refName: str) -> int:
	"""
	This function implements the behavior of pyEDAA's ``ScopeToRef`` procedure.

	Create and register a :class:`~pyEDAA.OSVVM.Project.ScopeToRef` option and return the options unique ID.

	:param refName:     Reference name.
	:returns:           The option's unique ID.
	:raises ValueError: When parameter 'refName' is empty.
	"""
	try:
		if refName == "":
			raise ValueError("Parameter 'refName' is a empty string.")

		ref = OSVVM_ScopeToRef(refName)
		return osvvmContext.AddOption(ref)
	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)


@export
def ScopeToCell(cellName: str) -> int:
	"""
	This function implements the behavior of pyEDAA's ``ScopeToCell`` procedure.

	Create and register a :class:`~pyEDAA.OSVVM.Project.ScopeToCell` option and return the options unique ID.

	:param cellName:    Cell name.
	:returns:           The option's unique ID.
	:raises ValueError: When parameter 'cellName' is empty.
	"""
	try:
		if cellName == "":
			raise ValueError("Parameter 'cellName' is a empty string.")

		ref = OSVVM_ScopeToCell(cellName)
		return osvvmContext.AddOption(ref)
	except OSVVMException as ex:  # pragma: no cover
		raise ex
	except Exception as ex:       # pragma: no cover
		osvvmContext.RaiseException(ex)
