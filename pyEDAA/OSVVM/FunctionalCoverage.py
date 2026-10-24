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
A data model of OSVVM's functional coverage YAML file (:file:`<testcase>_cov.yml`): its enumerations, the settings of a
coverage model, and the bins.

OSVVM's ``CoveragePkg`` writes the file (``WriteCovYaml``), OSVVM's script ``ReportCov2Html.tcl`` reads it.

* A coverage model states its :class:`ModelSettings`: its weight and goal, its :class:`WeightMode`, :class:`CountMode`
  and :class:`IllegalMode`, the seeds of its randomization, its threshold, and its total counts.
* A :class:`Bin` has a name - empty, if unnamed -, a :class:`BinType`, one range of values per dimension, a count,
  its *at least* count and its percentage of coverage.
"""
from __future__                        import annotations

from typing                            import Any, ClassVar, Generic, Iterable, Mapping, Optional as Nullable, Self, \
                                              TypeVar

from pyTooling.Common                  import getFullyQualifiedName, StringEnum
from pyTooling.Decorators              import export, readonly
from pyTooling.MetaClasses             import ExtendedType

from pyEDAA.Reports.FunctionalCoverage import ValueRange

from pyEDAA.OSVVM                      import OSVVMException


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


# A class with a property named like a class - ``WeightMode``, ``CountMode``, ``IllegalMode`` - can't name that class in
# the annotation of a field: the class body's namespace, where annotations are evaluated, binds the name to the
# property.
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
		:raises TypeError:      If parameter ``coverageWeight``, ``totalCount`` or ``totalGoal`` isn't of type
		                        :class:`int`.
		:raises TypeError:      If parameter ``goal`` or ``threshold`` isn't of type :class:`float`.
		:raises TypeError:      If parameter ``weightMode`` isn't of type :class:`WeightMode`.
		:raises TypeError:      If parameter ``seeds`` isn't a tuple of two :class:`int`.
		:raises TypeError:      If parameter ``countMode`` isn't of type :class:`CountMode`.
		:raises TypeError:      If parameter ``illegalMode`` isn't of type :class:`IllegalMode`.
		:raises TypeError:      If parameter ``thresholdEnable`` or ``isRequirement`` isn't of type :class:`bool`.
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
		:raises TypeError:       If parameter ``ranges`` isn't iterable, or contains an element not of type
		                         :class:`~pyEDAA.Reports.FunctionalCoverage.ValueRange`.
		:raises TypeError:       If parameter ``count`` or ``atLeast`` isn't of type :class:`int`.
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
