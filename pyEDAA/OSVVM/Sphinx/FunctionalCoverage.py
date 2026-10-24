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
The directive ``osvvm:functional-coverage``: a testcase's functional coverage models as tables, one per model.

.. code-block:: ReST

   .. osvvm:functional-coverage::
      :reportid:  demo
      :testsuite: Axi4Full
      :testcase:  TbAxi4_BasicReadWrite

A model's table has a row per bin, with the columns OSVVM's HTML report shows: the bin's name, its type, its range per
dimension - a cross has a range column per field -, its count, *at least* count and coverage in percent, and - if the
report states pass or fail, or the model is a requirement - the bin's status. A model of weight 0 - e.g. OSVVM's delay
coverage - is ignored in the testcase's coverage, which its title says.
"""
from __future__                        import annotations

from typing                            import Any, Optional as Nullable

from docutils                          import nodes
from docutils.parsers.rst.directives   import flag

from pyTooling.Decorators              import export
from pyTooling.Sphinx                  import ReportExtensionError, strip

from pyEDAA.Reports.FunctionalCoverage import ValueRange

from pyEDAA.OSVVM.FunctionalCoverage   import Bin, BinType, CoverageModel, Document as CoverageDocument
from pyEDAA.OSVVM.Sphinx.Testcase      import createCell, createTable, TestcaseDirective, TestcaseReports


__all__ = ["INTEGER_LOW", "INTEGER_HIGH"]

#: The lowest value of VHDL's type ``integer``, which OSVVM writes as the open lower end of a range.
INTEGER_LOW = -2_147_483_648

#: The highest value of VHDL's type ``integer``, which OSVVM writes as the open upper end of a range.
INTEGER_HIGH = 2_147_483_647


@export
class FunctionalCoverageTables(TestcaseDirective):
	"""
	The ``osvvm:functional-coverage`` directive: a testcase's coverage models as tables, one per model.
	"""

	directiveName: str = "functional-coverage"  #: Name the directive is invoked by.

	option_spec: dict[str, Any] = {  # type: ignore[misc]
		**TestcaseDirective.option_spec,
		"model":    strip,
		"settings": flag
	}  #: Mapping of option names to validator functions.

	def _Content(self) -> list[nodes.Node]:
		"""
		Create the tables of the testcase's coverage models, or a paragraph saying it has none.

		Option ``:model:`` selects one model by name, option ``:settings:`` adds a table of each model's settings.

		:returns:                     The nodes.
		:raises ReportExtensionError: If option ``:model:`` names no model of the testcase.
		"""
		if (document := TestcaseReports.FunctionalCoverage(self._testcase)) is None:
			return [nodes.paragraph(text=f"Testcase '{self._testcase._name}' has no coverage model.")]

		models = document.Models
		if (modelName := self.options.get("model", None)) is not None:
			models = [model for model in models if model.Name == modelName]
			if len(models) == 0:
				ex = ReportExtensionError(f"Testcase '{self._testcase._name}' has no coverage model '{modelName}'.")
				ex.add_note(f"Coverage models: {', '.join(model.Name for model in document.Models)}")
				raise ex

		result: list[nodes.Node] = []
		for model in models:
			result.extend(self.CreateModelNodes(document, model, "settings" in self.options, self._cssClasses))

		return result

	@classmethod
	def CreateModelNodes(
		cls,
		document: CoverageDocument,
		model: CoverageModel,
		withSettings: bool = False,
		classes: Nullable[list[str]] = None
	) -> list[nodes.Node]:
		"""
		Create the nodes of a coverage model: a title with its coverage, optionally a table of its settings, and the table
		of its bins.

		:param document:     The coverage report.
		:param model:        The coverage model.
		:param withSettings: Optional, whether the model's settings are shown. Default: ``False``.
		:param classes:      Optional, additional CSS classes of the tables. Default: ``None``.
		:returns:            The title and the tables.
		"""
		classes = [] if classes is None else classes
		settings = model.Settings
		title = f"{model.Name} - coverage {model.Coverage:.1f} %"
		if settings.CoverageWeight == 0:
			title += " (weight 0, ignored in the testcase's coverage)"

		result: list[nodes.Node] = [nodes.rubric(title, title, classes=["osvvm-coverage-model"])]
		if withSettings:
			result.append(cls._SettingsTable(model, classes))

		withStatus = document.WritePassFail or settings.IsRequirement
		columns: list[tuple[str, Nullable[tuple[str, ...]]]] = [("Name", None), ("Type", None)]
		columns.extend((fieldName, None) for fieldName in model.FieldNames)
		columns.extend((("Count", None), ("At Least", None), ("Coverage (%)", None)))
		if withStatus:
			columns.append(("Status", None))

		table, tableBody = createTable(columns, ["osvvm-coverage-table", *classes])
		for coverageBin in model.Bins:
			tableBody += (row := nodes.row("", classes=[f"osvvm-bin-{coverageBin.Type.value.lower()}"]))
			row += createCell(coverageBin.Name)
			row += createCell(coverageBin.Type.value)
			for valueRange in coverageBin.Ranges:
				row += createCell(cls.FormatRange(valueRange))
			row += createCell(f"{coverageBin.Count}")
			row += createCell(f"{coverageBin.AtLeast}")
			row += createCell(f"{coverageBin.PercentCoverage:.1f}")
			if withStatus:
				status = cls.BinStatus(coverageBin, settings.CoverageWeight)
				row += createCell(status, [f"osvvm-status-{status.lower()}"])

		tableBody += (row := nodes.row("", classes=["osvvm-coverage-total"]))
		row += nodes.entry(
			"", nodes.paragraph("", "Total coverage"), morecols=len(columns) - (2 if withStatus else 1) - 1
		)
		row += createCell(f"{model.Coverage:.1f}")
		if withStatus:
			row += createCell("")

		result.append(table)
		return result

	@staticmethod
	def _SettingsTable(model: CoverageModel, classes: list[str]) -> nodes.table:
		"""
		Create the table of a coverage model's settings, as OSVVM names them.

		:param model:   The coverage model.
		:param classes: Additional CSS classes of the table.
		:returns:       The table.
		"""
		settings = model.Settings
		table, tableBody = createTable([("Setting", None), ("Value", None)], ["osvvm-coverage-settings", *classes])
		for name, value in (
			("CovWeight",       f"{settings.CoverageWeight}"),
			("Goal",            f"{settings.Goal}"),
			("WeightMode",      settings.WeightMode.value),
			("Seeds",           ", ".join(f"{seed}" for seed in settings.Seeds)),
			("CountMode",       settings.CountMode.value),
			("IllegalMode",     settings.IllegalMode.value),
			("Threshold",       f"{settings.Threshold}"),
			("ThresholdEnable", f"{settings.ThresholdEnable}".upper()),
			("IsRequirement",   f"{settings.IsRequirement}".upper()),
			("TotalCovCount",   f"{settings.TotalCount}"),
			("TotalCovGoal",    f"{settings.TotalGoal}")
		):
			tableBody += (row := nodes.row())
			row += createCell(name)
			row += createCell(value)

		return table

	@staticmethod
	def FormatRange(valueRange: ValueRange) -> str:
		"""
		Write a bin's range of one dimension.

		:param valueRange: The range.
		:returns:          ``ALL`` for the whole integer range, the value for a range of one value, and otherwise the
		                   bounds; an open end - :data:`INTEGER_LOW` or :data:`INTEGER_HIGH` - is written as ``≤`` or ``≥``.
		"""
		low = valueRange.Low
		high = valueRange.High
		if low <= INTEGER_LOW and high >= INTEGER_HIGH:
			return "ALL"
		elif high >= INTEGER_HIGH:
			return f"≥ {low}"
		elif low <= INTEGER_LOW:
			return f"≤ {high}"
		elif low == high:
			return f"{low}"

		return f"{low} to {high}"

	@staticmethod
	def BinStatus(coverageBin: Bin, coverageWeight: int) -> str:
		"""
		Return a bin's status, as OSVVM's HTML report writes it.

		:param coverageBin:    The bin.
		:param coverageWeight: The weight of the bin's model.
		:returns:              ``PASSED`` or ``FAILED``, ``IGNORED`` for an ignore bin, and ``-`` for a model of weight 0.
		"""
		if coverageWeight < 1:
			return "-"
		elif coverageBin.Type is BinType.Ignore:
			return "IGNORED"
		elif coverageBin.Type is BinType.Illegal:
			return "PASSED" if coverageBin.Count == 0 else "FAILED"

		return "PASSED" if coverageBin.Count >= coverageBin.AtLeast else "FAILED"
