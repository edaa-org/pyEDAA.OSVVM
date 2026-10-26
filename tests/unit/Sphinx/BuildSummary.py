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
"""Testcases for the directive ``osvvm:build-summary``."""
from shutil                         import copy, copytree

from pyEDAA.OSVVM.Sphinx.Testsuites import formatSimulationTime

from tests.unit.Sphinx              import DEMO, Project

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


OSVVM_COLUMNS = "   :columns: status testcases checks alerts disabled-alerts requirements coverage runtime\n"


def rowOf(html: str, name: str) -> str:
	"""
	Return the table row naming a testsuite or testcase.

	:param html: The page.
	:param name: Name of the testsuite or testcase.
	:returns:    The row's HTML.
	"""
	end = html.index(f"{name}</span>")
	return html[html.rindex("<tr", 0, end):html.index("</tr>", end)]


class Table(Project):
	def test_DefaultColumns(self) -> None:
		self._build("Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n")

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		header = html[html.index("<thead>"):html.index("</thead>")]
		titles = (
			"Testcases", "Errored", "Alerts", "Expected Alerts", "Checks", "Requirements", "Functional Coverage",
			"Elapsed Time (HH:MM:SS.sss)"
		)
		for title in titles:
			with self.subTest(title=title):
				self.assertIn(f">{title}</th>", header)
		self.assertEqual(sorted(titles, key=lambda title: header.index(f">{title}</th>")), list(titles))
		self.assertNotIn(">Status</th>", header)
		self.assertNotIn("Disabled Alerts", header)
		self.assertNotIn("Simulation Time", header)
		self.assertIn('class="report-unittest-table osvvm-buildsummary-table osvvm-buildsummary-demo docutils', html)

	def test_TestcaseRow(self) -> None:
		self._build("Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n" + OSVVM_COLUMNS)

		cells = rowOf(self._html("index"), "TbDemo_Failed").split("<td")[2:]
		self.assertEqual(
			[
				"FAILED", "", "", "", "", "7", "9", "0", "2", "1", "1", "1", "2", "43.8 %", "00:00:00.250"
			],
			[cell[cell.index(">") + 1:cell.index("</td>")] for cell in cells]
		)
		self.assertIn('class="osvvm-status-failed"', cells[0])
		self.assertNotIn("mismatch", cells[7])
		self.assertIn('class="osvvm-error-mismatch"', cells[8])
		self.assertIn('class="osvvm-warning-mismatch"', cells[9])

	def test_TestsuiteRow(self) -> None:
		self._build("Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n" + OSVVM_COLUMNS)

		cells = rowOf(self._html("index"), "Demo").split("<td")[2:]
		self.assertEqual(
			["FAILED", "2", "1", "1", "4", "14", "17", "0", "3", "1", "1", "1", "2", "", "00:00:00.401"],
			[cell[cell.index(">") + 1:cell.index("</td>")] for cell in cells]
		)

	def test_Errored(self) -> None:
		self._build("Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n   :columns: errored\n")

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		self.assertIn(">Errored</th>", html[html.index("<thead>"):html.index("</thead>")])
		testsuiteCells = rowOf(html, "Demo").split("<td")[2:]
		self.assertEqual(["0"], [cell[cell.index(">") + 1:cell.index("</td>")] for cell in testsuiteCells])

		testcaseCells = rowOf(html, "TbDemo_Failed").split("<td")[2:]
		self.assertEqual([""], [cell[cell.index(">") + 1:cell.index("</td>")] for cell in testcaseCells])

	def test_ExpectedStatus(self) -> None:
		self._build("Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n" + OSVVM_COLUMNS)

		row = rowOf(self._html("index"), "TbExpected_Failed")
		self.assertIn('class="report-testcase testcase-expectedfailed', row)
		self.assertIn("FAILED (expected)</td>", row)

	def test_Columns(self) -> None:
		self._build(
			"Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n   :columns: simulation-time, generics status\n"
		)

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		header = html[html.index("<thead>"):html.index("</thead>")]
		self.assertLess(header.index("Simulation Time"), header.index("Generics"))
		self.assertLess(header.index("Generics"), header.index("Status"))
		self.assertNotIn("Checks", header)
		self.assertIn("<td>125 ns</td>", rowOf(html, "TbDemo_Failed"))
		self.assertIn("<td>WIDTH=8</td>", rowOf(html, "TbGenerics_WIDTH_8"))

	def test_UnknownColumn(self) -> None:
		self._build("Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n   :columns: status, timing\n")

		warnings = self._warningLines()
		self.assertEqual(
			"ERROR: Caught ReportExtensionError when checking options for directive 'build-summary'.", warnings[0]
		)
		self.assertEqual(
			"ERROR:   ReportExtensionError: build-summary::columns: Unknown column group 'timing'.", warnings[1]
		)

	def test_NotPassed(self) -> None:
		self._build(
			"Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n   :show-testcases: not-passed\n"
			"   :hide-build-summary:\n   :build-name: Renamed\n"
		)

		html = self._html("index")
		self.assertNotIn("TbAxi4_BasicReadWrite", html)
		self.assertNotIn("TbExpected_Failed", html)
		self.assertIn("TbDemo_Failed", html)
		self.assertIn("TbDemo_Skipped", html)
		self.assertNotIn('class="report-testsuitesummary', html)


class Reading(Project):
	def test_MissingSettings(self) -> None:
		build = self._path / "Demo"
		copytree(DEMO, build)
		(build / "reports" / "Demo" / "TbGenerics_WIDTH_8_run.yml").unlink()

		self._build(
			"Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n",
			osvvm_build_summaries={"demo": {"yaml_report": str(build / "Demo.yml")}}
		)

		warnings = self._warningLines()
		self.assertEqual(1, len(warnings))
		self.assertIn(
			"WARNING: Build summary 'Demo/Demo.yml': Test case 'TbGenerics_WIDTH_8' has no settings file", warnings[0]
		)
		self.assertIn("TbGenerics_WIDTH_8", self._html("index"))

	def test_MissingReportsDirectory(self) -> None:
		build = self._path / "Copy.yml"
		copy(DEMO / "Demo.yml", build)

		self._build(
			"Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n",
			osvvm_build_summaries={"demo": {"yaml_report": str(build)}}
		)

		self.assertEqual(
			[
				"WARNING: Build summary 'Copy.yml': Reports directory 'reports' doesn't exist, so its testcases have no "
				"report files. [osvvm.read]"
			],
			self._warningLines()
		)

	def test_MissingFile(self) -> None:
		self._build(
			"Index\n#####\n", osvvm_build_summaries={"demo": {"yaml_report": str(self._path / "Missing.yml")}}
		)

		self.assertEqual(
			[
				"ERROR: Caught ReportExtensionError when checking configuration variables.",
				"  conf.py: osvvm_build_summaries:[demo].yaml_report: Build summary file 'Missing.yml' doesn't exist."
			],
			self._warningLines()
		)


class SimulationTime(Project):
	def test_Units(self) -> None:
		self.assertEqual("430 ns", formatSimulationTime(430_000_000))
		self.assertEqual("3.53 us", formatSimulationTime(3_530_000_000))
		self.assertEqual("1.5 sec", formatSimulationTime(1_500_000_000_000_000))
		self.assertEqual("1 fs", formatSimulationTime(1))
		self.assertEqual("0 fs", formatSimulationTime(0))
