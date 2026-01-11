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
Data model for OSVVM's ``*.pro`` files.
"""
from pathlib               import Path
from typing                import Optional as Nullable, List, Dict, Mapping, Iterable, TypeVar, Generic, Generator, NoReturn

from pyTooling.Decorators  import readonly, export
from pyTooling.MetaClasses import ExtendedType
from pyTooling.Common      import getFullyQualifiedName
from pyVHDLModel           import VHDLVersion

from pyEDAA.OSVVM          import OSVVMException


__all__ = ["osvvmContext", "_ParentType"]


_ParentType = TypeVar("_ParentType", bound="Base")
"""Type variable for the parent reference."""


@export
class Base(Generic[_ParentType], metaclass=ExtendedType, slots=True):
	"""
	Base-class for all entities in the data model reflecting an OSVVM ``*.pro`` file.
	"""
	_parent: Nullable[_ParentType]  #: Reference to a parent object.

	def __init__(self, parent: Nullable[_ParentType] = None) -> None:
		"""
		Initializes the base-class with a parent reference.

		:param parent: Optional, reference to a parent object.
		"""
		self._parent = parent

	@readonly
	def Parent(self) -> Nullable[_ParentType]:
		"""
		Read-only property to access the parent object reference (:attr:`_parent`).

		:returns: Parent object.
		"""
		return self._parent


@export
class Named(Base[_ParentType], Generic[_ParentType]):
	"""
	Base-class for all named classes in the data model reflecting an OSVVM ``*.pro`` file.
	"""
	_name: str  #: Name of the entity.

	def __init__(
		self,
		name:   str,
		parent: Nullable[_ParentType] = None
	) -> None:
		"""
		Initializes the base-class with a parent reference.

		:param name:        Name of the entity.
		:param parent:      Optional, reference to a parent object.
		:raises TypeError:  When parameter 'name' is not of type string.
		:raises ValueError: When parameter 'name' is empty.
		"""
		super().__init__(parent)

		if not isinstance(name, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'name' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex
		elif name == "":
			raise ValueError(f"Parameter 'name' is empty.")

		self._name = name

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the entity's name (:attr:`_name`).

		:returns: Name of the entity.
		"""
		return self._name

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}: {self._name}"


@export
class Option(metaclass=ExtendedType, slots=True):
	"""
	Base-class for all options in the data model used within an OSVVM ``*.pro`` file.
	"""


@export
class NoNullRangeWarning(Option):
	"""
	Analysis option: Disable null-range warnings for VHDL files at analysis.
	"""
	def __init__(self) -> None:
		"""
		Initializes this option.
		"""
		super().__init__()

	def __repr__(self) -> str:
		return "NoNullRangeWarning"


@export
class SourceFile(Base[_ParentType], Generic[_ParentType]):
	"""
	A base-class describing any source file (VHDL, Verilog, ...) supported by OSVVM Scripts.
	"""

	_path: Path  #: Path to the source file.

	def __init__(
		self,
		path:   Path,
		parent: Nullable[Base[_ParentType]] = None
	) -> None:
		"""
		Initializes a source file.

		:param path:   Path to the source file.
		:param parent: Reference to the parent entity.
		:raises TypeError: When parameter 'path' is not of type :class:`pathlib.Path`.
		"""
		super().__init__(parent)

		if not isinstance(path, Path):  # pragma: no cover
			ex = TypeError(f"Parameter 'path' is not a Path.")
			ex.add_note(f"Got type '{getFullyQualifiedName(path)}'.")
			raise ex

		self._path = path

	@readonly
	def Path(self) -> Path:
		"""
		Read-only property to access the path to the sourcefile (:attr:`_path`).

		:returns: The sourcefile's path.
		"""
		return self._path

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}: {self._path}"


@export
class XDCConstraintFile(SourceFile):
	"""
	Represents an XDC constraint file.
	"""
	_scopeToRef:  Nullable[str]  #: Bind this constraint file to a reference within the design (e.g. VHDL entity name).
	_scopeToCell: Nullable[str]  #: Bind this constraint file to a cell name within the design.

	def __init__(self, path: Path, scopeToRef: Nullable[str], scopeToCell: Nullable[str]) -> None:
		"""
		Initializes an XDC constraint file.

		:param path:        Path to the XDC file.
		:param scopeToRef:  Optional, ``ScopeToRef`` parameter for Vivado.
		:param scopeToCell: Optional, ``ScopeToCell`` parameter for Vivado.
		:raises TypeError:  When parameter 'scopeToRef' is not of type string.
		:raises TypeError:  When parameter 'scopeToCell' is not of type string.
		"""
		super().__init__(path)

		if scopeToRef is not None and not isinstance(scopeToRef, str):
			ex = TypeError(f"Parameter 'scopeToRef' is not a str.")
			ex.add_note(f"Got type '{getFullyQualifiedName(scopeToRef)}'.")
			raise ex

		self._scopeToRef =  scopeToRef

		if scopeToCell is not None and not isinstance(scopeToCell, str):
			ex = TypeError(f"Parameter 'scopeToCell' is not a str.")
			ex.add_note(f"Got type '{getFullyQualifiedName(scopeToCell)}'.")
			raise ex

		self._scopeToCell = scopeToCell

	def __repr__(self) -> str:
		properties = []
		if self._scopeToRef is not None:
			properties.append(f"ScopeToRef={self._scopeToRef}")
		if self._scopeToCell is not None:
			properties.append(f"ScopeToCell={self._scopeToCell}")

		props = f" {{{', '.join(properties)}}}" if len(properties) > 0 else ""

		return f"{super().__repr__()}{props}"


@export
class VHDLSourceFile(SourceFile["VHDLLibrary"]):
	"""
	Represents a VHDL source file.
	"""
	_vhdlVersion:        VHDLVersion       #: VHDL language revision used for analyzing the file.
	_noNullRangeWarning: Nullable[bool]    #: Optional setting, if null-range warnings should be suppressed while analysis.
	_associatedFiles:    List[SourceFile]  #: List of associated XDC files.

	def __init__(
		self,
		path: Path,
		vhdlVersion:        VHDLVersion = VHDLVersion.VHDL2008,
		vhdlLibrary:        Nullable["VHDLLibrary"] = None,
		noNullRangeWarning: Nullable[bool] = None,
		associatedFiles:    Nullable[Iterable[SourceFile]] = None
	) -> None:
		"""
		Initializes a VHDL source file.

		:param path:               Path to the VHDL source file.
		:param vhdlVersion:        VHDL language revision used for analysis.
		:param vhdlLibrary:        Optional, VHDL library all contained design units are compiled into.
		:param noNullRangeWarning: Optional, suppress null-range warnings while analyzing.
		:param associatedFiles:    Optional, list of associated files.
		:raises TypeError:         When parameter 'vhdlLibrary' is not of type :class:`VHDLLibrary`.
		:raises TypeError:         When parameter 'vhdlversion' is not of type :class:`~pyVHDLModel.VHDLVersion`.
		:raises TypeError:         When parameter 'noNullRangeWarning' is not of type boolean.
		"""
		if vhdlLibrary is None:
			super().__init__(path)
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
		# TODO: iterate and check element types
		self._associatedFiles =    [] if associatedFiles is None else [f for f in associatedFiles]

	@readonly
	def VHDLLibrary(self) -> Nullable["VHDLLibrary"]:
		"""
		Read-only property to access the VHDL file's VHDL library (:attr:`_parent`).

		:returns: The VHDL library this file and its design units is compiled into.
		"""
		return self._parent

	@property
	def VHDLVersion(self) -> VHDLVersion:
		"""
		Property to access the VHDL language revision (:attr:`_vhdlVersion`).

		:returns: The used VHDL revision to analyze the file.
		"""
		return self._vhdlVersion

	@VHDLVersion.setter
	def VHDLVersion(self, value: VHDLVersion) -> None:
		if not isinstance(value, VHDLVersion):
			ex = TypeError(f"Parameter 'value' is not a VHDLVersion.")
			ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
			raise ex

		self._vhdlVersion = value

	@property
	def NoNullRangeWarning(self) -> Nullable[bool]:
		"""
		Property to access the no-null-range-warning option (:attr:`_noNullRangeWarning`).

		:returns: The option's value.
		"""
		return self._noNullRangeWarning

	@NoNullRangeWarning.setter
	def NoNullRangeWarning(self, value: bool) -> None:
		if value is not None and not isinstance(value, bool):
			ex = TypeError(f"Parameter 'value' is not a boolean.")
			ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
			raise ex

		self._noNullRangeWarning = value

	@readonly
	def AssociatedFiles(self) -> List[SourceFile]:
		"""
		Read-only property to access the list of associated files (:attr:`_associatedFiles`).

		:returns: The list of associated files.
		"""
		return self._associatedFiles

	def __repr__(self) -> str:
		options = ""
		if self._noNullRangeWarning is not None:
			options += f", NoNullRangeWarning"
		return f"VHDLSourceFile: {self._path} ({self._vhdlVersion}{options})"


@export
class VHDLLibrary(Named["Build"]):
	"""
	A VHDL library collecting multiple VHDL files containing VHDL design units.
	"""

	_files: List[VHDLSourceFile]  #: VHDL source files within this VHDL library.

	def __init__(
		self,
		name:      str,
		vhdlFiles: Nullable[Iterable[VHDLSourceFile]] = None,
		build:     Nullable["Build"] = None
	) -> None:
		"""
		Initializes a VHDL library.

		:param name:        Name of the VHDL library.
		:param vhdlFiles:   Optional, list of VHDL source files.
		:param build:       Optional, parent reference to a :class:`Build`.
		:raises TypeError:  When parameter 'name' is not of type string.
		:raises ValueError: When parameter 'name' is empty.
		:raises TypeError:  When parameter 'build' is not of type :class:`Build`.
		:raises TypeError:  When parameter 'vhdlFiles' is not an iterable.
		:raises TypeError:  When parameter 'vhdlFiles' contains elements not of type :class:`VHDLSourceFile`.
		"""
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
				if not isinstance(vhdlFile, VHDLSourceFile):
					ex = TypeError(f"Parameter 'vhdlFiles' contains elements not of type VHDLSourceFile.")
					ex.add_note(f"Got type '{getFullyQualifiedName(vhdlFile)}'.")
					raise ex

				vhdlFile._parent = self
				self._files.append(vhdlFile)
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'vhdlFiles' is not an iterable of VHDLSourceFile.")
			ex.add_note(f"Got type '{getFullyQualifiedName(vhdlFiles)}'.")
			raise ex

	@readonly
	def Build(self) -> Nullable["Build"]:
		"""
		Read-only property to access the build object (:attr:`_parent`).

		:returns: The parent object.
		"""
		return self._parent

	@readonly
	def Files(self) -> List[SourceFile]:
		"""
		Read-only property to access the list of VHDl source files in this VHDL library (:attr:`_files`).

		:returns: The list of VHDL source files in this VHDL library.
		"""
		return self._files

	def AddFile(self, file: VHDLSourceFile) -> None:
		"""
		Add a file to this VHDL library.

		:param file: VHDL source file to add.
		:raises TypeError: When parameter 'file' is not of type :class:`VHDLSourceFile`.
		"""
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
	"""
	Elaboration option: A generic value for a VHDL top-level entity.
	"""
	_name:  str  #: Name of the generic.
	_value: str  #: Value of the generic.

	def __init__(
		self,
		name:   str,
		value:  str
	) -> None:
		"""
		Initializes a generic value.

		:param name:       Name of the generic.
		:param value:      Value of the generic.
		:raises TypeError: When parameter 'name' us not of type string.
		:raises TypeError: When parameter 'value' us not of type string.
		"""
		super().__init__()

		if not isinstance(name, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'name' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex
		elif name == "":
			raise ValueError(f"Parameter 'name' is empty.")

		self._name = name

		if not isinstance(value, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'value' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
			raise ex

		self._value = value

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the generic's name (:attr:`_name`).

		:returns: The parent object.
		"""
		return self._name

	@readonly
	def Value(self) -> str:
		"""
		Read-only property to access the generic's value (:attr:`_value`).

		:returns: The parent object.
		"""
		return self._value

	def __repr__(self) -> str:
		return f"{self._name} = {self._value}"


@export
class ConstraintFile(Option):
	"""
	Associated file option: Associated constraint file for VHDL sourcefiles.
	"""
	_path:        Path           #: Path to the constraint file.
	_scopeToRef:  Nullable[str]  #: Optional, ScopeToRef binding name.
	_scopeToCell: Nullable[str]  #: Optional, ScopeToCell binding name.

	def __init__(
		self,
		path:        Path,
		scopeToRef:  Nullable[str] = None,
		scopeToCell: Nullable[str] = None
	) -> None:
		"""
		Initialize a constraint file option.

		:param path:        Path to the constraint file.
		:param scopeToRef:  Optional, ScopeToRef binding name.
		:param scopeToCell: Optional, ScopeToCell binding name.
		:raises TypeError:  When parameter 'path' is not of type :class:`~pathlib.Path`.
		:raises TypeError:  When parameter 'scopeToRef' is not of type string.
		:raises TypeError:  When parameter 'scopeToCell' is not of type string.
		"""
		super().__init__()

		if not isinstance(path, Path):  # pragma: no cover
			ex = TypeError(f"Parameter 'path' is not a Path.")
			ex.add_note(f"Got type '{getFullyQualifiedName(path)}'.")
			raise ex

		self._path = path

		if scopeToRef is not None and not isinstance(scopeToRef, str):
			ex = TypeError(f"Parameter 'scopeToRef' is not a str.")
			ex.add_note(f"Got type '{getFullyQualifiedName(path)}'.")
			raise ex

		self._scopeToRef = scopeToRef

		if scopeToCell is not None and not isinstance(scopeToCell, str):
			ex = TypeError(f"Parameter 'scopeToCell' is not a str.")
			ex.add_note(f"Got type '{getFullyQualifiedName(path)}'.")
			raise ex

		self._scopeToCell = scopeToCell

	@readonly
	def Path(self) -> Path:
		"""
		Read-only property to access the constraint file's path (:attr:`_path`).

		:returns: The constraint file's path.
		"""
		return self._path

	@readonly
	def ScopeToRef(self) -> Nullable[str]:
		"""
		Read-only property to access the constraint file's binding to a reference in the design (:attr:`_scopeToRef`).

		:returns: The ``ScopeToRef`` binding.
		"""
		return self._scopeToRef

	@readonly
	def ScopeToCell(self) -> Nullable[str]:
		"""
		Read-only property to access the constraint file's binding to a reference in the design (:attr:`_scopeToCell`).

		:returns: The ``ScopeToCell`` binding.
		"""
		return self._scopeToCell

	def __repr__(self) -> str:
		properties = []
		if self._scopeToRef is not None:
			properties.append(f"ScopeToRef={self._scopeToRef}")
		if self._scopeToCell is not None:
			properties.append(f"ScopeToCell={self._scopeToCell}")

		props = f" {{{', '.join(properties)}}}" if len(properties) > 0 else ""

		return f"{self._path}{props}"


@export
class ScopeToRef(Option):
	"""
	Constrain file option: ScopeToRef binding.
	"""
	_reference:  str  #: Reference name.

	def __init__(
		self,
		reference: str
	) -> None:
		"""
		Initialize a ScopeToRef binding.

		:param reference:  Reference name.
		:raises TypeError: When parameter 'reference' is not of type string.
		"""
		super().__init__()

		if not isinstance(reference, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'reference' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(reference)}'.")
			raise ex

		self._reference = reference

	@readonly
	def Reference(self) -> str:
		"""
		Read-only property to access the reference name (:attr:`_reference`).

		:returns: The reference name.
		"""
		return self._reference

	def __repr__(self) -> str:
		return f"{self._reference}"


@export
class ScopeToCell(Option):
	"""
	Constrain file option: ScopeToCell binding.
	"""
	_cell:  str  #: Cell name

	def __init__(
		self,
		cell: str
	) -> None:
		"""
		Initialize a ScopeToCell binding.

		:param cell:       Cell name.
		:raises TypeError: When parameter 'cell' is not of type string.
		"""
		super().__init__()

		if not isinstance(cell, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'cell' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(cell)}'.")
			raise ex

		self._cell = cell

	@readonly
	def Cell(self) -> str:
		"""
		Read-only property to access the cell name (:attr:`_cell`).

		:returns: The cell name.
		"""
		return self._cell

	def __repr__(self) -> str:
		return f"{self._cell}"


@export
class Testcase(Named["Testsuite"]):
	"""
	An OSVVM testcase.
	"""
	_toplevelName: Nullable[str]   #: Name of the VHDL simulation toplevel entity or configuration.
	_generics:     Dict[str, str]  #: A dictionary of toplevel generic values.

	def __init__(
		self,
		name:         str,
		toplevelName: Nullable[str] = None,
		generics:     Nullable[Iterable[GenericValue] | Mapping[str, str]] = None,
		testsuite:    Nullable["Testsuite"] = None
	) -> None:
		"""
		Initialize an OSVVM testcase.

		:param name:         Name of the testcase.
		:param toplevelName: Optional, name of the toplevel entity or configuration.
		:param generics:     Optional, list or dictionary of generic values to run the simulation.
		:param testsuite:    Optional, reference to the parent testsuite.
		:raises TypeError:   When parameter 'name' is not of type string.
		:raises ValueError:  When parameter 'name' is empty.
		:raises TypeError:   When parameter 'testsuite' is not of type :class:`Testsuite`.
		:raises TypeError:   When parameter 'toplevelName' is not of type string.
		:raises TypeError:   When parameter 'generics' is not a mapping or iterable.
		:raises TypeError:   When parameter 'generics' contains elements not of type :class:`GenericValue`.
		"""
		if testsuite is None:
			super().__init__(name, None)
		elif isinstance(testsuite, Testsuite):
			super().__init__(name, testsuite)
			testsuite._testcases[name] = self
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'testsuite' is not a Testsuite.")
			ex.add_note(f"Got type '{getFullyQualifiedName(testsuite)}'.")
			raise ex

		if toplevelName is not None and not isinstance(toplevelName, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'toplevelName' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(toplevelName)}'.")
			raise ex

		self._toplevelName = toplevelName

		self._generics = {}
		if generics is None:
			pass
		elif isinstance(generics, Mapping):
			for key, value in generics.items():
				# TODO: check for str and str?
				self._generics[key] = value
		elif isinstance(generics, Iterable):
			for item in generics:
				if not isinstance(item, GenericValue):  # pragma: no cover
					ex = TypeError(f"Parameter 'generics' contains elements which are not of type GenericValue.")
					ex.add_note(f"Got type '{getFullyQualifiedName(item)}'.")
					raise ex

				self._generics[item._name] = item._value
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'generics' is not an iterable of GenericValue nor a dictionary of strings.")
			ex.add_note(f"Got type '{getFullyQualifiedName(generics)}'.")
			raise ex

	@readonly
	def Testsuite(self) -> "Testsuite":
		"""
		Read-only property to access the parent testsuite (:attr:`_parent`).

		:returns: The parent testsuite.
		"""
		return self._parent

	@readonly
	def ToplevelName(self) -> str:
		"""
		Read-only property to access the testcases toplevel name (:attr:`_toplevelName`).

		:returns: The toplevel name.
		"""
		return self._toplevelName

	@readonly
	def Generics(self) -> Dict[str, str]:
		"""
		Read-only property to access the testcase's toplevel generics (:attr:`_generics`).

		:returns: The dictionary of generic values for this testcase.
		"""
		return self._generics

	# TODO: why is this not a setter?
	def SetToplevel(self, toplevelName: str) -> None:
		"""
		Set the testcase's toplevel entity or configuration.

		:param toplevelName: Name of the toplevel.
		:raises TypeError:   When parameter 'toplevelName' is not of type string.
		"""
		if not isinstance(toplevelName, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'toplevelName' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(toplevelName)}'.")
			raise ex
		elif toplevelName == "":
			raise ValueError(f"Parameter 'toplevelName' is empty.")

		self._toplevelName = toplevelName

	def AddGeneric(self, genericValue: GenericValue) -> None:
		"""
		Add a generic value to this testcase.

		:param genericValue: Generic value to be added.
		:raises TypeError:   When parameter 'genericValue' is not of type :class:`GenericValue`.
		"""
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
	"""
	An OSVVM testsuite containing multiple OSVVM testcases.
	"""
	_testcases: Dict[str, Testcase]  #: Dictionary of testcases.

	def __init__(
		self,
		name:      str,
		testcases: Nullable[Iterable[Testcase] | Mapping[str, Testcase]] = None,
		build:     Nullable["Build"] = None
	) -> None:
		"""
		Initialize an OSVVM testsuite.

		:param name:        Name of the testsuite.
		:param testcases:   Optional, list or dictionary of testcases.
		:param build:       Optional, reference to the parent build.
		:raises TypeError:  When parameter 'name' is not of type string.
		:raises ValueError: When parameter 'name' is empty.
		:raises TypeError:  When parameter 'build' is not of type :class:`Build`.
		:raises TypeError:  When parameter 'testcases' is not an iterable or mapping.
		:raises TypeError:  When parameter 'testcases' contains an element not of type :class:`Testcase`.
		"""
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
				# TODO: check types of key/value
				value._parent = self
				self._testcases[key] = value
		elif isinstance(testcases, Iterable):
			for item in testcases:
				if not isinstance(item, Testcase):  # pragma: no cover
					ex = TypeError(f"Parameter 'testcases' contains elements not of type Testcase.")
					ex.add_note(f"Got type '{getFullyQualifiedName(item)}'.")
					raise ex

				item._parent = self
				self._testcases[item._name] = item
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'testcases' is not an iterable of Testcase nor a mapping of Testcase.")
			ex.add_note(f"Got type '{getFullyQualifiedName(testcases)}'.")
			raise ex

	@readonly
	def Build(self) -> Nullable["Build"]:
		"""
		Read-only property to access the parent build (:attr:`_parent`).

		:returns: The parent build.
		"""
		return self._parent

	@readonly
	def Testcases(self) -> Dict[str, Testcase]:
		"""
		Read-only property to access the dictionary of testcases (:attr:`_testcases`).

		:returns: The dictionary of testcases.
		"""
		return self._testcases

	def AddTestcase(self, testcase: Testcase) -> None:
		"""
		Add a testcase to the testsuite.

		:param testcase:   Testcase to add.
		:raises TypeError: When parameter 'testcase' is not of type :class:`Testcase`.
		"""
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
	"""OSVVM option: Name of a build."""
	_name: str  #: Name of the build.

	def __init__(
		self,
		name: str,
	) -> None:
		"""
		Initialize the build name option.

		:param name:       Name of the build
		:raises TypeError: When parameter 'name' is not of type string.
		"""
		super().__init__()

		if not isinstance(name, str):  # pragma: no cover
			ex = TypeError(f"Parameter 'name' is not a string.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex

		self._name = name

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the build name (:attr:`_name`).

		:returns: Name of the build.
		"""
		return self._name

	def __repr__(self) -> str:
		return f"BuildName: {self._name}"


@export
class Build(Named["Project"]):
	"""
	An OSVVM build containing one or multiple OSVVM testsuites.
	"""
	_includedFiles: List[Path]              #: List of loaded (included) ``*.pro`` files.
	_vhdlLibraries: Dict[str, VHDLLibrary]  #: Dictionary of VHDL libraries.
	_testsuites:    Dict[str, Testsuite]    #: Dictionary of testsuites.

	def __init__(
		self,
		name:          str,
		vhdlLibraries: Nullable[Iterable[VHDLLibrary] | Mapping[str, VHDLLibrary]] = None,
		testsuites:    Nullable[Iterable[Testsuite] | Mapping[str, Testsuite]] = None,
		project:       Nullable[Base] = None
	) -> None:
		"""
		Initialize an OSVVM build.

		:param name:          Name of the build.
		:param vhdlLibraries: Optional, list or dictionary of VHDL libraries.
		:param testsuites:    Optional, list or dictionary of OSVVM testsuites.
		:param project:       Optional, reference to the parent project.
		:raises TypeError:    When parameter 'name' is not of type string.
		:raises ValueError:   When parameter 'name' is empty.
		:raises TypeError:    When parameter 'project' is not of type :class:`Project`.
		:raises TypeError:    When parameter 'vhdlLibraries' is not an iterable or mapping.
		:raises TypeError:    When parameter 'vhdlLibraries' contains an element not of type :class:`VHDLLibrary`.
		:raises TypeError:    When parameter 'testsuites' is not an iterable or mapping.
		:raises TypeError:    When parameter 'testsuites' contains an element not of type :class:`Testsuites`.
		"""
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
				# TODO: check used datatypes
				value._parent = self
				self._vhdlLibraries[key] = value
		elif isinstance(vhdlLibraries, Iterable):
			for item in vhdlLibraries:
				if not isinstance(item, VHDLLibrary):  # pragma: no cover
					ex = TypeError(f"Parameter 'vhdlLibraries' contains elements not of type VHDLLibrary.")
					ex.add_note(f"Got type '{getFullyQualifiedName(item)}'.")
					raise ex

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
				# TODO: check used datatypes
				value._parent = self
				self._testsuites[key] = value
		elif isinstance(testsuites, Iterable):
			for item in testsuites:
				if not isinstance(item, Testsuite):  # pragma: no cover
					ex = TypeError(f"Parameter 'testsuites' contains elements not of type Testsuite.")
					ex.add_note(f"Got type '{getFullyQualifiedName(item)}'.")
					raise ex

				item._parent = self
				self._testsuites[item._name] = item
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'testsuites' is not an iterable of Testsuite nor a mapping of Testsuite.")
			ex.add_note(f"Got type '{getFullyQualifiedName(testsuites)}'.")
			raise ex

	@readonly
	def Project(self) -> Nullable["Project"]:
		"""
		Read-only property to access the parent project (:attr:`_parent`).

		:returns: The parent project.
		"""
		return self._parent

	@readonly
	def IncludedFiles(self) -> Generator[Path, None, None]:
		"""
		Read-only property to return a generator for all included (loaded) ``*.pro`` files (:attr:`_includedFiles`).

		:returns: The sequence of loaded ``*.pro`` files.
		"""
		return (file for file in self._includedFiles)

	@readonly
	def VHDLLibraries(self) -> Dict[str, VHDLLibrary]:
		"""
		Read-only property to access the dictionary of VHDL libraries (:attr:`_vhdlLibraries`).

		:returns: The dictionary of VHDL libraries.
		"""
		return self._vhdlLibraries

	@readonly
	def Testsuites(self) -> Dict[str, Testsuite]:
		"""
		Read-only property to access the dictionary of testsuites (:attr:`_testsuites`).

		:returns: The dictionary of testsuites.
		"""
		return self._testsuites

	def AddVHDLLibrary(self, vhdlLibrary: VHDLLibrary) -> None:
		"""
		Add a VHDL library to the build.

		:param vhdlLibrary: VHDL library to add.
		:raises TypeError:  When parameter 'vhdlLibrary' is not of type :class:`VHDLLibrary`.
		"""
		if not isinstance(vhdlLibrary, VHDLLibrary):  # pragma: no cover
			ex = TypeError(f"Parameter 'vhdlLibrary' is not a VHDLLibrary.")
			ex.add_note(f"Got type '{getFullyQualifiedName(vhdlLibrary)}'.")
			raise ex

		vhdlLibrary._parent = self
		self._vhdlLibraries[vhdlLibrary._name] = vhdlLibrary

	def AddTestsuite(self, testsuite: Testsuite) -> None:
		"""
		Add a testsuite to the build.

		:param testsuite:  Testsuite to add.
		:raises TypeError: When parameter 'testsuite' is not of type :class:`Testsuite`.
		"""
		if not isinstance(testsuite, Testsuite):  # pragma: no cover
			ex = TypeError(f"Parameter 'testsuite' is not a Testsuite.")
			ex.add_note(f"Got type '{getFullyQualifiedName(testsuite)}'.")
			raise ex

		testsuite._parent = self
		self._testsuites[testsuite._name] = testsuite

	def __repr__(self) -> str:
		return f"Build: {self._name}"


@export
class Project(Named):
	"""
	An OSVVM project containing one or multiple OSVVM builds.
	"""
	_builds: Dict[str, Build]  #: Dictionary of builds

	def __init__(
		self,
		name:   str,
		builds: Nullable[Iterable[Build] | Mapping[str, Build]] = None
	) -> None:
		"""
		Initializes an OSVVM project.

		:param name:        Name of the build.
		:param builds:      Optional, list or dictionary of OSVVM builds.
		:raises TypeError:  When parameter 'name' is not of type string.
		:raises ValueError: When parameter 'name' is empty.
		:raises TypeError:  When parameter 'builds' is not an iterable or mapping.
		:raises TypeError:  When parameter 'builds' contains an element not of type :class:`Build`.
		"""
		super().__init__(name, None)

		self._builds = {}
		if builds is None:
			pass
		elif isinstance(builds, Mapping):
			for key, value in builds.items():
				# TODO: check used datatypes
				value._parent = self
				self._builds[key] = value
		elif isinstance(builds, Iterable):
			for item in builds:
				if not isinstance(item, Build):  # pragma: no cover
					ex = TypeError(f"Parameter 'builds' contains elements not of type Build.")
					ex.add_note(f"Got type '{getFullyQualifiedName(item)}'.")
					raise ex

				item._parent = self
				self._builds[item._name] = item
		else:  # pragma: no cover
			ex = TypeError(f"Parameter 'builds' is not an iterable of Build nor a mapping of Build.")
			ex.add_note(f"Got type '{getFullyQualifiedName(builds)}'.")
			raise ex

	@readonly
	def Builds(self) -> Dict[str, Build]:
		"""
		Read-only property to access the dictionary of builds (:attr:`_builds`).

		:returns: The dictionary of builds.
		"""
		return self._builds

	@readonly
	def IncludedFiles(self) -> Generator[Path, None, None]:
		"""
		Read-only property to return a generator for all included (loaded) ``*.pro`` files.

		.. note::

		   This generator iterates all builds (:attr:`_builds`) and returns a combined generator for all included files.

		:returns: The sequence of loaded ``*.pro`` files.
		"""
		for build in self._builds.values():
			yield from build.IncludedFiles

	def AddBuild(self, build: Build) -> None:
		"""
		Add a build to the project.

		:param build:      Build to add.
		:raises TypeError: When parameter 'build' is not of type :class:`Build`.
		"""
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
	"""
	The OSVVM TCL execution context.

	When an OSVVM ``*.pro`` file is executed, it relies on a context for storing the currently objects and settings. For
	example the currently used testsuite or the currently set VHDL language revision.

	.. hint::

	   The context stores the last seen exception within Python scripting in :attr:`_lastException`, because TCL doesn't
	   forward a raised Python exception through TCL back into the Python context. It just raises a generic
	   :exc:`~tkinter.TclError`. The helper function :func:`~pyEDAA.OSVVM.Project.TCL.getException` help to restore the
	   original Python exception using this context object.
	"""
	# _tcl:              TclEnvironment

	_processor:        "OsvvmProFileProcessor"  #: The TCL processor.
	_lastException:    Nullable[Exception]      #: Last Python exception seen.

	_workingDirectory: Path                     #: The working directory, where the processing started.
	_currentDirectory: Path                     #: The virtual working directory, e.g. updated by including other ``*.pro`` files.
	_includedFiles:    List[Path]               #: A list of used ``*.pro`` files.

	_vhdlversion:      VHDLVersion              #: The currently set VHDL language revision.

	_vhdlLibrary:      Nullable[VHDLLibrary]    #: The currently active VHDL library.
	_vhdlLibraries:    Dict[str, VHDLLibrary]   #: A dictionary of known VHDL libraries.

	_testsuite:        Nullable[Testsuite]      #: The currently active OSVVM testsuite.
	_testsuites:       Dict[str, Testsuite]     #: A dictionary of known testsuites.
	_testcase:         Nullable[Testcase]       #: The currently active OSVVM testcase.
	_options:          Dict[int, Option]        #: A dictionary of gathered options.

	_build:            Nullable[Build]          #: The currently active OSVVM build.
	_builds:           Dict[str, Build]         #: A dictionary of known OSVVM builds.

	def __init__(self) -> None:
		"""
		Initializes a TCL execution context for OSVVM ``*.pro`` file processing.
		"""
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
		"""
		Clear the TCL execution context.
		"""
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
		"""
		Read-only property to access the TCL processor (:attr:`_processor`).

		:returns: The TCL processor.
		"""
		return self._processor

	@property
	def LastException(self) -> Nullable[Exception]:
		"""
		Property to access the last seen Python exception (:attr:`_lastException`).

		:returns: The last seen Python exception. This might return ``None``.
		"""
		lastException = self._lastException
		self._lastException = None
		return lastException

	@LastException.setter
	def LastException(self, value: Exception) -> None:
		self._lastException = value

	@readonly
	def WorkingDirectory(self) -> Path:
		"""
		Read-only property to access the working directory (:attr:`_workingDirectory`).

		:returns: The working directory.
		"""
		return self._workingDirectory

	@readonly
	def CurrentDirectory(self) -> Path:
		"""
		Read-only property to access the current directory (:attr:`_currentDirectory`).

		The current directory is a virtual working directory used while processing ``*.pro`` files.

		:returns: The current directory.
		"""
		return self._currentDirectory

	@property
	def VHDLVersion(self) -> VHDLVersion:
		"""
		Property to access the VHDL language revision (:attr:`_vhdlVersion`).

		:returns: The currently set VHDL revision.
		"""
		return self._vhdlversion

	@VHDLVersion.setter
	def VHDLVersion(self, value: VHDLVersion) -> None:
		self._vhdlversion = value

	@readonly
	def IncludedFiles(self) -> List[Path]:
		"""
		Read-only property to access list of included ``*.pro`` files (:attr:`_includedFiles`).

		:returns: The list of loaded files.
		"""
		return self._includedFiles

	@readonly
	def VHDLLibrary(self) -> VHDLLibrary:
		"""
		Read-only property to access the currently active VHDL library (:attr:`_vhdlLibrary`).

		:returns: The active VHDL libraries.
		"""
		return self._vhdlLibrary

	@readonly
	def VHDLLibraries(self) -> Dict[str, VHDLLibrary]:
		"""
		Read-only property to access the dictionary of known VHDL libraries (:attr:`_vhdlLibraries`).

		:returns: The dictionary of VHDL libraries.
		"""
		return self._vhdlLibraries

	@readonly
	def Testsuite(self) -> Testsuite:
		"""
		Read-only property to access the currently active OSVVM testsuite (:attr:`_testsuite`).

		:returns: The active OSVVM testsuite.
		"""
		return self._testsuite

	@readonly
	def Testsuites(self) -> Dict[str, Testsuite]:
		"""
		Read-only property to access the dictionary of known OSVVM testsuites (:attr:`_testsuites`).

		:returns: The dictionary of OSVVM testsuites.
		"""
		return self._testsuites

	@readonly
	def TestCase(self) -> Testcase:
		"""
		Read-only property to access the currently active OSVVM testcase (:attr:`_testcase`).

		:returns: The active OSVVM testcase.
		"""
		return self._testcase

	@readonly
	def Build(self) -> Build:
		"""
		Read-only property to access the currently active OSVVM build (:attr:`_build`).

		:returns: The active OSVVM build.
		"""
		return self._build

	@readonly
	def Builds(self) -> Dict[str, Build]:
		"""
		Read-only property to access the dictionary of known OSVVM builds (:attr:`_build`).

		:returns: The dictionary of OSVVM builds.
		"""
		return self._builds

	def ToProject(self, projectName: str) -> Project:
		"""
		Convert the context to an OSVVM project.

		:param projectName: Name of the project.
		:returns:           OSVVM project.
		"""
		return Project(projectName, self._builds)

	def RaiseException(self, ex: Exception, cause: Nullable[Exception] = None) -> NoReturn:
		"""
		Raise an exception, but keep a reference to the exception object in the TCL execution context.

		:param ex: Exception to be raised.
		"""
		if cause is not None:
			ex.__cause__ = cause

		self._lastException = ex
		raise ex

	def BeginBuild(self, buildName: str) -> Build:
		"""
		Begin a new build context within the overall TCL execution context.

		:param buildName:       Name of the new build.
		:returns:               Currently active OSVVM build object.
		:raises OSVVMException: When a VHDL library has been created outside a build context.
		:raises OSVVMException: When a OSVVM testsuite has been created outside a build context.
		"""
		if len(self._vhdlLibraries) > 0:
			ex = OSVVMException(f"VHDL libraries have been created outside of an OSVVM build script.")
			ex.add_note(f"TCL command 'library' has been called before 'build'.")
			raise ex
		if len(self._testsuites) > 0:
			ex = OSVVMException(f"Testsuites have been created outside of an OSVVM build script.")
			ex.add_note(f"TCL command 'TestSuite' has been called before 'build'.")
			raise ex

		build = Build(buildName)
		build._vhdlLibraries = self._vhdlLibraries
		build._testsuites = self._testsuites

		self._build = build
		self._builds[buildName] = build

		return build

	def EndBuild(self) -> Build:
		"""
		Finalize the currently active build context.

		The TCL execution context is cleaned up: partially reset the context and initialize some fields with new data
		structures.

		:returns: The OSVVM build object.
		"""
		build = self._build

		self._vhdlLibrary = None
		self._vhdlLibraries = {}
		self._testcase = None
		self._testsuite = None
		self._testsuites = {}
		self._build = None

		# TODO: should this be handled in LoadBuildFile ?
		self._currentDirectory = self._workingDirectory

		return build

	def IncludeFile(self, proFileOrBuildDirectory: Path) -> Path:
		"""
		Include a specific ``*.pro`` file or the ``*.pro`` file from an OSVVM build directory.

		.. hint::

		   An OSVVM build directory is a directory:

		   * containing a ``build.pro`` file (new style), or
		   * containing a ``*.pro`` file with the same name as the directory its contained in (old style).

		:param proFileOrBuildDirectory: The path to the ``*.pro`` file or directory containing a ``*.pro`` file. |br|
		                                Only relative paths are supported.
		:returns:                       The resolved path to the found ``*.pro`` file.
		:raises TypeError:              When parameter 'proFileOrBuildDirectory' is not of type :class:`~pathlib.Path`.
		:raises OSVVMException:         When parameter 'proFileOrBuildDirectory' contains an absolut path.
		:raises OSVVMException:         When the resolved path doesn't reference to a ``*.pro`` file.
		:raises OSVVMException:         When the resolved path isn't an OSVVM build directory.
		:raises OSVVMException:         When the resolved path neither references a ``*.pro`` file nor an OSVVM build
		                                directory.
		"""
		if not isinstance(proFileOrBuildDirectory, Path):  # pragma: no cover
			ex = TypeError(f"Parameter 'proFileOrBuildDirectory' is not a Path.")
			ex.add_note(f"Got type '{getFullyQualifiedName(proFileOrBuildDirectory)}'.")
			self.RaiseException(ex)

		if proFileOrBuildDirectory.is_absolute():
			ex = OSVVMException(f"Absolute path '{proFileOrBuildDirectory}' not supported.")
			self.RaiseException(ex)

		path = (self._currentDirectory / proFileOrBuildDirectory).resolve()
		if path.is_file():
			if path.suffix == ".pro":
				self._currentDirectory = path.parent.relative_to(self._workingDirectory, walk_up=True)
				proFile = self._currentDirectory / path.name
			else:
				self.RaiseException(OSVVMException(f"Path '{proFileOrBuildDirectory}' is not a *.pro file."))
		elif path.is_dir():
			self._currentDirectory = path
			proFile = path / "build.pro"
			if not proFile.exists():
				proFile = path / f"{path.name}.pro"
				if not proFile.exists():  # pragma: no cover
					ex = OSVVMException(f"Path '{proFileOrBuildDirectory}' is not a build directory.")
					ex.__cause__ = FileNotFoundError(path / "build.pro")
					self.RaiseException(ex)
		else:  # pragma: no cover
			self.RaiseException(OSVVMException(f"Path '{proFileOrBuildDirectory}' is not a *.pro file or build directory."))

		self._includedFiles.append(proFile)
		return proFile

	def EvaluateFile(self, proFile: Path) -> None:
		"""
		Evaluate a ``*.pro`` file.

		:param proFile: OSVVM ``*.pro`` file to process.
		"""
		self._processor.EvaluateProFile(proFile)

	def SetLibrary(self, name: str) -> None:
		"""
		Set or create the currently active VHDL library.

		If the VHDL library isn't known in the current context, create a new VHDL library with the given name.

		:param name: Name of the VHDL library.
		:returns:    Activated VHDL library.
		"""
		try:
			self._vhdlLibrary = self._vhdlLibraries[name]
		except KeyError:
			self._vhdlLibrary = VHDLLibrary(name, build=self._build)
			self._vhdlLibraries[name] = self._vhdlLibrary

	def AddVHDLFile(self, vhdlFile: VHDLSourceFile) -> None:
		"""
		Add a VHDL source file to the currently active VHDL library.

		The VHDL source file's VHDL revision is derived from currently active VHDL revision of the TCL execution context.

		.. note::

		   If there is no active VHDL library in the context, a new VHDL library named ``default`` is created.

		:param vhdlFile: VHDL source file to be added.
		"""
		if self._vhdlLibrary is None:
			self.SetLibrary("default")

		vhdlFile.VHDLVersion = self._vhdlversion
		self._vhdlLibrary.AddFile(vhdlFile)

	def SetTestsuite(self, testsuiteName: str) -> None:
		"""
		Set or create the currently active OSVVM testsuite.

		If the testsuite isn't known in the current context, create a new testsuite with the given name.

		:param testsuiteName: Name of the OSVVM testsuite.
		:returns:             Activated OSVVM testsuite.
		"""
		try:
			self._testsuite = self._testsuites[testsuiteName]
		except KeyError:
			self._testsuite = Testsuite(testsuiteName)
			self._testsuites[testsuiteName] = self._testsuite

	# TODO: should this be called differently then Add***, because it doesn't take an object, but a new and creates a new object.
	def AddTestcase(self, testName: str) -> TestCase:
		"""
		Create a new testcase and add to the currently active OSVVM testsuite.

		.. note::

		   If there is no active OSVVM testsuite in the context, a new testsuite named ``default`` is created.

		:param testName: Name of the testcase.
		:returns:        The created OSVVM testcase object.
		"""
		if self._testsuite is None:
			self.SetTestsuite("default")

		self._testcase = Testcase(testName)
		self._testsuite._testcases[testName] = self._testcase

		return self._testcase

	def SetTestcaseToplevel(self, toplevel: str) -> TestCase:
		"""
		Set the testcase's toplevel entity or configuration name.

		:param toplevel:        Name of the toplevel entity or configuration.
		:returns:               The currently active OSVVM testcase.
		:raises OSVVMException: When there is no active OSVVM testcase.
		"""
		if self._testcase is None:
			self.RaiseException(OSVVMException("Can't set testcase toplevel, because no testcase was setup."))

		self._testcase.SetToplevel(toplevel)

		return self._testcase

	# TODO: this this an add operation or a register operation?
	def AddOption(self, option: Option) -> int:
		"""
		Register a new option and return a unique ID.

		.. hint::

		   TCL can't pass complex Python objects through the TCL layer back to Python. Therefore, complex objects like
		   options are registered in a dictionary and a unique ID (integer) is returned. Back in Python, this ID can be
		   converted back to the Python object.

		   This unique ID is based on :func:`id`.

		:param option: Option to register.
		:returns:      Unique option ID.
		"""
		optionID = id(option)
		self._options[optionID] = option

		return optionID


osvvmContext: Context = Context()
"""
Global OSVVM processing context.

:type: Context
"""
