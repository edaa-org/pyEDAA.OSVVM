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
"""Testcases for the directives ``osvvm:alert-log``, ``osvvm:functional-coverage`` and ``osvvm:scoreboards``."""
from pyEDAA.Reports.FunctionalCoverage   import ValueRange

from pyEDAA.OSVVM.Sphinx.FunctionalCoverage import FunctionalCoverageTables

from tests.unit.Sphinx                   import Project

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


def directive(name: str, testsuite: str, testcase: str, *options: str) -> str:
	"""
	Write a document with a directive naming a testcase of the demo build.

	:param name:      Name of the directive.
	:param testsuite: Name of the testsuite.
	:param testcase:  Name of the testcase.
	:param options:   More options, each as ``:name: value``.
	:returns:         The document.
	"""
	lines = "".join(f"   {option}\n" for option in options)
	return (
		f"Index\n#####\n\n.. osvvm:{name}::\n   :reportid: demo\n   :testsuite: {testsuite}\n   :testcase: {testcase}\n"
		f"{lines}"
	)


def cellsOf(html: str, name: str) -> list[str]:
	"""
	Return the texts of the cells of the table row, whose first cell names it.

	:param html: The page.
	:param name: The text of the row's first cell.
	:returns:    The texts of the row's cells.
	"""
	start = html.index(f">{name}</")
	row = html[html.rindex("<tr", 0, start):html.index("</tr>", start)]
	texts = []
	for cell in row.split("<td")[1:]:
		text = cell[cell.index(">") + 1:cell.index("</td>")]
		while "<" in text:
			text = text[:text.index("<")] + text[text.index(">") + 1:]
		texts.append(text)

	return texts


class AlertLog(Project):
	def test_Hierarchy(self) -> None:
		self._build(directive("alert-log", "Demo", "TbDemo_Failed"))

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		header = html[html.index("<thead>"):html.index("</thead>")]
		for title in ("Checks", "Requirements", "Alert Counts", "Disabled Alert Counts", "Goal", "Failures"):
			with self.subTest(title=title):
				self.assertIn(f"<p>{title}</p>", header)

		self.assertEqual(
			["TbDemo_Failed", "FAILED", "9", "7", "2", "2", "1", "0", "2", "1", "0", "1", "0"], cellsOf(html, "TbDemo_Failed")
		)
		self.assertEqual(
			["Parity", "FAILED", "0", "0", "0", "0", "0", "0", "0", "1", "0", "1", "0"], cellsOf(html, "Parity")
		)
		self.assertIn('<span class="report-indentation" style="--pyTooling-report-level: 4">Parity</span>', html)
		self.assertIn('class="osvvm-alertlog-item osvvm-alertlog-failed', html)

	def test_UnknownTestcase(self) -> None:
		self._build(directive("alert-log", "Demo", "TbMissing"))

		warnings = self._warningLines()
		self.assertEqual("ERROR: Caught ReportExtensionError when checking options for directive 'alert-log'.", warnings[0])
		self.assertEqual(
			"ERROR:   ReportExtensionError: Testsuite 'Demo' of 'demo' has no testcase 'TbMissing'.", warnings[1]
		)

	def test_Skipped(self) -> None:
		self._build(directive("alert-log", "Demo", "TbDemo_Skipped"))

		self.assertEqual([], self._warningLines())
		self.assertIn("Testcase ‘TbDemo_Skipped’ has no AlertLog report.", self._html("index"))


class FunctionalCoverage(Project):
	def test_Models(self) -> None:
		self._build(directive("functional-coverage", "Axi4Full", "TbAxi4_BasicReadWrite"))

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		self.assertIn("BurstLength - coverage 100.0 %", html)
		self.assertIn("WriteAddrDelayCov BurstLength - coverage 0.0 % (weight 0, ignored in the testcase’s coverage)", html)
		self.assertEqual(["Single", "COUNT", "1", "4", "1", "100.0", "PASSED"], cellsOf(html, "Single"))
		self.assertEqual(["TooLong", "ILLEGAL", "≥ 9", "0", "0", "0.0", "PASSED"], cellsOf(html, "TooLong"))
		self.assertEqual(["Other", "IGNORE", "≤ 0", "1", "0", "0.0", "IGNORED"], cellsOf(html, "Other"))
		self.assertNotIn("osvvm-coverage-settings", html)

	def test_Cross(self) -> None:
		self._build(directive("functional-coverage", "Axi4Full", "TbAxi4_BasicReadWrite", ":model: AddressCross"))

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		self.assertNotIn("BurstLength - coverage", html)
		header = html[html.index("<thead>"):html.index("</thead>")]
		self.assertLess(header.index("<p>Address</p>"), header.index("<p>Burst</p>"))
		self.assertIn("<td><p>256 to 511</p></td>\n<td><p>1</p></td>", html)

	def test_Settings(self) -> None:
		self._build(
			directive("functional-coverage", "Axi4Full", "TbAxi4_BasicReadWrite", ":model: BurstLength", ":settings:")
		)

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		self.assertIn('class="osvvm-coverage-settings', html)
		self.assertEqual(["WeightMode", "AT_LEAST"], cellsOf(html, "WeightMode"))
		self.assertEqual(["Seeds", "1, 2"], cellsOf(html, "Seeds"))

	def test_UnknownModel(self) -> None:
		self._build(directive("functional-coverage", "Axi4Full", "TbAxi4_BasicReadWrite", ":model: Missing"))

		warnings = self._warningLines()
		self.assertEqual(
			"ERROR: Caught ReportExtensionError when generating directive 'functional-coverage'.", warnings[0]
		)
		self.assertEqual(
			"ERROR:   ReportExtensionError: Testcase 'TbAxi4_BasicReadWrite' has no coverage model 'Missing'.", warnings[1]
		)

	def test_NoModel(self) -> None:
		self._build(directive("functional-coverage", "Demo", "TbDemo_Failed"))

		self.assertEqual([], self._warningLines())
		self.assertIn("Testcase ‘TbDemo_Failed’ has no coverage model.", self._html("index"))

	def test_FormatRange(self) -> None:
		self.assertEqual("ALL", FunctionalCoverageTables.FormatRange(ValueRange(-2_147_483_648, 2_147_483_647)))
		self.assertEqual("5", FunctionalCoverageTables.FormatRange(ValueRange(5, 5)))
		self.assertEqual("2 to 8", FunctionalCoverageTables.FormatRange(ValueRange(2, 8)))


class Scoreboards(Project):
	def test_Instance(self) -> None:
		self._build(directive("scoreboards", "Axi4Full", "TbAxi4_BasicReadWrite"))

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		self.assertIn("Scoreboards of instance slv", html)
		self.assertEqual(["WriteResp SB", "manager_1", "10", "0", "0", "10", "0", "0"], cellsOf(html, "WriteResp SB"))

	def test_Errors(self) -> None:
		self._build(directive("scoreboards", "Demo", "TbDemo_Failed", ":instance: int"))

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		self.assertEqual(["Uart_1 SB", "Uart_1", "6", "2", "6", "6", "0", "0"], cellsOf(html, "Uart_1 SB"))
		self.assertIn('class="osvvm-scoreboard osvvm-scoreboard-errors', html)

	def test_UnknownInstance(self) -> None:
		self._build(directive("scoreboards", "Demo", "TbDemo_Failed", ":instance: slv"))

		warnings = self._warningLines()
		self.assertEqual(
			"ERROR:   ReportExtensionError: Testcase 'TbDemo_Failed' has no scoreboard instance 'slv'.", warnings[1]
		)

	def test_NoScoreboard(self) -> None:
		self._build(directive("scoreboards", "Demo", "TbGenerics_WIDTH_8"))

		self.assertEqual([], self._warningLines())
		self.assertIn("Testcase ‘TbGenerics_WIDTH_8’ has no scoreboard.", self._html("index"))
