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
A page per testsuite and per testcase of an OSVVM build summary, generated without a source file.

A build summary declared in ``osvvm_build_summaries`` with the key ``pages`` gets a document per testsuite and per
testcase, named below that key's document name: ``<pages>/<testsuite>`` and ``<pages>/<testsuite>/<testcase>``. The
pages are pyTooling.Sphinx' unit test pages (:class:`~pyTooling.Sphinx.UnittestPages.UnittestReportPages`), with what
OSVVM states:

* A testcase's page shows its status, OSVVM status, elapsed and simulation time, checks, alerts, requirements,
  functional coverage, generics and links to its YAML reports and transcripts; then the reason of a skipped testcase or
  of an expected or known status, and its AlertLog, functional coverage and scoreboards as the directives
  ``osvvm:alert-log``, ``osvvm:functional-coverage`` and ``osvvm:scoreboards`` show them.
* A testsuite's page shows its counts, and a table of its testcases with their checks, alerts, requirements, functional
  coverage and simulation time, each linked to its page.

The directive ``osvvm:build-summary`` links every testsuite and testcase to its page, and lists the testsuites in a
hidden table of contents, so the pages are in the navigation below its document. Every testsuite and testcase with a
page is an object of domain ``osvvm``, referred to by the roles ``:osvvm:ts:`` and ``:osvvm:tc:``.
"""
from __future__                             import annotations

from os.path                                import relpath
from pathlib                                import Path
from typing                                 import TYPE_CHECKING, ClassVar

from docutils                               import nodes
from sphinx                                 import addnodes
from sphinx.application                     import Sphinx
from sphinx.util.logging                    import getLogger

from pyTooling.Common                       import getTypeName
from pyTooling.Decorators                   import export
from pyTooling.Sphinx                       import ReportExtensionError
from pyTooling.Sphinx.UnittestPages         import UnittestReportPages

from pyEDAA.OSVVM.Sphinx.AlertLog           import AlertLogTable
from pyEDAA.OSVVM.Sphinx.FunctionalCoverage import FunctionalCoverageTables
from pyEDAA.OSVVM.Sphinx.Scoreboard         import ScoreboardTables
from pyEDAA.OSVVM.Sphinx.Testcase           import createCell, TestcaseReports
from pyEDAA.OSVVM.Sphinx.Testsuites         import BuildSummary, formatSimulationTime

if TYPE_CHECKING:  # pragma: no cover
	from pyEDAA.OSVVM.Build                  import BuildSummaryDocument, Testcase


@export
class BuildReportPages(UnittestReportPages):
	"""
	The pages of one OSVVM build summary: a page per testsuite and per testcase, objects of domain ``osvvm``.
	"""

	_DOMAIN: ClassVar[str] = "osvvm"                     #: The pages' objects belong to domain ``osvvm``.
	_pages:  ClassVar[dict[str, BuildReportPages]] = {}  #: The pages of every build summary, by report ID.

	_build:           BuildSummaryDocument  #: The build summary.
	_sourceDirectory: Path                  #: The documentation's source directory.

	def __init__(
		self,
		reportID: str,
		prefix: str,
		yamlReport: Path,
		build: BuildSummaryDocument,
		sourceDirectory: Path
	) -> None:
		"""
		Compute the document names and entries of a build summary's testsuites and testcases.

		:param reportID:        Identifier of the build summary.
		:param prefix:          Document name the pages are generated below.
		:param yamlReport:      The build summary file.
		:param build:           The build summary.
		:param sourceDirectory: The documentation's source directory.
		"""
		super().__init__(reportID, prefix, yamlReport, build)

		self._build =           build
		self._sourceDirectory = sourceDirectory

	@classmethod
	def CreatePages(cls, sphinxApplication: Sphinx) -> None:
		"""
		Call-back for Sphinx' ``builder-inited`` event, after the build summaries are read: compute and register the pages.

		Only a build summary with the key ``pages`` gets pages. A build summary that couldn't be read gets none; this is
		logged as an error.

		:param sphinxApplication: Sphinx application instance.
		"""
		cls._pages = {}
		for reportID, configuration in BuildSummary._testSummaries.items():
			if (prefix := configuration["pages"]) is None:
				continue

			try:
				build = BuildSummary.GetReport(reportID)
			except ReportExtensionError as ex:
				cause = ex if ex.__cause__ is None else ex.__cause__
				getLogger(__name__).error(
					f"Caught {getTypeName(ex)} when generating the pages of build summary '{reportID}'.\n"
					f"  {getTypeName(cause)}: {cause}"
				)
				continue

			pages = cls(reportID, prefix, configuration["yaml_report"], build, Path(sphinxApplication.srcdir))
			cls._pages[reportID] = pages
			pages.Register(sphinxApplication.env)

	def _TestcaseFields(self, fieldList: nodes.field_list, docName: str, testcase: Testcase) -> None:
		"""
		Add the fields of a testcase's summary: the status and what OSVVM states, its testsuite and its report files.

		:param fieldList: The summary's field list.
		:param docName:   Name of the testcase page's document.
		:param testcase:  The testcase.
		"""
		status = testcase._status
		symbol = BuildSummary._ConvertTestcaseStatusToSymbol(status)
		self._Field(fieldList, "Status", nodes.Text(f"{symbol} {status.name}"))
		if (cell := BuildSummary._Status(testcase)).astext() != "":
			self._Field(fieldList, "OSVVM Status", nodes.Text(cell.astext()))

		self._Field(fieldList, "Elapsed Time", nodes.Text(BuildSummary._FormatTimedelta(testcase._totalDuration)))
		if (simulationTime := testcase.SimulationTime) is not None:
			self._Field(fieldList, "Simulation Time", nodes.Text(formatSimulationTime(simulationTime)))

		if testcase._assertionCount is not None:
			passed = testcase.PassedAssertionCount or 0
			checks = testcase.AssertionCount
			self._Field(fieldList, "Checks", nodes.Text(f"{checks} - {passed} passed, {checks - passed} failed"))
			self._Field(fieldList, "Alerts", nodes.Text(self._Alerts(
				testcase.FatalCount, testcase.ErrorCount, testcase.WarningCount
			)))
			self._Field(fieldList, "Expected Alerts", nodes.Text(self._Alerts(
				testcase.ExpectedFatalCount or 0, testcase.ExpectedErrorCount or 0, testcase.ExpectedWarningCount or 0
			)))
			self._Field(fieldList, "Disabled Alerts", nodes.Text(self._Alerts(
				testcase.DisabledFatalCount, testcase.DisabledErrorCount, testcase.DisabledWarningCount
			)))

		if testcase.RequirementsGoalCount > 0:
			self._Field(
				fieldList, "Requirements",
				nodes.Text(f"{testcase.PassedRequirementsCount} of {testcase.RequirementsGoalCount} passed")
			)

		if (coverage := testcase.FunctionalCoverage) is not None:
			self._Field(fieldList, "Functional Coverage", nodes.Text(f"{coverage * 100:.1f} %"))

		if len(testcase.Generics) > 0:
			generics = ", ".join(f"{name}={value}" for name, value in testcase.Generics.items())
			self._Field(fieldList, "Generics", nodes.Text(generics))

		self._Field(fieldList, "Testsuite", self._Reference("ts", testcase._parent, docName))
		if len(links := self._ReportLinks(docName, testcase)) > 0:
			self._Field(fieldList, "Reports", *links)

	@staticmethod
	def _Alerts(failures: int, errors: int, warnings: int) -> str:
		"""
		Write the counts of an alert count.

		:param failures: Number of failures.
		:param errors:   Number of errors.
		:param warnings: Number of warnings.
		:returns:        The counts, e.g. ``0 failures, 2 errors, 1 warnings``.
		"""
		return f"{failures} failures, {errors} errors, {warnings} warnings"

	def _ReportLinks(self, docName: str, testcase: Testcase) -> list[nodes.Node]:
		"""
		Create the links to a testcase's report files, which Sphinx copies into the build as downloads.

		The files are the YAML reports the page is built from - the settings file, the AlertLog, coverage and scoreboard
		reports -, and the transcripts. A file the settings name, but which doesn't exist, is logged as a warning.

		:param docName:  Name of the testcase page's document.
		:param testcase: The testcase.
		:returns:        The links, separated by commas.
		"""
		if (settings := testcase.TestcaseSettings) is None:
			return []

		buildDirectory = TestcaseReports.BuildDirectory(testcase)
		files: list[tuple[str, Path]] = [
			("settings", settings.ReportsTestsuiteDirectory / f"{testcase._name}_run.yml")
		]
		if settings.AlertLogFile is not None:
			files.append(("AlertLog", settings.AlertLogFile))

		if settings.FunctionalCoverageFile is not None:
			files.append(("coverage", settings.FunctionalCoverageFile))

		for instance, file in settings.ScoreboardFiles.items():
			files.append((f"scoreboard {instance}", file))

		for file in settings.TranscriptFiles:
			files.append(("transcript", file))

		links: list[nodes.Node] = []
		for title, file in files:
			if not (path := buildDirectory / file).exists():
				getLogger(__name__).warning(
					f"Report file '{path}' of testcase '{testcase._name}' doesn't exist.", type="osvvm", subtype="read"
				)
				continue

			if len(links) > 0:
				links.append(nodes.Text(", "))

			target = "/" + relpath(path, self._sourceDirectory).replace("\\", "/")
			links.append(addnodes.download_reference(
				"", "", nodes.literal(title, title), reftarget=target, refdoc=docName, refexplicit=True
			))

		return links

	def _TestcasePage(self, docName: str, testcase: Testcase) -> nodes.section:
		"""
		Build a testcase's page: the unit test page, followed by its AlertLog, functional coverage and scoreboards.

		A report that can't be read is logged as an error and named on the page.

		:param docName:  Name of the page's document.
		:param testcase: The testcase.
		:returns:        The page's top section.
		"""
		page = super()._TestcasePage(docName, testcase)

		for identifier, title, content in (
			("alertlog",            "AlertLog",            self._AlertLog),
			("functional-coverage", "Functional Coverage", self._FunctionalCoverage),
			("scoreboards",         "Scoreboards",         self._Scoreboards)
		):
			try:
				contentNodes = content(testcase)
			except ReportExtensionError as ex:
				cause = ex if ex.__cause__ is None else ex.__cause__
				getLogger(__name__).error(f"{ex}\n  {getTypeName(cause)}: {cause}", location=docName)
				contentNodes = [nodes.paragraph(text=f"{ex}")]

			if len(contentNodes) > 0:
				page += (section := nodes.section("", nodes.title(title, title), ids=[identifier]))
				section.extend(contentNodes)

		return page

	@staticmethod
	def _AlertLog(testcase: Testcase) -> list[nodes.Node]:
		"""
		Create the table of a testcase's AlertLog.

		:param testcase: The testcase.
		:returns:        The table, or nothing if the testcase has no AlertLog report.
		"""
		if (document := TestcaseReports.AlertLog(testcase)) is None:
			return []

		return [AlertLogTable.CreateTable(document)]

	@staticmethod
	def _FunctionalCoverage(testcase: Testcase) -> list[nodes.Node]:
		"""
		Create the tables of a testcase's coverage models.

		:param testcase: The testcase.
		:returns:        The titles and tables, or nothing if the testcase has no coverage model.
		"""
		if (document := TestcaseReports.FunctionalCoverage(testcase)) is None:
			return []

		return [node for model in document.Models for node in FunctionalCoverageTables.CreateModelNodes(document, model)]

	@staticmethod
	def _Scoreboards(testcase: Testcase) -> list[nodes.Node]:
		"""
		Create the tables of a testcase's scoreboard package instances.

		:param testcase: The testcase.
		:returns:        The titles and tables, or nothing if the testcase has no scoreboard.
		"""
		return [
			node
			for document in TestcaseReports.Scoreboards(testcase)
			for node in ScoreboardTables.CreateInstanceNodes(document)
		]

	def _TestcaseColumns(self, withAssertions: bool) -> list[tuple[str, int]]:
		"""
		Return the columns of the testcase table of a testsuite's page: the testcase, its status, its elapsed time, its
		checks, alerts, requirements, functional coverage and simulation time.

		:param withAssertions: Whether a testcase of the testsuite has checks.
		:returns:              One ``(title, width)`` pair per column.
		"""
		return [
			("Testcase", 6), ("Status", 2), ("Elapsed Time", 2), ("Checks", 1), ("Alerts (F/E/W)", 2), ("Requirements", 1),
			("Functional Coverage", 1), ("Simulation Time", 2)
		]

	def _TestcaseCells(self, docName: str, testcase: Testcase, withAssertions: bool) -> list[nodes.entry]:
		"""
		Create the cells of a testcase's row in the testcase table of a testsuite's page.

		:param docName:        Name of the testsuite page's document.
		:param testcase:       The testcase.
		:param withAssertions: Whether a testcase of the testsuite has checks.
		:returns:              The cells.
		"""
		cells = super()._TestcaseCells(docName, testcase, False)
		ran = testcase._assertionCount is not None
		goal = testcase.RequirementsGoalCount
		coverage = testcase.FunctionalCoverage
		simulationTime = testcase.SimulationTime

		cells.append(createCell(f"{testcase.PassedAssertionCount or 0} / {testcase.AssertionCount}" if ran else ""))
		cells.append(createCell(f"{testcase.FatalCount} / {testcase.ErrorCount} / {testcase.WarningCount}" if ran else ""))
		cells.append(createCell("" if goal == 0 else f"{testcase.PassedRequirementsCount} / {goal}"))
		cells.append(createCell("" if coverage is None else f"{coverage * 100:.1f} %"))
		cells.append(createCell("" if simulationTime is None else formatSimulationTime(simulationTime)))

		return cells
