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
The base-class of the directives showing a report of one testcase - its AlertLog, functional coverage or scoreboards -,
and the reading of those reports.

A testcase is named by three directive options: the build summary (``:reportid:``, as declared in
``osvvm_build_summaries``), the testsuite (``:testsuite:``) and the testcase (``:testcase:``, OSVVM's
``TestCaseFileName``). Its reports are the files its settings file :file:`<test>_run.yml` names, relative to the build
summary's directory. A report is read once per build, when a directive or a page needs it.
"""
from __future__                      import annotations

from pathlib                         import Path
from typing                          import Any, Callable, ClassVar, Optional as Nullable, Sequence, TypeVar

from docutils                        import nodes
from sphinx.application              import Sphinx
from sphinx.util.logging             import getLogger

from pyTooling.Common                import getTypeName
from pyTooling.Decorators            import export
from pyTooling.MetaClasses           import ExtendedType
from pyTooling.Sphinx                import BaseDirective, ReportExtensionError, SphinxExtensionError, strip, \
                                            stripAndNormalize
from pyTooling.Warning               import WarningCollector

from pyEDAA.OSVVM.AlertLog           import Document as AlertLogDocument
from pyEDAA.OSVVM.Build              import Testcase
from pyEDAA.OSVVM.FunctionalCoverage import Document as CoverageDocument
from pyEDAA.OSVVM.Scoreboard         import Document as ScoreboardDocument


DocumentType = TypeVar("DocumentType")  #: The type of a testcase's report document.


@export
class TestcaseReports(metaclass=ExtendedType, slots=True):
	"""
	The reports of the testcases of the build summaries: each read once per build, when it's needed first.

	A warning of a reader - e.g. a key the format doesn't define - is logged as a Sphinx warning.
	"""

	_documents: ClassVar[dict[Path, Any]] = {}  #: The documents read, by resolved path.

	@classmethod
	def Clear(cls, sphinxApplication: Sphinx) -> None:
		"""
		Call-back for Sphinx' ``builder-inited`` event: forget the documents of a previous build.

		:param sphinxApplication: Sphinx application instance.
		"""
		cls._documents = {}

	@classmethod
	def AlertLog(cls, testcase: Testcase) -> Nullable[AlertLogDocument]:
		"""
		Return a testcase's AlertLog report.

		:param testcase:              The testcase.
		:returns:                     The AlertLog report, or ``None`` if the testcase has no settings or no AlertLog file.
		:raises ReportExtensionError: If the AlertLog file can't be read.
		"""
		if (settings := testcase.TestcaseSettings) is None or settings.AlertLogFile is None:
			return None

		return cls._Read(testcase, settings.AlertLogFile, AlertLogDocument)

	@classmethod
	def FunctionalCoverage(cls, testcase: Testcase) -> Nullable[CoverageDocument]:
		"""
		Return a testcase's functional coverage report.

		:param testcase:              The testcase.
		:returns:                     The coverage report, or ``None`` if the testcase has no settings or no coverage model.
		:raises ReportExtensionError: If the coverage file can't be read.
		"""
		if (settings := testcase.TestcaseSettings) is None or settings.FunctionalCoverageFile is None:
			return None

		return cls._Read(testcase, settings.FunctionalCoverageFile, CoverageDocument)

	@classmethod
	def Scoreboards(cls, testcase: Testcase) -> list[ScoreboardDocument]:
		"""
		Return a testcase's scoreboard reports, one per scoreboard package instance.

		:param testcase:              The testcase.
		:returns:                     The scoreboard reports, in the order of the settings file; none if the testcase has no
		                              settings.
		:raises ReportExtensionError: If a scoreboard file can't be read.
		"""
		if (settings := testcase.TestcaseSettings) is None:
			return []

		return [cls._Read(testcase, path, ScoreboardDocument) for path in settings.ScoreboardFiles.values()]

	@staticmethod
	def BuildDirectory(testcase: Testcase) -> Path:
		"""
		Return the directory of a testcase's build summary, which the paths of its settings are relative to.

		:param testcase: The testcase.
		:returns:        The build summary's directory.
		"""
		return testcase._parent._parent._path.parent

	@classmethod
	def _Read(cls, testcase: Testcase, path: Path, reader: Callable[..., DocumentType]) -> DocumentType:
		"""
		Read a report of a testcase, or return it, if it was read before.

		:param testcase:              The testcase.
		:param path:                  The report file, relative to the build summary's directory.
		:param reader:                The document class reading the file.
		:returns:                     The document.
		:raises ReportExtensionError: If the file can't be read.
		"""
		file = (cls.BuildDirectory(testcase) / path).resolve()
		try:
			return cls._documents[file]
		except KeyError:
			pass

		try:
			with WarningCollector() as collector:
				document = reader(file, analyzeAndConvert=True)
		except Exception as cause:
			raise ReportExtensionError(f"Report '{path}' of testcase '{testcase._name}' can't be read.") from cause

		logger = getLogger(__name__)
		for warning in collector:
			logger.warning(f"Report '{file}' of testcase '{testcase._name}': {warning}", type="osvvm", subtype="read")

		cls._documents[file] = document
		return document


@export
def createTable(
	columns: Sequence[tuple[str, Nullable[Sequence[str]]]],
	classes: list[str]
) -> tuple[nodes.table, nodes.tbody]:
	"""
	Create a table with a header: a column per title, a group of columns per title with sub-titles.

	The header has a second row, if a column is a group.

	:param columns: One ``(title, sub-titles)`` pair per column; ``None`` for a column without sub-columns.
	:param classes: CSS classes of the table.
	:returns:       The table, and its body the rows are added to.
	"""
	columnCount = sum(1 if subTitles is None else len(subTitles) for _, subTitles in columns)
	grouped = any(subTitles is not None for _, subTitles in columns)

	table = nodes.table("", classes=classes)
	table += (tableGroup := nodes.tgroup(cols=columnCount))
	for _ in range(columnCount):
		tableGroup += nodes.colspec(colwidth=1)

	tableGroup += (tableHeader := nodes.thead())
	tableHeader += (headerRow := nodes.row())
	for title, subTitles in columns:
		if subTitles is None and grouped:
			headerRow += nodes.entry("", nodes.paragraph(title, title), morerows=1)
		elif subTitles is None:
			headerRow += nodes.entry("", nodes.paragraph(title, title))
		else:
			headerRow += nodes.entry("", nodes.paragraph(title, title), morecols=len(subTitles) - 1)

	if grouped:
		tableHeader += (subHeaderRow := nodes.row())
		for _, subTitles in columns:
			for subTitle in subTitles or ():
				subHeaderRow += nodes.entry("", nodes.paragraph(subTitle, subTitle))

	tableGroup += (tableBody := nodes.tbody())
	return table, tableBody


@export
def createCell(text: str, classes: Nullable[list[str]] = None) -> nodes.entry:
	"""
	Create a table cell holding a text.

	:param text:    The text.
	:param classes: Optional, CSS classes of the cell. Default: ``None``.
	:returns:       The cell.
	"""
	return nodes.entry("", nodes.paragraph(text, text), classes=[] if classes is None else classes)


@export
class TestcaseDirective(BaseDirective):
	"""
	Base-class of a directive showing a report of one testcase, named by the options ``:reportid:``, ``:testsuite:``
	and ``:testcase:``.

	A derived class creates the nodes in :meth:`_Content`.
	"""

	has_content =        False  #: A boolean; ``True`` if content is allowed.
	required_arguments = 0      #: Number of required directive arguments.
	optional_arguments = 0      #: Number of optional arguments.

	option_spec: dict[str, Any] = {  # type: ignore[misc]
		"class":     strip,
		"reportid":  stripAndNormalize,
		"testsuite": strip,
		"testcase":  strip
	}  #: Mapping of option names to validator functions.

	_cssClasses: list[str]  #: Additional CSS classes of the tables.
	_testcase:   Testcase   #: The testcase.

	def _CheckOptions(self) -> None:
		"""
		Parse all directive options, and look up the testcase.

		:raises SphinxExtensionError: If option ``:class:`` isn't a list of CSS class names.
		:raises SphinxExtensionError: If option ``:reportid:``, ``:testsuite:`` or ``:testcase:`` is missing.
		:raises ReportExtensionError: If the build summary wasn't read, or has no such testsuite or testcase.
		"""
		from pyEDAA.OSVVM.Sphinx.Testsuites import BuildSummary

		cssClasses = self._ParseStringOption("class", "", r"(\w+)?( +\w+)*")

		self._cssClasses = [] if cssClasses == "" else cssClasses.split(" ")
		self._testcase = BuildSummary.GetTestcase(
			self._ParseStringOption("reportid"), self._ParseStringOption("testsuite", regexp=r".+"),
			self._ParseStringOption("testcase", regexp=r".+")
		)

	def _Content(self) -> list[nodes.Node]:
		"""
		Create the nodes showing the testcase's report.

		:returns:                    The nodes.
		:raises NotImplementedError: If a derived class doesn't override it.
		"""
		raise NotImplementedError(f"{self.directiveName}: '_Content' is not implemented.")

	def run(self) -> list[nodes.Node]:
		"""
		Look up the testcase and return the nodes showing its report, or the error message.

		:returns: The nodes, or a container holding the error message.
		"""
		container = nodes.container()

		try:
			self._CheckOptions()
		except SphinxExtensionError as ex:
			message = f"Caught {getTypeName(ex)} when checking options for directive '{self.directiveName}'."
			return self._internalError(container, __name__, message, ex)

		try:
			return self._Content()
		except Exception as ex:
			message = f"Caught {getTypeName(ex)} when generating directive '{self.directiveName}'."
			return self._internalError(container, __name__, message, ex)
