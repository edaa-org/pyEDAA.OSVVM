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
VHDL name, the disabled, expected and external alerts, the requirements, the functional coverage and the simulation
time. :meth:`TestsuiteSummary.ToTestsuiteSummary` copies the hierarchy into the unified model, e.g. to merge it with
other reports or to write it as JUnit XML.

.. rubric:: Example

.. code-block:: Python

   from pathlib import Path
   from pyEDAA.OSVVM.Build import BuildSummaryDocument

   document = BuildSummaryDocument(Path("RunAllTests/RunAllTests.yml"), analyzeAndConvert=True)
   for testcase in document.IterateTestcases():
     print(f"{testcase.Name}: {testcase.Status.name} - {testcase.OSVVMStatus}")
"""
from __future__                 import annotations

from datetime                   import datetime, timedelta
from pathlib                    import Path
from re                         import fullmatch
from typing                     import Any, ClassVar, Iterable, Mapping, Optional as Nullable

from ruamel.yaml                import CommentedMap
from pyTooling.Common           import getFullyQualifiedName, StringEnum
from pyTooling.Decorators       import export, readonly
from pyTooling.MetaClasses      import ExtendedType
from pyTooling.Stopwatch        import Stopwatch
from pyTooling.Versioning       import YearMonthVersion

from pyEDAA.Reports.Unittesting import UnittestError, TestcaseStatus, TestsuiteStatus, TestcaseAggregateReturnType
from pyEDAA.Reports.Unittesting import DuplicateTestsuiteError as ut_DuplicateTestsuiteError
from pyEDAA.Reports.Unittesting import DuplicateTestcaseError as ut_DuplicateTestcaseError
from pyEDAA.Reports.Unittesting import Document as ut_Document, TestsuiteSummary as ut_TestsuiteSummary
from pyEDAA.Reports.Unittesting import Testsuite as ut_Testsuite, Testcase as ut_Testcase

from pyEDAA.OSVVM               import OSVVMException, YAMLDocumentMixin


__all__ = ["SCHEMAS"]

# A class with a property named like a class - ``Path`` - can't name that class in the annotation of a field: the class
# body's namespace, where annotations are evaluated, binds the name to the property.
_Path = Path


@export
class BuildSummaryError(OSVVMException, UnittestError):
	"""
	The exception raised by the build summary model and its reader.

	It's an :exc:`~pyEDAA.Reports.Unittesting.UnittestError` too, so code handling errors of the unified test entity
	model handles it as well.
	"""


@export
class DuplicateTestsuiteError(BuildSummaryError, ut_DuplicateTestsuiteError):
	"""
	The exception raised, if a build summary states a test suite twice.
	"""


@export
class DuplicateTestcaseError(BuildSummaryError, ut_DuplicateTestcaseError):
	"""
	The exception raised, if a test suite of a build summary states a test case twice.

	A test case is identified by its report files' base name (``TestCaseFileName``). OSVVM overwrites the reports of a
	test simulated twice with the same generics in one test suite.
	"""


@export
class FormatVersion(StringEnum):
	"""
	Version of OSVVM's build summary format, as a build summary's ``Version`` states it.

	OSVVM writes ``OsvvmBuildYamlVersion`` of :file:`OsvvmSettingsRequired.tcl`, so far only ``0.1``.
	"""

	Version0_1 = "0.1"  #: Format version 0.1.


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
	the VHDL code gives it (``Name``), the status OSVVM determined, the disabled alerts, the requirements, the
	functional coverage, the simulated time and the generics. The unified status
	(:data:`~pyEDAA.Reports.Unittesting.Testcase.Status`) is computed from the OSVVM status by :meth:`Aggregate`.

	OSVVM's alerts *failure*, *error* and *warning* are the unified *fatal errors*, *errors* and *warnings*; its
	affirmations are the unified assertions. The reason of a skipped test case is the test case's
	:data:`~pyEDAA.Reports.Unittesting.TestcaseOutputMixin.Message`.
	"""

	_TIME_UNITS: ClassVar[dict[str, int]] = {
		"fs":  1,
		"ps":  1_000,
		"ns":  1_000_000,
		"us":  1_000_000_000,
		"ms":  1_000_000_000_000,
		"sec": 1_000_000_000_000_000,
		"min": 60_000_000_000_000_000,
		"hr":  3_600_000_000_000_000_000,
	}  #: Femtoseconds per unit of VHDL's type ``time``.

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
	_simulationTime:          Nullable[int]           #: Simulated time in femtoseconds.
	_generics:                dict[str, str]          #: Generics the test case was simulated with.

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
		simulationTime: Nullable[int] = None,
		generics: Nullable[Mapping[str, str]] = None,
		reason: Nullable[str] = None,
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
		:param simulationTime:          Optional, simulated time in femtoseconds (``SimulationTime``).
		:param generics:                Optional, generics the test case was simulated with (``Generics``).
		:param reason:                  Optional, reason of a skipped test case (``Reason``).
		:param keyValuePairs:           Optional, mapping of key-value pairs to initialize the test case with.
		:param parent:                  Optional, reference to the parent test suite.
		:raises TypeError:              If parameter 'testName' is not of type :class:`str`.
		:raises TypeError:              If parameter 'vhdlName' is not of type :class:`str`.
		:raises TypeError:              If parameter 'osvvmStatus' is not of type :class:`OSVVMStatus`.
		:raises TypeError:              If parameter 'totalErrorCount' or 'simulationTime' is not of type :class:`int`.
		:raises TypeError:              If a parameter of the disabled alert counts or of the requirements is not of type
		                                :class:`int`.
		:raises TypeError:              If parameter 'functionalCoverage' is not of type :class:`float`.
		:raises ValueError:             If parameter 'functionalCoverage' is out of range 0.0..1.0.
		:raises TypeError:              If parameter 'generics' is not a mapping.
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
			reason,
			parent=parent
		)

		for parameterName, text in (
			("testName", testName),
			("vhdlName", vhdlName)
		):
			if text is not None and not isinstance(text, str):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'str'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(text)}'.")
				raise ex

		if osvvmStatus is not None and not isinstance(osvvmStatus, OSVVMStatus):
			ex = TypeError("Parameter 'osvvmStatus' is not of type 'OSVVMStatus'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(osvvmStatus)}'.")
			raise ex

		for parameterName, count in (("totalErrorCount", totalErrorCount), ("simulationTime", simulationTime)):
			if count is not None and not isinstance(count, int):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'int'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(count)}'.")
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

		if generics is not None and not isinstance(generics, Mapping):
			ex = TypeError("Parameter 'generics' is not a mapping.")
			ex.add_note(f"Got type '{getFullyQualifiedName(generics)}'.")
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
		self._simulationTime =          simulationTime
		self._generics =                {} if generics is None else dict(generics)

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

	@readonly
	def SimulationTime(self) -> Nullable[int]:
		"""
		Read-only property to access the simulated time (:attr:`_simulationTime`).

		:returns: The simulated time in femtoseconds, or ``None`` if it wasn't recorded.
		"""
		return self._simulationTime

	@readonly
	def Generics(self) -> dict[str, str]:
		"""
		Read-only property to access the generics the test case was simulated with (:attr:`_generics`).

		:returns: Dictionary of generic names and values.
		"""
		return self._generics

	@classmethod
	def Parse(cls, node: CommentedMap, *, parent: Nullable[Testsuite] = None) -> Testcase:
		"""
		Parse a test case of a build summary (an element of a test suite's ``TestCases``).

		The mapping must be valid according to the build summary's schema (:data:`SCHEMAS`). A test case without
		``TestCaseFileName`` - a skipped one, or one that failed to analyze - is named after its ``TestCaseName``. A test
		case without ``Status`` reported no results: its OSVVM status is :attr:`OSVVMStatus.NoReports`, as OSVVM's reader
		decides. A test case without ``Results`` has no counts.

		:param node:                    The YAML mapping of the test case.
		:param parent:                  Optional, reference to the parent test suite.
		:returns:                       The test case.
		:raises BuildSummaryError:      If the status is unknown. |br|
		                                The note lists the allowed values.
		:raises BuildSummaryError:      If the functional coverage is out of range 0..100.
		:raises BuildSummaryError:      If the simulation time isn't a VHDL time value.
		:raises DuplicateTestcaseError: If parameter 'parent' has a test case of the same name already.
		"""
		def counts(key: str) -> tuple[int, int, int]:
			"""
			Nested function reading an alert count of the results.

			:param key: The key of the alert count, e.g. ``DisabledAlertCount``.
			:returns:   The numbers of warnings, errors and failures; zeros, if the results have no such alert count.
			"""
			if results is None or (alertCount := results.get(key, None)) is None:
				return 0, 0, 0

			return int(alertCount["Warning"]), int(alertCount["Error"]), int(alertCount["Failure"])

		line =     node.lc.line + 1
		testName = node["TestCaseName"]
		name =     node.get("TestCaseFileName", testName)
		if parent is not None and name in parent._testcases:
			raise DuplicateTestcaseError(f"Test suite '{parent._name}' has test case '{name}' twice (line {line}).")

		if (status := node.get("Status", None)) is None:
			osvvmStatus = OSVVMStatus.NoReports
		else:
			try:
				osvvmStatus = OSVVMStatus.Parse(status)
			except ValueError as cause:
				ex = BuildSummaryError(f"Test case '{name}' at line {line} has unknown status '{status}'.")
				ex.add_note(f"Allowed values: {', '.join(OSVVMStatus)}.")
				raise ex from cause

		if (coverage := node.get("FunctionalCoverage", "")) == "":
			functionalCoverage = None
		elif 0.0 <= coverage <= 100.0:
			functionalCoverage = float(coverage) / 100.0
		else:
			ex = BuildSummaryError(f"Functional coverage of test case '{name}' at line {line} is out of range 0..100.")
			ex.add_note(f"Got value '{coverage}'.")
			raise ex

		if (simulationTime := node.get("SimulationTime", None)) is None:
			femtoseconds = None
		else:
			value, _, unit = simulationTime.partition(" ")
			if not value.isdigit() or unit not in cls._TIME_UNITS:
				ex = BuildSummaryError(f"Simulation time of test case '{name}' at line {line} is not a VHDL time.")
				ex.add_note(f"Got value '{simulationTime}'.")
				raise ex

			femtoseconds = int(value) * cls._TIME_UNITS[unit]

		results = node.get("Results", None)
		warningCount, errorCount, fatalCount = counts("AlertCount")
		expectedWarningCount, expectedErrorCount, expectedFatalCount = counts("ExpectedCount")
		disabledWarningCount, disabledErrorCount, disabledFatalCount = counts("DisabledAlertCount")
		generics = node.get("Generics", None)
		elapsedTime = node.get("ElapsedTime", None)

		return cls(
			str(name),
			testName=str(testName),
			vhdlName=None if (vhdlName := node.get("Name", None)) is None else str(vhdlName),
			osvvmStatus=osvvmStatus,
			totalDuration=None if elapsedTime is None else timedelta(seconds=float(elapsedTime)),
			assertionCount=None if results is None else int(results["AffirmCount"]),
			passedAssertionCount=None if results is None else int(results["PassedCount"]),
			totalErrorCount=None if results is None else int(results["TotalErrors"]),
			warningCount=warningCount,
			errorCount=errorCount,
			fatalCount=fatalCount,
			expectedWarningCount=expectedWarningCount,
			expectedErrorCount=expectedErrorCount,
			expectedFatalCount=expectedFatalCount,
			disabledWarningCount=disabledWarningCount,
			disabledErrorCount=disabledErrorCount,
			disabledFatalCount=disabledFatalCount,
			requirementsGoalCount=0 if results is None else int(results["RequirementsGoal"]),
			passedRequirementsCount=0 if results is None else int(results["RequirementsPassed"]),
			functionalCoverage=functionalCoverage,
			simulationTime=femtoseconds,
			generics=None if generics is None else {str(key): str(value) for key, value in generics.items()},
			reason=None if (reason := node.get("Reason", None)) is None else str(reason),
			parent=parent
		)

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
			self._simulationTime,
			self._generics,
			self._message,
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

	@classmethod
	def Parse(cls, node: CommentedMap, *, parent: Nullable[TestsuiteSummary] = None) -> Testsuite:
		"""
		Parse a test suite of a build summary (an element of ``TestSuites``) and its test cases.

		The mapping must be valid according to the build summary's schema (:data:`SCHEMAS`).

		:param node:                     The YAML mapping of the test suite.
		:param parent:                   Optional, reference to the build.
		:returns:                        The test suite.
		:raises DuplicateTestsuiteError: If parameter 'parent' has a test suite of the same name already.
		"""
		name = str(node["Name"])
		if parent is not None and name in parent._testsuites:
			raise DuplicateTestsuiteError(f"Build '{parent._name}' has test suite '{name}' twice (line {node.lc.line + 1}).")

		elapsedTime = node.get("ElapsedTime", None)
		testsuite = cls(
			name,
			totalDuration=None if elapsedTime is None else timedelta(seconds=float(elapsedTime)),
			parent=parent
		)

		for testcaseNode in node["TestCases"] or ():
			Testcase.Parse(testcaseNode, parent=testsuite)

		return testsuite

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
	"""
	The information about an OSVVM build (``BuildInfo``): when it finished, the simulator, the OSVVM version and the
	build's error counts.

	The build's start time and duration (``StartTime``, ``ElapsedTime``) are the
	:data:`~pyEDAA.Reports.Unittesting.Base.StartTime` and :data:`~pyEDAA.Reports.Unittesting.Base.TotalDuration` of
	the :class:`TestsuiteSummary`.
	"""

	_parent:             Nullable[TestsuiteSummary]  #: The build the information belongs to.
	_finishTime:         Nullable[datetime]          #: Time when the build finished.
	_simulator:          str                         #: Name of the simulator, followed by its arguments, if any.
	_simulatorVersion:   str                         #: Version of the simulator.
	_osvvmVersion:       YearMonthVersion            #: Version of OSVVM.
	_buildErrorCode:     int                         #: Error code of the build; ``0``, if the build succeeded.
	_analyzeErrorCount:  int                         #: Number of analysis errors.
	_simulateErrorCount: int                         #: Number of simulation errors.

	def __init__(
		self,
		simulator: str,
		simulatorVersion: str,
		osvvmVersion: YearMonthVersion,
		finishTime: Nullable[datetime] = None,
		buildErrorCode: int = 0,
		analyzeErrorCount: int = 0,
		simulateErrorCount: int = 0,
		*,
		parent: Nullable[TestsuiteSummary] = None
	) -> None:
		"""
		Initializes the information about an OSVVM build, and adds it to its build.

		The simulator's version is a string, because simulators number their versions in schemes of their own, e.g.
		``2023.4_2``.

		:param simulator:          Name of the simulator, followed by its arguments, if any (``Simulator``).
		:param simulatorVersion:   Version of the simulator (``SimulatorVersion``).
		:param osvvmVersion:       Version of OSVVM (``OsvvmVersion``).
		:param finishTime:         Optional, time when the build finished (``FinishTime``).
		:param buildErrorCode:     Optional, error code of the build (``BuildErrorCode``). Default: ``0``.
		:param analyzeErrorCount:  Optional, number of analysis errors (``AnalyzeErrorCount``). Default: ``0``.
		:param simulateErrorCount: Optional, number of simulation errors (``SimulateErrorCount``). Default: ``0``.
		:param parent:             Optional, the build the information belongs to.
		:raises ValueError:        If parameter 'simulator' is None.
		:raises ValueError:        If parameter 'simulatorVersion' is None.
		:raises ValueError:        If parameter 'osvvmVersion' is None.
		:raises TypeError:         If parameter 'simulator' is not of type :class:`str`.
		:raises TypeError:         If parameter 'simulatorVersion' is not of type :class:`str`.
		:raises TypeError:         If parameter 'osvvmVersion' is not of type
		                           :class:`~pyTooling.Versioning.YearMonthVersion`.
		:raises TypeError:         If parameter 'finishTime' is not of type :class:`~datetime.datetime`.
		:raises TypeError:         If parameter 'buildErrorCode' is not of type :class:`int`.
		:raises TypeError:         If parameter 'analyzeErrorCount' is not of type :class:`int`.
		:raises TypeError:         If parameter 'simulateErrorCount' is not of type :class:`int`.
		:raises TypeError:         If parameter 'parent' is not of type :class:`TestsuiteSummary`.
		:raises BuildSummaryError: If parameter 'parent' has build information already.
		"""
		for parameterName, text in (
			("simulator",        simulator),
			("simulatorVersion", simulatorVersion)
		):
			if text is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(text, str):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'str'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(text)}'.")
				raise ex

		if osvvmVersion is None:
			raise ValueError("Parameter 'osvvmVersion' is None.")
		elif not isinstance(osvvmVersion, YearMonthVersion):
			ex = TypeError("Parameter 'osvvmVersion' is not of type 'YearMonthVersion'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(osvvmVersion)}'.")
			raise ex

		if finishTime is not None and not isinstance(finishTime, datetime):
			ex = TypeError("Parameter 'finishTime' is not of type 'datetime'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(finishTime)}'.")
			raise ex

		for parameterName, count in (
			("buildErrorCode",     buildErrorCode),
			("analyzeErrorCount",  analyzeErrorCount),
			("simulateErrorCount", simulateErrorCount)
		):
			if not isinstance(count, int):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'int'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(count)}'.")
				raise ex

		if parent is not None:
			if not isinstance(parent, TestsuiteSummary):
				ex = TypeError("Parameter 'parent' is not of type 'TestsuiteSummary'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
				raise ex
			elif parent._buildInformation is not None:
				raise BuildSummaryError(f"Build '{parent._name}' has build information already.")

		self._parent =             parent
		self._finishTime =         finishTime
		self._simulator =          simulator
		self._simulatorVersion =   simulatorVersion
		self._osvvmVersion =       osvvmVersion
		self._buildErrorCode =     buildErrorCode
		self._analyzeErrorCount =  analyzeErrorCount
		self._simulateErrorCount = simulateErrorCount

		if parent is not None:
			parent._buildInformation = self

	@classmethod
	def Parse(cls, node: CommentedMap, *, parent: Nullable[TestsuiteSummary] = None) -> BuildInformation:
		"""
		Parse the information about a build (``BuildInfo``).

		The mapping must be valid according to the build summary's schema (:data:`SCHEMAS`). The build's start time and
		duration are read by :meth:`BuildSummaryDocument.Convert`.

		:param node:               The YAML mapping of the build information.
		:param parent:             Optional, the build the information belongs to.
		:returns:                  The build information.
		:raises BuildSummaryError: If the OSVVM version isn't a version ``YYYY.MM``, optionally followed by a revision
		                           letter.
		"""
		osvvmVersion = node["OsvvmVersion"]
		if (match := fullmatch(r"(\d{4})\.(\d{1,2})([a-z]?)", osvvmVersion)) is None:
			ex = BuildSummaryError(f"OSVVM version at line {node.lc.key('OsvvmVersion')[0] + 1} is not a version YYYY.MM.")
			ex.add_note(f"Got value '{osvvmVersion}'.")
			raise ex

		return cls(
			str(node["Simulator"]),
			str(node["SimulatorVersion"]),
			YearMonthVersion(int(match[1]), int(match[2]), postfix=None if match[3] == "" else match[3]),
			finishTime=datetime.fromisoformat(node["FinishTime"].isoformat()),
			buildErrorCode=int(node["BuildErrorCode"]),
			analyzeErrorCount=int(node["AnalyzeErrorCount"]),
			simulateErrorCount=int(node["SimulateErrorCount"]),
			parent=parent
		)

	@readonly
	def Parent(self) -> Nullable[TestsuiteSummary]:
		"""
		Read-only property to access the build the information belongs to (:attr:`_parent`).

		:returns: The build, or ``None`` if the information doesn't belong to one.
		"""
		return self._parent

	@readonly
	def FinishTime(self) -> Nullable[datetime]:
		"""
		Read-only property to access the time when the build finished (:attr:`_finishTime`).

		:returns: The finish time, or ``None`` if it wasn't recorded.
		"""
		return self._finishTime

	@readonly
	def Simulator(self) -> str:
		"""
		Read-only property to access the simulator's name, followed by its arguments, if any (:attr:`_simulator`).

		:returns: The simulator.
		"""
		return self._simulator

	@readonly
	def SimulatorVersion(self) -> str:
		"""
		Read-only property to access the simulator's version (:attr:`_simulatorVersion`).

		:returns: The simulator's version.
		"""
		return self._simulatorVersion

	@readonly
	def OSVVMVersion(self) -> YearMonthVersion:
		"""
		Read-only property to access OSVVM's version (:attr:`_osvvmVersion`).

		A revision letter of an OSVVM version, e.g. ``a`` of ``2025.06a``, is the version's postfix.

		:returns: OSVVM's version.
		"""
		return self._osvvmVersion

	@readonly
	def BuildErrorCode(self) -> int:
		"""
		Read-only property to access the build's error code (:attr:`_buildErrorCode`).

		:returns: The error code; ``0``, if the build succeeded.
		"""
		return self._buildErrorCode

	@readonly
	def AnalyzeErrorCount(self) -> int:
		"""
		Read-only property to access the number of analysis errors (:attr:`_analyzeErrorCount`).

		:returns: Number of analysis errors.
		"""
		return self._analyzeErrorCount

	@readonly
	def SimulateErrorCount(self) -> int:
		"""
		Read-only property to access the number of simulation errors (:attr:`_simulateErrorCount`).

		:returns: Number of simulation errors.
		"""
		return self._simulateErrorCount


@export
class Settings(metaclass=ExtendedType, slots=True):
	"""
	OSVVM's settings of a build (``OsvvmSettingsInfo``): where OSVVM put the build's reports and logs.

	Paths are relative to the build's directory. OSVVM writes an empty string for a file it didn't write; it is ``None``
	here.
	"""

	_parent:                   Nullable[TestsuiteSummary]  #: The build the settings belong to.
	_reportsSubdirectory:      _Path                       #: Directory of the reports.
	_simulationLogFile:        Nullable[_Path]             #: Log file of the build.
	_simulationHtmlLogFile:    Nullable[_Path]             #: Log file of the build in HTML.
	_requirementsSubdirectory: Nullable[_Path]             #: Directory of the requirements reports.
	_codeCoverageFile:         Nullable[_Path]             #: Code coverage report of the build.
	_cssFiles:                 list[_Path]                 #: Stylesheets of the HTML reports.
	_logoFile:                 Nullable[_Path]             #: Logo of the HTML reports.

	def __init__(
		self,
		reportsSubdirectory: Path,
		simulationLogFile: Nullable[Path] = None,
		simulationHtmlLogFile: Nullable[Path] = None,
		requirementsSubdirectory: Nullable[Path] = None,
		codeCoverageFile: Nullable[Path] = None,
		cssFiles: Nullable[Iterable[Path]] = None,
		logoFile: Nullable[Path] = None,
		*,
		parent: Nullable[TestsuiteSummary] = None
	) -> None:
		"""
		Initializes OSVVM's settings of a build, and adds them to their build.

		:param reportsSubdirectory:      Directory of the reports (``ReportsSubdirectory``).
		:param simulationLogFile:        Optional, log file of the build (``SimulationLogFile``).
		:param simulationHtmlLogFile:    Optional, log file of the build in HTML (``SimulationHtmlLogFile``).
		:param requirementsSubdirectory: Optional, directory of the requirements reports (``RequirementsSubdirectory``).
		:param codeCoverageFile:         Optional, code coverage report of the build (``CoverageSubdirectory``).
		:param cssFiles:                 Optional, stylesheets of the HTML reports (``Report2CssFiles``).
		:param logoFile:                 Optional, logo of the HTML reports (``Report2PngFile``).
		:param parent:                   Optional, the build the settings belong to.
		:raises ValueError:              If parameter 'reportsSubdirectory' is None.
		:raises TypeError:               If parameter 'reportsSubdirectory' is not of type :class:`~pathlib.Path`.
		:raises TypeError:               If parameter 'simulationLogFile' is not of type :class:`~pathlib.Path`.
		:raises TypeError:               If parameter 'simulationHtmlLogFile' is not of type :class:`~pathlib.Path`.
		:raises TypeError:               If parameter 'requirementsSubdirectory' is not of type :class:`~pathlib.Path`.
		:raises TypeError:               If parameter 'codeCoverageFile' is not of type :class:`~pathlib.Path`.
		:raises TypeError:               If parameter 'logoFile' is not of type :class:`~pathlib.Path`.
		:raises TypeError:               If parameter 'cssFiles' is not iterable.
		:raises TypeError:               If an element of parameter 'cssFiles' is not of type :class:`~pathlib.Path`.
		:raises TypeError:               If parameter 'parent' is not of type :class:`TestsuiteSummary`.
		:raises BuildSummaryError:       If parameter 'parent' has settings already.
		"""
		if reportsSubdirectory is None:
			raise ValueError("Parameter 'reportsSubdirectory' is None.")
		elif not isinstance(reportsSubdirectory, Path):
			ex = TypeError("Parameter 'reportsSubdirectory' is not of type 'Path'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(reportsSubdirectory)}'.")
			raise ex

		for parameterName, path in (
			("simulationLogFile",        simulationLogFile),
			("simulationHtmlLogFile",    simulationHtmlLogFile),
			("requirementsSubdirectory", requirementsSubdirectory),
			("codeCoverageFile",         codeCoverageFile),
			("logoFile",                 logoFile)
		):
			if path is not None and not isinstance(path, Path):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'Path'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(path)}'.")
				raise ex

		self._cssFiles = cssFileList = []
		if cssFiles is not None:
			if not isinstance(cssFiles, Iterable):
				ex = TypeError("Parameter 'cssFiles' is not iterable.")
				ex.add_note(f"Got type '{getFullyQualifiedName(cssFiles)}'.")
				raise ex

			for cssFile in cssFiles:
				if not isinstance(cssFile, Path):
					ex = TypeError("Element of parameter 'cssFiles' is not of type 'Path'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(cssFile)}'.")
					raise ex

				cssFileList.append(cssFile)

		if parent is not None:
			if not isinstance(parent, TestsuiteSummary):
				ex = TypeError("Parameter 'parent' is not of type 'TestsuiteSummary'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
				raise ex
			elif parent._settings is not None:
				raise BuildSummaryError(f"Build '{parent._name}' has settings already.")

		self._parent =                   parent
		self._reportsSubdirectory =      reportsSubdirectory
		self._simulationLogFile =        simulationLogFile
		self._simulationHtmlLogFile =    simulationHtmlLogFile
		self._requirementsSubdirectory = requirementsSubdirectory
		self._codeCoverageFile =         codeCoverageFile
		self._logoFile =                 logoFile

		if parent is not None:
			parent._settings = self

	@classmethod
	def Parse(cls, node: CommentedMap, *, parent: Nullable[TestsuiteSummary] = None) -> Settings:
		"""
		Parse OSVVM's settings of a build (``OsvvmSettingsInfo``).

		The mapping must be valid according to the build summary's schema (:data:`SCHEMAS`).

		:param node:   The YAML mapping of the settings.
		:param parent: Optional, the build the settings belong to.
		:returns:      The settings.
		"""
		cssFiles = node["Report2CssFiles"]

		return cls(
			Path(node["ReportsSubdirectory"]),
			simulationLogFile=None if (path := node["SimulationLogFile"]) == "" else Path(path),
			simulationHtmlLogFile=None if (path := node["SimulationHtmlLogFile"]) == "" else Path(path),
			requirementsSubdirectory=None if (path := node["RequirementsSubdirectory"]) == "" else Path(path),
			codeCoverageFile=None if (path := node["CoverageSubdirectory"]) == "" else Path(path),
			cssFiles=None if cssFiles == "" else (Path(cssFile) for cssFile in cssFiles),
			logoFile=None if (path := node["Report2PngFile"]) == "" else Path(path),
			parent=parent
		)

	@readonly
	def Parent(self) -> Nullable[TestsuiteSummary]:
		"""
		Read-only property to access the build the settings belong to (:attr:`_parent`).

		:returns: The build, or ``None`` if the settings don't belong to one.
		"""
		return self._parent

	@readonly
	def ReportsSubdirectory(self) -> Path:
		"""
		Read-only property to access the directory of the reports (:attr:`_reportsSubdirectory`).

		A test case's reports are in a subdirectory per test suite, e.g. :file:`reports/<testsuite>/`.

		:returns: The directory of the reports.
		"""
		return self._reportsSubdirectory

	@readonly
	def SimulationLogFile(self) -> Nullable[Path]:
		"""
		Read-only property to access the build's log file (:attr:`_simulationLogFile`).

		:returns: The log file, or ``None`` if OSVVM wrote none.
		"""
		return self._simulationLogFile

	@readonly
	def SimulationHtmlLogFile(self) -> Nullable[Path]:
		"""
		Read-only property to access the build's log file in HTML (:attr:`_simulationHtmlLogFile`).

		:returns: The HTML log file, or ``None`` if OSVVM wrote none.
		"""
		return self._simulationHtmlLogFile

	@readonly
	def RequirementsSubdirectory(self) -> Nullable[Path]:
		"""
		Read-only property to access the directory of the requirements reports (:attr:`_requirementsSubdirectory`).

		:returns: The directory, or ``None`` if the build has no requirements.
		"""
		return self._requirementsSubdirectory

	@readonly
	def CodeCoverageFile(self) -> Nullable[Path]:
		"""
		Read-only property to access the build's code coverage report (:attr:`_codeCoverageFile`).

		OSVVM names the key ``CoverageSubdirectory``, but states the report's file, e.g.
		:file:`CodeCoverage/<build>_code_cov/index.html`.

		:returns: The code coverage report, or ``None`` if the build didn't collect code coverage.
		"""
		return self._codeCoverageFile

	@readonly
	def CssFiles(self) -> list[Path]:
		"""
		Read-only property to access the stylesheets of the HTML reports (:attr:`_cssFiles`).

		:returns: List of stylesheets.
		"""
		return self._cssFiles

	@readonly
	def LogoFile(self) -> Nullable[Path]:
		"""
		Read-only property to access the logo of the HTML reports (:attr:`_logoFile`).

		:returns: The logo, or ``None`` if OSVVM states none.
		"""
		return self._logoFile


# ``BuildInformation`` and ``Settings`` are also property names of :class:`TestsuiteSummary`.
_BuildInformation = BuildInformation
_Settings =         Settings


@export
class TestsuiteSummary(ut_TestsuiteSummary):
	"""
	An OSVVM build: the root of the build's test entity hierarchy.

	Besides its test suites, a build has the :class:`BuildInformation` and OSVVM's :class:`Settings`.
	"""

	_buildInformation: Nullable[_BuildInformation]  #: Information about the build.
	_settings:         Nullable[_Settings]          #: OSVVM's settings of the build.

	def __init__(
		self,
		name: str,
		title: Nullable[str] = None,
		summary: Nullable[str] = None,
		description: Nullable[str] = None,
		startTime: Nullable[datetime] = None,
		totalDuration: Nullable[timedelta] = None,
		testsuites: Nullable[Iterable[Testsuite]] = None,
		keyValuePairs: Nullable[Mapping[str, Any]] = None
	) -> None:
		"""
		Initializes an OSVVM build.

		The build information and the settings are added by creating them with the build as parent.

		:param name:          Name of the build (``Name``).
		:param title:         Optional, short label of the build, written for a reader.
		:param summary:       Optional, summary of the build.
		:param description:   Optional, description of the build.
		:param startTime:     Optional, time when the build started (``StartTime`` of ``BuildInfo``).
		:param totalDuration: Optional, duration of the build (``ElapsedTime`` of ``BuildInfo``).
		:param testsuites:    Optional, test suites of the build.
		:param keyValuePairs: Optional, mapping of key-value pairs to initialize the build with.
		"""
		super().__init__(
			name,
			title, summary, description,
			startTime, None, None, None, totalDuration,
			TestsuiteStatus.Unknown,
			0, 0, 0,
			testsuites,
			keyValuePairs
		)

		self._buildInformation = None
		self._settings =         None

	@readonly
	def BuildInformation(self) -> Nullable[BuildInformation]:
		"""
		Read-only property to access the information about the build (:attr:`_buildInformation`).

		:returns: The build information, or ``None`` if it wasn't recorded.
		"""
		return self._buildInformation

	@readonly
	def Settings(self) -> Nullable[Settings]:
		"""
		Read-only property to access OSVVM's settings of the build (:attr:`_settings`).

		:returns: The settings, or ``None`` if they weren't recorded.
		"""
		return self._settings

	def ToTestsuiteSummary(self) -> ut_TestsuiteSummary:
		"""
		Convert the build and its test suites to a test suite summary of the unified test entity model.

		Call :meth:`Aggregate` before, so the unified status of each test case is computed.

		:returns: A test suite summary of the unified test entity model.
		"""
		return ut_TestsuiteSummary(
			self._name,
			startTime=self._startTime,
			totalDuration=self._totalDuration,
			status=self._status,
			testsuites=(testsuite.ToTestsuite() for testsuite in self._testsuites.values()),
			keyValuePairs=self._dict
		)


SCHEMAS: dict[FormatVersion, str] = {
	FormatVersion.Version0_1: "OSVVM-BuildSummary-0.1.schema.json",
}  #: The JSON Schema of :mod:`pyEDAA.OSVVM.Resources` a build summary is validated against, per format version.


@export
class BuildSummaryDocument(TestsuiteSummary, ut_Document, YAMLDocumentMixin):
	"""
	An OSVVM build summary file :file:`<build>.yml`: read and converted to the build's test entity hierarchy.

	:meth:`Analyze` validates the file against the schema of the format version it states (:data:`SCHEMAS`),
	:meth:`Convert` converts it by the ``Parse`` classmethods of the model's classes, e.g. :meth:`Testsuite.Parse`.
	"""

	_DESCRIPTION:    ClassVar[str] =                                "OSVVM build summary"  #: Format's name in messages.
	_ERROR:          ClassVar[type[BuildSummaryError]] =            BuildSummaryError      #: Exception of the reader.
	_FORMAT_VERSION: ClassVar[type[FormatVersion]] =                FormatVersion          #: The format's versions.
	_SCHEMAS:        ClassVar[dict[FormatVersion, str]] =           SCHEMAS                #: Schema per version.

	_date:           Nullable[datetime]  #: Time when OSVVM started to write the file (``Date``).

	def __init__(self, yamlReportFile: Path, analyzeAndConvert: bool = False) -> None:
		"""
		Initializes a build summary document, and optionally reads it.

		:param yamlReportFile:    Path to the YAML file.
		:param analyzeAndConvert: Optional, if true, analyze the file and convert its content. Default: ``False``.
		"""
		super().__init__("Unprocessed OSVVM YAML file")
		YAMLDocumentMixin.__init__(self)

		self._date = None

		ut_Document.__init__(self, yamlReportFile, analyzeAndConvert)

	@readonly
	def Date(self) -> Nullable[datetime]:
		"""
		Read-only property to access the time when OSVVM started to write the file (:attr:`_date`).

		:returns: The date, or ``None`` if the file wasn't converted yet.
		"""
		return self._date

	def Analyze(self) -> None:
		"""
		Analyze the YAML file: parse it, read its format version and validate it against the version's JSON Schema.

		The schema is chosen from :data:`SCHEMAS` by the format version the file states. A key the schema doesn't define
		is an error.

		.. hint::

		   The time spend for analysis will be made available via property :data:`AnalysisDuration`.

		:raises BuildSummaryError: If the file doesn't exist.
		:raises BuildSummaryError: If the file can't be read.
		:raises BuildSummaryError: If the file isn't UTF-8 encoded.
		:raises BuildSummaryError: If the file isn't valid YAML.
		:raises BuildSummaryError: If the file's content isn't a YAML mapping.
		:raises BuildSummaryError: If the file states no format version. |br|
		                           The note lists the supported format versions.
		:raises BuildSummaryError: If the file states an unsupported format version. |br|
		                           The note lists the supported format versions.
		:raises BuildSummaryError: If the JSON Schema can't be read.
		:raises BuildSummaryError: If the file isn't valid according to the JSON Schema. |br|
		                           A note per violation names its path and line.
		"""
		with Stopwatch() as sw:
			self._AnalyzeYAML()

		self._analysisDuration = sw.Duration

	def Convert(self) -> None:
		"""
		Convert the analyzed YAML data structure into the build's test entity hierarchy, and aggregate it.

		.. hint::

		   The time spend for model conversion will be made available via property :data:`ModelConversionDuration`.

		:raises BuildSummaryError:       If the YAML file was not analyzed before. |br|
		                                 Call 'Document.Analyze()' or create the document using
		                                 'Document(path, analyzeAndConvert=True)'.
		:raises BuildSummaryError:       If a value can't be converted, e.g. an unknown test case status.
		:raises DuplicateTestsuiteError: If the file states a test suite twice.
		:raises DuplicateTestcaseError:  If a test suite states a test case twice.
		"""
		if self._yamlDocument is None:
			ex = BuildSummaryError(f"OSVVM build summary '{self._path}' needs to be read and analyzed by a YAML parser.")
			ex.add_note("Call 'Document.Analyze()' or create the document using 'Document(path, analyzeAndConvert=True)'.")
			raise ex

		with Stopwatch() as sw:
			root =      self._yamlDocument
			buildInfo = root["BuildInfo"]

			self._date =          datetime.fromisoformat(root["Date"].isoformat())
			self._name =          str(root["Name"])
			self._startTime =     datetime.fromisoformat(buildInfo["StartTime"].isoformat())
			self._totalDuration = timedelta(seconds=float(buildInfo["ElapsedTime"]))

			BuildInformation.Parse(buildInfo, parent=self)
			Settings.Parse(root["OsvvmSettingsInfo"], parent=self)

			for testsuiteNode in root.get("TestSuites", None) or ():
				Testsuite.Parse(testsuiteNode, parent=self)

			self.Aggregate()

		self._modelConversion = sw.Duration
