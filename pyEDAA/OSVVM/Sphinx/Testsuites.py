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
The directive ``osvvm:build-summary``: OSVVM's build summary as a table, per testsuite and testcase.

The build summaries are declared in :file:`conf.py` under ``osvvm_build_summaries``, each with an identifier a
directive names in its ``:reportid:`` option, the build summary file :file:`<build>.yml` and optionally the key
``pages``:

.. code-block:: Python

   # doc/conf.py
   osvvm_build_summaries = {
     "demo": {
       "yaml_report": "../temp/OsvvmLibraries_RunDemoTests/OsvvmLibraries_RunDemoTests.yml",
       "pages":       "osvvm/demo",
     }
   }

A build summary is read once, when the builder is initialized, with the settings file :file:`<test>_run.yml` of every
testcase, which names the testcase's other report files. A warning of the reader - e.g. a key the format doesn't
define, or a missing settings file - is logged as a Sphinx warning.

The table is rendered by pyTooling.Sphinx' :class:`~pyTooling.Sphinx.Unittest.UnittestSummaryBase`; its columns are
chosen by option ``:columns:`` from :data:`COLUMNS`.
"""
from __future__                      import annotations

from os.path                         import relpath
from pathlib                         import Path
from typing                          import TYPE_CHECKING, Any, Callable, ClassVar, Optional as Nullable, TypedDict

from docutils                        import nodes
from docutils.parsers.rst.directives import flag
from sphinx                          import addnodes
from sphinx.util.logging             import getLogger

from pyTooling.Common                import getTypeName
from pyTooling.Decorators            import export
from pyTooling.Sphinx                import BaseDirective, ReportExtensionError, SphinxExtensionError, strip, \
                                            stripAndNormalize
from pyTooling.Sphinx.Pages          import ReportPages
from pyTooling.Sphinx.Unittest       import Column, ColumnGroup, ShowTestcases, UnittestSummaryBase
from pyTooling.Warning               import WarningCollector

from pyEDAA.OSVVM.Build              import BuildSummaryDocument, Testcase

if TYPE_CHECKING:  # pragma: no cover
	from pyEDAA.Reports.Unittesting    import TestsuiteBase


__all__ = ["CONFIG_VALUE", "COLUMNS", "DEFAULT_COLUMNS", "TIME_UNITS"]

#: Name of the configuration value in :file:`conf.py` declaring the build summaries.
CONFIG_VALUE = "osvvm_build_summaries"

#: The column groups option ``:columns:`` chooses from, by name, with their titles.
COLUMNS = {
	"status":          "Status",
	"testcases":       "Testcases",
	"errored":         "Errored",
	"checks":          "Checks",
	"alerts":          "Alerts",
	"expected-alerts": "Expected Alerts",
	"disabled-alerts": "Disabled Alerts",
	"requirements":    "Requirements",
	"coverage":        "Functional Coverage",
	"simulation-time": "Simulation Time",
	"runtime":         "Elapsed Time",
	"generics":        "Generics",
}

#: The column groups of a table without option ``:columns:``: the columns of the directive before the option.
DEFAULT_COLUMNS = (
	"testcases", "errored", "alerts", "expected-alerts", "checks", "requirements", "coverage", "runtime"
)

#: The units a simulation time is written in, as femtoseconds per unit, the largest first.
TIME_UNITS = (
	("sec", 1_000_000_000_000_000),
	("ms",  1_000_000_000_000),
	("us",  1_000_000_000),
	("ns",  1_000_000),
	("ps",  1_000),
	("fs",  1),
)


@export
class BuildSummaryConfiguration(TypedDict):
	"""An entry of ``osvvm_build_summaries``, after :meth:`BuildSummary.CheckConfiguration` read it."""

	yaml_report: Path           #: The build summary file :file:`<build>.yml`.
	pages:       Nullable[str]  #: Document name the pages per testsuite and testcase are generated below, if any.


@export
class BuildSummary(UnittestSummaryBase):
	"""
	The ``osvvm:build-summary`` directive: a table of an OSVVM build summary, per testsuite and testcase.

	Besides the counts of testcases per status and the elapsed time, a testcase's row shows what OSVVM states for it:
	its OSVVM status - and whether it was expected or is known -, its checks, alerts, disabled and expected alerts,
	requirements, functional coverage, simulation time and generics. A testsuite's row sums the counts of its
	testcases.
	"""

	directiveName: str = "build-summary"  #: Name the directive is invoked by.

	has_content =        False  #: A boolean; ``True`` if content is allowed.
	required_arguments = 0      #: Number of required directive arguments.
	optional_arguments = 6      #: Number of optional arguments.

	option_spec: dict[str, Any] = {  # type: ignore[misc]
		"class":              strip,
		"reportid":           stripAndNormalize,
		"build-name":         strip,
		"show-testcases":     stripAndNormalize,
		"hide-build-summary": flag,
		"columns":            stripAndNormalize
	}  #: Mapping of option names to validator functions.

	configValues: ClassVar[dict[str, tuple[Any, str, Any]]] = {
		"build_summaries": ({}, "env", dict)
	}  #: Values added to :file:`conf.py`, as ``name: (default, rebuild, types)``, prefixed by ``osvvm_``.

	_CONFIG_VALUE: ClassVar[str] = CONFIG_VALUE     #: Configuration value declaring the build summaries.
	_REPORT_KEY:   ClassVar[str] = "yaml_report"    #: Key of a build summary's file in its configuration.
	_REPORT_KIND:  ClassVar[str] = "Build summary"  #: The kind of report, as a message names it.

	_testSummaries: ClassVar[dict[str, BuildSummaryConfiguration]] = {}  #: Configurations, by report ID.
	_reports:       ClassVar[dict[str, BuildSummaryDocument]] = {}       #: Build summaries read, by report ID.
	_readErrors:    ClassVar[dict[str, Exception]] = {}                  #: Why a build summary wasn't read, by ID.

	_columnNames: list[str]  #: Names of the column groups shown, from :data:`COLUMNS`.

	def _CheckOptions(self) -> None:
		"""
		Parse all directive options or use default values.

		:raises SphinxExtensionError: If option ``:class:`` isn't a list of CSS class names.
		:raises SphinxExtensionError: If option ``:show-testcases:`` is neither ``all`` nor ``not-passed``.
		:raises SphinxExtensionError: If option ``:reportid:`` is missing.
		:raises ReportExtensionError: If option ``:columns:`` names a column group not in :data:`COLUMNS`. |br|
		                              The note lists the column groups.
		:raises ReportExtensionError: If ``osvvm_build_summaries`` has no entry for the report ID.
		"""
		cssClasses = self._ParseStringOption("class", "", r"(\w+)?( +\w+)*")
		showTestcases = self._ParseStringOption("show-testcases", "all", r"all|not-passed")
		columns = self._ParseStringOption("columns", " ".join(DEFAULT_COLUMNS), r"[a-z\- ,]+")

		self._cssClasses = [] if cssClasses == "" else cssClasses.split(" ")
		self._reportID = self._ParseStringOption("reportid")
		self._testsuiteSummaryName = self._ParseStringOption("build-name", "", r".+")
		self._showTestcases = ShowTestcases[showTestcases.replace("-", "_")]
		self._hideTestsuiteSummary = "hide-build-summary" in self.options
		self._columnNames = columnNames = []

		for columnName in columns.replace(",", " ").split():
			if columnName not in COLUMNS:
				ex = ReportExtensionError(f"{self.directiveName}::columns: Unknown column group '{columnName}'.")
				ex.add_note(f"Column groups: {', '.join(COLUMNS)}")
				raise ex

			columnNames.append(columnName)

		try:
			buildSummary = self._testSummaries[self._reportID]
		except KeyError as ex:
			raise ReportExtensionError(f"No build summary configuration item for '{self._reportID}'.") from ex
		self._reportFile = buildSummary["yaml_report"]

	@classmethod
	def _ReadReport(cls, reportFile: Path) -> BuildSummaryDocument:
		"""
		Read a build summary, and the settings file of each of its testcases.

		A warning of the reader is logged as a Sphinx warning. A build summary without its reports directory - e.g. a
		copy of the file alone - is logged once, and its testcases have no settings.

		:param reportFile: The build summary file.
		:returns:          The build summary, aggregated.
		"""
		logger = getLogger(__name__)

		with WarningCollector() as collector:
			document = BuildSummaryDocument(reportFile, analyzeAndConvert=True)
			reportsDirectory = reportFile.parent / document.Settings.ReportsSubdirectory
			if reportsDirectory.is_dir():
				document.ReadTestcaseSettings()
			else:
				logger.warning(
					f"{cls._REPORT_KIND} '{reportFile}': Reports directory '{reportsDirectory}' doesn't exist, so its testcases "
					f"have no report files.", type="osvvm", subtype="read"
				)

		for warning in collector:
			logger.warning(f"{cls._REPORT_KIND} '{reportFile}': {warning}", type="osvvm", subtype="read")

		return document

	@classmethod
	def GetTestcase(cls, reportID: str, testsuiteName: str, testcaseName: str) -> Testcase:
		"""
		Return a testcase of a build summary read by :meth:`ReadReports`.

		:param reportID:              Identifier of the build summary.
		:param testsuiteName:         Name of the testsuite.
		:param testcaseName:          Name of the testcase.
		:returns:                     The testcase.
		:raises ReportExtensionError: If the build summary wasn't read.
		:raises ReportExtensionError: If the build summary has no such testsuite.
		:raises ReportExtensionError: If the testsuite has no such testcase.
		"""
		build = cls.GetReport(reportID)

		try:
			testsuite = build._testsuites[testsuiteName]
		except KeyError as cause:
			ex = ReportExtensionError(f"{cls._REPORT_KIND} '{reportID}' has no testsuite '{testsuiteName}'.")
			ex.add_note(f"Testsuites: {', '.join(build._testsuites)}")
			raise ex from cause

		try:
			return testsuite._testcases[testcaseName]
		except KeyError as cause:
			ex = ReportExtensionError(f"Testsuite '{testsuiteName}' of '{reportID}' has no testcase '{testcaseName}'.")
			ex.add_note(f"Testcases: {', '.join(testsuite._testcases)}")
			raise ex from cause

	def _Pages(self) -> Nullable[ReportPages[Any]]:
		"""
		Return the pages of the build summary, if it was declared with the key ``pages``.

		:returns: The build summary's pages, or ``None`` if it has none.
		"""
		from pyEDAA.OSVVM.Sphinx.Pages import BuildReportPages

		if not BuildReportPages.HasPages(self._reportID):
			return None

		return BuildReportPages.GetPages(self._reportID)

	def _TableClasses(self) -> list[str]:
		"""
		Return the CSS classes of the table: ``report-unittest-table``, ``osvvm-buildsummary-table``,
		``osvvm-buildsummary-<report ID>`` and the classes of option ``:class:``.

		:returns: The CSS classes.
		"""
		return [
			"report-unittest-table", "osvvm-buildsummary-table", f"osvvm-buildsummary-{self._reportID}", *self._cssClasses
		]

	def _Columns(self) -> list[Column | ColumnGroup]:
		"""
		Return the column groups option ``:columns:`` names, in its order.

		:returns: The columns and groups of columns.
		"""
		def sumOf(count: Callable[[Testcase], int]) -> Callable[[TestsuiteBase[Any]], str]:
			"""
			Nested function returning a function, which sums a count of a testsuite's testcases.

			:param count: The function returning a testcase's count.
			:returns:     The function writing the sum of a testsuite or of the build.
			"""
			return lambda testsuite: f"{sum(count(testcase) for testcase in testsuite.IterateTestcases())}"

		def alerts(attribute: str, kind: str) -> Column:
			"""
			Nested function creating a column of alerts, its cell marked if a testcase's count isn't zero.

			OSVVM's alert counts are less the expected alerts, so a count other than zero means the alerts weren't the
			expected ones.

			:param attribute: The count's attribute, e.g. ``ErrorCount``.
			:param kind:      The kind of alert, as the mismatch's CSS class names it: ``failure``, ``error`` or ``warning``.
			:returns:         The column.
			"""
			def testcaseCell(testcase: Testcase) -> nodes.entry:
				"""
				Nested function creating the cell of a testcase.

				:param testcase: The testcase.
				:returns:        The cell.
				"""
				count = getattr(testcase, attribute)
				classes = [] if count == 0 else [f"osvvm-{kind}-mismatch"]
				return nodes.entry("", nodes.Text(f"{count}"), classes=classes)

			title = {"failure": "Failures", "error": "Errors", "warning": "Warnings"}[kind]
			return Column(title, 1, testsuite=sumOf(lambda testcase: getattr(testcase, attribute)), testcase=testcaseCell)

		def runtime(entity: TestsuiteBase[Any] | Testcase) -> str:
			"""
			Nested function formatting the elapsed time of a testsuite, the build or a testcase.

			:param entity: The testsuite, the build or the testcase.
			:returns:      The elapsed time.
			"""
			return self._FormatTimedelta(entity.TotalDuration)

		groups: dict[str, Column | ColumnGroup] = {
			"status":          Column("Status", 2, testsuite=lambda ts: ts.Status.name.upper(), testcase=self._Status),
			"testcases":       ColumnGroup("Testcases", [
				Column("Passed",  1, testsuite=lambda testsuite: f"{testsuite.Passed}"),
				Column("Failed",  1, testsuite=lambda testsuite: f"{testsuite.Failed}"),
				Column("Skipped", 1, testsuite=lambda testsuite: f"{testsuite.Skipped}"),
				Column("Total",   1, testsuite=lambda testsuite: f"{testsuite.TestcaseCount}")
			]),
			"errored":         Column("Errored", 1, testsuite=lambda testsuite: f"{testsuite.Errored}"),
			"checks":          ColumnGroup("Checks", [
				Column(
					"Passed", 1, testsuite=sumOf(lambda tc: tc.PassedAssertionCount or 0),
					testcase=lambda tc: "" if tc._passedAssertionCount is None else f"{tc._passedAssertionCount}"
				),
				Column(
					"Total", 1, testsuite=sumOf(lambda tc: tc.AssertionCount),
					testcase=lambda tc: "" if tc._assertionCount is None else f"{tc._assertionCount}"
				)
			]),
			"alerts":          ColumnGroup("Alerts", [
				alerts("FatalCount",   "failure"),
				alerts("ErrorCount",   "error"),
				alerts("WarningCount", "warning")
			]),
			"expected-alerts": ColumnGroup("Expected Alerts", [
				Column("Failures", 1, testcase=lambda testcase: f"{testcase.ExpectedFatalCount}"),
				Column("Errors",   1, testcase=lambda testcase: f"{testcase.ExpectedErrorCount}"),
				Column("Warnings", 1, testcase=lambda testcase: f"{testcase.ExpectedWarningCount}")
			]),
			"disabled-alerts": Column(
				"Disabled Alerts", 1, testsuite=sumOf(self._DisabledCount), testcase=lambda tc: f"{self._DisabledCount(tc)}"
			),
			"requirements":    ColumnGroup("Requirements", [
				Column(
					"Passed", 1, testsuite=sumOf(lambda tc: tc.PassedRequirementsCount),
					testcase=lambda tc: "" if tc.RequirementsGoalCount == 0 else f"{tc.PassedRequirementsCount}"
				),
				Column(
					"Goal", 1, testsuite=sumOf(lambda tc: tc.RequirementsGoalCount),
					testcase=lambda tc: "" if tc.RequirementsGoalCount == 0 else f"{tc.RequirementsGoalCount}"
				)
			]),
			"coverage":        Column(
				"Functional Coverage", 1,
				testcase=lambda tc: "" if tc.FunctionalCoverage is None else f"{tc.FunctionalCoverage * 100:.1f} %"
			),
			"simulation-time": Column(
				"Simulation Time", 2,
				testcase=lambda tc: "" if tc.SimulationTime is None else formatSimulationTime(tc.SimulationTime)
			),
			"runtime":         Column("Elapsed Time (HH:MM:SS.sss)", 2, testsuite=runtime, testcase=runtime),
			"generics":        Column(
				"Generics", 3, testcase=lambda tc: ", ".join(f"{name}={value}" for name, value in tc.Generics.items())
			),
		}

		return [groups[columnName] for columnName in self._columnNames]

	@staticmethod
	def _Status(testcase: Testcase) -> nodes.entry:
		"""
		Create the cell of a testcase's OSVVM status, marked if the status was expected or is known.

		:param testcase: The testcase.
		:returns:        The cell, with the CSS class ``osvvm-status-<status>``.
		"""
		if (status := testcase.OSVVMStatus) is None:
			return nodes.entry("", nodes.Text(""))

		text = status.value
		if testcase.ExpectedResults is not None:
			text += " (expected)"
		elif testcase.KnownStatus is not None:
			text += " (known)"

		return nodes.entry("", nodes.Text(text), classes=[f"osvvm-status-{status.value.lower()}"])

	@staticmethod
	def _DisabledCount(testcase: Testcase) -> int:
		"""
		Return the number of a testcase's disabled alerts.

		:param testcase: The testcase.
		:returns:        The sum of disabled failures, errors and warnings.
		"""
		return testcase.DisabledFatalCount + testcase.DisabledErrorCount + testcase.DisabledWarningCount


@export
class BuildInformation(BaseDirective):
	"""
	The ``osvvm:build-information`` directive: the information about a build, as OSVVM's HTML build summary shows it.

	A field per fact: the build's name and status, the testcases per status, the start and finish time, the elapsed
	time, the simulator, OSVVM's version, the build's error code, the analysis and simulation errors, and links to the
	build's log files, which Sphinx copies into the build as downloads.
	"""

	directiveName: str = "build-information"  #: Name the directive is invoked by.

	has_content =        False  #: A boolean; ``True`` if content is allowed.
	required_arguments = 0      #: Number of required directive arguments.
	optional_arguments = 0      #: Number of optional arguments.

	option_spec: dict[str, Any] = {  # type: ignore[misc]
		"class":    strip,
		"reportid": stripAndNormalize
	}  #: Mapping of option names to validator functions.

	def run(self) -> list[nodes.Node]:
		"""
		Return the build's information as a field list, or the error message.

		:returns: The field list, or a container holding the error message.
		"""
		container = nodes.container()

		try:
			cssClasses = self._ParseStringOption("class", "", r"(\w+)?( +\w+)*")
			reportID = self._ParseStringOption("reportid")
			build = BuildSummary.GetReport(reportID)
		except SphinxExtensionError as ex:
			message = f"Caught {getTypeName(ex)} when checking options for directive '{self.directiveName}'."
			return self._internalError(container, __name__, message, ex)

		fieldList = nodes.field_list(classes=["osvvm-build-information", *([] if cssClasses == "" else cssClasses.split())])
		information = build.BuildInformation
		version = information.OSVVMVersion
		fields: list[tuple[str, str | list[nodes.Node]]] = [
			("Build",            build.Name),
			("Status",           f"{BuildSummary._ConvertTestsuiteStatusToSymbol(build.Status)} {build.Status.name}"),
			("Testcases",        f"{build.TestcaseCount} - {build.Passed} passed, {build.Failed} failed, "
			                     f"{build.Skipped} skipped"),
			("Start Time",       f"{build.StartTime:%Y-%m-%d %H:%M:%S %Z}"),
			("Finish Time",      "" if information.FinishTime is None else f"{information.FinishTime:%Y-%m-%d %H:%M:%S %Z}"),
			("Elapsed Time",     BuildSummary._FormatTimedelta(build.TotalDuration)),
			("Simulator",        f"{information.Simulator} {information.SimulatorVersion}"),
			("OSVVM Version",    f"{version.Major}.{version.Minor:02}{version.Postfix}"),
			("Build Error Code", f"{information.BuildErrorCode}"),
			("Analyze Errors",   f"{information.AnalyzeErrorCount}"),
			("Simulate Errors",  f"{information.SimulateErrorCount}"),
		]
		if len(logs := self._LogLinks(build)) > 0:
			fields.append(("Logs", logs))

		for name, value in fields:
			content = [nodes.Text(value)] if isinstance(value, str) else value
			body = nodes.field_body("", nodes.paragraph("", "", *content))
			fieldList += nodes.field("", nodes.field_name(name, name), body)

		return [fieldList]

	def _LogLinks(self, build: BuildSummaryDocument) -> list[nodes.Node]:
		"""
		Create the links to the build's log files: the simulation log and its HTML form.

		A log file the build summary names, but which doesn't exist, is logged as a warning.

		:param build: The build summary.
		:returns:     The links, separated by commas.
		"""
		settings = build.Settings
		links: list[nodes.Node] = []
		for title, file in (("log", settings.SimulationLogFile), ("HTML log", settings.SimulationHtmlLogFile)):
			if file is None:
				continue
			elif not (path := build.Path.parent / file).exists():
				getLogger(__name__).warning(
					f"Log file '{path}' of build '{build.Name}' doesn't exist.", location=self.get_location(), type="osvvm",
					subtype="read"
				)
				continue

			if len(links) > 0:
				links.append(nodes.Text(", "))

			target = "/" + relpath(path, self.env.srcdir).replace("\\", "/")
			links.append(addnodes.download_reference(
				"", "", nodes.literal(title, title), reftarget=target, refdoc=self.env.docname, refexplicit=True
			))

		return links


@export
def formatSimulationTime(femtoseconds: int) -> str:
	"""
	Write a simulation time in the largest unit of :data:`TIME_UNITS` it reaches, with up to three decimals.

	:param femtoseconds: The simulation time in femtoseconds.
	:returns:            The simulation time, e.g. ``3.53 us``.
	"""
	for unit, factor in TIME_UNITS:
		if femtoseconds >= factor:
			return f"{femtoseconds / factor:.3f}".rstrip("0").rstrip(".") + f" {unit}"

	return "0 fs"
