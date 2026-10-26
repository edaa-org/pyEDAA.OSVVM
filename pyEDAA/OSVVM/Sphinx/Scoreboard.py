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
The directive ``osvvm:scoreboards``: a testcase's scoreboards as tables, one per scoreboard package instance.

.. code-block:: ReST

   .. osvvm:scoreboards::
      :reportid:  demo
      :testsuite: Axi4Full
      :testcase:  TbAxi4_BasicReadWrite

A scoreboard package instance - e.g. ``slv`` of ``ScoreboardPkg_slv`` - has a report :file:`<test>_sb_<instance>.yml`.
Its table has a row per scoreboard, with the columns OSVVM's HTML report shows: the name, the AlertLog parent, the items
pushed, the failed checks, the items checked, popped and dropped, and the items left in the FIFO. A scoreboard with
failed checks is marked.
"""
from __future__                   import annotations

from typing                       import Any, Optional as Nullable

from docutils                     import nodes

from pyTooling.Decorators         import export
from pyTooling.Sphinx             import ReportExtensionError, strip

from pyEDAA.OSVVM.Scoreboard      import Document as ScoreboardDocument
from pyEDAA.OSVVM.Sphinx.Testcase import createCell, createTable, TestcaseDirective, TestcaseReports


@export
class ScoreboardTables(TestcaseDirective):
	"""
	The ``osvvm:scoreboards`` directive: a testcase's scoreboards as tables, one per scoreboard package instance.
	"""

	directiveName: str = "scoreboards"  #: Name the directive is invoked by.

	option_spec: dict[str, Any] = {  # type: ignore[misc]
		**TestcaseDirective.option_spec,
		"instance": strip
	}  #: Mapping of option names to validator functions.

	def _Content(self) -> list[nodes.Node]:
		"""
		Create the tables of the testcase's scoreboard package instances, or a paragraph saying it has none.

		Option ``:instance:`` selects one scoreboard package instance by name, e.g. ``slv``.

		:returns:                     The nodes.
		:raises ReportExtensionError: If option ``:instance:`` names no scoreboard package instance of the testcase.
		"""
		documents = TestcaseReports.Scoreboards(self._testcase)
		if len(documents) == 0:
			return [nodes.paragraph(text=f"Testcase '{self._testcase._name}' has no scoreboard.")]

		if (instance := self.options.get("instance", None)) is not None:
			selected = [document for document in documents if document.Name == instance]
			if len(selected) == 0:
				ex = ReportExtensionError(f"Testcase '{self._testcase._name}' has no scoreboard instance '{instance}'.")
				ex.add_note(f"Scoreboard instances: {', '.join(f'{document.Name}' for document in documents)}")
				raise ex

			documents = selected

		result: list[nodes.Node] = []
		for document in documents:
			result.extend(self.CreateInstanceNodes(document, self._cssClasses))

		return result

	@classmethod
	def CreateInstanceNodes(cls, document: ScoreboardDocument, classes: Nullable[list[str]] = None) -> list[nodes.Node]:
		"""
		Create the nodes of a scoreboard package instance: a title and the table of its scoreboards.

		:param document: The scoreboard report.
		:param classes:  Optional, additional CSS classes of the table. Default: ``None``.
		:returns:        The title and the table, with the CSS class ``osvvm-scoreboard-table``.
		"""
		title = f"Scoreboards of instance {document.Name}"
		table, tableBody = createTable(
			[
				("Name", None), ("Parent", None), ("Items", None), ("Errors", None), ("Checked", None), ("Popped", None),
				("Dropped", None), ("In FIFO", None)
			],
			["osvvm-scoreboard-table", *([] if classes is None else classes)]
		)

		for scoreboard in document.Scoreboards:
			errorClass = [] if scoreboard.ErrorCount == 0 else ["osvvm-scoreboard-errors"]
			tableBody += (row := nodes.row("", classes=["osvvm-scoreboard", *errorClass]))
			row += createCell(scoreboard.Name)
			row += createCell(scoreboard.AlertLogParentName)
			row += createCell(f"{scoreboard.ItemCount}")
			row += createCell(f"{scoreboard.ErrorCount}", errorClass)
			row += createCell(f"{scoreboard.CheckedItemCount}")
			row += createCell(f"{scoreboard.PoppedItemCount}")
			row += createCell(f"{scoreboard.DroppedItemCount}")
			row += createCell(f"{scoreboard.FifoCount}")

		return [nodes.rubric(title, title, classes=["osvvm-scoreboard-instance"]), table]
