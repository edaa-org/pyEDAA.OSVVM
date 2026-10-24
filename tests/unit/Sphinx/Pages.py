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
"""Testcases for the pages per testsuite and testcase, the roles ``:osvvm:ts:`` and ``:osvvm:tc:``, and the directive
``osvvm:build-information``."""
from re                  import findall, sub
from shutil              import copytree

from tests.unit.Sphinx   import DEMO, DEMO_BUILD, Project

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


PAGES = {"demo": {"yaml_report": str(DEMO_BUILD), "pages": "osvvm/demo"}}
"""The demo build, declared with pages."""


def fieldsOf(html: str) -> dict[str, str]:
	"""
	Return the fields of the first field list of a page, as text.

	:param html: The page.
	:returns:    The fields' texts, by field name.
	"""
	start = html.index("<dl class=")
	fieldList = html[start:html.index("</dl>", start)]
	return {
		sub("<[^>]+>", "", name).strip(" :"): sub(r"\s+", " ", sub("<[^>]+>", "", value)).strip()
		for name, value in findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", fieldList.replace("\n", " "))
	}


class Pages(Project):
	def test_DocNames(self) -> None:
		self._build("Index\n#####\n", osvvm_build_summaries=PAGES)

		self.assertEqual([], self._warningLines())
		for docName in (
			"osvvm/demo/Axi4Full", "osvvm/demo/Demo", "osvvm/demo/Axi4Full/TbAxi4_BasicReadWrite",
			"osvvm/demo/Demo/TbDemo_Skipped", "osvvm/demo/Demo/TbGenerics_WIDTH_8"
		):
			with self.subTest(docName=docName):
				self.assertTrue((self._path / "build" / "html" / f"{docName}.html").exists())

	def test_TestcasePage(self) -> None:
		self._build("Index\n#####\n", osvvm_build_summaries=PAGES)

		html = self._html("osvvm/demo/Demo/TbDemo_Failed")
		fields = fieldsOf(html)
		self.assertEqual("❌ Failed", fields["Status"])
		self.assertEqual("FAILED", fields["OSVVM Status"])
		self.assertEqual("125 ns", fields["Simulation Time"])
		self.assertEqual("9 - 7 passed, 2 failed", fields["Checks"])
		self.assertEqual("0 failures, 2 errors, 1 warnings", fields["Alerts"])
		self.assertEqual("0 failures, 1 errors, 0 warnings", fields["Disabled Alerts"])
		self.assertEqual("1 of 2 passed", fields["Requirements"])
		self.assertEqual("43.8 %", fields["Functional Coverage"])
		self.assertEqual("Demo", fields["Testsuite"])
		self.assertEqual(
			["settings", "AlertLog", "scoreboard int", "transcript"],
			[sub(r" \(.*\)$", "", link) for link in fields["Reports"].split(", ")]
		)
		self.assertEqual(4, html.count("reference download internal"))
		self.assertNotIn(".html\" download", html)
		for title in ("AlertLog", "Scoreboards"):
			with self.subTest(section=title):
				self.assertIn(f"<h2>{title}", html)
		self.assertNotIn("<h2>Functional Coverage", html)
		self.assertIn('class="osvvm-alertlog-table', html)
		self.assertIn("Scoreboards of instance int", html)

	def test_TestcasePage_Coverage(self) -> None:
		self._build("Index\n#####\n", osvvm_build_summaries=PAGES)

		html = self._html("osvvm/demo/Axi4Full/TbAxi4_BasicReadWrite")
		self.assertIn("<h2>Functional Coverage", html)
		self.assertEqual(3, html.count('class="osvvm-coverage-table'))
		self.assertEqual("WIDTH=8", fieldsOf(self._html("osvvm/demo/Demo/TbGenerics_WIDTH_8"))["Generics"])

	def test_TestcasePage_Expected(self) -> None:
		self._build("Index\n#####\n", osvvm_build_summaries=PAGES)

		html = self._html("osvvm/demo/Demo/TbExpected_Failed")
		self.assertEqual("FAILED (expected)", fieldsOf(html)["OSVVM Status"])
		self.assertIn("<h2>Message", html)
		self.assertIn("Checks the error path", html)

	def test_TestcasePage_Skipped(self) -> None:
		self._build("Index\n#####\n", osvvm_build_summaries=PAGES)

		html = self._html("osvvm/demo/Demo/TbDemo_Skipped")
		fields = fieldsOf(html)
		self.assertEqual("SKIPPED", fields["OSVVM Status"])
		self.assertNotIn("Checks", fields)
		self.assertNotIn("Reports", fields)
		self.assertIn("Not supported by NVC", html)
		self.assertNotIn("<h2>AlertLog", html)

	def test_TestsuitePage(self) -> None:
		self._build("Index\n#####\n", osvvm_build_summaries=PAGES)

		html = self._html("osvvm/demo/Demo")
		header = html[html.index("<thead>"):html.index("</thead>")]
		self.assertEqual(
			[
				"Testcase", "Status", "Elapsed Time", "Checks", "Alerts (F/E/W)", "Requirements", "Functional Coverage",
				"Simulation Time"
			],
			findall(r"<p>([^<]*)</p>", header)
		)
		start = html.index(">TbDemo_Failed</span>")
		row = html[start:html.index("</tr>", start)]
		self.assertEqual(
			["❌ Failed", "00:00:00.250", "7 / 9", "0 / 2 / 1", "1 / 2", "43.8 %", "125 ns"], findall(r"<p>([^<]*)</p>", row)
		)

	def test_Navigation(self) -> None:
		app = self._build(
			"Index\n#####\n\n.. osvvm:build-summary::\n   :reportid: demo\n", osvvm_build_summaries=PAGES
		)

		self.assertEqual([], self._warningLines())
		self.assertEqual(["osvvm/demo/Axi4Full", "osvvm/demo/Demo"], app.env.toctree_includes["index"])
		self.assertIn("osvvm/demo/Demo/TbDemo_Failed", app.env.toctree_includes["osvvm/demo/Demo"])
		html = self._html("index")
		self.assertIn(
			'href="osvvm/demo/Demo/TbDemo_Failed.html"><span class="xref osvvm osvvm-tc">TbDemo_Failed</span></a>', html
		)

	def test_MissingReportFile(self) -> None:
		build = self._path / "Demo"
		copytree(DEMO, build)
		(build / "results" / "Demo" / "TbGenerics_WIDTH_8.log").unlink()

		self._build(
			"Index\n#####\n",
			osvvm_build_summaries={"demo": {"yaml_report": str(build / "Demo.yml"), "pages": "osvvm/demo"}}
		)

		self.assertEqual(
			[
				"WARNING: Report file 'Demo/results/Demo/TbGenerics_WIDTH_8.log' of testcase 'TbGenerics_WIDTH_8' doesn't "
				"exist. [osvvm.read]"
			],
			self._warningLines()
		)


class Roles(Project):
	def test_References(self) -> None:
		self._build(
			"Index\n#####\n\n:osvvm:tc:`TbDemo_Failed`, :osvvm:tc:`demo:Demo.TbGenerics_WIDTH_8`, :osvvm:ts:`Axi4Full` and "
			":osvvm:tc:`TbMissing`.\n",
			osvvm_build_summaries=PAGES
		)

		html = self._html("index")
		self.assertIn(
			'href="osvvm/demo/Demo/TbDemo_Failed.html"><span class="xref osvvm osvvm-tc">TbDemo_Failed</span>', html
		)
		self.assertIn('href="osvvm/demo/Demo/TbGenerics_WIDTH_8.html"', html)
		self.assertIn('href="osvvm/demo/Axi4Full.html"><span class="xref osvvm osvvm-ts">Axi4Full</span>', html)
		self.assertEqual(
			["src/index.rst:4: WARNING: testcase 'TbMissing' not found in the OSVVM build summaries [ref.tc]"],
			self._warningLines()
		)


class BuildInformation(Project):
	def test_Fields(self) -> None:
		self._build("Index\n#####\n\n.. osvvm:build-information::\n   :reportid: demo\n")

		self.assertEqual([], self._warningLines())
		html = self._html("index")
		fields = fieldsOf(html)
		self.assertEqual("Demo", fields["Build"])
		self.assertEqual("❌ Failed", fields["Status"])
		self.assertEqual("5 - 3 passed, 1 failed, 1 skipped", fields["Testcases"])
		self.assertEqual("2026-10-10 18:44:02 UTC", fields["Start Time"])
		self.assertEqual("NVC 1.23.0", fields["Simulator"])
		self.assertEqual("2026.09", fields["OSVVM Version"])
		self.assertEqual("2", fields["Simulate Errors"])
		self.assertEqual("log", sub(r" \(.*\)$", "", fields["Log"]))
		self.assertEqual(1, html.count("reference download internal"))

	def test_UnknownReport(self) -> None:
		self._build("Index\n#####\n\n.. osvvm:build-information::\n   :reportid: other\n")

		warnings = self._warningLines()
		self.assertEqual(
			"ERROR: Caught ReportExtensionError when checking options for directive 'build-information'.", warnings[0]
		)
