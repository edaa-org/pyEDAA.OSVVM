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
"""Testcases for reading OSVVM's build summary files."""
from datetime                   import timedelta
from io                         import StringIO
from pathlib                    import Path
from tempfile                   import TemporaryDirectory
from textwrap                   import dedent

from ruamel.yaml                import YAML
from pyTooling.Testing          import Testcase
from pyTooling.Versioning       import YearMonthVersion

from pyEDAA.Reports.Unittesting import TestcaseStatus

from pyEDAA.OSVVM.Build         import BuildSummaryError, DuplicateTestcaseError, OSVVMStatus, BuildSummaryDocument
from pyEDAA.OSVVM.Build         import BuildInformation, Testcase as OSVVMTestcase

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


DIRECTORY = Path("tests/data/OSVVM/Build")

MINIMAL = dedent("""\
	Version: "0.1"
	Date: 2026-10-10T16:50:45+00:00
	Name:     "Minimal"
	BuildInfo:
	  StartTime:            2026-10-10T16:50:45+00:00
	  FinishTime:           2026-10-10T16:50:49+00:00
	  ElapsedTime:              4.225
	  Simulator:            "NVC"
	  SimulatorVersion:     "1.23.0"
	  OsvvmVersion:         "2026.09"
	  BuildErrorCode:       0
	  AnalyzeErrorCount:    0
	  SimulateErrorCount:   0
	OsvvmSettingsInfo:
	  ReportsSubdirectory:  "reports"
	  SimulationLogFile: ""
	  SimulationHtmlLogFile: ""
	  RequirementsSubdirectory: ""
	  CoverageSubdirectory: ""
	  Report2CssFiles:            ""
	  Report2PngFile:  ""
	""")


class Latest(Testcase):
	def test_OsvvmLibraries(self) -> None:
		doc = BuildSummaryDocument(DIRECTORY / "OsvvmLibraries.yml", analyzeAndConvert=True)

		self.assertEqual("Osvvm-Libraries_OsvvmLibraries", doc.Name)
		self.assertEqual(0, len(doc.Testsuites))
		self.assertEqual(YearMonthVersion(2026, 9), doc.BuildInformation.OSVVMVersion)

	def test_RunAllTests_ExternalErrors(self) -> None:
		with self.assertRaises(BuildSummaryError) as context:
			_ = BuildSummaryDocument(DIRECTORY / "RunAllTests.yml", analyzeAndConvert=True)

		notes = context.exception.__notes__
		self.assertEqual(4, len(notes))
		expected = "Additional properties are not allowed ('ExternalErrors' was unexpected)"
		self.assertEqual(f"/TestSuites/0/TestCases/0/Results (line 11): {expected}", notes[0])


class Generics(Testcase):
	def test_Ethernet(self) -> None:
		doc = BuildSummaryDocument(Path("tests/data/OSVVM/OSVVMLibraries_RunAllTests.yml"), analyzeAndConvert=True)

		ethernet = doc.Testsuites["Ethernet"]
		testcase = ethernet.Testcases["Tb_xMii1_MII_INTERFACE_RGMII_MII_BPS_BPS_1G"]

		self.assertEqual(6, len(ethernet.Testcases))
		self.assertEqual("Tb_xMii1", testcase.TestName)
		self.assertEqual({"MII_INTERFACE": "RGMII", "MII_BPS": "BPS_1G"}, testcase.Generics)
		self.assertIsNone(testcase.FunctionalCoverage)
		self.assertEqual({}, ethernet.Testcases["Tb_xMii1"].Generics)


class EdgeCases(Testcase):
	def setUp(self) -> None:
		self.doc = BuildSummaryDocument(DIRECTORY / "EdgeCases.yml", analyzeAndConvert=True)
		self.demo = self.doc.Testsuites["Demo"]

	def test_Skipped(self) -> None:
		testcase = self.demo.Testcases["TbDemo_Skipped"]

		self.assertIs(OSVVMStatus.Skipped, testcase.OSVVMStatus)
		self.assertIs(TestcaseStatus.Skipped, testcase.Status)
		self.assertEqual("Not supported by NVC", testcase.Message)
		self.assertIsNone(testcase.TotalErrorCount)
		self.assertEqual(timedelta(), testcase.TotalDuration)

	def test_AnalyzeFailed(self) -> None:
		testcase = self.demo.Testcases["TbDemo_AnalyzeFailed"]

		self.assertIs(OSVVMStatus.AnalyzeFailed, testcase.OSVVMStatus)
		self.assertIs(TestcaseStatus.Errored, testcase.Status)

	def test_NoReports(self) -> None:
		testcase = self.demo.Testcases["TbDemo_Crashed"]

		self.assertIs(OSVVMStatus.NoReports, testcase.OSVVMStatus)
		self.assertIs(TestcaseStatus.Errored, testcase.Status)
		self.assertIsNone(testcase.VHDLName)

	def test_Failed(self) -> None:
		testcase = self.demo.Testcases["TbDemo_Failed"]

		self.assertIs(TestcaseStatus.Failed, testcase.Status)
		self.assertEqual(125_000_000, testcase.SimulationTime)
		self.assertEqual(0.4375, testcase.FunctionalCoverage)
		self.assertEqual(3, testcase.TotalErrorCount)
		self.assertEqual(1, testcase.WarningCount)
		self.assertEqual(2, testcase.ErrorCount)
		self.assertEqual(1, testcase.DisabledErrorCount)
		self.assertEqual(2, testcase.RequirementsGoalCount)
		self.assertEqual(1, testcase.PassedRequirementsCount)
		self.assertEqual(2, testcase.FailedAssertionCount)

	def test_EmptyTestsuite(self) -> None:
		self.assertEqual(0, len(self.doc.Testsuites["Empty"].Testcases))

	def test_Build(self) -> None:
		self.assertEqual(4, self.doc.TestcaseCount)
		self.assertEqual(YearMonthVersion(2025, 6), self.doc.BuildInformation.OSVVMVersion)
		self.assertEqual("a", self.doc.BuildInformation.OSVVMVersion.Postfix)
		self.assertEqual(1, self.doc.BuildInformation.AnalyzeErrorCount)
		self.assertEqual([], self.doc.Settings.CssFiles)
		self.assertIsNone(self.doc.Settings.SimulationHtmlLogFile)
		self.assertEqual(Path("reports"), self.doc.Settings.RequirementsSubdirectory)


class Errors(Testcase):
	def read(self, text: str) -> BuildSummaryDocument:
		"""
		Write a build summary to a temporary file and read it.

		:param text: The build summary.
		:returns:    The document.
		"""
		with TemporaryDirectory() as directory:
			path = Path(directory) / "build.yml"
			with path.open("w", encoding="utf-8") as file:
				file.write(text)

			return BuildSummaryDocument(path, analyzeAndConvert=True)

	def test_Minimal(self) -> None:
		doc = self.read(MINIMAL)

		self.assertEqual("Minimal", doc.Name)
		self.assertIsNone(doc.Settings.LogoFile)

	def test_Missing(self) -> None:
		with self.assertRaises(BuildSummaryError) as context:
			_ = BuildSummaryDocument(DIRECTORY / "Missing.yml", analyzeAndConvert=True)

		self.assertEqual(f"OSVVM build summary '{DIRECTORY / 'Missing.yml'}' does not exist.", str(context.exception))

	def test_UnsupportedVersion(self) -> None:
		with self.assertRaises(BuildSummaryError) as context:
			_ = self.read(MINIMAL.replace('Version: "0.1"', 'Version: "0.2"'))

		self.assertIn("states unsupported format version '0.2'.", str(context.exception))
		self.assertEqual(["Supported format versions: 0.1."], context.exception.__notes__)

	def test_MissingKey(self) -> None:
		with self.assertRaises(BuildSummaryError) as context:
			_ = self.read(MINIMAL.replace('  Simulator:            "NVC"\n', ""))

		self.assertIn("using JSON Schema 'OSVVM-BuildSummary-0.1.schema.json'.", str(context.exception))
		self.assertEqual(["/BuildInfo (line 4): 'Simulator' is a required property"], context.exception.__notes__)

	def test_UnknownKey(self) -> None:
		with self.assertRaises(BuildSummaryError) as context:
			_ = self.read(MINIMAL.replace('Name:     "Minimal"\n', 'Name:     "Minimal"\nColor: "red"\n'))

		expected = "Additional properties are not allowed ('Color' was unexpected)"
		self.assertEqual([f"/ (line 1): {expected}"], context.exception.__notes__)

	def test_UnknownStatus(self) -> None:
		testsuites = dedent("""\
			TestSuites:
			  - Name: Suite
			    TestCases:
			      - TestCaseName: "tc"
			        Status: "DONE"
			""")
		with self.assertRaises(BuildSummaryError) as context:
			_ = self.read(MINIMAL + testsuites)

		self.assertEqual(1, len(context.exception.__notes__))
		note = context.exception.__notes__[0]
		self.assertTrue(note.startswith("/TestSuites/0/TestCases/0/Status (line 26): 'DONE' is not one of"))

	def test_Parse_UnknownStatus(self) -> None:
		node = YAML().load(StringIO('TestCaseName: "tc"\nStatus: "DONE"\n'))
		with self.assertRaises(BuildSummaryError) as context:
			_ = OSVVMTestcase.Parse(node)

		self.assertEqual("Test case 'tc' at line 1 has unknown status 'DONE'.", str(context.exception))

	def test_DuplicateTestcase(self) -> None:
		testsuites = dedent("""\
			TestSuites:
			  - Name: Suite
			    TestCases:
			      - TestCaseName: "tc"
			      - TestCaseName: "tc"
			""")
		with self.assertRaises(DuplicateTestcaseError) as context:
			_ = self.read(MINIMAL + testsuites)

		self.assertEqual("Test suite 'Suite' has test case 'tc' twice (line 26).", str(context.exception))

	def test_OSVVMVersion(self) -> None:
		with self.assertRaises(BuildSummaryError) as context:
			_ = self.read(MINIMAL.replace('"2026.09"', '"latest"'))

		note = context.exception.__notes__[0]
		self.assertTrue(note.startswith("/BuildInfo/OsvvmVersion (line 10): 'latest' does not match"))

	def test_Parse_OSVVMVersion(self) -> None:
		node = YAML().load(StringIO(MINIMAL.replace('"2026.09"', '"latest"')))["BuildInfo"]
		with self.assertRaises(BuildSummaryError) as context:
			_ = BuildInformation.Parse(node)

		self.assertEqual("OSVVM version at line 10 is not a version YYYY.MM.", str(context.exception))
