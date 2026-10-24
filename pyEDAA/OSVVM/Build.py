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
"""
A data model for OSVVM's build summary file :file:`<build>.yml`, derived from the unified test entity model of
:mod:`pyEDAA.Reports.Unittesting`.

OSVVM writes a build summary per build (``build <file>.pro``): its test suites, their test cases and the build's
information and settings. The hierarchy matches the unified model - a test suite summary of test suites of test cases
-, so the classes of this module derive from the unified classes and add what OSVVM states besides: per test case the
VHDL name, the disabled alerts, the requirements and the functional coverage. :meth:`Testsuite.ToTestsuite` copies a
test suite into the unified model, e.g. to merge it with other reports or to write it as JUnit XML.
"""
from __future__                 import annotations

from datetime                   import datetime, timedelta
from pathlib                    import Path
from typing                     import Any, ClassVar, Iterable, Iterator, List, Mapping, Optional as Nullable

from ruamel.yaml                import YAML, CommentedMap, CommentedSeq
from pyTooling.Common           import getFullyQualifiedName, StringEnum
from pyTooling.Decorators       import export, InheritDocString, notimplemented, readonly
from pyTooling.MetaClasses      import ExtendedType
from pyTooling.Stopwatch        import Stopwatch
from pyTooling.Versioning       import CalendarVersion, SemanticVersion

from pyEDAA.Reports.Unittesting import UnittestError, TestcaseStatus, TestsuiteStatus, TestsuiteType, \
                                       TestcaseAggregateReturnType
from pyEDAA.Reports.Unittesting import Document as ut_Document, TestsuiteSummary as ut_TestsuiteSummary
from pyEDAA.Reports.Unittesting import Testsuite as ut_Testsuite, Testcase as ut_Testcase

from pyEDAA.OSVVM               import OSVVMException


@export
class BuildSummaryError(OSVVMException, UnittestError):
	"""
	The exception raised by the build summary model and its reader.

	It's an :exc:`~pyEDAA.Reports.Unittesting.UnittestError` too, so code handling errors of the unified test entity
	model handles it as well.
	"""


@export
class OSVVMStatus(StringEnum):
	"""
	Status of a test case, as OSVVM states it in a build summary.

	OSVVM's ``GetTestResultStatus`` of :file:`AlertLogPkg.vhd` writes the status of a test case that ran; OSVVM's
	scripts write ``SKIPPED`` and ``ANALYZE_FAILED``. OSVVM's reader of build summaries assigns ``NOREPORTS`` to a test
	case without results, e.g. a simulation that crashed; an expected status may name it.
	"""

	Passed =        "PASSED"          #: The test case has no errors.
	Failed =        "FAILED"          #: The test case has errors.
	Skipped =       "SKIPPED"         #: The test case was skipped (``SkipTest``).
	AnalyzeFailed = "ANALYZE_FAILED"  #: The test case's sources failed to analyze.
	StopLimit =     "STOPLIMIT"       #: The test case stopped, because an alert count reached its stop limit.
	TimeOut =       "TIMEOUT"         #: The test case timed out.
	ManualChecks =  "MANUALCHECKS"    #: The test case has no errors, but needs manual checks.
	NoChecks =      "NOCHECKS"        #: The test case has no errors, but did no affirmations.
	NoReports =     "NOREPORTS"       #: The test case reported no results.

	__TESTCASE_STATUS: ClassVar[dict[str, TestcaseStatus]] = {
		Passed:        TestcaseStatus.Passed,
		Failed:        TestcaseStatus.Failed,
		Skipped:       TestcaseStatus.Skipped,
		AnalyzeFailed: TestcaseStatus.Errored,
		StopLimit:     TestcaseStatus.Failed,
		TimeOut:       TestcaseStatus.Failed,
		ManualChecks:  TestcaseStatus.Failed,
		NoChecks:      TestcaseStatus.Weak,
		NoReports:     TestcaseStatus.Errored,
	}

	def ToTestcaseStatus(self) -> TestcaseStatus:
		"""
		Convert the status to the status of the unified test entity model.

		OSVVM counts every status except passed, skipped and - unless ``FailOnNoChecks`` is set - no checks as failed. A
		test case without checks is weak; a test case, which failed to analyze or reported no results, is errored.

		:returns: The status of the unified test entity model.
		"""
		return self.__TESTCASE_STATUS[self]


# A class with a property named like a class - ``OSVVMStatus`` - can't name that class in the annotation of a field: the
# class body's namespace, where annotations are evaluated, binds the name to the property.
_OSVVMStatus = OSVVMStatus


@export
class Testcase(ut_Testcase):
	"""
	A test case of an OSVVM build: a simulation of a test bench, with the results OSVVM states for it.

	A test case's name is the base name of its report files (``TestCaseFileName``): the test's name, extended by the
	values of the generics it was simulated with, so the simulations of one test with different generics are distinct
	test cases. OSVVM's JUnit XML report names test cases the same way.

	Besides the fields of the unified test case, an OSVVM test case states the test's name (``TestCaseName``), the name
	the VHDL code gives it (``Name``), the status OSVVM determined, the disabled alerts, the requirements and the
	functional coverage. The unified status (:data:`~pyEDAA.Reports.Unittesting.Testcase.Status`) is computed from the
	OSVVM status by :meth:`Aggregate`.

	OSVVM's alerts *failure*, *error* and *warning* are the unified *fatal errors*, *errors* and *warnings*; its
	affirmations are the unified assertions.
	"""

	_vhdlName:                Nullable[str]           #: Name of the test case, as its VHDL code states it.
	_testName:                Nullable[str]           #: Name of the test, without the generics' values.
	_osvvmStatus:             Nullable[_OSVVMStatus]  #: Status of the test case, as OSVVM states it.
	_totalErrorCount:         Nullable[int]           #: Total number of errors, as OSVVM counted them.
	_disabledWarningCount:    int                     #: Number of disabled warnings.
	_disabledErrorCount:      int                     #: Number of disabled errors.
	_disabledFatalCount:      int                     #: Number of disabled failures.
	_requirementsGoalCount:   int                     #: Number of passed checks the requirements need.
	_passedRequirementsCount: int                     #: Number of passed requirement checks.
	_functionalCoverage:      Nullable[float]         #: Functional coverage in range 0.0..1.0.

	def __init__(
		self,
		name: str,
		title: Nullable[str] = None,
		summary: Nullable[str] = None,
		description: Nullable[str] = None,
		testName: Nullable[str] = None,
		vhdlName: Nullable[str] = None,
		osvvmStatus: Nullable[OSVVMStatus] = None,
		totalDuration: Nullable[timedelta] = None,
		assertionCount: Nullable[int] = None,
		passedAssertionCount: Nullable[int] = None,
		totalErrorCount: Nullable[int] = None,
		warningCount: int = 0,
		errorCount: int = 0,
		fatalCount: int = 0,
		expectedWarningCount: int = 0,
		expectedErrorCount: int = 0,
		expectedFatalCount: int = 0,
		disabledWarningCount: int = 0,
		disabledErrorCount: int = 0,
		disabledFatalCount: int = 0,
		requirementsGoalCount: int = 0,
		passedRequirementsCount: int = 0,
		functionalCoverage: Nullable[float] = None,
		keyValuePairs: Nullable[Mapping[str, Any]] = None,
		*,
		parent: Nullable[Testsuite] = None
	) -> None:
		"""
		Initializes an OSVVM test case.

		:param name:                    Name of the test case: the base name of its report files (``TestCaseFileName``).
		:param title:                   Optional, short label of the test case, written for a reader.
		:param summary:                 Optional, summary of the test case.
		:param description:             Optional, description of the test case.
		:param testName:                Optional, name of the test, without the generics' values (``TestCaseName``).
		:param vhdlName:                Optional, name of the test case, as its VHDL code states it (``Name``).
		:param osvvmStatus:             Optional, status of the test case, as OSVVM states it (``Status``).
		:param totalDuration:           Optional, duration of the simulation (``ElapsedTime``).
		:param assertionCount:          Optional, number of affirmations (``AffirmCount``).
		:param passedAssertionCount:    Optional, number of passed affirmations (``PassedCount``).
		:param totalErrorCount:         Optional, total number of errors, as OSVVM counted them (``TotalErrors``).
		:param warningCount:            Optional, number of warnings. Default: ``0``.
		:param errorCount:              Optional, number of errors. Default: ``0``.
		:param fatalCount:              Optional, number of failures. Default: ``0``.
		:param expectedWarningCount:    Optional, number of expected warnings. Default: ``0``.
		:param expectedErrorCount:      Optional, number of expected errors. Default: ``0``.
		:param expectedFatalCount:      Optional, number of expected failures. Default: ``0``.
		:param disabledWarningCount:    Optional, number of disabled warnings. Default: ``0``.
		:param disabledErrorCount:      Optional, number of disabled errors. Default: ``0``.
		:param disabledFatalCount:      Optional, number of disabled failures. Default: ``0``.
		:param requirementsGoalCount:   Optional, number of passed checks the requirements need (``RequirementsGoal``).
		                                Default: ``0``.
		:param passedRequirementsCount: Optional, number of passed requirement checks (``RequirementsPassed``).
		                                Default: ``0``.
		:param functionalCoverage:      Optional, functional coverage in range 0.0..1.0 (``FunctionalCoverage``).
		:param keyValuePairs:           Optional, mapping of key-value pairs to initialize the test case with.
		:param parent:                  Optional, reference to the parent test suite.
		:raises TypeError:              If parameter 'testName' or 'vhdlName' is not of type :class:`str`.
		:raises TypeError:              If parameter 'osvvmStatus' is not of type :class:`OSVVMStatus`.
		:raises TypeError:              If parameter 'totalErrorCount' is not of type :class:`int`.
		:raises TypeError:              If a parameter of the disabled alert counts or of the requirements is not of type
		                                :class:`int`.
		:raises TypeError:              If parameter 'functionalCoverage' is not of type :class:`float`.
		:raises ValueError:             If parameter 'functionalCoverage' is out of range 0.0..1.0.
		"""
		super().__init__(
			name,
			title, summary, description,
			None, None, None, None, totalDuration,
			TestcaseStatus.Unknown,
			assertionCount, None, passedAssertionCount,
			warningCount, errorCount, fatalCount,
			expectedWarningCount, expectedErrorCount, expectedFatalCount,
			keyValuePairs,
			parent=parent
		)

		for parameterName, text in (("testName", testName), ("vhdlName", vhdlName)):
			if text is not None and not isinstance(text, str):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'str'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(text)}'.")
				raise ex

		if osvvmStatus is not None and not isinstance(osvvmStatus, OSVVMStatus):
			ex = TypeError("Parameter 'osvvmStatus' is not of type 'OSVVMStatus'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(osvvmStatus)}'.")
			raise ex

		if totalErrorCount is not None and not isinstance(totalErrorCount, int):
			ex = TypeError("Parameter 'totalErrorCount' is not of type 'int'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(totalErrorCount)}'.")
			raise ex

		for parameterName, count in (
			("disabledWarningCount",    disabledWarningCount),
			("disabledErrorCount",      disabledErrorCount),
			("disabledFatalCount",      disabledFatalCount),
			("requirementsGoalCount",   requirementsGoalCount),
			("passedRequirementsCount", passedRequirementsCount)
		):
			if not isinstance(count, int):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'int'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(count)}'.")
				raise ex

		if functionalCoverage is not None:
			if not isinstance(functionalCoverage, float):
				ex = TypeError("Parameter 'functionalCoverage' is not of type 'float'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(functionalCoverage)}'.")
				raise ex
			elif not (0.0 <= functionalCoverage <= 1.0):
				ex = ValueError("Parameter 'functionalCoverage' is out of range 0.0..1.0.")
				ex.add_note(f"Got value '{functionalCoverage}'.")
				raise ex

		self._testName =                testName
		self._vhdlName =                vhdlName
		self._osvvmStatus =             osvvmStatus
		self._totalErrorCount =         totalErrorCount
		self._disabledWarningCount =    disabledWarningCount
		self._disabledErrorCount =      disabledErrorCount
		self._disabledFatalCount =      disabledFatalCount
		self._requirementsGoalCount =   requirementsGoalCount
		self._passedRequirementsCount = passedRequirementsCount
		self._functionalCoverage =      functionalCoverage

	@readonly
	def TestName(self) -> Nullable[str]:
		"""
		Read-only property to access the name of the test, without the generics' values (:attr:`_testName`).

		The test's name is the name given to OSVVM's ``TestName``, or the simulated design unit's name. The simulations of
		one test with different generics have the same test name.

		:returns: The test's name, or ``None`` if it wasn't recorded.
		"""
		return self._testName

	@readonly
	def VHDLName(self) -> Nullable[str]:
		"""
		Read-only property to access the name of the test case, as its VHDL code states it (:attr:`_vhdlName`).

		OSVVM fails a test case, whose VHDL name differs from its name, if ``FailOnVhdlNameNotMatchTestName`` is set.

		:returns: The VHDL name, or ``None`` if it wasn't recorded.
		"""
		return self._vhdlName

	@readonly
	def OSVVMStatus(self) -> Nullable[OSVVMStatus]:
		"""
		Read-only property to access the status of the test case, as OSVVM states it (:attr:`_osvvmStatus`).

		:returns: The OSVVM status, or ``None`` if the test case wasn't read from an OSVVM file.
		"""
		return self._osvvmStatus

	@readonly
	def TotalErrorCount(self) -> Nullable[int]:
		"""
		Read-only property to access the total number of errors, as OSVVM counted them (:attr:`_totalErrorCount`).

		OSVVM counts the alerts beyond the expected ones and - depending on its settings - disabled alerts and failed
		requirements.

		:returns: The total number of errors, or ``None`` if it wasn't recorded.
		"""
		return self._totalErrorCount

	@readonly
	def DisabledWarningCount(self) -> int:
		"""
		Read-only property to access the number of disabled warnings (:attr:`_disabledWarningCount`).

		:returns: Number of disabled warnings.
		"""
		return self._disabledWarningCount

	@readonly
	def DisabledErrorCount(self) -> int:
		"""
		Read-only property to access the number of disabled errors (:attr:`_disabledErrorCount`).

		:returns: Number of disabled errors.
		"""
		return self._disabledErrorCount

	@readonly
	def DisabledFatalCount(self) -> int:
		"""
		Read-only property to access the number of disabled failures (:attr:`_disabledFatalCount`).

		:returns: Number of disabled failures.
		"""
		return self._disabledFatalCount

	@readonly
	def RequirementsGoalCount(self) -> int:
		"""
		Read-only property to access the number of passed checks the requirements need (:attr:`_requirementsGoalCount`).

		:returns: Number of passed checks the requirements need.
		"""
		return self._requirementsGoalCount

	@readonly
	def PassedRequirementsCount(self) -> int:
		"""
		Read-only property to access the number of passed requirement checks (:attr:`_passedRequirementsCount`).

		:returns: Number of passed requirement checks.
		"""
		return self._passedRequirementsCount

	@readonly
	def FunctionalCoverage(self) -> Nullable[float]:
		"""
		Read-only property to access the functional coverage (:attr:`_functionalCoverage`).

		:returns: The functional coverage in range 0.0..1.0, or ``None`` if the test case has no coverage model.
		"""
		return self._functionalCoverage

	def Copy(self) -> Testcase:
		"""
		Copy the test case without its parent.

		:returns: A test case with the same fields.
		"""
		return self.__class__(
			self._name,
			self._title, self._summary, self._description,
			self._testName,
			self._vhdlName,
			self._osvvmStatus,
			self._totalDuration,
			self._assertionCount,
			self._passedAssertionCount,
			self._totalErrorCount,
			self._warningCount, self._errorCount, self._fatalCount,
			self._expectedWarningCount, self._expectedErrorCount, self._expectedFatalCount,
			self._disabledWarningCount, self._disabledErrorCount, self._disabledFatalCount,
			self._requirementsGoalCount,
			self._passedRequirementsCount,
			self._functionalCoverage,
			self._dict
		)

	def Aggregate(self, strict: bool = True) -> TestcaseAggregateReturnType:
		"""
		Compute the unified status from the OSVVM status, then aggregate the test case.

		A test case without OSVVM status is aggregated as a unified test case.

		:param strict: Optional, if true, a fatal error fails a test case without OSVVM status. Default: ``True``.
		:returns:      The test case's warning, error and fatal error counts, the expected ones and its duration.
		"""
		if self._status is TestcaseStatus.Unknown and self._osvvmStatus is not None:
			self._status = self._osvvmStatus.ToTestcaseStatus()

		return super().Aggregate(strict)

	def ToTestcase(self) -> ut_Testcase:
		"""
		Convert the test case to a test case of the unified test entity model.

		The fields of the unified test case and the key-value pairs are copied; the OSVVM-specific fields are dropped.

		:returns: A test case of the unified test entity model.
		"""
		return ut_Testcase(
			self._name,
			totalDuration=self._totalDuration,
			status=self._status,
			assertionCount=self._assertionCount,
			passedAssertionCount=self._passedAssertionCount,
			warningCount=self._warningCount,
			errorCount=self._errorCount,
			fatalCount=self._fatalCount,
			expectedWarningCount=self._expectedWarningCount,
			expectedErrorCount=self._expectedErrorCount,
			expectedFatalCount=self._expectedFatalCount,
			keyValuePairs=self._dict,
			message=self._message
		)


@export
class Testsuite(ut_Testsuite):
	"""
	A test suite of an OSVVM build (``TestSuite``): it groups the build's test cases.

	OSVVM states a test suite's name and the duration of its simulations (``ElapsedTime``). OSVVM's test suites don't
	nest.
	"""

	def ToTestsuite(self) -> ut_Testsuite:
		"""
		Convert the test suite and its test cases to a test suite of the unified test entity model.

		:returns: A test suite of the unified test entity model.
		"""
		return ut_Testsuite(
			self._name,
			totalDuration=self._totalDuration,
			status=self._status,
			testcases=(testcase.ToTestcase() for testcase in self._testcases.values()),
			keyValuePairs=self._dict
		)


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
	_datetime: datetime

	def __init__(
		self,
		name: str,
		title: Nullable[str] = None,
		summary: Nullable[str] = None,
		description: Nullable[str] = None,
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
		*,
		parent: Nullable[TestsuiteType] = None
	) -> None:
		"""
		Initializes the fields of a test summary.

		:param name:               Name of the test summary.
		:param title:              Optional, short label of the test summary, written for a reader.
		:param summary:            Optional, summary of the test summary.
		:param description:        Optional, description of the test summary.
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
			title, summary, description,
			startTime, setupDuration, testDuration, teardownDuration, totalDuration,
			status,
			warningCount, errorCount, fatalCount,
			testsuites,
			keyValuePairs,
			parent=parent
		)


@export
class BuildSummaryDocument(TestsuiteSummary, ut_Document):
	_yamlDocument: Nullable[YAML]             #: Internal YAML document instance.
	_version:      Nullable[SemanticVersion]  #: YAML data structure version.

	def __init__(self, yamlReportFile: Path, analyzeAndConvert: bool = False) -> None:
		super().__init__("Unprocessed OSVVM YAML file")

		self._yamlDocument = None
		self._version =      None

		ut_Document.__init__(self, yamlReportFile, analyzeAndConvert)

	@readonly
	def Version(self) -> Nullable[SemanticVersion]:
		"""
		Read-only property to access the YAML file's data structure version (:attr:`_version`).

		:returns: The YAML data structures version.
		"""
		return self._version

	def Analyze(self) -> None:
		"""
		Analyze the YAML file, parse the content into an YAML data structure.

		.. hint::

		   The time spend for analysis will be made available via property :data:`AnalysisDuration`..
		"""
		if not self._path.exists():
			raise BuildSummaryError(f"OSVVM YAML file '{self._path}' does not exist.") \
				from FileNotFoundError(f"File '{self._path}' not found.")

		with Stopwatch() as sw:
			try:
				yamlReader = YAML()
				self._yamlDocument = yamlReader.load(self._path)
			except Exception as ex:
				raise BuildSummaryError(f"Couldn't open '{self._path}'.") from ex

		self._analysisDuration = sw.Duration

	@notimplemented
	def Write(self, path: Nullable[Path] = None, overwrite: bool = False) -> None:
		"""
		Write the data model as XML into a file adhering to the Any JUnit dialect.

		:param path:               Optional path to the YAML file, if internal path shouldn't be used.
		:param overwrite:          If true, overwrite an existing file.
		:raises BuildSummaryError: If the file cannot be overwritten.
		:raises BuildSummaryError: If the internal YAML data structure wasn't generated.
		:raises BuildSummaryError: If the file cannot be opened or written.
		"""
		if path is None:
			path = self._path

		if not overwrite and path.exists():
			raise BuildSummaryError(f"OSVVM YAML file '{path}' can not be overwritten.") \
				from FileExistsError(f"File '{path}' already exists.")

		# if regenerate:
		# 	self.Generate(overwrite=True)

		if self._yamlDocument is None:
			ex = BuildSummaryError("Internal YAML document tree is empty and needs to be generated before write is possible.")
			# ex.add_note(f"Call 'BuildSummaryDocument.Generate()' or 'BuildSummaryDocument.Write(..., regenerate=True)'.")
			raise ex

		# with path.open("w", encoding="utf-8") as file:
		# 	self._yamlDocument.writexml(file, addindent="\t", encoding="utf-8", newl="\n")

	@staticmethod
	def _ParseSequenceFromYAML(node: CommentedMap, fieldName: str) -> Nullable[CommentedSeq]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = BuildSummaryError(f"Sequence field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if value is None:
			return ()
		elif not isinstance(value, CommentedSeq):
			line = node._yaml_line_col.data[fieldName][0] + 1
			ex = BuildSummaryError(f"Field '{fieldName}' is not a sequence.")  # TODO: from TypeError??
			ex.add_note(f"Found type {value.__class__.__name__} at line {line}.")
			raise ex

		return value

	@staticmethod
	def _ParseMapFromYAML(node: CommentedMap, fieldName: str) -> Nullable[CommentedMap]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = BuildSummaryError(
				f"Dictionary field '{fieldName}' not found in node starting at line {node.lc.line + 1}."
			)
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if value is None:
			return {}
		elif not isinstance(value, CommentedMap):
			line = node._yaml_line_col.data[fieldName][0] + 1
			ex = BuildSummaryError(f"Field '{fieldName}' is not a list.")  # TODO: from TypeError??
			ex.add_note(f"Type mismatch found for line {line}.")
			raise ex
		return value

	@staticmethod
	def _ParseStrFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[str]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = BuildSummaryError(f"String field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, str):
			raise BuildSummaryError(f"Field '{fieldName}' is not of type str.")  # TODO: from TypeError??

		return value

	@staticmethod
	def _ParseIntFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[int]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = BuildSummaryError(f"Integer field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, int):
			raise BuildSummaryError(f"Field '{fieldName}' is not of type int.")  # TODO: from TypeError??

		return value

	@staticmethod
	def _ParseDateFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[datetime]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = BuildSummaryError(f"Date field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, datetime):
			raise BuildSummaryError(f"Field '{fieldName}' is not of type datetime.")  # TODO: from TypeError??

		return value

	@staticmethod
	def _ParseDurationFieldFromYAML(node: CommentedMap, fieldName: str) -> Nullable[timedelta]:
		try:
			value = node[fieldName]
		except KeyError as ex:
			newEx = BuildSummaryError(f"Duration field '{fieldName}' not found in node starting at line {node.lc.line + 1}.")
			newEx.add_note(f"Available fields: {', '.join(key for key in node)}")
			raise newEx from ex

		if not isinstance(value, float):
			raise BuildSummaryError(f"Field '{fieldName}' is not of type float.")  # TODO: from TypeError??

		return timedelta(seconds=value)

	def Convert(self) -> None:
		"""
		Convert the parsed YAML data structure into a test entity hierarchy.

		This method converts the root element.

		.. hint::

		   The time spend for model conversion will be made available via property :data:`ModelConversionDuration`.

		:raises BuildSummaryError: If XML was not read and parsed before.
		"""
		if self._yamlDocument is None:
			ex = BuildSummaryError(f"OSVVM YAML file '{self._path}' needs to be read and analyzed by a YAML parser.")
			ex.add_note("Call 'Document.Analyze()' or create document using 'Document(path, parse=True)'.")
			raise ex

		with Stopwatch() as sw:
			self._version = SemanticVersion.Parse(self._yamlDocument["Version"])
			if not (self._version >> "0.1"):
				ex = BuildSummaryError(f"Unsupported YAML data structure version {self._version} for file '{self._path}'.")
				ex.add_note("Supported versions are: 1.0")
				raise ex

			self._name = self._yamlDocument["Name"]
			buildInfo = self._ParseMapFromYAML(self._yamlDocument, "BuildInfo")
			self._startTime = self._ParseDateFieldFromYAML(buildInfo, "StartTime")
			self._totalDuration = self._ParseDurationFieldFromYAML(buildInfo, "ElapsedTime")

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
		testName = self._ParseStrFieldFromYAML(yamlTestcase, "TestCaseName")
		totalDuration = self._ParseDurationFieldFromYAML(yamlTestcase, "ElapsedTime")
		osvvmStatus = OSVVMStatus.Parse(self._ParseStrFieldFromYAML(yamlTestcase, "Status").upper())
		yamlResults = self._ParseMapFromYAML(yamlTestcase, "Results")
		assertionCount = self._ParseIntFieldFromYAML(yamlResults, "AffirmCount")
		passedAssertionCount = self._ParseIntFieldFromYAML(yamlResults, "PassedCount")
		totalErrorCount = self._ParseIntFieldFromYAML(yamlResults, "TotalErrors")
		requirementsGoalCount = self._ParseIntFieldFromYAML(yamlResults, "RequirementsGoal")
		passedRequirementsCount = self._ParseIntFieldFromYAML(yamlResults, "RequirementsPassed")

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

		functionalCoverage = yamlTestcase.get("FunctionalCoverage", "")

		_ = Testcase(
			self._ParseStrFieldFromYAML(yamlTestcase, "TestCaseFileName"),
			testName=testName,
			vhdlName=self._ParseStrFieldFromYAML(yamlTestcase, "Name"),
			osvvmStatus=osvvmStatus,
			totalDuration=totalDuration,
			assertionCount=assertionCount,
			passedAssertionCount=passedAssertionCount,
			totalErrorCount=totalErrorCount,
			warningCount=warningCount,
			errorCount=errorCount,
			fatalCount=failureCount,
			expectedWarningCount=expectedWarningCount,
			expectedErrorCount=expectedErrorCount,
			expectedFatalCount=expectedFailureCount,
			disabledWarningCount=disabledWarningCount,
			disabledErrorCount=disabledErrorCount,
			disabledFatalCount=disabledFailureCount,
			requirementsGoalCount=requirementsGoalCount,
			passedRequirementsCount=passedRequirementsCount,
			functionalCoverage=None if functionalCoverage == "" else float(functionalCoverage) / 100.0,
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
