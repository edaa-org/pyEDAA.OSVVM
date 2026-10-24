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
# Copyright 2021-2026 Electronic Design Automation Abstraction (EDA²)                                                  #
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
"""Testcase for OSVVM specific file formats."""
from datetime                   import datetime, timedelta, timezone
from pathlib                    import Path

from pyTooling.Testing          import Testcase as py_Testcase
from pyTooling.Versioning       import YearMonthVersion

from pyEDAA.Reports.Unittesting import TestcaseStatus, TestsuiteStatus, Testcase as ut_Testcase
from pyEDAA.Reports.Unittesting import Testsuite as ut_Testsuite, TestsuiteSummary as ut_TestsuiteSummary

from pyEDAA.OSVVM.Build         import BuildSummaryError, FormatVersion, OSVVMStatus, ExpectedResults, Testsuite, \
                                       Testcase, BuildInformation, Settings, TestsuiteSummary, BuildSummaryDocument

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


class Instantiation(py_Testcase):
	def test_Testcase(self) -> None:
		tc = Testcase("tc")

		self.assertEqual("tc", tc.Name)

	def test_Testsuite(self) -> None:
		ts = Testsuite("ts")

		self.assertEqual("ts", ts.Name)

	def test_TestsuiteSummary(self) -> None:
		tss = TestsuiteSummary("tss")

		self.assertEqual("tss", tss.Name)

	def test_BuildSummaryDocument(self) -> None:
		summaryFile = Path("summary.yaml")
		doc = BuildSummaryDocument(summaryFile)

		self.assertEqual("Unprocessed OSVVM YAML file", doc.Name)


class Status(py_Testcase):
	def test_ToTestcaseStatus(self) -> None:
		self.assertIs(TestcaseStatus.Passed, OSVVMStatus.Passed.ToTestcaseStatus())
		self.assertIs(TestcaseStatus.Failed, OSVVMStatus.Failed.ToTestcaseStatus())
		self.assertIs(TestcaseStatus.Skipped, OSVVMStatus.Skipped.ToTestcaseStatus())
		self.assertIs(TestcaseStatus.Errored, OSVVMStatus.AnalyzeFailed.ToTestcaseStatus())
		self.assertIs(TestcaseStatus.Failed, OSVVMStatus.StopLimit.ToTestcaseStatus())
		self.assertIs(TestcaseStatus.Failed, OSVVMStatus.TimeOut.ToTestcaseStatus())
		self.assertIs(TestcaseStatus.Failed, OSVVMStatus.ManualChecks.ToTestcaseStatus())
		self.assertIs(TestcaseStatus.Weak, OSVVMStatus.NoChecks.ToTestcaseStatus())
		self.assertIs(TestcaseStatus.Errored, OSVVMStatus.NoReports.ToTestcaseStatus())

	def test_Parse(self) -> None:
		self.assertIs(OSVVMStatus.AnalyzeFailed, OSVVMStatus.Parse("ANALYZE_FAILED"))


class OSVVMTestcase(py_Testcase):
	def test_Fields(self) -> None:
		tc = Testcase(
			"tc_G1_4",
			testName="tc",
			vhdlName="tcVHDL",
			osvvmStatus=OSVVMStatus.Passed,
			totalDuration=timedelta(seconds=1.5),
			assertionCount=10,
			passedAssertionCount=8,
			totalErrorCount=2,
			warningCount=1,
			errorCount=2,
			fatalCount=3,
			expectedWarningCount=4,
			expectedErrorCount=5,
			expectedFatalCount=6,
			disabledWarningCount=7,
			disabledErrorCount=8,
			disabledFatalCount=9,
			requirementsGoalCount=11,
			passedRequirementsCount=12,
			functionalCoverage=0.5
		)

		self.assertEqual("tc_G1_4", tc.Name)
		self.assertEqual("tc", tc.TestName)
		self.assertEqual("tcVHDL", tc.VHDLName)
		self.assertIs(OSVVMStatus.Passed, tc.OSVVMStatus)
		self.assertEqual(timedelta(seconds=1.5), tc.TotalDuration)
		self.assertEqual(10, tc.AssertionCount)
		self.assertEqual(8, tc.PassedAssertionCount)
		self.assertEqual(2, tc.FailedAssertionCount)
		self.assertEqual(2, tc.TotalErrorCount)
		self.assertEqual(1, tc.WarningCount)
		self.assertEqual(2, tc.ErrorCount)
		self.assertEqual(3, tc.FatalCount)
		self.assertEqual(4, tc.ExpectedWarningCount)
		self.assertEqual(5, tc.ExpectedErrorCount)
		self.assertEqual(6, tc.ExpectedFatalCount)
		self.assertEqual(7, tc.DisabledWarningCount)
		self.assertEqual(8, tc.DisabledErrorCount)
		self.assertEqual(9, tc.DisabledFatalCount)
		self.assertEqual(11, tc.RequirementsGoalCount)
		self.assertEqual(12, tc.PassedRequirementsCount)
		self.assertEqual(0.5, tc.FunctionalCoverage)

	def test_Defaults(self) -> None:
		tc = Testcase("tc")

		self.assertIsNone(tc.TestName)
		self.assertIsNone(tc.VHDLName)
		self.assertIsNone(tc.OSVVMStatus)
		self.assertIsNone(tc.TotalErrorCount)
		self.assertEqual(0, tc.DisabledWarningCount)
		self.assertEqual(0, tc.RequirementsGoalCount)
		self.assertIsNone(tc.FunctionalCoverage)

	def test_Parent(self) -> None:
		ts = Testsuite("ts")
		tc = Testcase("tc", parent=ts)

		self.assertIs(ts, tc.Parent)
		self.assertIs(tc, ts.Testcases["tc"])

	def test_OSVVMStatus_Type(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = Testcase("tc", osvvmStatus="PASSED")

		self.assertEqual("Parameter 'osvvmStatus' is not of type 'OSVVMStatus'.", str(context.exception))

	def test_VHDLName_Type(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = Testcase("tc", vhdlName=1)

		self.assertEqual("Parameter 'vhdlName' is not of type 'str'.", str(context.exception))

	def test_DisabledCount_Type(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = Testcase("tc", disabledErrorCount=None)

		self.assertEqual("Parameter 'disabledErrorCount' is not of type 'int'.", str(context.exception))

	def test_FunctionalCoverage_Type(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = Testcase("tc", functionalCoverage=1)

		self.assertEqual("Parameter 'functionalCoverage' is not of type 'float'.", str(context.exception))

	def test_FunctionalCoverage_Range(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = Testcase("tc", functionalCoverage=1.5)

		self.assertEqual("Parameter 'functionalCoverage' is out of range 0.0..1.0.", str(context.exception))

	def test_Aggregate(self) -> None:
		tc = Testcase("tc", osvvmStatus=OSVVMStatus.NoChecks, assertionCount=0, passedAssertionCount=0)
		tc.Aggregate()

		self.assertIs(TestcaseStatus.Weak, tc.Status)

	def test_Aggregate_Failed(self) -> None:
		tc = Testcase("tc", osvvmStatus=OSVVMStatus.TimeOut, assertionCount=3, passedAssertionCount=3)
		tc.Aggregate()

		self.assertIs(TestcaseStatus.Failed, tc.Status)

	def test_Aggregate_NoOSVVMStatus(self) -> None:
		tc = Testcase("tc", assertionCount=3, passedAssertionCount=3)
		tc.Aggregate()

		self.assertIs(TestcaseStatus.Passed, tc.Status)

	def test_Copy(self) -> None:
		ts = Testsuite("ts")
		tc = Testcase("tc", vhdlName="tcVHDL", osvvmStatus=OSVVMStatus.Failed, disabledWarningCount=2, parent=ts)
		copy = tc.Copy()

		self.assertIs(Testcase, type(copy))
		self.assertIsNone(copy.Parent)
		self.assertEqual("tcVHDL", copy.VHDLName)
		self.assertIs(OSVVMStatus.Failed, copy.OSVVMStatus)
		self.assertEqual(2, copy.DisabledWarningCount)


class Expected(py_Testcase):
	def test_ExpectedResults(self) -> None:
		expected = ExpectedResults(OSVVMStatus.Failed, 3, 1, 2, 0)

		self.assertIs(OSVVMStatus.Failed, expected.OSVVMStatus)
		self.assertEqual(3, expected.TotalErrorCount)
		self.assertEqual(1, expected.WarningCount)
		self.assertEqual(2, expected.ErrorCount)
		self.assertEqual(0, expected.FatalCount)

	def test_ExpectedResults_None(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = ExpectedResults(None)

		self.assertEqual("Parameter 'osvvmStatus' is None.", str(context.exception))

	def test_Aggregate_Matches(self) -> None:
		expected = ExpectedResults(OSVVMStatus.Failed, 1, 0, 1, 0)
		tc = Testcase("tc", osvvmStatus=OSVVMStatus.Failed, totalErrorCount=1, errorCount=1, expectedResults=expected)
		tc.Aggregate()

		self.assertIs(TestcaseStatus.ExpectedFailed, tc.Status)

	def test_Aggregate_Mismatch(self) -> None:
		expected = ExpectedResults(OSVVMStatus.Failed, 1, 0, 1, 0)
		tc = Testcase("tc", osvvmStatus=OSVVMStatus.Failed, totalErrorCount=2, errorCount=2, expectedResults=expected)
		tc.Aggregate()

		self.assertIs(TestcaseStatus.Failed, tc.Status)

	def test_Aggregate_Skipped(self) -> None:
		tc = Testcase("tc", osvvmStatus=OSVVMStatus.Skipped, expectedResults=ExpectedResults(OSVVMStatus.Skipped))
		tc.Aggregate()

		self.assertIs(TestcaseStatus.ExpectedFailed, tc.Status)

	def test_ExpectedResults_Type(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = Testcase("tc", expectedResults="FAILED")

		self.assertEqual("Parameter 'expectedResults' is not of type 'ExpectedResults'.", str(context.exception))


class Conversion(py_Testcase):
	def test_ToTestcase(self) -> None:
		tc = Testcase("tc", osvvmStatus=OSVVMStatus.Passed, assertionCount=3, passedAssertionCount=3, warningCount=1)
		tc.Aggregate()
		unified = tc.ToTestcase()

		self.assertIs(ut_Testcase, type(unified))
		self.assertEqual("tc", unified.Name)
		self.assertIs(TestcaseStatus.Passed, unified.Status)
		self.assertEqual(3, unified.AssertionCount)
		self.assertEqual(1, unified.WarningCount)

	def test_ToTestsuite(self) -> None:
		ts = Testsuite("ts", totalDuration=timedelta(seconds=2))
		Testcase("tc1", osvvmStatus=OSVVMStatus.Passed, parent=ts)
		Testcase("tc2", osvvmStatus=OSVVMStatus.Failed, parent=ts)
		ts.Aggregate()
		unified = ts.ToTestsuite()

		self.assertIs(ut_Testsuite, type(unified))
		self.assertEqual("ts", unified.Name)
		self.assertEqual(timedelta(seconds=2), unified.TotalDuration)
		self.assertEqual(2, len(unified.Testcases))
		for testcase in unified.Testcases.values():
			self.assertIs(ut_Testcase, type(testcase))
			self.assertIs(unified, testcase.Parent)
		self.assertIs(TestcaseStatus.Failed, unified.Testcases["tc2"].Status)


class Build(py_Testcase):
	def test_BuildInformation(self) -> None:
		tss = TestsuiteSummary("build")
		finishTime = datetime(2026, 10, 10, 16, 50, 49, tzinfo=timezone.utc)
		info = BuildInformation("NVC", "1.23.0", YearMonthVersion(2026, 9), finishTime, 1, 2, 3, parent=tss)

		self.assertIs(info, tss.BuildInformation)
		self.assertIs(tss, info.Parent)
		self.assertEqual("NVC", info.Simulator)
		self.assertEqual("1.23.0", info.SimulatorVersion)
		self.assertEqual(YearMonthVersion(2026, 9), info.OSVVMVersion)
		self.assertEqual(finishTime, info.FinishTime)
		self.assertEqual(1, info.BuildErrorCode)
		self.assertEqual(2, info.AnalyzeErrorCount)
		self.assertEqual(3, info.SimulateErrorCount)

	def test_BuildInformation_Twice(self) -> None:
		tss = TestsuiteSummary("build")
		BuildInformation("NVC", "1.23.0", YearMonthVersion(2026, 9), parent=tss)

		with self.assertRaises(BuildSummaryError) as context:
			_ = BuildInformation("GHDL", "6.0.0", YearMonthVersion(2026, 9), parent=tss)

		self.assertEqual("Build 'build' has build information already.", str(context.exception))

	def test_BuildInformation_OSVVMVersion(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = BuildInformation("NVC", "1.23.0", "2026.09")

		self.assertEqual("Parameter 'osvvmVersion' is not of type 'YearMonthVersion'.", str(context.exception))

	def test_Settings(self) -> None:
		tss = TestsuiteSummary("build")
		settings = Settings(
			Path("reports"),
			simulationLogFile=Path("logs/build.log"),
			cssFiles=(Path("reports/CssOsvvmStyle.css"), ),
			logoFile=Path("reports/OsvvmLogo.png"),
			parent=tss
		)

		self.assertIs(settings, tss.Settings)
		self.assertIs(tss, settings.Parent)
		self.assertEqual(Path("reports"), settings.ReportsSubdirectory)
		self.assertEqual(Path("logs/build.log"), settings.SimulationLogFile)
		self.assertIsNone(settings.SimulationHtmlLogFile)
		self.assertIsNone(settings.RequirementsSubdirectory)
		self.assertIsNone(settings.CodeCoverageFile)
		self.assertEqual([Path("reports/CssOsvvmStyle.css")], settings.CssFiles)
		self.assertEqual(Path("reports/OsvvmLogo.png"), settings.LogoFile)

	def test_Settings_CssFiles(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = Settings(Path("reports"), cssFiles=("reports/CssOsvvmStyle.css", ))

		self.assertEqual("Element of parameter 'cssFiles' is not of type 'Path'.", str(context.exception))

	def test_ToTestsuiteSummary(self) -> None:
		tss = TestsuiteSummary("build", totalDuration=timedelta(seconds=3))
		ts = Testsuite("ts", parent=tss)
		Testcase("tc", osvvmStatus=OSVVMStatus.Passed, parent=ts)
		tss.Aggregate()
		unified = tss.ToTestsuiteSummary()

		self.assertIs(ut_TestsuiteSummary, type(unified))
		self.assertEqual("build", unified.Name)
		self.assertEqual(timedelta(seconds=3), unified.TotalDuration)
		self.assertIs(TestsuiteStatus.Passed, unified.Status)
		self.assertIs(ut_Testsuite, type(unified.Testsuites["ts"]))
		self.assertIs(ut_Testcase, type(unified.Testsuites["ts"].Testcases["tc"]))


class Document(py_Testcase):
	def test_OsvvmLibraries(self) -> None:
		doc = BuildSummaryDocument(Path("tests/data/OSVVM/OSVVMLibraries_OsvvmLibraries.yml"), analyzeAndConvert=True)

		self.assertIs(FormatVersion.Version0_1, doc.Version)
		self.assertEqual(datetime(2026, 2, 22, 20, 21, 10, tzinfo=timezone(timedelta(hours=1))), doc.Date)
		self.assertEqual("OsvvmLibraries", doc.Name)
		self.assertEqual(timedelta(seconds=6.723), doc.TotalDuration)
		self.assertEqual("NVC", doc.BuildInformation.Simulator)
		self.assertEqual("1.19.2", doc.BuildInformation.SimulatorVersion)
		self.assertEqual(YearMonthVersion(2026, 1), doc.BuildInformation.OSVVMVersion)
		self.assertEqual(Path("logs/OsvvmLibraries.log"), doc.Settings.SimulationLogFile)
		self.assertIsNone(doc.Settings.RequirementsSubdirectory)
		self.assertEqual([Path("reports/CssOsvvmStyle.css")], doc.Settings.CssFiles)

	def test_RunAllTests(self) -> None:
		doc = BuildSummaryDocument(Path("tests/data/OSVVM/OSVVMLibraries_RunAllTests.yml"), analyzeAndConvert=True)
		testcase = doc.Testsuites["StreamTransactionPkg"].Testcases["TbStream_SendGet1"]

		self.assertIs(OSVVMStatus.Passed, testcase.OSVVMStatus)
		self.assertIs(TestcaseStatus.Passed, testcase.Status)
		self.assertEqual("TbStream_SendGet1", testcase.VHDLName)
		self.assertEqual(1296, testcase.AssertionCount)
		self.assertEqual(1294, testcase.PassedAssertionCount)
		self.assertEqual(2, testcase.ExpectedErrorCount)
		self.assertEqual(1.0, testcase.FunctionalCoverage)
		self.assertIs(TestsuiteStatus.Passed, doc.Status)
