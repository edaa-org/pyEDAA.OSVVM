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
from typing                import Any, Callable, Dict, Iterable, Iterator, Optional as Nullable, Self

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
		:raises ValueError:  If parameter ``failureCount``, ``errorCount`` or ``warningCount`` is ``None``.
		:raises TypeError:   If parameter ``failureCount``, ``errorCount`` or ``warningCount`` isn't of type :class:`int`.
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


@export
def _format(node: Node) -> str:
	"""
	User-defined :external+pyTool:ref:`pyTooling Tree <STRUCT/Tree>` formatting function for nodes referencing :class:`AlertLogItems <AlertLogItem>`.

	:param node: Node to format.
	:returns:    String representation (one-liner) describing an AlertLogItem.
	"""
	return f"{node['Name']}: {node['TotalErrors']}={node['AlertCountFailures']}/{node['AlertCountErrors']}/{node['AlertCountWarnings']} {node['PassedCount']}/{node['AffirmCount']}"


@export
class AlertLogItem(metaclass=ExtendedType, slots=True):
	"""
	An *AlertLogItem* represents an AlertLog hierarchy item.

	An item has a reference to its parent item in the AlertLog hierarchy. If the item is the top-most element (root
	element), the parent reference is ``None``.

	An item can contain further child items.
	"""
	_parent:                     "AlertLogItem"             #: Reference to the parent item.
	_name:                       str                        #: Name of the AlertLog item.
	_children:                   Dict[str, "AlertLogItem"]  #: Dictionary of child items.

	_status:                     AlertLogStatus             #: AlertLog item's status
	_totalErrors:                int                        #: Total number of warnings, errors and failures.
	_alertCountWarnings:         int                        #: Warning count.
	_alertCountErrors:           int                        #: Error count.
	_alertCountFailures:         int                        #: Failure count.
	_passedCount:                int                        #: Passed affirmation count.
	_affirmCount:                int                        #: Overall affirmation count (incl. failed affirmations).
	_requirementsPassed:         int                        #: Count of passed requirements.
	_requirementsGoal:           int                        #: Overall expected requirements.
	_disabledAlertCountWarnings: int                        #: Count of disabled warnings.
	_disabledAlertCountErrors:   int                        #: Count of disabled errors.
	_disabledAlertCountFailures: int                        #: Count of disabled failures.

	def __init__(
		self,
		name: str,
		status: AlertLogStatus = AlertLogStatus.Unknown,
		totalErrors: int = 0,
		alertCountWarnings: int = 0,
		alertCountErrors: int = 0,
		alertCountFailures: int = 0,
		passedCount: int = 0,
		affirmCount: int = 0,
		requirementsPassed: int = 0,
		requirementsGoal: int = 0,
		disabledAlertCountWarnings: int = 0,
		disabledAlertCountErrors: int = 0,
		disabledAlertCountFailures: int = 0,
		children: Iterable["AlertLogItem"] = None,
		parent: Nullable["AlertLogItem"] = None
	) -> None:
		self._name = name
		self._parent = parent
		if parent is not None:
			if not isinstance(parent, AlertLogItem):
				ex = TypeError("Parameter 'parent' is not an AlertLogItem.")
				ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
				raise ex
			elif name in parent._children:
				raise DuplicateAlertLogItemError(
					f"AlertLogItem '{name}' already exists in '{parent._name}'.", item=parent._children[name]
				)

			parent._children[name] = self

		self._children = {}
		if children is not None:
			for child in children:
				if not isinstance(child, AlertLogItem):
					ex = TypeError("Item in parameter 'children' is not an AlertLogItem.")
					ex.add_note(f"Got type '{getFullyQualifiedName(child)}'.")
					raise ex
				elif child._name in self._children:
					raise DuplicateAlertLogItemError(
						f"AlertLogItem '{child._name}' already exists in '{self._name}'.", item=self._children[child._name]
					)
				elif child._parent is not None:
					raise AlreadyInAlertLogError(
						f"AlertLogItem '{child._name}' is already part of another AlertLog hierarchy ({child._parent._name}).",
						item=child
					)

				self._children[child._name] = child
				child._parent = self

		self._status = status
		self._totalErrors = totalErrors
		self._alertCountWarnings = alertCountWarnings
		self._alertCountErrors = alertCountErrors
		self._alertCountFailures = alertCountFailures
		self._passedCount = passedCount
		self._affirmCount = affirmCount
		self._requirementsPassed = requirementsPassed
		self._requirementsGoal = requirementsGoal
		self._disabledAlertCountWarnings = disabledAlertCountWarnings
		self._disabledAlertCountErrors = disabledAlertCountErrors
		self._disabledAlertCountFailures = disabledAlertCountFailures

	@property
	def Parent(self) -> Nullable["AlertLogItem"]:
		"""
		Property to access the parent item of this item (:attr:`_parent`).

		:returns: The item's parent item. ``None``, if it's the top-most item (root).
		"""
		return self._parent

	@Parent.setter
	def Parent(self, value: Nullable["AlertLogItem"]) -> None:
		if value is None:
			del self._parent._children[self._name]
		else:
			if not isinstance(value, AlertLogItem):
				ex = TypeError("Parameter 'value' is not an AlertLogItem.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex
			elif self._name in value._children:
				raise DuplicateAlertLogItemError(
					f"AlertLogItem '{self._name}' already exists in '{value._name}'.", item=value._children[self._name]
				)

			value._children[self._name] = self

		self._parent = value

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
	def TotalErrors(self) -> int:
		"""
		Read-only property to access the AlertLog item's total error count (:attr:`_totalErrors`).

		:returns: AlertLog item's total errors.
		"""
		return self._totalErrors

	@readonly
	def AlertCountWarnings(self) -> int:
		"""
		Read-only property to access the AlertLog item's warning count (:attr:`_alertCountWarnings`).

		:returns: AlertLog item's warning count.
		"""
		return self._alertCountWarnings

	@readonly
	def AlertCountErrors(self) -> int:
		"""
		Read-only property to access the AlertLog item's error count (:attr:`_alertCountErrors`).

		:returns: AlertLog item's error count.
		"""
		return self._alertCountErrors

	@readonly
	def AlertCountFailures(self) -> int:
		"""
		Read-only property to access the AlertLog item's failure count (:attr:`_alertCountFailures`).

		:returns: AlertLog item's failure count.
		"""
		return self._alertCountFailures

	@readonly
	def PassedCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's passed affirmation count (:attr:`_alertCountFailures`).

		:returns: AlertLog item's passed affirmations.
		"""
		return self._passedCount

	@readonly
	def AffirmCount(self) -> int:
		"""
		Read-only property to access the AlertLog item's overall affirmation count (:attr:`_affirmCount`).

		:returns: AlertLog item's overall affirmations.
		"""
		return self._affirmCount

	@readonly
	def RequirementsPassed(self) -> int:
		return self._requirementsPassed

	@readonly
	def RequirementsGoal(self) -> int:
		return self._requirementsGoal

	@readonly
	def DisabledAlertCountWarnings(self) -> int:
		"""
		Read-only property to access the AlertLog item's count of disabled warnings (:attr:`_disabledAlertCountWarnings`).

		:returns: AlertLog item's count of disabled warnings.
		"""
		return self._disabledAlertCountWarnings

	@readonly
	def DisabledAlertCountErrors(self) -> int:
		"""
		Read-only property to access the AlertLog item's count of disabled errors (:attr:`_disabledAlertCountErrors`).

		:returns: AlertLog item's count of disabled errors.
		"""
		return self._disabledAlertCountErrors

	@readonly
	def DisabledAlertCountFailures(self) -> int:
		"""
		Read-only property to access the AlertLog item's count of disabled failures (:attr:`_disabledAlertCountFailures`).

		:returns: AlertLog item's count of disabled failures.
		"""
		return self._disabledAlertCountFailures

	@readonly
	def Children(self) -> Dict[str, "AlertLogItem"]:
		return self._children

	def __iter__(self) -> Iterator["AlertLogItem"]:
		"""
		Iterate all child AlertLog items.

		:returns: An iterator of child items.
		"""
		return iter(self._children.values())

	def __len__(self) -> int:
		"""
		Returns number of child AlertLog items.

		:returns: The number of nested AlertLog items.
		"""
		return len(self._children)

	def __getitem__(self, name: str) -> "AlertLogItem":
		"""Index access for returning child AlertLog items.

		:param name:      The child's name.
		:returns:         The referenced child.
		:raises KeyError: When the child referenced by parameter 'name' doesn't exist.
		"""
		return self._children[name]

	def ToTree(self, format: Callable[[Node], str] = _format) -> Node:
		"""
		Convert the AlertLog hierarchy starting from this AlertLog item to a :external+pyTool:ref:`pyTooling Tree <STRUCT/Tree>`.

		:params format: A user-defined :external+pyTool:ref:`pyTooling Tree <STRUCT/Tree>` formatting function.
		:returns:       A tree of nodes referencing an AlertLog item.
		"""
		node = Node(
			value=self,
			keyValuePairs={
				"Name": self._name,
				"TotalErrors": self._totalErrors,
				"AlertCountFailures":  self._alertCountFailures,
				"AlertCountErrors": self._alertCountErrors,
				"AlertCountWarnings": self._alertCountWarnings,
				"PassedCount": self._passedCount,
				"AffirmCount": self._affirmCount
			},
			children=(child.ToTree() for child in self._children.values()),
			format=format
		)

		return node


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
