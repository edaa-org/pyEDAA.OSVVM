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
"""Testcases for reading OSVVM's test case settings files and linking them to a build summary's test cases."""
from pathlib                       import Path
from shutil                        import copy
from tempfile                      import TemporaryDirectory

from pyTooling.Testing             import Testcase
from pyTooling.Warning             import WarningCollector

from pyEDAA.OSVVM.Build            import BuildSummaryDocument, TestcaseSettingsWarning
from pyEDAA.OSVVM.TestcaseSettings import TestcaseSettingsDocument

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


DIRECTORY = Path("tests/data/OSVVM/TestcaseSettings")
BUILD =     DIRECTORY / "Osvvm-Libraries_RunDemoTestsWithCoverage"


class Document(Testcase):
	def test_Settings(self) -> None:
		doc = TestcaseSettingsDocument(BUILD / "reports/Axi4Full/TbAxi4_BasicReadWrite_run.yml", analyzeAndConvert=True)

		self.assertEqual("TbAxi4_BasicReadWrite", doc.TestName)
		self.assertEqual("TbAxi4_BasicReadWrite", doc.TestcaseFileName)
		self.assertEqual("Axi4Full", doc.TestsuiteName)
		self.assertEqual("Osvvm-Libraries_RunDemoTestsWithCoverage", doc.BuildName)
		self.assertEqual(Path("../../../../AXI4/Axi4/TestCases/TbAxi4_BasicReadWrite.vhd"), doc.TestcaseFile)
		self.assertEqual(Path("reports/Axi4Full"), doc.ReportsTestsuiteDirectory)
		self.assertEqual(Path("reports/Axi4Full/TbAxi4_BasicReadWrite_alerts.yml"), doc.AlertLogFile)
		self.assertEqual(Path("reports/Axi4Full/TbAxi4_BasicReadWrite_cov.yml"), doc.FunctionalCoverageFile)
		self.assertIsNone(doc.RequirementsFile)
		self.assertEqual({"slv": Path("reports/Axi4Full/TbAxi4_BasicReadWrite_sb_slv.yml")}, doc.ScoreboardFiles)
		self.assertEqual([Path("results/Axi4Full/TbAxi4_BasicReadWrite.log")], doc.TranscriptFiles)
		self.assertEqual("", doc.GenericNames)
		self.assertEqual({}, doc.Generics)
		self.assertIs(doc, doc.Settings.Parent)
		self.assertEqual(
			Path("CodeCoverage/Osvvm-Libraries_RunDemoTestsWithCoverage_code_cov/index.html"),
			doc.Settings.CodeCoverageFile
		)

	def test_Generics(self) -> None:
		doc = TestcaseSettingsDocument(DIRECTORY / "Generics_run.yml", analyzeAndConvert=True)

		self.assertEqual("Tb_xMii1", doc.TestName)
		self.assertEqual("Tb_xMii1_MII_INTERFACE_MII_MII_BPS_BPS_10M", doc.TestcaseFileName)
		self.assertEqual("_MII_INTERFACE_MII_MII_BPS_BPS_10M", doc.GenericNames)
		self.assertEqual({"MII_INTERFACE": "MII", "MII_BPS": "BPS_10M"}, doc.Generics)
		self.assertIsNone(doc.FunctionalCoverageFile)


class Link(Testcase):
	def test_ReadTestcaseSettings(self) -> None:
		build = BuildSummaryDocument(BUILD / "Osvvm-Libraries_RunDemoTestsWithCoverage.yml", analyzeAndConvert=True)
		build.ReadTestcaseSettings()

		testcase = build.Testsuites["Axi4Full"].Testcases["TbAxi4_BasicReadWrite"]
		self.assertEqual(Path("reports/Axi4Full/TbAxi4_BasicReadWrite_alerts.yml"), testcase.TestcaseSettings.AlertLogFile)
		for testcase in build.Testsuites["Axi4Full"].Testcases.values():
			self.assertIsInstance(testcase.TestcaseSettings, TestcaseSettingsDocument)

	def test_ReadTestcaseSettings_Missing(self) -> None:
		with TemporaryDirectory() as directory:
			buildFile = Path(directory) / "Osvvm-Libraries_RunDemoTestsWithCoverage.yml"
			copy(BUILD / buildFile.name, buildFile)
			build = BuildSummaryDocument(buildFile, analyzeAndConvert=True)

			with WarningCollector() as warnings:
				build.ReadTestcaseSettings()

		self.assertEqual(2, len(warnings))
		for warning in warnings:
			self.assertIsInstance(warning, TestcaseSettingsWarning)
		self.assertIsNone(warnings[0].Testcase.TestcaseSettings)
