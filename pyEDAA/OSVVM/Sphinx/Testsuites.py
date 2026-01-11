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
# Copyright 2025-2026 Patrick Lehmann - Bötzingen, Germany                                                             #
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
**Report build results as Sphinx documentation page(s).**
"""
from datetime import timedelta
from enum     import Flag
from pathlib  import Path
from typing   import Dict, Tuple, Any, List, Mapping, Generator, TypedDict, ClassVar, Optional as Nullable

from docutils                          import nodes
from docutils.parsers.rst.directives   import flag
from sphinx.config                     import Config
from sphinx.application                import Sphinx
from pyTooling.Decorators              import export
from pyEDAA.Reports.Unittesting        import TestcaseStatus, TestsuiteStatus
from sphinx_reports.Common             import ReportExtensionError
from sphinx_reports.Sphinx             import strip, BaseDirective, stripAndNormalize

from pyEDAA.OSVVM.Build                import BuildSummaryDocument, TestsuiteSummary, Testsuite, Testcase


class report_DictType(TypedDict):
	yaml_report: Path


@export
class ShowTestcases(Flag):
	passed = 1
	failed = 2
	skipped = 4
	excluded = 8
	errors = 16
	aborted = 32

	all = passed | failed | skipped | excluded | errors | aborted
	not_passed = all & ~passed

	def __eq__(self, other):
		if isinstance(other, TestcaseStatus):
			if other is TestcaseStatus.Passed:
				return ShowTestcases.passed in self
			elif other is TestcaseStatus.Failed:
				return ShowTestcases.failed in self
			elif other is TestcaseStatus.Skipped:
				return ShowTestcases.skipped in self
			elif other is TestcaseStatus.Excluded:
				return ShowTestcases.excluded in self
			elif other is TestcaseStatus.Errored or other is TestcaseStatus.SetupError:
				return ShowTestcases.errors in self
			elif other is TestcaseStatus.Aborted:
				return ShowTestcases.aborted in self

		return False


@export
class BuildSummary(BaseDirective):
	"""
	This directive will be replaced by a table representing unit test results.
	"""
	has_content = False
	required_arguments = 0
	optional_arguments = 6

	option_spec = {
		"class":              strip,
		"reportid":           stripAndNormalize,
		"build-name":         strip,
		"show-testcases":     stripAndNormalize,
		"hide-build-summary": flag
	}

	directiveName: str = "build-summary"
	configPrefix:  str = "build_summaries"
	configValues:  Dict[str, Tuple[Any, str, Any]] = {
		f"{configPrefix}": ({}, "env", Dict)
	}  #: A dictionary of all configuration values used by unittest directives.

	_buildSummaries:       ClassVar[Dict[str, report_DictType]] = {}

	_cssClasses:           List[str]
	_reportID:             str
	_hideTestsuiteSummary: bool
	_buildName:            Nullable[str]
	_showTestcases:        ShowTestcases
	_yamlReport:           Path
	_build:                TestsuiteSummary

	def _CheckOptions(self) -> None:
		"""
		Parse all directive options or use default values.
		"""
		cssClasses = self._ParseStringOption("class", "", r"(\w+)?( +\w+)*")
		showTestcases = self._ParseStringOption("show-testcases", "all", r"all|not-passed")

		self._cssClasses = [] if cssClasses == "" else cssClasses.split(" ")
		self._reportID = self._ParseStringOption("reportid")
		self._buildName = self._ParseStringOption("build-name", "", r".+")
		self._showTestcases = ShowTestcases[showTestcases.replace("-", "_")]
		self._hideTestsuiteSummary = "hide-build-summary" in self.options

		try:
			buildSummary = self._buildSummaries[self._reportID]
		except KeyError as ex:
			raise ReportExtensionError(f"No build summary configuration item for '{self._reportID}'.") from ex
		self._yamlReport = buildSummary["yaml_report"]

	@classmethod
	def CheckConfiguration(cls, sphinxApplication: Sphinx, sphinxConfiguration: Config) -> None:
		"""
		Check configuration fields and load necessary values.

		:param sphinxApplication:   Sphinx application instance.
		:param sphinxConfiguration: Sphinx configuration instance.
		"""
		cls._CheckConfiguration(sphinxConfiguration)

	@classmethod
	def ReadReports(cls, sphinxApplication: Sphinx) -> None:
		"""
		Read build report files.

		:param sphinxApplication:   Sphinx application instance.
		"""
		print(f"[REPORT] Reading build reports ...")

	@classmethod
	def _CheckConfiguration(cls, sphinxConfiguration: Config) -> None:
		from pyEDAA.OSVVM.Sphinx import OSVVMDomain

		variableName = f"{OSVVMDomain.name}_{cls.configPrefix}"

		try:
			allBuildReports: Dict[str, report_DictType] = sphinxConfiguration[f"{OSVVMDomain.name}_{cls.configPrefix}"]
		except (KeyError, AttributeError) as ex:
			raise ReportExtensionError(f"Configuration option '{variableName}' is not configured.") from ex

		# try:
		# 	testsuiteConfiguration = allBuildReports[self._reportID]
		# except KeyError as ex:
		# 	raise ReportExtensionError(f"conf.py: {OSVVMDomain.name}_{self.configPrefix}: No configuration found for '{self._reportID}'.") from ex

		for reportID, buildReport in allBuildReports.items():
			buildReportName = f"conf.py: {variableName}:[{reportID}]"

			try:
				yamlReport = Path(buildReport["yaml_report"])
			except KeyError as ex:
				raise ReportExtensionError(f"{buildReportName}.yaml_report: Configuration is missing.") from ex

			if not yamlReport.exists():
				raise ReportExtensionError(f"{buildReportName}.yaml_report: OSVVM Build Report file '{yamlReport}' doesn't exist.") from FileNotFoundError(yamlReport)

			cls._buildSummaries[reportID] = {
				"yaml_report": yamlReport
			}

	def _sortedValues(self, d: Mapping[str, Testsuite]) -> Generator[Testsuite, None, None]:
		for key in sorted(d.keys()):
			yield d[key]

	def _convertTestcaseStatusToSymbol(self, status: TestcaseStatus) -> str:
		if status is TestcaseStatus.Passed:
			return "✅"
		elif status is TestcaseStatus.Failed:
			return "❌"
		elif status is TestcaseStatus.Skipped:
			return "⚠️"
		elif status is TestcaseStatus.Aborted:
			return "🚫"
		elif status is TestcaseStatus.Excluded:
			return "➖"
		elif status is TestcaseStatus.Errored:
			return "❗"
		elif status is TestcaseStatus.SetupError:
			return "⛔"
		elif status is TestcaseStatus.Unknown:
			return "❓"
		else:
			return "❌"

	def _convertTestsuiteStatusToSymbol(self, status: TestsuiteStatus) -> str:
		if status is TestsuiteStatus.Passed:
			return "✅"
		elif status is TestsuiteStatus.Failed:
			return "❌"
		elif status is TestsuiteStatus.Skipped:
			return "⚠️"
		elif status is TestsuiteStatus.Aborted:
			return "🚫"
		elif status is TestsuiteStatus.Excluded:
			return "➖"
		elif status is TestsuiteStatus.Errored:
			return "❗"
		elif status is TestsuiteStatus.SetupError:
			return "⛔"
		elif status is TestsuiteStatus.Unknown:
			return "❓"
		else:
			return "❌"

	def _formatTimedelta(self, delta: timedelta) -> str:
		if delta is None:
			return ""

		# Compute by hand, because timedelta._to_microseconds is not officially documented
		microseconds = (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds
		milliseconds = (microseconds + 500) // 1000
		seconds = milliseconds // 1000
		minutes = seconds // 60
		hours = minutes // 60
		return f"{hours:02}:{minutes % 60:02}:{seconds % 60:02}.{milliseconds % 1000:03}"

	def _GenerateBuildSummaryTable(self) -> nodes.Element:
		columns = [
			("Testsuite", (
				("  Testcase", 50),
			), None),
			("Testsuite Status", (
				("Skipped", 50),
				("Errored", 50),
				("Failed", 50),
				("Passed", 50),
				("Testcases", 50),
			), None),
			("Warnings", (
				("Counted", 50),
				("Expected", 50),
			), None),
			("Errors", (
				("Counted", 50),
				("Expected", 50),
			), None),
			("Failures", (
				("Counted", 50),
				("Expected", 50),
			), None),
			("Assertions", (
				("passed", 50),
				("Total", 50),
			), None),
			("Requirements", (
				("Passed", 50),
				("Total", 50),
			), None),
			("Coverage", (
				("Code", 50),
				("Functional", 50),
			), None),
			("Runtime (HH:MM:SS.sss)", None, 100),
		]

		cssClasses = ["osvvm-buildsummary-table", f"osvvm-buildsummary-{self._reportID}"]
		cssClasses.extend(self._cssClasses)

		tableGroup = self._CreateDoubleRowTableHeader(
			identifier=self._reportID,
			columns=columns,
			classes=cssClasses
		)
		tableGroup += (tableBody := nodes.tbody())

		self.renderRoot(tableBody, self._build, not self._hideTestsuiteSummary, self._buildName)

		return tableGroup.parent

	def renderRoot(self, tableBody: nodes.tbody, testsuiteSummary: TestsuiteSummary, includeRoot: bool = True, testsuiteSummaryName: Nullable[str] = None) -> None:
		level = 0

		if includeRoot:
			level += 1
			state = self._convertTestsuiteStatusToSymbol(testsuiteSummary._status)

			tableRow = nodes.row("", classes=["osvvm-buildsummary", f"buildsummary-{testsuiteSummary._status.name.lower()}"])
			tableBody += tableRow

			tableRow += nodes.entry("", nodes.Text(f"{state}{testsuiteSummary.Name if testsuiteSummaryName == '' else testsuiteSummaryName}"))
			tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.TestcaseCount}"))
			tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.Skipped}"))
			tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.Errored}"))
			tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.Failed}"))
			tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.Passed}"))
			for _ in range(12):
				tableRow += nodes.entry()
			tableRow += nodes.entry("", nodes.Text(f"{self._formatTimedelta(testsuiteSummary.TotalDuration)}"))

		for ts in self._sortedValues(testsuiteSummary._testsuites):
			self.renderTestsuite(tableBody, ts, level)

		self.renderSummary(tableBody, testsuiteSummary)

	def renderTestsuite(self, tableBody: nodes.tbody, testsuite: Testsuite, level: int) -> None:
		state = self._convertTestsuiteStatusToSymbol(testsuite._status)

		tableBody += (tableRow := nodes.row("", classes=["osvvm-testsuite", f"testsuite-{testsuite._status.name.lower()}"]))
		tableRow += nodes.entry("", nodes.Text(f"{'  ' * level}{state}{testsuite.Name}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuite.TestcaseCount}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuite.Skipped}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuite.Errored}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuite.Failed}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuite.Passed}"))
		for _ in range(12):
			tableRow += nodes.entry()
		tableRow += nodes.entry("", nodes.Text(f"{self._formatTimedelta(testsuite.TotalDuration)}"))

		for ts in self._sortedValues(testsuite._testsuites):
			self.renderTestsuite(tableBody, ts, level + 1)

		for testcase in self._sortedValues(testsuite._testcases):
			# if testcase._status == self._showTestcases:
				self.renderTestcase(tableBody, testcase, level)

	def renderTestcase(self, tableBody: nodes.tbody, testcase: Testcase, level: int) -> None:
		state = self._convertTestcaseStatusToSymbol(testcase._status)

		def countVsExpected(count: int, expectedCount: int, kind: str) -> Tuple[nodes.entry, nodes.entry]:
			classes = []
			if count == expectedCount == 0:
				text = f"⸻"
			else:
				if count != expectedCount:
					classes = [f"osvvm-{kind}-mismatch"]

			return (
				nodes.entry("", nodes.paragraph(text=f"{count}"),         classes=classes),
				nodes.entry("", nodes.paragraph(text=f"{expectedCount}"), classes=classes)
			)

		def functionalCoverage(percent: float, kind: str) -> nodes.entry:
			classes = []
			if percent is None:
				text = f"⸻"
			else:
				text = f"{percent * 100:.1f}"

			return nodes.entry("", nodes.paragraph(text=text), classes=classes)

		warningCell,     expectedWarningCell =     countVsExpected(testcase.WarningCount, testcase.ExpectedWarningCount, "warning")
		errorCell,       expectedErrorCell =       countVsExpected(testcase.ErrorCount, testcase.ExpectedErrorCount, "error")
		failureCell,     expectedFailureCell =     countVsExpected(testcase.FatalCount, testcase.ExpectedFatalCount, "failure")
		assertionCell,   expectedAssertionCell =   countVsExpected(testcase.PassedAssertionCount, testcase.AssertionCount, "assertion")
		requirementCell, expectedRequirementCell = countVsExpected(testcase.PassedAssertionCount, testcase.AssertionCount, "requirement")
		coverageCell, _ =    countVsExpected(testcase.PassedAssertionCount, testcase.AssertionCount, "assertion")
		# tableRow += countVsExpected(testcase.PassedRequirementsCount, testcase.RequirementsCount, "requirement")
		# tableRow += functionalCoverage(testcase.FunctionalCoverage)

		classes = ["osvvm-testcase", f"testcase-{testcase._status.name.lower()}"]
		classes.extend(warningCell["classes"])
		classes.extend(errorCell["classes"])
		classes.extend(failureCell["classes"])
		classes.extend(assertionCell["classes"])
		classes.extend(requirementCell["classes"])
		classes.extend(coverageCell["classes"])

		tableRow =	nodes.row("", classes=classes)
		tableBody += tableRow

		tableRow += nodes.entry("", nodes.Text(f"{'  ' * level}{state}{testcase.Name}"))
		for _ in range(5):
			tableRow += nodes.entry()
		tableRow += warningCell
		tableRow += expectedWarningCell
		tableRow += errorCell
		tableRow += expectedErrorCell
		tableRow += failureCell
		tableRow += expectedFailureCell
		tableRow += assertionCell
		tableRow += expectedAssertionCell
		tableRow += requirementCell
		tableRow += expectedRequirementCell
		tableRow += coverageCell
		tableRow += coverageCell
		tableRow += nodes.entry("", nodes.Text(f"{self._formatTimedelta(testcase.TotalDuration)}"))

	def renderSummary(self, tableBody: nodes.tbody, testsuiteSummary: TestsuiteSummary) -> None:
		state = self._convertTestsuiteStatusToSymbol(testsuiteSummary._status)

		tableRow = nodes.row("", classes=["osvvm-summary", f"testsuitesummary-{testsuiteSummary._status.name.lower()}"])
		tableBody += tableRow

		tableRow += nodes.entry("", nodes.Text(f"{state} {testsuiteSummary.Status.name.upper()}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.TestcaseCount}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.Skipped}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.Errored}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.Failed}"))
		tableRow += nodes.entry("", nodes.Text(f"{testsuiteSummary.Passed}"))
		for _ in range(12):
			tableRow += nodes.entry()
		tableRow += nodes.entry("", nodes.Text(f"{self._formatTimedelta(testsuiteSummary.TotalDuration)}"))

	def run(self) -> List[nodes.Node]:
		container = nodes.container()

		try:
			self._CheckOptions()
		except ReportExtensionError as ex:
			message = f"Caught {ex.__class__.__name__} when checking options for directive '{self.directiveName}'."
			return self._internalError(container, __name__, message, ex)

		# Assemble a list of Python source files
		try:
			self._build = BuildSummaryDocument(self._yamlReport, analyzeAndConvert=True)
		except Exception as ex:
			message = f"Caught {ex.__class__.__name__} when reading and parsing '{self._yamlReport}'."
			return self._internalError(container, __name__, message, ex)

		try:
			container += self._GenerateBuildSummaryTable()
		except Exception as ex:
			message = f"Caught {ex.__class__.__name__} when generating the document structure for JUnit document '{self._yamlReport}'."
			return self._internalError(container, __name__, message, ex)

		return [container]
