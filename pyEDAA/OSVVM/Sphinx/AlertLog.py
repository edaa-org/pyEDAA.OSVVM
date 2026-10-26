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
The directive ``osvvm:alert-log``: a testcase's AlertLog hierarchy as a table, with the counts of each item.

.. code-block:: ReST

   .. osvvm:alert-log::
      :reportid:  demo
      :testsuite: Axi4Full
      :testcase:  TbAxi4_BasicReadWrite

The table has a row per AlertLog item - the test first, then its items, each indented by its depth -, with the columns
OSVVM's HTML report shows: the status, the checks, the requirements, the alert counts and the disabled alert counts.
"""
from __future__                   import annotations

from typing                       import Optional as Nullable

from docutils                     import nodes

from pyTooling.Decorators         import export
from pyTooling.Sphinx.Node        import ReportIndentation

from pyEDAA.OSVVM.AlertLog        import AlertLogItem, Document as AlertLogDocument
from pyEDAA.OSVVM.Sphinx.Testcase import createCell, createTable, TestcaseDirective, TestcaseReports


@export
class AlertLogTable(TestcaseDirective):
	"""
	The ``osvvm:alert-log`` directive: a testcase's AlertLog hierarchy as a table.
	"""

	directiveName: str = "alert-log"  #: Name the directive is invoked by.

	def _Content(self) -> list[nodes.Node]:
		"""
		Create the table of the testcase's AlertLog, or a paragraph saying it has none.

		:returns: The nodes.
		"""
		if (document := TestcaseReports.AlertLog(self._testcase)) is None:
			return [nodes.paragraph(text=f"Testcase '{self._testcase._name}' has no AlertLog report.")]

		return [self.CreateTable(document, self._cssClasses)]

	@classmethod
	def CreateTable(cls, document: AlertLogDocument, classes: Nullable[list[str]] = None) -> nodes.table:
		"""
		Create the table of an AlertLog: a row per item, the test first.

		:param document: The AlertLog report.
		:param classes:  Optional, additional CSS classes of the table. Default: ``None``.
		:returns:        The table, with the CSS class ``osvvm-alertlog-table``.
		"""
		table, tableBody = createTable(
			[
				("Name",                  None),
				("Status",                None),
				("Checks",                ("Total", "Passed", "Failed")),
				("Requirements",          ("Goal", "Passed")),
				("Alert Counts",          ("Failures", "Errors", "Warnings")),
				("Disabled Alert Counts", ("Failures", "Errors", "Warnings"))
			],
			["osvvm-alertlog-table", *([] if classes is None else classes)]
		)

		cls._AddRows(tableBody, document, 0)
		return table

	@classmethod
	def _AddRows(cls, tableBody: nodes.tbody, item: AlertLogItem, level: int) -> None:
		"""
		Add the row of an AlertLog item, then - recursively - the rows of its children.

		:param tableBody: The table body the rows are added to.
		:param item:      The AlertLog item.
		:param level:     The item's depth in the hierarchy, shown by indentation.
		"""
		status = item.Status.value
		alertClass = [] if item.TotalErrorCount == 0 else ["osvvm-alerts"]

		tableBody += (row := nodes.row("", classes=["osvvm-alertlog-item", f"osvvm-alertlog-{status.lower()}"]))
		row += nodes.entry("", nodes.paragraph("", "", ReportIndentation("", item.Name, level=2 * level)))
		row += createCell(status, [f"osvvm-status-{status.lower()}"])
		row += createCell(f"{item.AffirmCount}")
		row += createCell(f"{item.PassedCount}")
		row += createCell(f"{item.AffirmCount - item.PassedCount}")
		row += createCell(f"{item.RequirementsGoalCount}")
		row += createCell(f"{item.PassedRequirementsCount}")
		row += createCell(f"{item.FailureCount}", alertClass)
		row += createCell(f"{item.ErrorCount}", alertClass)
		row += createCell(f"{item.WarningCount}", alertClass)
		row += createCell(f"{item.DisabledFailureCount}")
		row += createCell(f"{item.DisabledErrorCount}")
		row += createCell(f"{item.DisabledWarningCount}")

		for child in item.Children.values():
			cls._AddRows(tableBody, child, level + 1)
