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
# Copyright 2021-2026 Electronic Design Automation Abstraction (EDA²)                                                  #
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
"""A data model for OSVVM's AlertLog YAML file format."""
from __future__            import annotations

from datetime              import timedelta
from pathlib               import Path
from typing                import Any, Callable, Generator, Iterable, Iterator, Optional as Nullable, Self

from ruamel.yaml           import YAML, CommentedMap, CommentedSeq

from pyTooling.Common      import getFullyQualifiedName, StringEnum
from pyTooling.Decorators  import export, readonly
from pyTooling.Exceptions  import AlreadyInHierarchyError, DuplicateElementError
from pyTooling.MetaClasses import ExtendedType
from pyTooling.Stopwatch   import Stopwatch
from pyTooling.Tree        import Node
from pyTooling.Warning     import WarningCollector

from pyEDAA.OSVVM          import OSVVMException, UnknownKeyWarning


@export
class AlertLogError(OSVVMException):
	"""
	The exception is raised by the AlertLog data model.

	E.g., an AlertLog YAML file can't be read or converted, or an item is added twice.
	"""


@export
class DuplicateAlertLogItemError(AlertLogError, DuplicateElementError):
	"""
	The exception is raised when an AlertLog item is added to an item, which has a child of the same name already.
	"""

	_item: Nullable[AlertLogItem]  #: The child of the same name, which is in the item already.

	def __init__(self, message: str, /, *, item: Nullable[AlertLogItem] = None) -> None:
		"""
		Initializes the exception with the child of the same name, which is in the item already.

		:param message: The exception's message.
		:param item:    Optional, the child of the same name, which is in the item already. Default: ``None``.
		"""
		super().__init__(message)
		self._item = item

	@readonly
	def Item(self) -> Nullable[AlertLogItem]:
		"""
		Read-only property to access the child of the same name, which is in the item already (:attr:`_item`).

		:returns: The child, or ``None`` if it wasn't recorded.
		"""
		return self._item


@export
class AlreadyInAlertLogError(AlertLogError, AlreadyInHierarchyError):
	"""
	The exception is raised when an AlertLog item is given as a child, but it has a parent already.
	"""

	_item: Nullable[AlertLogItem]  #: The item, which has a parent already.

	def __init__(self, message: str, /, *, item: Nullable[AlertLogItem] = None) -> None:
		"""
		Initializes the exception with the item, which has a parent already.

		:param message: The exception's message.
		:param item:    Optional, the item, which has a parent already. Default: ``None``.
		"""
		super().__init__(message)
		self._item = item

	@readonly
	def Item(self) -> Nullable[AlertLogItem]:
		"""
		Read-only property to access the item, which has a parent already (:attr:`_item`).

		:returns: The item, or ``None`` if it wasn't recorded.
		"""
		return self._item


@export
class FormatVersion(StringEnum):
	"""
	Version of OSVVM's AlertLog YAML format, as a file's ``Version`` states it.

	OSVVM writes ``ALERT_YAML_VERSION`` of ``OsvvmScriptSettingsPkg``, so far only ``0.1``. The format grew within this
	version: the root's ``Results`` state ``ExpectedCount`` since OSVVM 2025.06 and ``ExternalErrors`` since OSVVM
	2026.08, so both are optional.
	"""

	Version0_1 = "0.1"  #: Format version 0.1.


@export
class AlertLogStatus(StringEnum):
	"""
	Status of an :class:`AlertLogItem`, as OSVVM's ``GetTestResultStatus`` writes it.

	An item below the root is either passed or failed. The root, which is the test, may also have stopped, timed out, or
	have no or manual checks. The values are OSVVM's defaults of ``OsvvmSettingsPkg`` (``ALERT_LOG_PASS_NAME``, ...);
	:meth:`Parse` ignores their case.
	"""

	Unknown =      "UNKNOWN"       #: Status of an item, which wasn't read from a file. OSVVM doesn't write it.
	Passed =       "PASSED"        #: The item has no errors.
	Failed =       "FAILED"        #: The item has errors.
	StopLimit =    "STOPLIMIT"     #: The test stopped, because an alert count reached its stop limit (root only).
	TimeOut =      "TIMEOUT"       #: The test timed out (root only).
	ManualChecks = "MANUALCHECKS"  #: The test has no errors, but needs manual checks (root only).
	NoChecks =     "NOCHECKS"      #: The test has no errors, but did no affirmations (root only).

	@classmethod
	def Parse(cls, value: Nullable[str]) -> Nullable[Self]:
		"""
		Convert a status, as written in an AlertLog file, to the member carrying that value, ignoring the case.

		:param value:          The status.
		:returns:              The member carrying that value. ``None``, if parameter ``value`` is ``None`` or empty.
		:raises TypeError:     If parameter ``value`` isn't of type :class:`str`.
		:raises AlertLogError: If no member carries that value. |br|
		                       The note lists the values it accepts.
		"""
		try:
			return super().Parse(value.upper() if isinstance(value, str) else value)
		except ValueError as cause:
			ex = AlertLogError(f"Unknown AlertLog status '{value}'.")
			ex.add_note(f"Allowed values: {', '.join(member.value for member in cls)}.")
			raise ex from cause

	def __bool__(self) -> bool:
		"""
		Convert an AlertLog status to a boolean.

		:returns: ``True``, if the status is :attr:`Passed`.
		"""
		return self is AlertLogStatus.Passed


@export
class AlertCount(metaclass=ExtendedType, slots=True):
	"""
	An alert count: the number of failures, errors and warnings, as OSVVM's ``AlertCountType`` holds it.

	An alert count is a value, like a number: it belongs to no element, and two alert counts are equal, if their counts
	are equal.
	"""

	_failureCount: int  #: Number of failures.
	_errorCount:   int  #: Number of errors.
	_warningCount: int  #: Number of warnings.

	def __init__(self, failureCount: int = 0, errorCount: int = 0, warningCount: int = 0) -> None:
		"""
		Initializes an alert count.

		A count may be negative: the settings' external errors subtract the alerts a test expects.

		:param failureCount: Optional, number of failures. Default: ``0``.
		:param errorCount:   Optional, number of errors. Default: ``0``.
		:param warningCount: Optional, number of warnings. Default: ``0``.
		:raises ValueError:  If parameter ``failureCount`` is ``None``.
		:raises ValueError:  If parameter ``errorCount`` is ``None``.
		:raises ValueError:  If parameter ``warningCount`` is ``None``.
		:raises TypeError:   If parameter ``failureCount`` isn't of type :class:`int`.
		:raises TypeError:   If parameter ``errorCount`` isn't of type :class:`int`.
		:raises TypeError:   If parameter ``warningCount`` isn't of type :class:`int`.
		"""
		for parameterName, count in (
			("failureCount", failureCount),
			("errorCount",   errorCount),
			("warningCount", warningCount)
		):
			if count is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(count, int):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'int'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(count)}'.")
				raise ex

		self._failureCount = failureCount
		self._errorCount =   errorCount
		self._warningCount = warningCount

	@classmethod
	def Parse(cls, node: CommentedMap) -> Self:
		"""
		Parse an alert count.

		OSVVM writes an alert count as a flow mapping, e.g. ``AlertCount: {Failure: 0, Error: 2, Warning: 1}``. A key
		the format doesn't define is reported as :exc:`~pyEDAA.OSVVM.UnknownKeyWarning`.

		:param node:                           The YAML mapping.
		:returns:                              The alert count.
		:raises AlertLogError:                 If the mapping has no key ``Failure``, ``Error`` or ``Warning``.
		:raises AlertLogError:                 If the value of key ``Failure``, ``Error`` or ``Warning`` isn't an integer.
		:raises UnhandledCriticalWarningError: If the mapping has an unknown key, and no warning collector collects the
		                                       warning.
		"""
		line = node.lc.line + 1
		for key in node:
			if key not in ("Failure", "Error", "Warning"):
				keyLine = node.lc.key(key)[0] + 1
				WarningCollector.Raise(
					UnknownKeyWarning(f"Unknown key '{key}' in alert count at line {keyLine}.", key=key, line=keyLine)
				)

		for key in ("Failure", "Error", "Warning"):
			if key not in node:
				raise AlertLogError(f"Alert count at line {line} has no key '{key}'.")
			elif not isinstance(node[key], int):
				ex = AlertLogError(f"Key '{key}' of alert count at line {line} is not an integer.")
				ex.add_note(f"Got type '{getFullyQualifiedName(node[key])}'.")
				raise ex

		return cls(node["Failure"], node["Error"], node["Warning"])

	@readonly
	def FailureCount(self) -> int:
		"""
		Read-only property to access the number of failures (:attr:`_failureCount`).

		:returns: Number of failures.
		"""
		return self._failureCount

	@readonly
	def ErrorCount(self) -> int:
		"""
		Read-only property to access the number of errors (:attr:`_errorCount`).

		:returns: Number of errors.
		"""
		return self._errorCount

	@readonly
	def WarningCount(self) -> int:
		"""
		Read-only property to access the number of warnings (:attr:`_warningCount`).

		:returns: Number of warnings.
		"""
		return self._warningCount

	def __eq__(self, other: Any) -> bool:
		"""
		Compare two alert counts.

		:param other: The other alert count.
		:returns:     ``True``, if the numbers of failures, errors and warnings are equal.
		"""
		if not isinstance(other, AlertCount):
			return NotImplemented

		return (
			self._failureCount == other._failureCount and
			self._errorCount == other._errorCount and
			self._warningCount == other._warningCount
		)

	def __hash__(self) -> int:
		"""
		Return a hash of the alert count, consistent with :meth:`__eq__`.

		:returns: The hash of the numbers of failures, errors and warnings.
		"""
		return hash((self._failureCount, self._errorCount, self._warningCount))

	def __repr__(self) -> str:
		"""
		Return a representation of the alert count.

		:returns: The numbers of failures, errors and warnings.
		"""
		return (
			f"AlertCount(failureCount={self._failureCount}, errorCount={self._errorCount}, "
			f"warningCount={self._warningCount})"
		)


# A class with a property named like a class - ``AlertCount``, ``Settings`` - can't name that class in the annotation
# of a field: the class body's namespace, where annotations are evaluated, binds the name to the property.
_AlertCount = AlertCount


@export
def _format(node: Node) -> str:
	"""
	User-defined :external+pyTool:ref:`pyTooling Tree <STRUCT/Tree>` formatting function for nodes referencing
	:class:`AlertLogItems <AlertLogItem>`.

	:param node: Node to format.
	:returns:    String representation (one-liner) describing an AlertLogItem.
	"""
	return (
		f"{node['Name']}: {node['TotalErrorCount']}="
		f"{node['FailureCount']}/{node['ErrorCount']}/{node['WarningCount']} {node['PassedCount']}/{node['AffirmCount']}"
	)


@export
class AlertLogItem(metaclass=ExtendedType, slots=True):
	"""
	An *AlertLogItem* represents an item of OSVVM's AlertLog hierarchy: an AlertLog ID with its alert counts.

	An item has a reference to its parent item in the AlertLog hierarchy. If the item is the top-most element (root
	element), the parent reference is ``None``. An item can contain further child items, which are unique by name.
	"""

	_parent:                  Nullable[AlertLogItem]   #: Reference to the parent item.
	_name:                    str                      #: Name of the AlertLog item.
	_children:                dict[str, AlertLogItem]  #: Child items, by name.

	_status:                  AlertLogStatus           #: AlertLog item's status.
	_totalErrorCount:         int                      #: Total number of errors, as OSVVM computed it.
	_alertCount:              _AlertCount              #: Number of failures, errors and warnings.
	_passedCount:             int                      #: Number of passed affirmations.
	_affirmCount:             int                      #: Number of affirmations (incl. failed affirmations).
	_passedRequirementsCount: int                      #: Number of passed requirements.
	_requirementsGoalCount:   int                      #: Number of requirements to pass.
	_disabledAlertCount:      _AlertCount              #: Number of disabled failures, errors and warnings.

	def __init__(
		self,
		name:                    str,
		status:                  AlertLogStatus = AlertLogStatus.Unknown,
		totalErrorCount:         int = 0,
		alertCount:              Nullable[AlertCount] = None,
		passedCount:             int = 0,
		affirmCount:             int = 0,
		passedRequirementsCount: int = 0,
		requirementsGoalCount:   int = 0,
		disabledAlertCount:      Nullable[AlertCount] = None,
		children:                Nullable[Iterable[AlertLogItem]] = None,
		*,
		parent:                  Nullable[AlertLogItem] = None
	) -> None:
		"""
		Initializes an AlertLog item, and adds it to the children of its parent.

		:param name:                        Name of the AlertLog item.
		:param status:                      Optional, the item's status. Default: :attr:`AlertLogStatus.Unknown`.
		:param totalErrorCount:             Optional, total number of errors. Default: ``0``.
		:param alertCount:                  Optional, number of failures, errors and warnings. Default: ``None``, no
		                                    alerts.
		:param passedCount:                 Optional, number of passed affirmations. Default: ``0``.
		:param affirmCount:                 Optional, number of affirmations. Default: ``0``.
		:param passedRequirementsCount:     Optional, number of passed requirements. Default: ``0``.
		:param requirementsGoalCount:       Optional, number of requirements to pass. Default: ``0``.
		:param disabledAlertCount:          Optional, number of disabled failures, errors and warnings. Default: ``None``,
		                                    no disabled alerts.
		:param children:                    Optional, child items. Default: ``None``.
		:param parent:                      Optional, the parent item; the item is added to its children. Default:
		                                    ``None``.
		:raises ValueError:                 If parameter ``name`` is ``None``.
		:raises TypeError:                  If parameter ``name`` isn't of type :class:`str`.
		:raises ValueError:                 If parameter ``status`` is ``None``.
		:raises TypeError:                  If parameter ``status`` isn't of type :class:`AlertLogStatus`.
		:raises ValueError:                 If parameter ``totalErrorCount`` is ``None``.
		:raises ValueError:                 If parameter ``passedCount`` is ``None``.
		:raises ValueError:                 If parameter ``affirmCount`` is ``None``.
		:raises ValueError:                 If parameter ``passedRequirementsCount`` is ``None``.
		:raises ValueError:                 If parameter ``requirementsGoalCount`` is ``None``.
		:raises TypeError:                  If parameter ``totalErrorCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``passedCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``affirmCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``passedRequirementsCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``requirementsGoalCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``alertCount`` isn't of type :class:`AlertCount`.
		:raises TypeError:                  If parameter ``disabledAlertCount`` isn't of type :class:`AlertCount`.
		:raises TypeError:                  If parameter ``children`` isn't iterable.
		:raises TypeError:                  If parameter ``children`` contains an element not of type
		                                    :class:`AlertLogItem`.
		:raises DuplicateAlertLogItemError: If parameter ``children`` contains two items of the same name.
		:raises AlreadyInAlertLogError:     If parameter ``children`` contains an item, which has a parent already.
		:raises TypeError:                  If parameter ``parent`` isn't of type :class:`AlertLogItem`.
		:raises DuplicateAlertLogItemError: If parameter ``parent`` has a child of the same name already.
		"""
		if name is None:
			raise ValueError("Parameter 'name' is None.")
		elif not isinstance(name, str):
			ex = TypeError("Parameter 'name' is not of type 'str'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex

		if status is None:
			raise ValueError("Parameter 'status' is None.")
		elif not isinstance(status, AlertLogStatus):
			ex = TypeError("Parameter 'status' is not of type 'AlertLogStatus'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(status)}'.")
			raise ex

		for parameterName, count in (
			("totalErrorCount",         totalErrorCount),
			("passedCount",             passedCount),
			("affirmCount",             affirmCount),
			("passedRequirementsCount", passedRequirementsCount),
			("requirementsGoalCount",   requirementsGoalCount)
		):
			if count is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(count, int):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'int'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(count)}'.")
				raise ex

		for parameterName, value in (
			("alertCount",         alertCount),
			("disabledAlertCount", disabledAlertCount)
		):
			if value is not None and not isinstance(value, AlertCount):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'AlertCount'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex

		if parent is not None:
			if not isinstance(parent, AlertLogItem):
				ex = TypeError("Parameter 'parent' is not of type 'AlertLogItem'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
				raise ex
			elif name in parent._children:
				raise DuplicateAlertLogItemError(
					f"AlertLog item '{parent._name}' has a child '{name}' already.", item=parent._children[name]
				)

		self._parent =                  parent
		self._name =                    name
		self._status =                  status
		self._totalErrorCount =         totalErrorCount
		self._alertCount =              AlertCount() if alertCount is None else alertCount
		self._passedCount =             passedCount
		self._affirmCount =             affirmCount
		self._passedRequirementsCount = passedRequirementsCount
		self._requirementsGoalCount =   requirementsGoalCount
		self._disabledAlertCount =      AlertCount() if disabledAlertCount is None else disabledAlertCount

		self._children = childDict = {}

		if children is not None:
			if not isinstance(children, Iterable):
				ex = TypeError("Parameter 'children' is not iterable.")
				ex.add_note(f"Got type '{getFullyQualifiedName(children)}'.")
				raise ex

			for child in children:
				if not isinstance(child, AlertLogItem):
					ex = TypeError("Parameter 'children' contains an element not of type 'AlertLogItem'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(child)}'.")
					raise ex
				elif child._name in childDict:
					raise DuplicateAlertLogItemError(
						f"AlertLog item '{name}' has a child '{child._name}' already.", item=childDict[child._name]
					)
				elif child._parent is not None:
					raise AlreadyInAlertLogError(
						f"AlertLog item '{child._name}' is a child of '{child._parent._name}' already.", item=child
					)

				childDict[child._name] = child
				child._parent = self

		if parent is not None:
			parent._children[name] = self

	@classmethod
	def Parse(cls, node: CommentedMap, *, parent: Nullable[AlertLogItem] = None) -> AlertLogItem:
		"""
		Parse an entry of ``Children``: its name, status and ``Results``, and its children.

		A key the format doesn't define is reported as :exc:`~pyEDAA.OSVVM.UnknownKeyWarning`.

		:param node:                           The YAML mapping of the entry.
		:param parent:                         Optional, the parent item; the item is added to its children. Default:
		                                       ``None``.
		:returns:                              The AlertLog item.
		:raises AlertLogError:                 If the mapping or its ``Results`` lack a key the format requires.
		:raises AlertLogError:                 If a value isn't of the type the format requires.
		:raises AlertLogError:                 If the status is unknown.
		:raises DuplicateAlertLogItemError:    If parameter ``parent`` has a child of the same name already.
		:raises UnhandledCriticalWarningError: If a mapping has an unknown key, and no warning collector collects the
		                                       warning.
		"""
		line = node.lc.line + 1
		for key in node:
			if key not in ("Name", "Status", "Results", "Children"):
				keyLine = node.lc.key(key)[0] + 1
				WarningCollector.Raise(
					UnknownKeyWarning(f"Unknown key '{key}' in AlertLog item at line {keyLine}.", key=key, line=keyLine)
				)

		for key, keyType, typeName in (
			("Name",    str,          "a string"),
			("Status",  str,          "a string"),
			("Results", CommentedMap, "a mapping")
		):
			if key not in node:
				raise AlertLogError(f"AlertLog item at line {line} has no key '{key}'.")
			elif not isinstance(node[key], keyType):
				ex = AlertLogError(f"Key '{key}' of AlertLog item at line {line} is not {typeName}.")
				ex.add_note(f"Got type '{getFullyQualifiedName(node[key])}'.")
				raise ex

		if "Children" not in node:
			raise AlertLogError(f"AlertLog item at line {line} has no key 'Children'.")
		elif node["Children"] is not None and not isinstance(node["Children"], CommentedSeq):
			ex = AlertLogError(f"Key 'Children' of AlertLog item at line {line} is not a sequence.")
			ex.add_note(f"Got type '{getFullyQualifiedName(node['Children'])}'.")
			raise ex

		results = node["Results"]
		for key in results:
			if key not in (
				"TotalErrors", "AlertCount", "PassedCount", "AffirmCount", "RequirementsPassed", "RequirementsGoal",
				"DisabledAlertCount"
			):
				keyLine = results.lc.key(key)[0] + 1
				WarningCollector.Raise(
					UnknownKeyWarning(f"Unknown key '{key}' in results at line {keyLine}.", key=key, line=keyLine)
				)

		for key, keyType, typeName in (
			("TotalErrors",        int,          "an integer"),
			("AlertCount",         CommentedMap, "a mapping"),
			("PassedCount",        int,          "an integer"),
			("AffirmCount",        int,          "an integer"),
			("RequirementsPassed", int,          "an integer"),
			("RequirementsGoal",   int,          "an integer"),
			("DisabledAlertCount", CommentedMap, "a mapping")
		):
			if key not in results:
				raise AlertLogError(f"Results of AlertLog item at line {line} have no key '{key}'.")
			elif not isinstance(results[key], keyType):
				ex = AlertLogError(f"Key '{key}' of results of AlertLog item at line {line} is not {typeName}.")
				ex.add_note(f"Got type '{getFullyQualifiedName(results[key])}'.")
				raise ex

		try:
			status = AlertLogStatus.Parse(node["Status"])
		except AlertLogError as ex:
			ex.add_note(f"Status of AlertLog item at line {line}.")
			raise

		item = AlertLogItem(
			node["Name"],
			status,
			results["TotalErrors"],
			AlertCount.Parse(results["AlertCount"]),
			results["PassedCount"],
			results["AffirmCount"],
			results["RequirementsPassed"],
			results["RequirementsGoal"],
			AlertCount.Parse(results["DisabledAlertCount"]),
			parent=parent
		)

		for child in () if node["Children"] is None else node["Children"]:
			if not isinstance(child, CommentedMap):
				ex = AlertLogError(f"Child of AlertLog item '{item._name}' at line {line} is not a mapping.")
				ex.add_note(f"Got type '{getFullyQualifiedName(child)}'.")
				raise ex

			AlertLogItem.Parse(child, parent=item)

		return item

	@property
	def Parent(self) -> Nullable[AlertLogItem]:
		"""
		Property to access the parent item of this item (:attr:`_parent`).

		Assigning an item moves this item, with its children, from its previous parent to the children of the new parent.
		Assigning ``None`` removes it from its previous parent.

		:returns:                           The item's parent item. ``None``, if it's the top-most item (root).
		:raises TypeError:                  If the assigned value isn't of type :class:`AlertLogItem`.
		:raises DuplicateAlertLogItemError: If the assigned item has a child of the same name already.
		:raises AlertLogError:              If the assigned item is this item or one of its descendants.
		"""
		return self._parent

	@Parent.setter
	def Parent(self, value: Nullable[AlertLogItem]) -> None:
		if value is self._parent:
			return
		elif value is not None:
			if not isinstance(value, AlertLogItem):
				ex = TypeError("Parameter 'value' is not of type 'AlertLogItem'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex
			elif self._name in value._children:
				raise DuplicateAlertLogItemError(
					f"AlertLog item '{value._name}' has a child '{self._name}' already.", item=value._children[self._name]
				)

			ancestor = value
			while ancestor is not None:
				if ancestor is self:
					raise AlertLogError(f"AlertLog item '{self._name}' can't be a child of itself or of its descendants.")

				ancestor = ancestor._parent

		if self._parent is not None:
			del self._parent._children[self._name]

		self._parent = value
		if value is not None:
			value._children[self._name] = self

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the AlertLog item's name (:attr:`_name`).

		:returns: AlertLog item's name.
		"""
		return self._name

	@readonly
	def Status(self) -> AlertLogStatus:
		"""
		Read-only property to access the AlertLog item's status (:attr:`_status`).

		:returns: AlertLog item's status.
		"""
		return self._status

	@readonly
	def TotalErrorCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's total number of errors (:attr:`_totalErrorCount`).

		OSVVM computes it from the item's alerts and those of its children, its failed requirements and, for the root, the
		expected alerts and the settings.

		:returns: AlertLog item's total number of errors.
		"""
		return self._totalErrorCount

	@readonly
	def AlertCount(self) -> AlertCount:
		"""
		Read-only property to access the AlertLog item's number of failures, errors and warnings (:attr:`_alertCount`).

		:returns: AlertLog item's alert count.
		"""
		return self._alertCount

	@readonly
	def PassedCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of passed affirmations (:attr:`_passedCount`).

		:returns: AlertLog item's number of passed affirmations.
		"""
		return self._passedCount

	@readonly
	def AffirmCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of affirmations (:attr:`_affirmCount`).

		:returns: AlertLog item's number of affirmations, passed and failed.
		"""
		return self._affirmCount

	@readonly
	def PassedRequirementsCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of passed requirements (:attr:`_passedRequirementsCount`).

		:returns: AlertLog item's number of passed requirements.
		"""
		return self._passedRequirementsCount

	@readonly
	def RequirementsGoalCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of requirements to pass (:attr:`_requirementsGoalCount`).

		:returns: AlertLog item's number of requirements to pass.
		"""
		return self._requirementsGoalCount

	@readonly
	def DisabledAlertCount(self) -> AlertCount:
		"""
		Read-only property to access the AlertLog item's number of disabled failures, errors and warnings
		(:attr:`_disabledAlertCount`).

		:returns: AlertLog item's alert count of disabled alerts.
		"""
		return self._disabledAlertCount

	@readonly
	def Children(self) -> dict[str, AlertLogItem]:
		"""
		Read-only property to access the child items (:attr:`_children`).

		:returns: The child items, by name, in the order of the AlertLog file.
		"""
		return self._children

	def IterateItems(
		self,
		predicate: Nullable[Callable[[AlertLogItem], bool]] = None
	) -> Generator[AlertLogItem, None, None]:
		"""
		Iterate all items below this item: each child, followed by the items below it, in the order of the AlertLog file.

		:param predicate: Optional, a filter function; only items it returns ``True`` for are yielded. Default:
		                  ``None``, all items.
		:returns:         A generator of the items below this item.
		"""
		if predicate is None:
			for child in self._children.values():
				yield child
				yield from child.IterateItems()
		else:
			for child in self._children.values():
				if predicate(child):
					yield child

				yield from child.IterateItems(predicate)

	def __iter__(self) -> Iterator[AlertLogItem]:
		"""
		Iterate all child AlertLog items.

		:returns: An iterator of child items.
		"""
		return iter(self._children.values())

	def __len__(self) -> int:
		"""
		Returns the number of child AlertLog items.

		:returns: The number of child items.
		"""
		return len(self._children)

	def __getitem__(self, name: str) -> AlertLogItem:
		"""
		Index access for returning child AlertLog items.

		:param name:      The child's name.
		:returns:         The referenced child.
		:raises KeyError: When the child referenced by parameter 'name' doesn't exist.
		"""
		return self._children[name]

	def ToTree(self, format: Callable[[Node], str] = _format) -> Node:
		"""
		Convert the AlertLog hierarchy starting from this AlertLog item to a :external+pyTool:ref:`pyTooling Tree
		<STRUCT/Tree>`.

		:param format: Optional, a user-defined :external+pyTool:ref:`pyTooling Tree <STRUCT/Tree>` formatting function
		               for all nodes. Default: ``_format``.
		:returns:      A tree of nodes referencing an AlertLog item.
		"""
		return Node(
			value=self,
			keyValuePairs={
				"Name":            self._name,
				"TotalErrorCount": self._totalErrorCount,
				"FailureCount":    self._alertCount._failureCount,
				"ErrorCount":      self._alertCount._errorCount,
				"WarningCount":    self._alertCount._warningCount,
				"PassedCount":     self._passedCount,
				"AffirmCount":     self._affirmCount
			},
			children=[child.ToTree(format) for child in self._children.values()],
			format=format
		)


@export
class Settings(metaclass=ExtendedType, slots=True):
	"""
	The root's ``Settings``: the settings of ``AlertLogPkg`` deciding whether a test failed.

	The settings belong to the :class:`Document`, which is the root of the AlertLog hierarchy.
	"""

	_parent:                  Nullable[Document]  #: The document the settings belong to.
	_externalErrors:          _AlertCount         #: External errors, less the alerts the test expects.
	_failOnDisabledErrors:    bool                #: If true, disabled alerts are errors.
	_failOnRequirementErrors: bool                #: If true, failed requirements are errors.
	_failOnWarning:           bool                #: If true, warnings are errors.

	def __init__(
		self,
		externalErrors:          AlertCount,
		failOnDisabledErrors:    bool,
		failOnRequirementErrors: bool,
		failOnWarning:           bool,
		*,
		parent:                  Nullable[Document] = None
	) -> None:
		"""
		Initializes the settings, and adds them to their document.

		:param externalErrors:          External errors, less the alerts the test expects.
		:param failOnDisabledErrors:    If true, disabled alerts are errors.
		:param failOnRequirementErrors: If true, failed requirements are errors.
		:param failOnWarning:           If true, warnings are errors.
		:param parent:                  Optional, the document the settings belong to. Default: ``None``.
		:raises ValueError:             If parameter ``externalErrors`` is ``None``.
		:raises TypeError:              If parameter ``externalErrors`` isn't of type :class:`AlertCount`.
		:raises ValueError:             If parameter ``failOnDisabledErrors`` is ``None``.
		:raises ValueError:             If parameter ``failOnRequirementErrors`` is ``None``.
		:raises ValueError:             If parameter ``failOnWarning`` is ``None``.
		:raises TypeError:              If parameter ``failOnDisabledErrors`` isn't of type :class:`bool`.
		:raises TypeError:              If parameter ``failOnRequirementErrors`` isn't of type :class:`bool`.
		:raises TypeError:              If parameter ``failOnWarning`` isn't of type :class:`bool`.
		:raises TypeError:              If parameter ``parent`` isn't of type :class:`Document`.
		:raises AlertLogError:          If parameter ``parent`` has settings already.
		"""
		if externalErrors is None:
			raise ValueError("Parameter 'externalErrors' is None.")
		elif not isinstance(externalErrors, AlertCount):
			ex = TypeError("Parameter 'externalErrors' is not of type 'AlertCount'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(externalErrors)}'.")
			raise ex

		for parameterName, flag in (
			("failOnDisabledErrors",    failOnDisabledErrors),
			("failOnRequirementErrors", failOnRequirementErrors),
			("failOnWarning",           failOnWarning)
		):
			if flag is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(flag, bool):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'bool'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(flag)}'.")
				raise ex

		if parent is not None:
			if not isinstance(parent, Document):
				ex = TypeError("Parameter 'parent' is not of type 'Document'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
				raise ex
			elif parent._settings is not None:
				raise AlertLogError(f"AlertLog document '{parent._path}' has settings already.")

		self._parent =                  parent
		self._externalErrors =          externalErrors
		self._failOnDisabledErrors =    failOnDisabledErrors
		self._failOnRequirementErrors = failOnRequirementErrors
		self._failOnWarning =           failOnWarning

		if parent is not None:
			parent._settings = self

	@classmethod
	def Parse(cls, node: CommentedMap, *, parent: Nullable[Document] = None) -> Self:
		"""
		Parse the root's ``Settings``.

		OSVVM writes the flags as strings ``"true"`` or ``"false"``; their case is ignored. A key the format doesn't define
		is reported as :exc:`~pyEDAA.OSVVM.UnknownKeyWarning`.

		:param node:                           The YAML mapping.
		:param parent:                         Optional, the document the settings belong to. Default: ``None``.
		:returns:                              The settings.
		:raises AlertLogError:                 If the mapping lacks a key the format requires.
		:raises AlertLogError:                 If a value isn't of the type the format requires.
		:raises AlertLogError:                 If a flag is neither ``true`` nor ``false``.
		:raises AlertLogError:                 If parameter ``parent`` has settings already.
		:raises UnhandledCriticalWarningError: If a mapping has an unknown key, and no warning collector collects the
		                                       warning.
		"""
		line = node.lc.line + 1
		for key in node:
			if key not in ("ExternalErrors", "FailOnDisabledErrors", "FailOnRequirementErrors", "FailOnWarning"):
				keyLine = node.lc.key(key)[0] + 1
				WarningCollector.Raise(
					UnknownKeyWarning(f"Unknown key '{key}' in settings at line {keyLine}.", key=key, line=keyLine)
				)

		if "ExternalErrors" not in node:
			raise AlertLogError(f"Settings at line {line} have no key 'ExternalErrors'.")
		elif not isinstance(node["ExternalErrors"], CommentedMap):
			ex = AlertLogError(f"Key 'ExternalErrors' of settings at line {line} is not a mapping.")
			ex.add_note(f"Got type '{getFullyQualifiedName(node['ExternalErrors'])}'.")
			raise ex

		flags = {}
		for key in ("FailOnDisabledErrors", "FailOnRequirementErrors", "FailOnWarning"):
			if key not in node:
				raise AlertLogError(f"Settings at line {line} have no key '{key}'.")
			elif not isinstance(value := node[key], str):
				ex = AlertLogError(f"Key '{key}' of settings at line {line} is not a string.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex
			elif value.lower() not in ("true", "false"):
				ex = AlertLogError(f"Key '{key}' of settings at line {line} is neither 'true' nor 'false'.")
				ex.add_note(f"Got value '{value}'.")
				raise ex

			flags[key] = value.lower() == "true"

		return cls(
			AlertCount.Parse(node["ExternalErrors"]),
			flags["FailOnDisabledErrors"],
			flags["FailOnRequirementErrors"],
			flags["FailOnWarning"],
			parent=parent
		)

	@readonly
	def Parent(self) -> Nullable[Document]:
		"""
		Read-only property to access the document the settings belong to (:attr:`_parent`).

		:returns: The document, or ``None`` if the settings belong to no document.
		"""
		return self._parent

	@readonly
	def ExternalErrors(self) -> AlertCount:
		"""
		Read-only property to access the external errors, less the alerts the test expects (:attr:`_externalErrors`).

		A test passes external errors to ``WriteAlertYaml``, e.g. errors found by a script. A count is negative, if the
		test expects more alerts of that kind than external errors are passed.

		:returns: The external errors.
		"""
		return self._externalErrors

	@readonly
	def FailOnDisabledErrors(self) -> bool:
		"""
		Read-only property to access whether disabled alerts are errors (:attr:`_failOnDisabledErrors`).

		:returns: ``True``, if disabled alerts are errors.
		"""
		return self._failOnDisabledErrors

	@readonly
	def FailOnRequirementErrors(self) -> bool:
		"""
		Read-only property to access whether failed requirements are errors (:attr:`_failOnRequirementErrors`).

		:returns: ``True``, if failed requirements are errors.
		"""
		return self._failOnRequirementErrors

	@readonly
	def FailOnWarning(self) -> bool:
		"""
		Read-only property to access whether warnings are errors (:attr:`_failOnWarning`).

		:returns: ``True``, if warnings are errors.
		"""
		return self._failOnWarning


_Settings = Settings


# TODO: Derive from common Document class?
@export
class Document(AlertLogItem):
	"""
	An *AlertLog Document* represents an OSVVM AlertLog report document (YAML file).

	The document inherits :class:`AlertLogItem` and represents the AlertLog hierarchy's root element.

	When analyzing and converting the document, the YAML analysis duration as well as the model conversion duration gets
	captured.
	"""

	_path:                   Path                       #: Path to the YAML file.
	_yamlDocument:           Nullable[YAML]             #: Internal YAML document instance.
	_version:                Nullable[FormatVersion]    #: YAML data structure version.
	_settings:               Nullable[_Settings]        #: The settings deciding whether the test failed.

	_analysisDuration:        Nullable[timedelta]       #: YAML file analysis duration in seconds.
	_modelConversionDuration: Nullable[timedelta]       #: Data structure conversion duration in seconds.

	def __init__(self, filename: Path, analyzeAndConvert: bool = False) -> None:
		"""
		Initializes an AlertLog YAML document.

		:param filename:          Path to the YAML file.
		:param analyzeAndConvert: If true, analyze the YAML document and convert the content to an AlertLog data model instance.
		"""
		super().__init__("", parent=None)

		self._path = filename
		self._yamlDocument = None
		self._version = None
		self._settings = None

		self._analysisDuration = None
		self._modelConversionDuration =  None

		if analyzeAndConvert:
			self.Analyze()
			self.Convert()

	@property
	def Path(self) -> Path:
		"""
		Read-only property to access the path to the YAML file of this document (:attr:`_path`).

		:returns: The document's path to the YAML file.
		"""
		return self._path

	@readonly
	def Settings(self) -> Nullable[Settings]:
		"""
		Read-only property to access the settings deciding whether the test failed (:attr:`_settings`).

		:returns: The settings; ``None`` before the document was converted.
		"""
		return self._settings

	@readonly
	def AnalysisDuration(self) -> timedelta:
		"""
		Read-only property to access the time spent for YAML file analysis (:attr:`_analysisDuration`).

		:returns: The YAML file analysis duration.
		"""
		if self._analysisDuration is None:
			raise AlertLogError(f"Document '{self._path}' was not analyzed.")

		return self._analysisDuration

	@readonly
	def ModelConversionDuration(self) -> timedelta:
		"""
		Read-only property to access the time spent for data structure to AlertLog hierarchy conversion (:attr:`_modelConversionDuration`).

		:returns: The data structure conversion duration.
		"""
		if self._modelConversionDuration is None:
			raise AlertLogError(f"Document '{self._path}' was not converted.")

		return self._modelConversionDuration

	def Analyze(self) -> None:
		"""
		Analyze the YAML file (specified by :attr:`_path`) and store the YAML document in :attr:`_yamlDocument`.

		:raises AlertLogError: If YAML file doesn't exist.
		:raises AlertLogError: If YAML file can't be opened.
		"""
		if not self._path.exists():
			raise AlertLogError(f"OSVVM AlertLog YAML file '{self._path}' does not exist.") \
				from FileNotFoundError(f"File '{self._path}' not found.")

		with Stopwatch() as sw:
			try:
				yamlReader = YAML()
				self._yamlDocument = yamlReader.load(self._path)
			except Exception as ex:
				raise AlertLogError(f"Couldn't open '{self._path}'.") from ex

		self._analysisDuration = sw.Duration

	def Convert(self) -> None:
		"""
		Convert the YAML data structure to the settings and a hierarchy of :class:`AlertLogItem` instances.

		A key the format doesn't define is reported as :exc:`~pyEDAA.OSVVM.UnknownKeyWarning`.

		:raises AlertLogError:                 If YAML file was not analyzed.
		:raises AlertLogError:                 If a mapping lacks a key the format requires.
		:raises AlertLogError:                 If a value isn't of the type the format requires.
		:raises UnhandledCriticalWarningError: If a mapping has an unknown key, and no warning collector collects the
		                                       warning.
		"""
		if self._yamlDocument is None:
			ex = AlertLogError(f"OSVVM AlertLog YAML file '{self._path}' needs to be read and analyzed by a YAML parser.")
			ex.add_note("Call 'Document.Analyze()' or create the document using 'Document(path, analyzeAndConvert=True)'.")
			raise ex

		with Stopwatch() as sw:
			version = self._yamlDocument.get("Version", None)
			try:
				self._version = FormatVersion.Parse(version)
			except (TypeError, ValueError) as cause:
				ex = AlertLogError(f"Unsupported YAML data structure version '{version}' for file '{self._path}'.")
				ex.add_note(f"Supported format versions: {', '.join(FormatVersion)}.")
				raise ex from cause

			if self._version is None:
				ex = AlertLogError(f"No YAML data structure version in file '{self._path}'.")
				ex.add_note(f"Supported format versions: {', '.join(FormatVersion)}.")
				raise ex

			self._name = self._ParseStrFieldFromYAML(self._yamlDocument, "Name")
			self._status = AlertLogStatus.Parse(self._ParseStrFieldFromYAML(self._yamlDocument, "Status"))
			Settings.Parse(self._ParseMapFromYAML(self._yamlDocument, "Settings"), parent=self)
			for child in self._ParseSequenceFromYAML(self._yamlDocument, "Children"):
				AlertLogItem.Parse(child, parent=self)

		self._modelConversionDuration = sw.Duration

	@staticmethod
	def _ParseSequenceFromYAML(node: CommentedMap, fieldName: str) -> Nullable[CommentedSeq]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = OSVVMException(f"Sequence field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if value is None:
			return ()
		elif not isinstance(value, CommentedSeq):
			ex = AlertLogError(f"Field '{fieldName}' is not a sequence.")  # TODO: from TypeError??
			ex.add_note(f"Found type {value.__class__.__name__} at line {node._yaml_line_col.data[fieldName][0] + 1}.")
			raise ex

		return value

	@staticmethod
	def _ParseMapFromYAML(node: CommentedMap, fieldName: str) -> Nullable[CommentedMap]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = OSVVMException(f"Dictionary field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if value is None:
			return {}
		elif not isinstance(value, CommentedMap):
			ex = AlertLogError(f"Field '{fieldName}' is not a list.")  # TODO: from TypeError??
			ex.add_note(f"Type mismatch found for line {node._yaml_line_col.data[fieldName][0] + 1}.")
			raise ex
		return value

	@staticmethod
	def _ParseStrFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[str]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = OSVVMException(f"String field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, str):
			raise AlertLogError(f"Field '{fieldName}' is not of type str.")  # TODO: from TypeError??

		return value
