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
"""Reader for OSVVM test report summary files in YAML format."""
from datetime              import timedelta, datetime
from pathlib               import Path
from typing                import Optional as Nullable, Iterator, Iterable, Mapping, Any, List

from ruamel.yaml           import YAML, CommentedMap, CommentedSeq
from pyTooling.Decorators  import export, InheritDocString, notimplemented, readonly
from pyTooling.MetaClasses import ExtendedType
from pyTooling.Common      import getFullyQualifiedName
from pyTooling.Stopwatch   import Stopwatch
from pyTooling.Versioning  import CalendarVersion, SemanticVersion

from pyEDAA.Reports.Unittesting import UnittestException, Document, TestcaseStatus, TestsuiteStatus, TestsuiteType, TestsuiteKind
from pyEDAA.Reports.Unittesting import TestsuiteSummary as ut_TestsuiteSummary, Testsuite as ut_Testsuite
from pyEDAA.Reports.Unittesting import Testcase as ut_Testcase


@export
class OsvvmException:
	pass


@export
@InheritDocString(UnittestException)
class UnittestException(UnittestException, OsvvmException):
	"""@InheritDocString(UnittestException)"""


@export
@InheritDocString(ut_Testcase)
class Testcase(ut_Testcase):
	"""@InheritDocString(ut_Testcase)"""

	_disabledWarningCount: int
	_disabledErrorCount:   int
	_disabledFatalCount:   int

	_requirementsCount:       Nullable[int]
	_passedRequirementsCount: Nullable[int]
	_failedRequirementsCount: Nullable[int]
	_functionalCoverage:      Nullable[float]

	def __init__(
		self,
		name: str,
		startTime: Nullable[datetime] = None,
		setupDuration: Nullable[timedelta] = None,
		testDuration: Nullable[timedelta] = None,
		teardownDuration: Nullable[timedelta] = None,
		totalDuration:  Nullable[timedelta] = None,
		status: TestcaseStatus = TestcaseStatus.Unknown,
		assertionCount: Nullable[int] = None,
		failedAssertionCount: Nullable[int] = None,
		passedAssertionCount: Nullable[int] = None,
		requirementsCount: Nullable[int] = None,
		passedRequirementsCount: Nullable[int] = None,
		failedRequirementsCount: Nullable[int] = None,
		functionalCoverage: Nullable[float] = None,
		warningCount: int = 0,
		errorCount: int = 0,
		fatalCount: int = 0,
		disabledWarningCount: int = 0,
		disabledErrorCount: int = 0,
		disabledFatalCount: int = 0,
		expectedWarningCount: int = 0,
		expectedErrorCount: int = 0,
		expectedFatalCount: int = 0,
		keyValuePairs: Nullable[Mapping[str, Any]] = None,
		parent: Nullable["Testsuite"] = None
	) -> None:
		"""
		Initializes the fields of a test case.

		:param name:                    Name of the test entity.
		:param startTime:               Time when the test entity was started.
		:param setupDuration:           Duration it took to set up the entity.
		:param testDuration:            Duration of the entity's test run.
		:param teardownDuration:        Duration it took to tear down the entity.
		:param totalDuration:           Total duration of the entity's execution (setup + test + teardown)
		:param status:                  Status of the test case.
		:param assertionCount:          Number of assertions within the test.
		:param failedAssertionCount:    Number of failed assertions within the test.
		:param passedAssertionCount:    Number of passed assertions within the test.
		:param requirementsCount:       Number of requirements within the test.
		:param failedRequirementsCount: Number of failed requirements within the test.
		:param passedRequirementsCount: Number of passed requirements within the test.
		:param warningCount:            Count of encountered warnings.
		:param errorCount:              Count of encountered errors.
		:param fatalCount:              Count of encountered fatal errors.
		:param disabledWarningCount:    Count of disabled warnings.
		:param disabledErrorCount:      Count of disabled errors.
		:param disabledFatalCount:      Count of disabled fatal errors.
		:param expectedWarningCount:    Count of expected warnings.
		:param expectedErrorCount:      Count of expected errors.
		:param expectedFatalCount:      Count of expected fatal errors.
		:param keyValuePairs:           Mapping of key-value pairs to initialize the test case.
		:param parent:                  Reference to the parent test suite.
		:raises TypeError:              If parameter 'parent' is not a Testsuite.
		:raises ValueError:             If parameter 'assertionCount' is not consistent.
		"""
		super().__init__(
			name,
			startTime, setupDuration, testDuration, teardownDuration, totalDuration,
			status,
			assertionCount, failedAssertionCount, passedAssertionCount,
			warningCount, errorCount, fatalCount,
			expectedWarningCount, expectedErrorCount, expectedFatalCount,
			keyValuePairs,
			parent
		)

		if not isinstance(disabledWarningCount, int):
			ex = TypeError(f"Parameter 'disabledWarningCount' is not of type 'int'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(disabledWarningCount)}'.")
			raise ex

		if not isinstance(disabledErrorCount, int):
			ex = TypeError(f"Parameter 'disabledErrorCount' is not of type 'int'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(disabledErrorCount)}'.")
			raise ex

		if not isinstance(disabledFatalCount, int):
			ex = TypeError(f"Parameter 'disabledFatalCount' is not of type 'int'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(disabledFatalCount)}'.")
			raise ex

		self._disabledWarningCount = disabledWarningCount
		self._disabledErrorCount =   disabledErrorCount
		self._disabledFatalCount =   disabledFatalCount

		if requirementsCount is not None and not isinstance(requirementsCount, int):
			ex = TypeError(f"Parameter 'requirementsCount' is not of type 'int'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(requirementsCount)}'.")
			raise ex

		if passedRequirementsCount is not None and not isinstance(passedRequirementsCount, int):
			ex = TypeError(f"Parameter 'passedRequirementsCount' is not of type 'int'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(passedRequirementsCount)}'.")
			raise ex

		if failedRequirementsCount is not None and not isinstance(failedRequirementsCount, int):
			ex = TypeError(f"Parameter 'failedRequirementsCount' is not of type 'int'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(failedRequirementsCount)}'.")
			raise ex

		if requirementsCount is not None:
			if passedRequirementsCount is not None:
				if failedRequirementsCount is not None:
					if passedRequirementsCount + failedRequirementsCount != requirementsCount:
						raise ValueError(f"Parameter 'requirementsCount' is not the sum of 'passedRequirementsCount' and 'failedRequirementsCount'.")
				else:
					failedRequirementsCount = requirementsCount - passedRequirementsCount
			elif failedRequirementsCount is not None:
				passedRequirementsCount = requirementsCount - failedRequirementsCount
			else:
				passedRequirementsCount = requirementsCount
				failedRequirementsCount = 0
		else:
			if passedRequirementsCount is not None:
				if failedRequirementsCount is not None:
					requirementsCount = passedRequirementsCount + failedRequirementsCount
				else:
					requirementsCount = passedRequirementsCount
					failedRequirementsCount = 0
			elif failedRequirementsCount is not None:
				requirementsCount = failedRequirementsCount
				passedRequirementsCount = 0

		self._requirementsCount = requirementsCount
		self._passedRequirementsCount = passedRequirementsCount
		self._failedRequirementsCount = failedRequirementsCount

		if functionalCoverage is not None:
			if not isinstance(functionalCoverage, float):
				ex = TypeError(f"Parameter 'functionalCoverage' is not of type 'float'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(functionalCoverage)}'.")
				raise ex

			if not (0.0 <= functionalCoverage <= 1.0):
				raise ValueError(f"Parameter 'functionalCoverage' is not in range 0.0..1.0.")

		self._functionalCoverage = functionalCoverage

	@readonly
	def DisabledWarningCount(self) -> int:
		"""
		Read-only property returning the number of disabled warnings.

		:returns: Count of disabled warnings.
		"""
		return self._disabledWarningCount

	@readonly
	def DisabledErrorCount(self) -> int:
		"""
		Read-only property returning the number of disabled errors.

		:returns: Count of disabled errors.
		"""
		return self._disabledErrorCount

	@readonly
	def DisabledFatalCount(self) -> int:
		"""
		Read-only property returning the number of disabled fatal errors.

		:returns: Count of disabled fatal errors.
		"""
		return self._disabledFatalCount

	@readonly
	def RequirementsCount(self) -> int:
		"""
		Read-only property returning the number of requirements.

		:returns: Count of requirements.
		"""
		return self._requirementsCount

	@readonly
	def PassedRequirementsCount(self) -> int:
		"""
		Read-only property returning the number of passed requirements.

		:returns: Count of passed rerquirements.
		"""
		return self._passedRequirementsCount

	@readonly
	def FailedRequirementsCount(self) -> int:
		"""
		Read-only property returning the number of failed requirements.

		:returns: Count of failed requirements.
		"""
		return self._failedRequirementsCount

	@readonly
	def FunctionalCoverage(self) -> float:
		"""
		Read-only property returning the functional coverage.

		:returns: Percentage of functional coverage.
		"""
		return self._functionalCoverage


@export
@InheritDocString(ut_Testsuite)
class Testsuite(ut_Testsuite):
	"""@InheritDocString(ut_Testsuite)"""


@export
class BuildInformation(metaclass=ExtendedType, slots=True):
	_startTime:          datetime
	_finishTime:         datetime
	_elapsed:            timedelta
	_simulator:          str
	_simulatorVersion:   SemanticVersion
	_osvvmVersion:       CalendarVersion
	_buildErrorCode:     int
	_analyzeErrorCount:  int
	_simulateErrorCount: int

	def __init__(self) -> None:
		pass


@export
class Settings(metaclass=ExtendedType, slots=True):
	_baseDirectory:            Path
	_reportsSubdirectory:      Path
	_simulationLogFile:        Path
	_simulationHtmlLogFile:    Path
	_requirementsSubdirectory: Path
	_coverageSubdirectory:     Path
	_report2CssFiles:          List[Path]
	_report2PngFile:           List[Path]

	def __init__(self) -> None:
		pass


@export
@InheritDocString(ut_TestsuiteSummary)
class TestsuiteSummary(ut_TestsuiteSummary):
	"""@InheritDocString(ut_TestsuiteSummary)"""

	_datetime: datetime

	def __init__(
		self,
		name: str,
		startTime: Nullable[datetime] = None,
		setupDuration: Nullable[timedelta] = None,
		testDuration: Nullable[timedelta] = None,
		teardownDuration: Nullable[timedelta] = None,
		totalDuration:  Nullable[timedelta] = None,
		status: TestsuiteStatus = TestsuiteStatus.Unknown,
		warningCount: int = 0,
		errorCount: int = 0,
		fatalCount: int = 0,
		testsuites: Nullable[Iterable[TestsuiteType]] = None,
		keyValuePairs: Nullable[Mapping[str, Any]] = None,
		parent: Nullable[TestsuiteType] = None
	) -> None:
		"""
		Initializes the fields of a test summary.

		:param name:               Name of the test summary.
		:param startTime:          Time when the test summary was started.
		:param setupDuration:      Duration it took to set up the test summary.
		:param testDuration:       Duration of all tests listed in the test summary.
		:param teardownDuration:   Duration it took to tear down the test summary.
		:param totalDuration:      Total duration of the entity's execution (setup + test + teardown)
		:param status:             Overall status of the test summary.
		:param warningCount:       Count of encountered warnings incl. warnings from sub-elements.
		:param errorCount:         Count of encountered errors incl. errors from sub-elements.
		:param fatalCount:         Count of encountered fatal errors incl. fatal errors from sub-elements.
		:param testsuites:         List of test suites to initialize the test summary with.
		:param keyValuePairs:      Mapping of key-value pairs to initialize the test summary with.
		:param parent:             Reference to the parent test summary.
		"""
		super().__init__(
			name,
			startTime, setupDuration, testDuration, teardownDuration, totalDuration,
			status,
			warningCount, errorCount, fatalCount,
			testsuites,
			keyValuePairs,
			parent
		)


@export
class BuildSummaryDocument(TestsuiteSummary, Document):
	_yamlDocument: Nullable[YAML]

	def __init__(self, yamlReportFile: Path, analyzeAndConvert: bool = False) -> None:
		super().__init__("Unprocessed OSVVM YAML file")

		self._yamlDocument = None

		Document.__init__(self, yamlReportFile, analyzeAndConvert)

	def Analyze(self) -> None:
		"""
		Analyze the YAML file, parse the content into an YAML data structure.

		.. hint::

		   The time spend for analysis will be made available via property :data:`AnalysisDuration`..
		"""
		if not self._path.exists():
			raise UnittestException(f"OSVVM YAML file '{self._path}' does not exist.") \
				from FileNotFoundError(f"File '{self._path}' not found.")

		with Stopwatch() as sw:
			try:
				yamlReader = YAML()
				self._yamlDocument = yamlReader.load(self._path)
			except Exception as ex:
				raise UnittestException(f"Couldn't open '{self._path}'.") from ex

		self._analysisDuration = sw.Duration

	@notimplemented
	def Write(self, path: Nullable[Path] = None, overwrite: bool = False) -> None:
		"""
		Write the data model as XML into a file adhering to the Any JUnit dialect.

		:param path:               Optional path to the YAML file, if internal path shouldn't be used.
		:param overwrite:          If true, overwrite an existing file.
		:raises UnittestException: If the file cannot be overwritten.
		:raises UnittestException: If the internal YAML data structure wasn't generated.
		:raises UnittestException: If the file cannot be opened or written.
		"""
		if path is None:
			path = self._path

		if not overwrite and path.exists():
			raise UnittestException(f"OSVVM YAML file '{path}' can not be overwritten.") \
				from FileExistsError(f"File '{path}' already exists.")

		# if regenerate:
		# 	self.Generate(overwrite=True)

		if self._yamlDocument is None:
			ex = UnittestException(f"Internal YAML document tree is empty and needs to be generated before write is possible.")
			# ex.add_note(f"Call 'BuildSummaryDocument.Generate()' or 'BuildSummaryDocument.Write(..., regenerate=True)'.")
			raise ex

		# with path.open("w", encoding="utf-8") as file:
		# 	self._yamlDocument.writexml(file, addindent="\t", encoding="utf-8", newl="\n")

	@staticmethod
	def _ParseSequenceFromYAML(node: CommentedMap, fieldName: str) -> Nullable[CommentedSeq]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = UnittestException(f"Sequence field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if value is None:
			return ()
		elif not isinstance(value, CommentedSeq):
			line = node._yaml_line_col.data[fieldName][0] + 1
			ex = UnittestException(f"Field '{fieldName}' is not a sequence.")  # TODO: from TypeError??
			ex.add_note(f"Found type {value.__class__.__name__} at line {line}.")
			raise ex

		return value

	@staticmethod
	def _ParseMapFromYAML(node: CommentedMap, fieldName: str) -> Nullable[CommentedMap]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = UnittestException(f"Dictionary field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if value is None:
			return {}
		elif not isinstance(value, CommentedMap):
			line = node._yaml_line_col.data[fieldName][0] + 1
			ex = UnittestException(f"Field '{fieldName}' is not a list.")  # TODO: from TypeError??
			ex.add_note(f"Type mismatch found for line {line}.")
			raise ex
		return value

	@staticmethod
	def _ParseStrFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[str]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = UnittestException(f"String field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, str):
			raise UnittestException(f"Field '{fieldName}' is not of type str.")  # TODO: from TypeError??

		return value

	@staticmethod
	def _ParseIntFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[int]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = UnittestException(f"Integer field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, int):
			raise UnittestException(f"Field '{fieldName}' is not of type int.")  # TODO: from TypeError??

		return value

	@staticmethod
	def _ParseDateFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[datetime]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = UnittestException(f"Date field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, datetime):
			raise UnittestException(f"Field '{fieldName}' is not of type datetime.")  # TODO: from TypeError??

		return value

	@staticmethod
	def _ParseDurationFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[timedelta]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = UnittestException(f"Duration field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, float):
			raise UnittestException(f"Field '{fieldName}' is not of type float.")  # TODO: from TypeError??

		return timedelta(seconds=value)

	def Convert(self) -> None:
		"""
		Convert the parsed YAML data structure into a test entity hierarchy.

		This method converts the root element.

		.. hint::

		   The time spend for model conversion will be made available via property :data:`ModelConversionDuration`.

		:raises UnittestException: If XML was not read and parsed before.
		"""
		if self._yamlDocument is None:
			ex = UnittestException(f"OSVVM YAML file '{self._path}' needs to be read and analyzed by a YAML parser.")
			ex.add_note(f"Call 'Document.Analyze()' or create document using 'Document(path, parse=True)'.")
			raise ex

		with Stopwatch() as sw:
			self._name = self._yamlDocument["Name"]
			buildInfo = self._ParseMapFromYAML(self._yamlDocument, "BuildInfo")
			self._startTime = self._ParseDateFieldFromYAML(buildInfo, "StartTime")
			self._totalDuration = self._ParseDurationFieldFromYAML(buildInfo, "Elapsed")

			if "TestSuites" in self._yamlDocument:
				for yamlTestsuite in self._ParseSequenceFromYAML(self._yamlDocument, "TestSuites"):
					self._ConvertTestsuite(self, yamlTestsuite)

			self.Aggregate()

		self._modelConversion = sw.Duration

	def _ConvertTestsuite(self, parentTestsuite: Testsuite, yamlTestsuite: CommentedMap) -> None:
		testsuiteName = self._ParseStrFieldFromYAML(yamlTestsuite, "Name")
		totalDuration = self._ParseDurationFieldFromYAML(yamlTestsuite, "ElapsedTime")

		testsuite = Testsuite(
			testsuiteName,
			totalDuration=totalDuration,
			parent=parentTestsuite
		)

		# if yamlTestsuite['TestCases'] is not None:
		for yamlTestcase in self._ParseSequenceFromYAML(yamlTestsuite, 'TestCases'):
			self._ConvertTestcase(testsuite, yamlTestcase)

	def _ConvertTestcase(self, parentTestsuite: Testsuite, yamlTestcase: CommentedMap) -> None:
		testcaseName = self._ParseStrFieldFromYAML(yamlTestcase, "TestCaseName")
		totalDuration = self._ParseDurationFieldFromYAML(yamlTestcase, "ElapsedTime")
		yamlStatus = self._ParseStrFieldFromYAML(yamlTestcase, "Status").lower()
		yamlResults = self._ParseMapFromYAML(yamlTestcase, "Results")
		assertionCount = self._ParseIntFieldFromYAML(yamlResults, "AffirmCount")
		passedAssertionCount = self._ParseIntFieldFromYAML(yamlResults, "PassedCount")

		totalErrors = self._ParseIntFieldFromYAML(yamlResults, "TotalErrors")

		yamlAlertCount = self._ParseMapFromYAML(yamlResults, "AlertCount")
		warningCount = self._ParseIntFieldFromYAML(yamlAlertCount, "Warning")
		errorCount = self._ParseIntFieldFromYAML(yamlAlertCount, "Error")
		failureCount = self._ParseIntFieldFromYAML(yamlAlertCount, "Failure")

		yamlDisabledAlertCount = self._ParseMapFromYAML(yamlResults, "DisabledAlertCount")
		disabledWarningCount = self._ParseIntFieldFromYAML(yamlDisabledAlertCount, "Warning")
		disabledErrorCount = self._ParseIntFieldFromYAML(yamlDisabledAlertCount, "Error")
		disabledFailureCount = self._ParseIntFieldFromYAML(yamlDisabledAlertCount, "Failure")

		yamlExpectedAlertCount = self._ParseMapFromYAML(yamlResults, "ExpectedCount")
		expectedWarningCount = self._ParseIntFieldFromYAML(yamlExpectedAlertCount, "Warning")
		expectedErrorCount = self._ParseIntFieldFromYAML(yamlExpectedAlertCount, "Error")
		expectedFailureCount = self._ParseIntFieldFromYAML(yamlExpectedAlertCount, "Failure")

		# FIXME: write a Parse classmethod in enum
		if yamlStatus == "passed":
			status = TestcaseStatus.Passed
		elif yamlStatus == "skipped":
			status = TestcaseStatus.Skipped
		elif yamlStatus == "failed":
			status = TestcaseStatus.Failed
		else:
			status = TestcaseStatus.Unknown

		if (
			abs(warningDiff := warningCount - expectedWarningCount) +
			abs(errorDiff := errorCount - expectedErrorCount) +
			abs(failureDiff := failureCount - expectedFailureCount) -
			totalErrors
		) == 0:
			if warningDiff > 0:
				status |= TestcaseStatus.Warned
			if errorDiff > 0:
				status |= TestcaseStatus.Errored
			if failureDiff > 0:
				status |= TestcaseStatus.Aborted
		else:
			status |= TestcaseStatus.Inconsistent

		_ = Testcase(
			testcaseName,
			totalDuration=totalDuration,
			status=status,
			assertionCount=assertionCount,
			passedAssertionCount=passedAssertionCount,
			warningCount=warningCount,
			errorCount=errorCount,
			fatalCount=failureCount,
			disabledWarningCount=disabledWarningCount,
			disabledErrorCount=disabledErrorCount,
			disabledFatalCount=disabledFailureCount,
			expectedWarningCount=expectedWarningCount,
			expectedErrorCount=expectedErrorCount,
			expectedFatalCount=expectedFailureCount,
			parent=parentTestsuite
		)

	def __contains__(self, key: str) -> bool:
		return key in self._testsuites

	def __iter__(self) -> Iterator[Testsuite]:
		return iter(self._testsuites.values())

	def __getitem__(self, key: str) -> Testsuite:
		return self._testsuites[key]

	def __len__(self) -> int:
		return self._testsuites.__len__()
