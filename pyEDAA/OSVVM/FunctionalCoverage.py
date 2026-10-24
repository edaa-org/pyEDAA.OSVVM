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
# Copyright 2026-2026 Electronic Design Automation Abstraction (EDA²)                                                  #
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
A data model of OSVVM's functional coverage YAML file (:file:`<testcase>_cov.yml`), and its conversion to the
functional coverage model of pyEDAA.Reports.

OSVVM's ``CoveragePkg`` writes the file (``WriteCovYaml``), OSVVM's script ``ReportCov2Html.tcl`` reads it. The file
states its format version, the total coverage of the testcase, a setting, and the coverage models. It is validated
against the JSON Schema of the format version it states, listed in :data:`SCHEMAS` - e.g.
:file:`OSVVM-FunctionalCoverage-0.1.schema.json`, derived from OSVVM's writer.

* A :class:`CoverageModel` has a name, the testcases, which sampled it, its coverage, its :class:`ModelSettings`,
  the names of its fields - one per dimension -, and its bins.
* A :class:`Bin` has a name - empty, if unnamed -, a :class:`BinType`, one range of values per dimension, a count,
  its *at least* count and its percentage of coverage.

:meth:`Document.ConvertToFunctionalCoverageReport` converts a coverage model to a
:class:`~pyEDAA.Reports.FunctionalCoverage.Covergroup` with one coverage item, named as the model: a
:class:`~pyEDAA.Reports.FunctionalCoverage.Coverpoint` - its expression is the model's field name - for a model of one
dimension, a :class:`~pyEDAA.Reports.FunctionalCoverage.Cross` of the field names for a model of more dimensions.

.. rubric:: Example

.. code-block:: Python

   from pathlib import Path
   from pyEDAA.OSVVM.FunctionalCoverage import Document

   document = Document(Path("TbStream_SendGetRandom1_cov.yml"), analyzeAndConvert=True)
   report = document.ConvertToFunctionalCoverageReport()
   for covergroup in report.IterateCovergroups():
     print(f"{covergroup.Name}: {covergroup.HitCoverage:.1%}")
"""
from __future__                        import annotations

from json                              import JSONDecodeError, loads
from pathlib                           import Path
from typing                            import Any, ClassVar, Generic, Iterable, Mapping, Optional as Nullable, Self, \
                                              TypeVar

from ruamel.yaml                       import YAML, YAMLError
from pyTooling.Common                  import getFullyQualifiedName, getResourceFile, StringEnum
from pyTooling.Decorators              import export, readonly
from pyTooling.Exceptions              import ToolingException
from pyTooling.MetaClasses             import ExtendedType
from pyTooling.Stopwatch               import Stopwatch

from pyEDAA.Reports.FunctionalCoverage import BinKind, Covergroup, Coverpoint, CoverpointBin, Cross, CrossBin, \
                                              Document as fc_Document, FunctionalCoverageReport, ValueRange

from pyEDAA.OSVVM                      import OSVVMException, Resources


__all__ = ["SCHEMAS", "ParentType"]

ParentType = TypeVar("ParentType")


@export
class CoverageError(OSVVMException):
	"""The exception is raised when OSVVM's functional coverage YAML file can't be read or is inconsistent."""


@export
class FormatVersion(StringEnum):
	"""
	Version of OSVVM's functional coverage YAML format, as a file's ``Version`` states it.

	OSVVM's ``CoveragePkg`` writes the version of ``COVERAGE_YAML_VERSION`` (``OsvvmScriptSettingsPkg``), since OSVVM
	2026.01. Before, from OSVVM 2021.10 to 2025.06a, it wrote version ``1.0``, which isn't supported.
	"""

	Version0_1 = "0.1"  #: Format 0.1, written by OSVVM 2026.01 and later.


SCHEMAS: dict[FormatVersion, str] = {
	FormatVersion.Version0_1: "OSVVM-FunctionalCoverage-0.1.schema.json",
}  #: The JSON Schema a coverage file is validated against, per format version.


@export
class BinType(StringEnum):
	"""The type of a bin, as a bin's ``Type`` states it: OSVVM's action of the bin."""

	Count =   "COUNT"    #: Counts toward the coverage (``COV_COUNT``).
	Ignore =  "IGNORE"   #: Excluded from the coverage (``COV_IGNORE``).
	Illegal = "ILLEGAL"  #: Excluded from the coverage, a hit is an error (``COV_ILLEGAL``).


@export
class WeightMode(StringEnum):
	"""How a coverage model weights its bins in intelligent coverage, as a model's ``WeightMode`` states it."""

	AtLeast =      "AT_LEAST"       #: Weight is the *at least* count.
	Remain =       "REMAIN"         #: Weight is the remaining count up to the *at least* count.
	Weight =       "WEIGHT"         #: Weight is the bin's weight; deprecated.
	RemainExp =    "REMAIN_EXP"     #: Deprecated.
	RemainScaled = "REMAIN_SCALED"  #: Deprecated.
	RemainWeight = "REMAIN_WEIGHT"  #: Deprecated.


@export
class CountMode(StringEnum):
	"""Which bins a sampled value counts in, as a model's ``CountMode`` states it."""

	CountFirst = "COUNT_FIRST"  #: The first bin containing the value.
	CountAll =   "COUNT_ALL"    #: Every bin containing the value.


@export
class IllegalMode(StringEnum):
	"""What a hit of an illegal bin raises, as a model's ``IllegalMode`` states it."""

	IllegalOn =      "ILLEGAL_ON"       #: An alert of level error.
	IllegalFailure = "ILLEGAL_FAILURE"  #: An alert of level failure.
	IllegalOff =     "ILLEGAL_OFF"      #: No alert.


# A class with a property named like a class - ``WeightMode``, ``CountMode``, ``IllegalMode``, ``Settings`` - can't name
# that class in the annotation of a field: the class body's namespace, where annotations are evaluated, binds the name
# to the property.
_WeightMode =  WeightMode
_CountMode =   CountMode
_IllegalMode = IllegalMode


@export
class ModelSettings(metaclass=ExtendedType, slots=True):
	"""
	The ``Settings`` of a coverage model: its weight, goal and modes, the seeds of its randomization, and its total
	counts.

	It is a value, as a path is: it names no parent.
	"""

	_coverageWeight:  int              #: Weight of the model in the testcase's coverage (``CovWeight``).
	_goal:            float            #: Coverage goal in percent, scaling the *at least* counts (``Goal``).
	_weightMode:      _WeightMode      #: How the model weights its bins in intelligent coverage.
	_seeds:           tuple[int, int]  #: The seeds of the model's randomization.
	_countMode:       _CountMode       #: Which bins a sampled value counts in.
	_illegalMode:     _IllegalMode     #: What a hit of an illegal bin raises.
	_threshold:       float            #: Threshold in percent of intelligent coverage.
	_thresholdEnable: bool             #: Whether the threshold is enabled.
	_isRequirement:   bool             #: Whether the model is a requirement.
	_totalCount:      int              #: The hits counted toward the scaled *at least* counts (``TotalCovCount``).
	_totalGoal:       int              #: The sum of the scaled *at least* counts (``TotalCovGoal``).

	def __init__(
		self,
		coverageWeight: int,
		goal: float,
		weightMode: WeightMode,
		seeds: tuple[int, int],
		countMode: CountMode,
		illegalMode: IllegalMode,
		threshold: float,
		thresholdEnable: bool,
		isRequirement: bool,
		totalCount: int,
		totalGoal: int
	) -> None:
		"""
		Initializes the settings of a coverage model.

		:param coverageWeight:  Weight of the model in the testcase's coverage; ``0`` excludes it.
		:param goal:            Coverage goal in percent, scaling the *at least* counts.
		:param weightMode:      How the model weights its bins in intelligent coverage.
		:param seeds:           The two seeds of the model's randomization.
		:param countMode:       Which bins a sampled value counts in.
		:param illegalMode:     What a hit of an illegal bin raises.
		:param threshold:       Threshold in percent of intelligent coverage.
		:param thresholdEnable: Whether the threshold is enabled.
		:param isRequirement:   Whether the model is a requirement.
		:param totalCount:      The hits counted toward the scaled *at least* counts.
		:param totalGoal:       The sum of the scaled *at least* counts.
		:raises TypeError:      If parameter ``coverageWeight`` isn't of type :class:`int`.
		:raises TypeError:      If parameter ``totalCount`` isn't of type :class:`int`.
		:raises TypeError:      If parameter ``totalGoal`` isn't of type :class:`int`.
		:raises TypeError:      If parameter ``goal`` isn't of type :class:`float`.
		:raises TypeError:      If parameter ``threshold`` isn't of type :class:`float`.
		:raises TypeError:      If parameter ``weightMode`` isn't of type :class:`WeightMode`.
		:raises TypeError:      If parameter ``seeds`` isn't a tuple of two :class:`int`.
		:raises TypeError:      If parameter ``countMode`` isn't of type :class:`CountMode`.
		:raises TypeError:      If parameter ``illegalMode`` isn't of type :class:`IllegalMode`.
		:raises TypeError:      If parameter ``thresholdEnable`` isn't of type :class:`bool`.
		:raises TypeError:      If parameter ``isRequirement`` isn't of type :class:`bool`.
		"""
		for parameterName, value in (
			("coverageWeight", coverageWeight),
			("totalCount",     totalCount),
			("totalGoal",      totalGoal)
		):
			if not isinstance(value, int) or isinstance(value, bool):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'int'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex

		for parameterName, value in (
			("goal",      goal),
			("threshold", threshold)
		):
			if not isinstance(value, float):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'float'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex

		for parameterName, value, enumeration in (
			("weightMode",  weightMode,  WeightMode),
			("countMode",   countMode,   CountMode),
			("illegalMode", illegalMode, IllegalMode)
		):
			if not isinstance(value, enumeration):
				ex = TypeError(f"Parameter '{parameterName}' is not of type '{enumeration.__name__}'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex

		if not isinstance(seeds, tuple) or len(seeds) != 2 or \
				not all(isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds):
			ex = TypeError("Parameter 'seeds' is not a tuple of two 'int'.")
			ex.add_note(f"Got value '{seeds!r}'.")
			raise ex

		for parameterName, value in (
			("thresholdEnable", thresholdEnable),
			("isRequirement",   isRequirement)
		):
			if not isinstance(value, bool):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'bool'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex

		self._coverageWeight =  coverageWeight
		self._goal =            goal
		self._weightMode =      weightMode
		self._seeds =           seeds
		self._countMode =       countMode
		self._illegalMode =     illegalMode
		self._threshold =       threshold
		self._thresholdEnable = thresholdEnable
		self._isRequirement =   isRequirement
		self._totalCount =      totalCount
		self._totalGoal =       totalGoal

	@classmethod
	def Parse(cls, settings: Mapping[str, Any]) -> Self:
		"""
		Parse the settings of a coverage model from its ``Settings`` mapping.

		:param settings:     The ``Settings`` mapping.
		:returns:            The settings.
		:raises KeyError:    If a setting is missing.
		:raises ValueError:  If a mode isn't one OSVVM writes, or a flag isn't ``TRUE`` or ``FALSE``.
		:raises TypeError:   If a setting isn't of the type OSVVM writes.
		"""
		flags = {"TRUE": True, "FALSE": False}
		for flag in ("ThresholdEnable", "IsRequirement"):
			if settings[flag] not in flags:
				ex = ValueError(f"Setting '{flag}' is not 'TRUE' or 'FALSE'.")
				ex.add_note(f"Got value '{settings[flag]}'.")
				raise ex

		return cls(
			settings["CovWeight"],
			float(settings["Goal"]),
			WeightMode.Parse(settings["WeightMode"]),
			tuple(settings["Seeds"]),
			CountMode.Parse(settings["CountMode"]),
			IllegalMode.Parse(settings["IllegalMode"]),
			float(settings["Threshold"]),
			flags[settings["ThresholdEnable"]],
			flags[settings["IsRequirement"]],
			settings["TotalCovCount"],
			settings["TotalCovGoal"]
		)

	@readonly
	def CoverageWeight(self) -> int:
		"""
		Read-only property to access the weight of the model in the testcase's coverage (:attr:`_coverageWeight`).

		:returns: The weight; ``0``, if the model is excluded from the testcase's coverage.
		"""
		return self._coverageWeight

	@readonly
	def Goal(self) -> float:
		"""
		Read-only property to access the coverage goal, which scales the *at least* counts (:attr:`_goal`).

		:returns: The goal, in percent.
		"""
		return self._goal

	@readonly
	def WeightMode(self) -> WeightMode:
		"""
		Read-only property to access how the model weights its bins in intelligent coverage (:attr:`_weightMode`).

		:returns: The weight mode.
		"""
		return self._weightMode

	@readonly
	def Seeds(self) -> tuple[int, int]:
		"""
		Read-only property to access the seeds of the model's randomization (:attr:`_seeds`).

		:returns: The two seeds.
		"""
		return self._seeds

	@readonly
	def CountMode(self) -> CountMode:
		"""
		Read-only property to access which bins a sampled value counts in (:attr:`_countMode`).

		:returns: The count mode.
		"""
		return self._countMode

	@readonly
	def IllegalMode(self) -> IllegalMode:
		"""
		Read-only property to access what a hit of an illegal bin raises (:attr:`_illegalMode`).

		:returns: The illegal mode.
		"""
		return self._illegalMode

	@readonly
	def Threshold(self) -> float:
		"""
		Read-only property to access the threshold of intelligent coverage (:attr:`_threshold`).

		:returns: The threshold, in percent.
		"""
		return self._threshold

	@readonly
	def ThresholdEnable(self) -> bool:
		"""
		Read-only property to access whether the threshold is enabled (:attr:`_thresholdEnable`).

		:returns: ``True``, if the threshold is enabled.
		"""
		return self._thresholdEnable

	@readonly
	def IsRequirement(self) -> bool:
		"""
		Read-only property to access whether the model is a requirement (:attr:`_isRequirement`).

		:returns: ``True``, if the model is a requirement.
		"""
		return self._isRequirement

	@readonly
	def TotalCount(self) -> int:
		"""
		Read-only property to access the hits counted toward the scaled *at least* counts (:attr:`_totalCount`).

		:returns: The number of hits, as the file states it.
		"""
		return self._totalCount

	@readonly
	def TotalGoal(self) -> int:
		"""
		Read-only property to access the sum of the scaled *at least* counts (:attr:`_totalGoal`).

		:returns: The number of hits required, as the file states it.
		"""
		return self._totalGoal


_ModelSettings = ModelSettings


@export
class Element(Generic[ParentType], metaclass=ExtendedType, slots=True):
	"""
	Base-class of the elements of the format's model below the report: a reference to the element containing it, and
	to the report's root.
	"""

	_PARENT_TYPE: ClassVar[tuple[type, ...]]  #: The types a parent may have; assigned by each class.

	_parent: Nullable[ParentType]  #: The element containing this one, or ``None``.
	_root:   Nullable[Report]      #: The report's root, or ``None`` while the element isn't part of a report.

	def __init__(self, *, parent: Nullable[ParentType] = None) -> None:
		"""
		Initializes an element with its parent and the parent's root.

		The parent doesn't list the element yet: the class adds it to the parent's collection, after setting its fields.

		:param parent:     Optional, the element containing this one. Default: ``None``.
		:raises TypeError: If parameter ``parent`` isn't of a type this class declares in :attr:`_PARENT_TYPE`.
		"""
		if parent is None:
			self._parent = None
			self._root =   None
		elif not isinstance(parent, self._PARENT_TYPE):
			typeNames = " or ".join(f"'{parentType.__name__}'" for parentType in self._PARENT_TYPE)
			ex = TypeError(f"Parameter 'parent' is not of type {typeNames}.")
			ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
			raise ex
		else:
			self._parent = parent
			self._root =   parent._root

	@readonly
	def Parent(self) -> Nullable[ParentType]:
		"""
		Read-only property to access the element containing this one (:attr:`_parent`).

		:returns: The parent, or ``None`` if the element belongs to none.
		"""
		return self._parent

	@readonly
	def Root(self) -> Nullable[Report]:
		"""
		Read-only property to access the report's root (:attr:`_root`).

		:returns: The report, or ``None`` while the element isn't part of a report.
		"""
		return self._root


@export
class Bin(Element["CoverageModel"]):
	"""
	A bin of a coverage model: its name, type, one range of values per dimension, its count, *at least* count and
	percentage of coverage.

	Its parent is the :class:`CoverageModel`.
	"""

	_PARENT_TYPE: ClassVar[tuple[type, ...]]  #: A bin is in a coverage model; assigned below that class.

	_name:            str               #: Name of the bin; empty, if unnamed.
	_type:            BinType           #: Type of the bin.
	_ranges:          list[ValueRange]  #: The range of values per dimension.
	_count:           int               #: How often the bin was hit.
	_atLeast:         int               #: How often the bin must be hit to be covered.
	_percentCoverage: float             #: The count in percent of the *at least* count, as the file states it.

	def __init__(
		self,
		name: str,
		binType: BinType,
		ranges: Iterable[ValueRange],
		count: int,
		atLeast: int,
		percentCoverage: float,
		*,
		parent: Nullable[CoverageModel] = None
	) -> None:
		"""
		Initializes a bin, and adds it to its coverage model.

		:param name:             Name of the bin; empty, if unnamed.
		:param binType:          Type of the bin.
		:param ranges:           The range of values per dimension.
		:param count:            How often the bin was hit.
		:param atLeast:          How often the bin must be hit to be covered.
		:param percentCoverage:  The count in percent of the *at least* count, as the file states it.
		:param parent:           Optional, the coverage model containing the bin. Default: ``None``.
		:raises TypeError:       If parameter ``parent`` isn't of type :class:`CoverageModel`.
		:raises TypeError:       If parameter ``name`` isn't of type :class:`str`.
		:raises TypeError:       If parameter ``binType`` isn't of type :class:`BinType`.
		:raises TypeError:       If parameter ``ranges`` isn't iterable.
		:raises TypeError:       If an element of parameter ``ranges`` isn't of type
		                         :class:`~pyEDAA.Reports.FunctionalCoverage.ValueRange`.
		:raises TypeError:       If parameter ``count`` isn't of type :class:`int`.
		:raises TypeError:       If parameter ``atLeast`` isn't of type :class:`int`.
		:raises TypeError:       If parameter ``percentCoverage`` isn't of type :class:`float`.
		:raises CoverageError:   If parameter ``ranges`` has not one range per dimension of the coverage model.
		"""
		super().__init__(parent=parent)

		if not isinstance(name, str):
			ex = TypeError("Parameter 'name' is not of type 'str'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex

		if not isinstance(binType, BinType):
			ex = TypeError("Parameter 'binType' is not of type 'BinType'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(binType)}'.")
			raise ex

		for parameterName, value in (
			("count",   count),
			("atLeast", atLeast)
		):
			if not isinstance(value, int) or isinstance(value, bool):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'int'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex

		if not isinstance(percentCoverage, float):
			ex = TypeError("Parameter 'percentCoverage' is not of type 'float'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(percentCoverage)}'.")
			raise ex

		if not isinstance(ranges, Iterable):
			ex = TypeError("Parameter 'ranges' is not iterable.")
			ex.add_note(f"Got type '{getFullyQualifiedName(ranges)}'.")
			raise ex

		self._name =            name
		self._type =            binType
		self._ranges =          rangeList = []
		self._count =           count
		self._atLeast =         atLeast
		self._percentCoverage = percentCoverage

		for valueRange in ranges:
			if not isinstance(valueRange, ValueRange):
				ex = TypeError("Parameter 'ranges' contains an element not of type 'ValueRange'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(valueRange)}'.")
				raise ex

			rangeList.append(valueRange)

		if parent is not None:
			if len(rangeList) != len(parent._fieldNames):
				ex = CoverageError(f"Bin has not one range per dimension of coverage model '{parent._name}'.")
				ex.add_note(f"Got {len(rangeList)} ranges for {len(parent._fieldNames)} dimensions.")
				raise ex from ValueError("Parameter 'ranges' doesn't match the dimensions.")

			parent._bins.append(self)

	@classmethod
	def Parse(cls, coverageBin: Mapping[str, Any], *, parent: Nullable[CoverageModel] = None) -> Self:
		"""
		Parse a bin from an item of a coverage model's ``Bins``.

		:param coverageBin:    The bin's mapping.
		:param parent:         Optional, the coverage model containing the bin. Default: ``None``.
		:returns:              The bin.
		:raises KeyError:      If a key is missing.
		:raises ValueError:    If the bin's type isn't one OSVVM writes, or a range's maximum is less than its minimum.
		:raises CoverageError: If the bin has not one range per dimension of the coverage model.
		"""
		return cls(
			coverageBin["Name"],
			BinType.Parse(coverageBin["Type"]),
			[ValueRange(valueRange["Min"], valueRange["Max"]) for valueRange in coverageBin["Range"]],
			coverageBin["Count"],
			coverageBin["AtLeast"],
			float(coverageBin["PercentCov"]),
			parent=parent
		)

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the name of the bin (:attr:`_name`).

		:returns: The name; empty, if the bin is unnamed.
		"""
		return self._name

	@readonly
	def Type(self) -> BinType:
		"""
		Read-only property to access the type of the bin (:attr:`_type`).

		:returns: The bin's type.
		"""
		return self._type

	@readonly
	def Ranges(self) -> list[ValueRange]:
		"""
		Read-only property to access the range of values per dimension (:attr:`_ranges`).

		:returns: The ranges, one per dimension.
		"""
		return self._ranges

	@readonly
	def Count(self) -> int:
		"""
		Read-only property to access how often the bin was hit (:attr:`_count`).

		:returns: The number of hits.
		"""
		return self._count

	@readonly
	def AtLeast(self) -> int:
		"""
		Read-only property to access how often the bin must be hit to be covered (:attr:`_atLeast`).

		:returns: The number of hits required.
		"""
		return self._atLeast

	@readonly
	def PercentCoverage(self) -> float:
		"""
		Read-only property to access the count in percent of the *at least* count (:attr:`_percentCoverage`).

		:returns: The percentage, as the file states it; above 100, if the bin was hit more often than required.
		"""
		return self._percentCoverage


@export
class CoverageModel(Element["Report"]):
	"""
	A coverage model: its name, the testcases, which sampled it, its coverage, its settings, the names of its fields -
	one per dimension -, and its bins.

	Its parent is the :class:`Report`.
	"""

	_PARENT_TYPE: ClassVar[tuple[type, ...]]  #: A coverage model is in a report; assigned below that class.

	_name:       str             #: Name of the coverage model.
	_testcases:  list[str]       #: The names of the testcases, which sampled the model.
	_coverage:   float           #: The model's coverage in percent, as the file states it.
	_settings:   _ModelSettings  #: The model's settings.
	_fieldNames: list[str]       #: The names of the model's fields, one per dimension.
	_bins:       list[Bin]       #: The bins.

	def __init__(
		self,
		name: str,
		testcases: Iterable[str],
		coverage: float,
		settings: ModelSettings,
		fieldNames: Iterable[str],
		*,
		parent: Nullable[Report] = None
	) -> None:
		"""
		Initializes a coverage model, and adds it to its report.

		Its bins are added by creating them with this model as their parent.

		:param name:        Name of the coverage model.
		:param testcases:   The names of the testcases, which sampled the model.
		:param coverage:    The model's coverage in percent, as the file states it.
		:param settings:    The model's settings.
		:param fieldNames:  The names of the model's fields, one per dimension.
		:param parent:      Optional, the report containing the model. Default: ``None``.
		:raises TypeError:  If parameter ``parent`` isn't of type :class:`Report`.
		:raises TypeError:  If parameter ``name`` isn't of type :class:`str`.
		:raises TypeError:  If parameter ``testcases`` or ``fieldNames`` isn't iterable, or contains an element not of
		                    type :class:`str`.
		:raises TypeError:  If parameter ``coverage`` isn't of type :class:`float`.
		:raises TypeError:  If parameter ``settings`` isn't of type :class:`ModelSettings`.
		:raises ValueError: If parameter ``fieldNames`` is empty.
		"""
		super().__init__(parent=parent)

		if not isinstance(name, str):
			ex = TypeError("Parameter 'name' is not of type 'str'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex

		if not isinstance(coverage, float):
			ex = TypeError("Parameter 'coverage' is not of type 'float'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(coverage)}'.")
			raise ex

		if not isinstance(settings, ModelSettings):
			ex = TypeError("Parameter 'settings' is not of type 'ModelSettings'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(settings)}'.")
			raise ex

		self._name =       name
		self._testcases =  testcaseList = []
		self._coverage =   coverage
		self._settings =   settings
		self._fieldNames = fieldNameList = []
		self._bins =       []

		for parameterName, values, valueList in (
			("testcases",  testcases,  testcaseList),
			("fieldNames", fieldNames, fieldNameList)
		):
			if not isinstance(values, Iterable):
				ex = TypeError(f"Parameter '{parameterName}' is not iterable.")
				ex.add_note(f"Got type '{getFullyQualifiedName(values)}'.")
				raise ex

			for value in values:
				if not isinstance(value, str):
					ex = TypeError(f"Parameter '{parameterName}' contains an element not of type 'str'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
					raise ex

				valueList.append(value)

		if len(fieldNameList) == 0:
			raise ValueError("Parameter 'fieldNames' is empty.")

		if parent is not None:
			parent._models.append(self)

	@classmethod
	def Parse(cls, model: Mapping[str, Any], *, parent: Nullable[Report] = None) -> Self:
		"""
		Parse a coverage model and its bins from an item of ``Models``.

		:param model:          The coverage model's mapping.
		:param parent:         Optional, the report containing the model. Default: ``None``.
		:returns:              The coverage model.
		:raises KeyError:      If a key is missing.
		:raises CoverageError: If ``BinInfo.Dimensions`` isn't the number of field names, or ``BinInfo.NumBins`` isn't
		                       the number of bins.
		"""
		binInfo = model["BinInfo"]
		coverageModel = cls(
			model["Name"],
			model["TestCases"],
			float(model["Coverage"]),
			ModelSettings.Parse(model["Settings"]),
			binInfo["FieldNames"],
			parent=parent
		)

		if binInfo["Dimensions"] != len(coverageModel._fieldNames):
			ex = CoverageError(f"Coverage model '{coverageModel._name}' states another number of dimensions than fields.")
			ex.add_note(f"Got {binInfo['Dimensions']} dimensions for {len(coverageModel._fieldNames)} field names.")
			raise ex

		for coverageBin in model["Bins"]:
			Bin.Parse(coverageBin, parent=coverageModel)

		if binInfo["NumBins"] != len(coverageModel._bins):
			ex = CoverageError(f"Coverage model '{coverageModel._name}' states another number of bins than it has.")
			ex.add_note(f"Got {binInfo['NumBins']} stated for {len(coverageModel._bins)} bins.")
			raise ex

		return coverageModel

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the name of the coverage model (:attr:`_name`).

		:returns: The name.
		"""
		return self._name

	@readonly
	def Testcases(self) -> list[str]:
		"""
		Read-only property to access the names of the testcases, which sampled the model (:attr:`_testcases`).

		:returns: The names of the testcases.
		"""
		return self._testcases

	@readonly
	def Coverage(self) -> float:
		"""
		Read-only property to access the model's coverage, as the file states it (:attr:`_coverage`).

		:returns: The coverage, in percent, relative to the goal.
		"""
		return self._coverage

	@readonly
	def Settings(self) -> ModelSettings:
		"""
		Read-only property to access the model's settings (:attr:`_settings`).

		:returns: The settings.
		"""
		return self._settings

	@readonly
	def FieldNames(self) -> list[str]:
		"""
		Read-only property to access the names of the model's fields (:attr:`_fieldNames`).

		OSVVM names an unnamed field ``Bin<n>``, counting from 1.

		:returns: The names, one per dimension.
		"""
		return self._fieldNames

	@readonly
	def Dimensions(self) -> int:
		"""
		Read-only property to return the number of the model's dimensions.

		:returns: The number of field names.
		"""
		return len(self._fieldNames)

	@readonly
	def Bins(self) -> list[Bin]:
		"""
		Read-only property to access the bins (:attr:`_bins`).

		:returns: The bins, in the order the file lists them.
		"""
		return self._bins


Bin._PARENT_TYPE = (CoverageModel, )


@export
class Report(metaclass=ExtendedType, mixin=True):
	"""
	The root of OSVVM's functional coverage YAML file: its format version, the testcase's coverage, its setting, and
	the coverage models.

	It is the root of every element below it.
	"""

	_root:          Report                   #: The report's root: the report itself.
	_version:       Nullable[FormatVersion]  #: Version of the file format; ``None`` before the file was read.
	_coverage:      Nullable[float]          #: The testcase's coverage in percent, as the file states it.
	_writePassFail: bool                     #: Whether OSVVM's HTML report states pass or fail per bin.
	_models:        list[CoverageModel]      #: The coverage models.

	def __init__(
		self,
		version: Nullable[FormatVersion] = None,
		coverage: Nullable[float] = None,
		writePassFail: bool = False
	) -> None:
		"""
		Initializes a report; empty, without parameters.

		Its coverage models are added by creating them with this report as their parent.

		:param version:       Optional, version of the file format. Default: ``None``.
		:param coverage:      Optional, the testcase's coverage in percent, as the file states it. Default: ``None``.
		:param writePassFail: Optional, whether OSVVM's HTML report states pass or fail per bin. Default: ``False``.
		:raises TypeError:    If parameter ``version`` isn't of type :class:`FormatVersion`.
		:raises TypeError:    If parameter ``coverage`` isn't of type :class:`float`.
		:raises TypeError:    If parameter ``writePassFail`` isn't of type :class:`bool`.
		"""
		if version is not None and not isinstance(version, FormatVersion):
			ex = TypeError("Parameter 'version' is not of type 'FormatVersion'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(version)}'.")
			raise ex

		if coverage is not None and not isinstance(coverage, float):
			ex = TypeError("Parameter 'coverage' is not of type 'float'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(coverage)}'.")
			raise ex

		if not isinstance(writePassFail, bool):
			ex = TypeError("Parameter 'writePassFail' is not of type 'bool'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(writePassFail)}'.")
			raise ex

		self._root =          self
		self._version =       version
		self._coverage =      coverage
		self._writePassFail = writePassFail
		self._models =        []

	@readonly
	def Version(self) -> Nullable[FormatVersion]:
		"""
		Read-only property to access the version of the file format (:attr:`_version`).

		:returns: The format version, or ``None`` before the file was read.
		"""
		return self._version

	@readonly
	def Coverage(self) -> Nullable[float]:
		"""
		Read-only property to access the testcase's coverage, as the file states it (:attr:`_coverage`).

		:returns: The coverage in percent, or ``None`` before the file was read.
		"""
		return self._coverage

	@readonly
	def WritePassFail(self) -> bool:
		"""
		Read-only property to access whether OSVVM's HTML report states pass or fail per bin (:attr:`_writePassFail`).

		:returns: ``True``, if OSVVM's settings ``WritePassFail`` or ``ErrorIfNotCovered`` were set.
		"""
		return self._writePassFail

	@readonly
	def Models(self) -> list[CoverageModel]:
		"""
		Read-only property to access the coverage models (:attr:`_models`).

		OSVVM lists the models of weight ``0`` last. The names needn't be unique: several instances of a model may share
		a name.

		:returns: The coverage models, in the order the file lists them.
		"""
		return self._models


CoverageModel._PARENT_TYPE = (Report, )


@export
class Document(fc_Document, Report):
	"""
	OSVVM's functional coverage YAML file: read into the format's model, and converted to the functional coverage model
	of pyEDAA.Reports.
	"""

	_yamlDocument: Nullable[Mapping[str, Any]]  #: The parsed YAML document, after :meth:`Analyze`.

	def __init__(self, yamlReportFile: Path, analyzeAndConvert: bool = False) -> None:
		"""
		Initializes the document, and optionally reads it.

		:param yamlReportFile:    Path to the YAML file.
		:param analyzeAndConvert: Optional, if true, analyze the file and convert its content. Default: ``False``.
		:raises ValueError:       If parameter ``yamlReportFile`` is ``None``.
		:raises TypeError:        If parameter ``yamlReportFile`` isn't of type :class:`~pathlib.Path`.
		:raises CoverageError:    If ``analyzeAndConvert`` is true, and the file can't be read or converted.
		"""
		super().__init__(yamlReportFile)
		Report.__init__(self)

		self._yamlDocument = None

		if analyzeAndConvert:
			self.Analyze()
			self.Convert()

	def Analyze(self) -> None:
		"""
		Read and parse the YAML file, read its format version and validate it against the version's JSON Schema in
		:data:`SCHEMAS`.

		:raises CoverageError: If the file doesn't exist.
		:raises CoverageError: If the file isn't valid YAML.
		:raises CoverageError: If the file states no or an unsupported format version. |br|
		                       The note lists the supported format versions.
		:raises CoverageError: If the JSON Schema can't be read.
		:raises CoverageError: If the file isn't valid according to the JSON Schema. |br|
		                       A note per error names its path in the file.
		"""
		if not self._path.exists():
			raise CoverageError(f"OSVVM coverage file '{self._path}' does not exist.") \
				from FileNotFoundError(f"File '{self._path}' not found.")

		from jsonschema import Draft202012Validator

		with Stopwatch() as sw:
			try:
				yamlDocument = YAML(typ="safe", pure=True).load(self._path)
			except YAMLError as ex:
				raise CoverageError(f"YAML syntax error in OSVVM coverage file '{self._path}'.") from ex

			version = yamlDocument.get("Version", None) if isinstance(yamlDocument, Mapping) else None
			if version not in [member.value for member in FormatVersion]:
				ex = CoverageError(f"OSVVM coverage file '{self._path}' states an unsupported format version.")
				ex.add_note(f"Got version '{version}'." if version is not None else "Got no version.")
				ex.add_note(f"Supported format versions: {', '.join(member.value for member in FormatVersion)}.")
				raise ex

			schemaFile = SCHEMAS[FormatVersion(version)]
			try:
				schema = loads(getResourceFile(Resources, schemaFile).read_text(encoding="utf-8"))
			except (ToolingException, OSError, JSONDecodeError) as ex:
				raise CoverageError(f"Couldn't read JSON Schema '{schemaFile}' from package resources.") from ex

			errors = sorted(Draft202012Validator(schema).iter_errors(yamlDocument), key=lambda error: list(error.path))
			if len(errors) > 0:
				ex = CoverageError(f"Validation error for '{self._path}' using JSON Schema '{schemaFile}'.")
				for error in errors:
					ex.add_note(f"/{'/'.join(str(part) for part in error.path)}: {error.message}")
				raise ex

			self._yamlDocument = yamlDocument

		self._analysisDuration = sw.Duration

	def Convert(self) -> None:
		"""
		Convert the parsed YAML document to the format's model.

		:raises CoverageError: If the YAML file was not analyzed before. |br|
		                       Call 'Document.Analyze()' or create the document using
		                       'Document(path, analyzeAndConvert=True)'.
		:raises CoverageError: If a range's maximum is less than its minimum.
		:raises CoverageError: If a coverage model or a bin is inconsistent.
		"""
		if self._yamlDocument is None:
			ex = CoverageError(f"OSVVM coverage file '{self._path}' needs to be read and analyzed by a YAML parser.")
			ex.add_note("Call 'Document.Analyze()' or create the document using 'Document(path, analyzeAndConvert=True)'.")
			raise ex

		with Stopwatch() as sw:
			try:
				self._version =       FormatVersion.Parse(self._yamlDocument["Version"])
				self._coverage =      float(self._yamlDocument["Coverage"])
				self._writePassFail = {0: False, 1: True}[self._yamlDocument["Settings"]["WritePassFail"]]
				self._models =        []

				for model in self._yamlDocument["Models"]:
					CoverageModel.Parse(model, parent=self)
			except ValueError as ex:
				raise CoverageError(f"OSVVM coverage file '{self._path}' has an invalid value.") from ex

		self._conversionDuration = sw.Duration

	def ConvertToFunctionalCoverageReport(self) -> FunctionalCoverageReport:
		"""
		Convert the format's model to the functional coverage model, and aggregate it.

		The report is named after the testcase: the file's name without ``_cov``. A coverage model becomes a covergroup of
		its weight and goal, its settings key-value pairs of it, named as OSVVM names them. The covergroup has one
		coverage item, named as the model: a coverpoint of the model's field name for a model of one dimension, a cross of
		the field names for a model of more dimensions. The model's coverage and total counts aren't copied:
		:meth:`~pyEDAA.Reports.FunctionalCoverage.FunctionalCoverageReport.Aggregate` computes them.

		:returns: The report's root of the functional coverage model.
		"""
		binKinds = {
			BinType.Count:   BinKind.Count,
			BinType.Ignore:  BinKind.Ignore,
			BinType.Illegal: BinKind.Illegal
		}

		report = FunctionalCoverageReport(
			self._path.stem.removesuffix("_cov"),
			keyValuePairs={"WritePassFail": self._writePassFail}
		)
		for model in self._models:
			settings = model._settings
			covergroup = Covergroup(
				model._name,
				settings._coverageWeight,
				settings._goal,
				model._testcases,
				keyValuePairs={
					"WeightMode":      settings._weightMode,
					"Seeds":           settings._seeds,
					"CountMode":       settings._countMode,
					"IllegalMode":     settings._illegalMode,
					"Threshold":       settings._threshold,
					"ThresholdEnable": settings._thresholdEnable,
					"IsRequirement":   settings._isRequirement
				},
				parent=report
			)

			if len(model._fieldNames) == 1:
				coverpoint = Coverpoint(model._name, model._fieldNames[0], parent=covergroup)
				for coverageBin in model._bins:
					CoverpointBin(
						None if coverageBin._name == "" else coverageBin._name,
						binKinds[coverageBin._type],
						coverageBin._ranges,
						coverageBin._count,
						coverageBin._atLeast,
						parent=coverpoint
					)
			else:
				cross = Cross(model._name, model._fieldNames, parent=covergroup)
				for coverageBin in model._bins:
					CrossBin(
						None if coverageBin._name == "" else coverageBin._name,
						binKinds[coverageBin._type],
						[(valueRange, ) for valueRange in coverageBin._ranges],
						coverageBin._count,
						coverageBin._atLeast,
						parent=cross
					)

		report.Aggregate()
		return report
