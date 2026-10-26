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
from typing                import Callable, Generator, Iterable, Optional as Nullable, Self

from ruamel.yaml           import YAML, CommentedMap, CommentedSeq

from pyTooling.Common      import getFullyQualifiedName, StringEnum
from pyTooling.Decorators  import export, readonly
from pyTooling.Exceptions  import AlreadyInHierarchyError, DuplicateElementError
from pyTooling.MetaClasses import ExtendedType
from pyTooling.Stopwatch   import Stopwatch
from pyTooling.Tree        import Node

from pyEDAA.OSVVM          import OSVVMException


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
	_warningCount:            int                      #: Number of warnings.
	_errorCount:              int                      #: Number of errors.
	_failureCount:            int                      #: Number of failures.
	_passedCount:             int                      #: Number of passed affirmations.
	_affirmCount:             int                      #: Number of affirmations (incl. failed affirmations).
	_passedRequirementsCount: int                      #: Number of passed requirements.
	_requirementsGoalCount:   int                      #: Number of requirements to pass.
	_disabledWarningCount:    int                      #: Number of disabled warnings.
	_disabledErrorCount:      int                      #: Number of disabled errors.
	_disabledFailureCount:    int                      #: Number of disabled failures.

	def __init__(
		self,
		name:                    str,
		status:                  AlertLogStatus = AlertLogStatus.Unknown,
		totalErrorCount:         int = 0,
		warningCount:            int = 0,
		errorCount:              int = 0,
		failureCount:            int = 0,
		passedCount:             int = 0,
		affirmCount:             int = 0,
		passedRequirementsCount: int = 0,
		requirementsGoalCount:   int = 0,
		disabledWarningCount:    int = 0,
		disabledErrorCount:      int = 0,
		disabledFailureCount:    int = 0,
		children:                Nullable[Iterable[AlertLogItem]] = None,
		*,
		parent:                  Nullable[AlertLogItem] = None
	) -> None:
		"""
		Initializes an AlertLog item, and adds it to the children of its parent.

		:param name:                        Name of the AlertLog item.
		:param status:                      Optional, the item's status. Default: :attr:`AlertLogStatus.Unknown`.
		:param totalErrorCount:             Optional, total number of errors. Default: ``0``.
		:param warningCount:                Optional, number of warnings. Default: ``0``.
		:param errorCount:                  Optional, number of errors. Default: ``0``.
		:param failureCount:                Optional, number of failures. Default: ``0``.
		:param passedCount:                 Optional, number of passed affirmations. Default: ``0``.
		:param affirmCount:                 Optional, number of affirmations. Default: ``0``.
		:param passedRequirementsCount:     Optional, number of passed requirements. Default: ``0``.
		:param requirementsGoalCount:       Optional, number of requirements to pass. Default: ``0``.
		:param disabledWarningCount:        Optional, number of disabled warnings. Default: ``0``.
		:param disabledErrorCount:          Optional, number of disabled errors. Default: ``0``.
		:param disabledFailureCount:        Optional, number of disabled failures. Default: ``0``.
		:param children:                    Optional, child items. Default: ``None``.
		:param parent:                      Optional, the parent item; the item is added to its children. Default:
		                                    ``None``.
		:raises ValueError:                 If parameter ``name`` is ``None``.
		:raises TypeError:                  If parameter ``name`` isn't of type :class:`str`.
		:raises ValueError:                 If parameter ``status`` is ``None``.
		:raises TypeError:                  If parameter ``status`` isn't of type :class:`AlertLogStatus`.
		:raises ValueError:                 If parameter ``totalErrorCount`` is ``None``.
		:raises ValueError:                 If parameter ``warningCount`` is ``None``.
		:raises ValueError:                 If parameter ``errorCount`` is ``None``.
		:raises ValueError:                 If parameter ``failureCount`` is ``None``.
		:raises ValueError:                 If parameter ``passedCount`` is ``None``.
		:raises ValueError:                 If parameter ``affirmCount`` is ``None``.
		:raises ValueError:                 If parameter ``passedRequirementsCount`` is ``None``.
		:raises ValueError:                 If parameter ``requirementsGoalCount`` is ``None``.
		:raises ValueError:                 If parameter ``disabledWarningCount`` is ``None``.
		:raises ValueError:                 If parameter ``disabledErrorCount`` is ``None``.
		:raises ValueError:                 If parameter ``disabledFailureCount`` is ``None``.
		:raises TypeError:                  If parameter ``totalErrorCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``warningCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``errorCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``failureCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``passedCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``affirmCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``passedRequirementsCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``requirementsGoalCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``disabledWarningCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``disabledErrorCount`` isn't of type :class:`int`.
		:raises TypeError:                  If parameter ``disabledFailureCount`` isn't of type :class:`int`.
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
			("warningCount",            warningCount),
			("errorCount",              errorCount),
			("failureCount",            failureCount),
			("passedCount",             passedCount),
			("affirmCount",             affirmCount),
			("passedRequirementsCount", passedRequirementsCount),
			("requirementsGoalCount",   requirementsGoalCount),
			("disabledWarningCount",    disabledWarningCount),
			("disabledErrorCount",      disabledErrorCount),
			("disabledFailureCount",    disabledFailureCount)
		):
			if count is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(count, int):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'int'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(count)}'.")
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
		self._warningCount =            warningCount
		self._errorCount =              errorCount
		self._failureCount =            failureCount
		self._passedCount =             passedCount
		self._affirmCount =             affirmCount
		self._passedRequirementsCount = passedRequirementsCount
		self._requirementsGoalCount =   requirementsGoalCount
		self._disabledWarningCount =    disabledWarningCount
		self._disabledErrorCount =      disabledErrorCount
		self._disabledFailureCount =    disabledFailureCount

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
	def WarningCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of warnings (:attr:`_warningCount`).

		:returns: AlertLog item's number of warnings.
		"""
		return self._warningCount

	@readonly
	def ErrorCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of errors (:attr:`_errorCount`).

		:returns: AlertLog item's number of errors.
		"""
		return self._errorCount

	@readonly
	def FailureCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of failures (:attr:`_failureCount`).

		:returns: AlertLog item's number of failures.
		"""
		return self._failureCount

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
	def DisabledWarningCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of disabled warnings (:attr:`_disabledWarningCount`).

		:returns: AlertLog item's number of disabled warnings.
		"""
		return self._disabledWarningCount

	@readonly
	def DisabledErrorCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of disabled errors (:attr:`_disabledErrorCount`).

		:returns: AlertLog item's number of disabled errors.
		"""
		return self._disabledErrorCount

	@readonly
	def DisabledFailureCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's number of disabled failures (:attr:`_disabledFailureCount`).

		:returns: AlertLog item's number of disabled failures.
		"""
		return self._disabledFailureCount

	@readonly
	def Children(self) -> dict[str, AlertLogItem]:
		"""
		Read-only property to access the child items (:attr:`_children`).

		:returns: The child items, by name, in the order of the AlertLog file.
		"""
		return self._children

	@readonly
	def ChildCount(self) -> int:
		"""
		Read-only property to return the number of child items.

		:returns: Number of child items.
		"""
		return len(self._children)

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
				"FailureCount":    self._failureCount,
				"ErrorCount":      self._errorCount,
				"WarningCount":    self._warningCount,
				"PassedCount":     self._passedCount,
				"AffirmCount":     self._affirmCount
			},
			children=[child.ToTree(format) for child in self._children.values()],
			format=format
		)


@export
class Settings(metaclass=ExtendedType, mixin=True):
	_externalWarningCount:    int
	_externalErrorCount:      int
	_externalFailureCount:    int
	_failOnDisabledErrors:    bool
	_failOnRequirementErrors: bool
	_failOnWarning:           bool

	def __init__(self) -> None:
		self._externalWarningCount =    0
		self._externalErrorCount =      0
		self._externalFailureCount =    0
		self._failOnDisabledErrors =    False
		self._failOnRequirementErrors = True
		self._failOnWarning =           False


# TODO: Derive from common Document class?
@export
class Document(AlertLogItem, Settings):
	"""
	An *AlertLog Document* represents an OSVVM AlertLog report document (YAML file).

	The document inherits :class:`AlertLogItem` and represents the AlertLog hierarchy's root element.

	When analyzing and converting the document, the YAML analysis duration as well as the model conversion duration gets
	captured.
	"""

	_path:                   Path                       #: Path to the YAML file.
	_yamlDocument:           Nullable[YAML]             #: Internal YAML document instance.
	_version:                Nullable[FormatVersion]    #: YAML data structure version.

	_analysisDuration:        Nullable[timedelta]       #: YAML file analysis duration in seconds.
	_modelConversionDuration: Nullable[timedelta]       #: Data structure conversion duration in seconds.

	def __init__(self, filename: Path, analyzeAndConvert: bool = False) -> None:
		"""
		Initializes an AlertLog YAML document.

		:param filename:          Path to the YAML file.
		:param analyzeAndConvert: If true, analyze the YAML document and convert the content to an AlertLog data model instance.
		"""
		super().__init__("", parent=None)
		Settings.__init__(self)

		self._path = filename
		self._yamlDocument = None
		self._version = None

		self._analysisDuration = None
		self._modelConversionDuration =  None

		if analyzeAndConvert:
			self.Analyze()
			self.Parse()

	@property
	def Path(self) -> Path:
		"""
		Read-only property to access the path to the YAML file of this document (:attr:`_path`).

		:returns: The document's path to the YAML file.
		"""
		return self._path

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

	def Parse(self) -> None:
		"""
		Convert the YAML data structure to a hierarchy of :class:`AlertLogItem` instances.

		:raises AlertLogError: If YAML file was not analyzed.
		"""
		if self._yamlDocument is None:
			ex = AlertLogError(f"OSVVM AlertLog YAML file '{self._path}' needs to be read and analyzed by a YAML parser.")
			ex.add_note("Call 'Document.Analyze()' or create the document using 'Document(path, parse=True)'.")
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
			for child in self._ParseSequenceFromYAML(self._yamlDocument, "Children"):
				_ = self._ParseAlertLogItem(child, self)

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

	@staticmethod
	def _ParseIntFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[int]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = OSVVMException(f"Integer field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, int):
			raise AlertLogError(f"Field '{fieldName}' is not of type int.")  # TODO: from TypeError??

		return value

	def _ParseAlertLogItem(self, child: CommentedMap, parent: Nullable[AlertLogItem] = None) -> AlertLogItem:
		results = self._ParseMapFromYAML(child, "Results")
		yamlAlertCount = self._ParseMapFromYAML(results, "AlertCount")
		yamlDisabledAlertCount = self._ParseMapFromYAML(results, "DisabledAlertCount")
		alertLogItem = AlertLogItem(
			self._ParseStrFieldFromYAML(child, "Name"),
			AlertLogStatus.Parse(self._ParseStrFieldFromYAML(child, "Status")),
			self._ParseIntFieldFromYAML(results, "TotalErrors"),
			self._ParseIntFieldFromYAML(yamlAlertCount, "Warning"),
			self._ParseIntFieldFromYAML(yamlAlertCount, "Error"),
			self._ParseIntFieldFromYAML(yamlAlertCount, "Failure"),
			self._ParseIntFieldFromYAML(results, "PassedCount"),
			self._ParseIntFieldFromYAML(results, "AffirmCount"),
			self._ParseIntFieldFromYAML(results, "RequirementsPassed"),
			self._ParseIntFieldFromYAML(results, "RequirementsGoal"),
			self._ParseIntFieldFromYAML(yamlDisabledAlertCount, "Warning"),
			self._ParseIntFieldFromYAML(yamlDisabledAlertCount, "Error"),
			self._ParseIntFieldFromYAML(yamlDisabledAlertCount, "Failure"),
			children=(self._ParseAlertLogItem(ch) for ch in self._ParseSequenceFromYAML(child, "Children")),
			parent=parent
		)

		return alertLogItem
