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
"""Testcases for OSVVM's functional coverage YAML file format and its conversion to pyEDAA.Reports."""
from pathlib                           import Path
from tempfile                          import TemporaryDirectory

from pyTooling.Testing                 import Testcase

from pyEDAA.Reports.FunctionalCoverage import BinKind, Coverpoint as fc_Coverpoint, Cross as fc_Cross, ValueRange

from pyEDAA.OSVVM.FunctionalCoverage   import Bin, BinType, CountMode, CoverageError, CoverageModel, Document, \
                                              FormatVersion, IllegalMode, ModelSettings, WeightMode


if __name__ == "__main__":  # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unittest <testcase module>'")
	exit(1)


DIRECTORY = Path("tests/data/OSVVM/Coverage")  #: Directory of the coverage files of the tests.

SETTINGS = {
	"CovWeight":       0,
	"Goal":            100.0,
	"WeightMode":      "REMAIN",
	"Seeds":           [56101531, 1187811199],
	"CountMode":       "COUNT_FIRST",
	"IllegalMode":     "ILLEGAL_ON",
	"Threshold":       45.0,
	"ThresholdEnable": "FALSE",
	"IsRequirement":   "TRUE",
	"TotalCovCount":   22,
	"TotalCovGoal":    100
}  #: The settings of a coverage model, as OSVVM writes them.


def CreateModel(dimensions: int, numberOfBins: int = 1) -> dict:
	"""
	Create the mapping of a coverage model of one bin, as OSVVM writes it.

	:param dimensions:   The number of dimensions the model states.
	:param numberOfBins: Optional, the number of bins the model states. Default: ``1``.
	:returns:            The model's mapping.
	"""
	return {
		"Name":      "DelayCov BurstLength",
		"TestCases": ["TbStream_SendGetRandom1"],
		"Coverage":  22.0,
		"Settings":  SETTINGS,
		"BinInfo":   {"Dimensions": dimensions, "FieldNames": ["Bin1"], "NumBins": numberOfBins},
		"Bins":      [
			{"Name": "", "Type": "COUNT", "Range": [{"Min": 3, "Max": 11}], "Count": 19, "AtLeast": 80, "PercentCov": 23.75}
		]
	}


class Enumerations(Testcase):
	def test_FormatVersion(self) -> None:
		self.assertIs(FormatVersion.Version0_1, FormatVersion.Parse("0.1"))

	def test_BinType(self) -> None:
		self.assertEqual(["COUNT", "IGNORE", "ILLEGAL"], [binType.value for binType in BinType])

	def test_Modes(self) -> None:
		self.assertIs(WeightMode.Remain, WeightMode.Parse("REMAIN"))
		self.assertIs(CountMode.CountAll, CountMode.Parse("COUNT_ALL"))
		self.assertIs(IllegalMode.IllegalFailure, IllegalMode.Parse("ILLEGAL_FAILURE"))


class Settings(Testcase):
	def test_Parse(self) -> None:
		settings = ModelSettings.Parse(SETTINGS)

		self.assertEqual(0, settings.CoverageWeight)
		self.assertEqual(100.0, settings.Goal)
		self.assertIs(WeightMode.Remain, settings.WeightMode)
		self.assertEqual((56101531, 1187811199), settings.Seeds)
		self.assertIs(CountMode.CountFirst, settings.CountMode)
		self.assertIs(IllegalMode.IllegalOn, settings.IllegalMode)
		self.assertEqual(45.0, settings.Threshold)
		self.assertFalse(settings.ThresholdEnable)
		self.assertTrue(settings.IsRequirement)
		self.assertEqual(22, settings.TotalCount)
		self.assertEqual(100, settings.TotalGoal)

	def test_Flag(self) -> None:
		settings = dict(SETTINGS)
		settings["IsRequirement"] = "YES"

		with self.assertRaises(ValueError) as context:
			_ = ModelSettings.Parse(settings)
		self.assertEqual("Setting 'IsRequirement' is not 'TRUE' or 'FALSE'.", str(context.exception))

	def test_ParameterChecks(self) -> None:
		valid = (0, 100.0, WeightMode.Remain, (1, 2), CountMode.CountFirst, IllegalMode.IllegalOn, 45.0, False, False, 0, 0)
		for index, value, message in (
			(0,  0.0,                   "Parameter 'coverageWeight' is not of type 'int'."),
			(1,  100,                   "Parameter 'goal' is not of type 'float'."),
			(2,  "REMAIN",              "Parameter 'weightMode' is not of type 'WeightMode'."),
			(3,  (1, ),                 "Parameter 'seeds' is not a tuple of two 'int'."),
			(4,  IllegalMode.IllegalOn, "Parameter 'countMode' is not of type 'CountMode'."),
			(7,  "FALSE",               "Parameter 'thresholdEnable' is not of type 'bool'."),
			(10, 1.0,                   "Parameter 'totalGoal' is not of type 'int'."),
		):
			arguments = list(valid)
			arguments[index] = value
			with self.subTest(message=message):
				with self.assertRaises(TypeError) as context:
					_ = ModelSettings(*arguments)
				self.assertEqual(message, str(context.exception))


class Bins(Testcase):
	def test_Parse(self) -> None:
		coverageBin = Bin.Parse(
			{"Name": "zero", "Type": "ILLEGAL", "Range": [{"Min": 0, "Max": 0}, {"Min": 2, "Max": 8}], "Count": 2,
			 "AtLeast": 0, "PercentCov": 100.0}
		)

		self.assertEqual("zero", coverageBin.Name)
		self.assertIs(BinType.Illegal, coverageBin.Type)
		self.assertEqual([ValueRange(0, 0), ValueRange(2, 8)], coverageBin.Ranges)
		self.assertEqual(2, coverageBin.Count)
		self.assertEqual(0, coverageBin.AtLeast)
		self.assertEqual(100.0, coverageBin.PercentCoverage)
		self.assertIsNone(coverageBin.Parent)
		self.assertIsNone(coverageBin.Root)

	def test_Parse_Integers(self) -> None:
		"""A number OSVVM writes as a real is a float, also when it is written without decimals."""
		settings = dict(SETTINGS)
		settings["Goal"] =      100
		settings["Threshold"] = 45
		coverageBin = Bin.Parse({"Name": "", "Type": "COUNT", "Range": [], "Count": 1, "AtLeast": 1, "PercentCov": 100})

		self.assertIsInstance(ModelSettings.Parse(settings).Goal, float)
		self.assertIsInstance(ModelSettings.Parse(settings).Threshold, float)
		self.assertIsInstance(coverageBin.PercentCoverage, float)

	def test_Parse_Type(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = Bin.Parse({"Name": "", "Type": "AUTO", "Range": [], "Count": 0, "AtLeast": 1, "PercentCov": 0.0})
		self.assertEqual("'AUTO' is not a valid BinType.", str(context.exception))

	def test_ParameterChecks(self) -> None:
		count =  BinType.Count
		ranges = [ValueRange(0, 0)]
		for arguments, message in (
			((None, count,   ranges,   0,   1, 0.0), "Parameter 'name' is not of type 'str'."),
			(("",   "COUNT", ranges,   0,   1, 0.0), "Parameter 'binType' is not of type 'BinType'."),
			(("",   count,   1,        0,   1, 0.0), "Parameter 'ranges' is not iterable."),
			(("",   count,   [(0, 0)], 0,   1, 0.0), "Parameter 'ranges' contains an element not of type 'ValueRange'."),
			(("",   count,   ranges,   0.0, 1, 0.0), "Parameter 'count' is not of type 'int'."),
			(("",   count,   ranges,   0,   1, 0),   "Parameter 'percentCoverage' is not of type 'float'."),
		):
			with self.subTest(message=message):
				with self.assertRaises(TypeError) as context:
					_ = Bin(*arguments)
				self.assertEqual(message, str(context.exception))


class Models(Testcase):
	def test_Parse(self) -> None:
		model = CoverageModel.Parse(CreateModel(1))

		self.assertEqual("DelayCov BurstLength", model.Name)
		self.assertEqual(["TbStream_SendGetRandom1"], model.Testcases)
		self.assertEqual(22.0, model.Coverage)
		self.assertEqual(0, model.Settings.CoverageWeight)
		self.assertEqual(["Bin1"], model.FieldNames)
		self.assertEqual(1, model.Dimensions)
		self.assertIsNone(model.Parent)
		self.assertEqual(1, len(model.Bins))

		coverageBin = model.Bins[0]
		self.assertIs(model, coverageBin.Parent)
		self.assertEqual("", coverageBin.Name)
		self.assertIs(BinType.Count, coverageBin.Type)
		self.assertEqual([ValueRange(3, 11)], coverageBin.Ranges)
		self.assertEqual(19, coverageBin.Count)
		self.assertEqual(80, coverageBin.AtLeast)
		self.assertEqual(23.75, coverageBin.PercentCoverage)

	def test_Dimensions(self) -> None:
		with self.assertRaises(CoverageError) as context:
			_ = CoverageModel.Parse(CreateModel(2))
		self.assertEqual(
			"Coverage model 'DelayCov BurstLength' states another number of dimensions than fields.",
			str(context.exception)
		)
		self.assertEqual(["Got 2 dimensions for 1 field names."], context.exception.__notes__)

	def test_NumberOfBins(self) -> None:
		with self.assertRaises(CoverageError) as context:
			_ = CoverageModel.Parse(CreateModel(1, 2))
		self.assertEqual(
			"Coverage model 'DelayCov BurstLength' states another number of bins than it has.",
			str(context.exception)
		)

	def test_BinRanges(self) -> None:
		model = CoverageModel("M", ["T"], 0.0, ModelSettings.Parse(SETTINGS), ["Bin1", "Bin2"])

		with self.assertRaises(CoverageError) as context:
			_ = Bin("", BinType.Count, [ValueRange(0, 0)], 0, 1, 0.0, parent=model)
		self.assertEqual("Bin has not one range per dimension of coverage model 'M'.", str(context.exception))
		self.assertEqual([], model.Bins)

	def test_ParameterChecks(self) -> None:
		parsed =  ModelSettings.Parse(SETTINGS)
		mapping = SETTINGS
		fields =  ["Bin1"]
		for arguments, exception, message in (
			((1,   ["T"], 0.0, parsed,  fields), TypeError,  "Parameter 'name' is not of type 'str'."),
			(("M", ["T"], 0,   parsed,  fields), TypeError,  "Parameter 'coverage' is not of type 'float'."),
			(("M", ["T"], 0.0, mapping, fields), TypeError,  "Parameter 'settings' is not of type 'ModelSettings'."),
			(("M", 1,     0.0, parsed,  fields), TypeError,  "Parameter 'testcases' is not iterable."),
			(("M", ["T"], 0.0, parsed,  [1]),    TypeError,  "Parameter 'fieldNames' contains an element not of type 'str'."),
			(("M", ["T"], 0.0, parsed,  []),     ValueError, "Parameter 'fieldNames' is empty."),
		):
			with self.subTest(message=message):
				with self.assertRaises(exception) as context:
					_ = CoverageModel(*arguments)
				self.assertEqual(message, str(context.exception))


class Documents(Testcase):
	def test_SendGetRandom1(self) -> None:
		document = Document(DIRECTORY / "TbStream_SendGetRandom1_cov.yml", analyzeAndConvert=True)

		self.assertIs(FormatVersion.Version0_1, document.Version)
		self.assertEqual(100.0, document.Coverage)
		self.assertFalse(document.WritePassFail)
		self.assertIsNotNone(document.AnalysisDuration)
		self.assertIsNotNone(document.ModelConversionDuration)
		self.assertEqual(6, len(document.Models))
		self.assertEqual(
			["DelayCov BurstLength", "DelayCov BurstDelay", "DelayCov BeatDelay"] * 2,
			[model.Name for model in document.Models]
		)
		self.assertEqual([1, 1, 1, 1, 2, 2], [model.Dimensions for model in document.Models])
		self.assertIs(document, document.Models[0].Root)
		self.assertIs(document, document.Models[0].Bins[0].Root)

	def test_Convert_NotAnalyzed(self) -> None:
		document = Document(DIRECTORY / "TbStream_SendGetRandom1_cov.yml")

		with self.assertRaises(CoverageError) as context:
			document.Convert()
		self.assertIn("needs to be read and analyzed by a YAML parser", str(context.exception))

	def test_Missing(self) -> None:
		with self.assertRaises(CoverageError) as context:
			_ = Document(DIRECTORY / "Missing_cov.yml", analyzeAndConvert=True)
		self.assertIsInstance(context.exception.__cause__, FileNotFoundError)

	def test_Version(self) -> None:
		with TemporaryDirectory() as directory:
			path = Path(directory) / "Test_cov.yml"
			path.write_text('Version: "9.9"\nCoverage: 0.00\n', encoding="utf-8")

			with self.assertRaises(CoverageError) as context:
				_ = Document(path, analyzeAndConvert=True)
		self.assertEqual(
			f"OSVVM functional coverage YAML file '{path}' states unsupported format version '9.9'.",
			str(context.exception)
		)
		self.assertEqual(
			[
				"Supported format versions: 0.1.",
				"OSVVM restarted its YAML format versions at 0.1 with OSVVM 2026.01; files of older releases aren't supported."
			],
			context.exception.__notes__
		)

	def test_OldVersion(self) -> None:
		"""OSVVM 2021.10 to 2025.06a wrote format version 1.0."""
		text = (DIRECTORY / "TbStream_SendGetRandom1_cov.yml").read_text(encoding="utf-8")
		text = text.replace('Version: "0.1"', 'Version: "1.0"', 1)

		with TemporaryDirectory() as directory:
			path = Path(directory) / "Test_cov.yml"
			path.write_text(text, encoding="utf-8")

			with self.assertRaises(CoverageError) as context:
				_ = Document(path, analyzeAndConvert=True)
		self.assertEqual(
			f"OSVVM functional coverage YAML file '{path}' states unsupported format version '1.0'.",
			str(context.exception)
		)

	def test_Syntax(self) -> None:
		with TemporaryDirectory() as directory:
			path = Path(directory) / "Test_cov.yml"
			path.write_text('Version: "0.1"\nModels: [\n', encoding="utf-8")

			with self.assertRaises(CoverageError) as context:
				_ = Document(path, analyzeAndConvert=True)
		self.assertEqual(f"YAML syntax error in OSVVM functional coverage YAML file '{path}'.", str(context.exception))

	def test_Schema_MissingKey(self) -> None:
		with TemporaryDirectory() as directory:
			path = Path(directory) / "Test_cov.yml"
			path.write_text('Version: "0.1"\nCoverage: 0.00\nSettings:\n  WritePassFail: 0\n', encoding="utf-8")

			with self.assertRaises(CoverageError) as context:
				_ = Document(path, analyzeAndConvert=True)
		self.assertEqual(
			f"Validation error for OSVVM functional coverage YAML file '{path}' using JSON Schema "
			"'OSVVM-FunctionalCoverage-0.1.schema.json'.",
			str(context.exception)
		)
		self.assertEqual(["/ (line 1): 'Models' is a required property"], context.exception.__notes__)

	def test_Schema_UnknownKey(self) -> None:
		"""A key the format version doesn't have is rejected."""
		text = (DIRECTORY / "TbStream_SendGetRandom1_cov.yml").read_text(encoding="utf-8")
		text = text.replace("      CovWeight: 0\n", "      CovWeight: 0\n      ParentName: \"DelayCov\"\n", 1)

		with TemporaryDirectory() as directory:
			path = Path(directory) / "Test_cov.yml"
			path.write_text(text, encoding="utf-8")

			with self.assertRaises(CoverageError) as context:
				_ = Document(path, analyzeAndConvert=True)
		self.assertEqual(
			["/Models/0/Settings (line 10): Additional properties are not allowed ('ParentName' was unexpected)"],
			context.exception.__notes__
		)

	def test_Schema_Values(self) -> None:
		"""A value of another type or out of the values OSVVM writes is rejected, each with a note."""
		text = (DIRECTORY / "TbStream_SendGetRandom1_cov.yml").read_text(encoding="utf-8")
		text = text.replace('Type: "COUNT"', 'Type: "AUTO"', 1).replace("Count: 19", "Count: -1", 1)

		with TemporaryDirectory() as directory:
			path = Path(directory) / "Test_cov.yml"
			path.write_text(text, encoding="utf-8")

			with self.assertRaises(CoverageError) as context:
				_ = Document(path, analyzeAndConvert=True)
		self.assertEqual(
			[
				"/Models/0/Bins/0/Count (line 32): -1 is less than the minimum of 0",
				"/Models/0/Bins/0/Type (line 29): 'AUTO' is not one of ['COUNT', 'IGNORE', 'ILLEGAL']"
			],
			context.exception.__notes__
		)

	def test_InvalidRange(self) -> None:
		"""A range of a minimum above its maximum passes the schema, and is rejected while converting."""
		text = (DIRECTORY / "TbStream_SendGetRandom1_cov.yml").read_text(encoding="utf-8")
		text = text.replace("{Min: 3, Max: 11}", "{Min: 11, Max: 3}", 1)

		with TemporaryDirectory() as directory:
			path = Path(directory) / "Test_cov.yml"
			path.write_text(text, encoding="utf-8")

			with self.assertRaises(CoverageError) as context:
				_ = Document(path, analyzeAndConvert=True)
		self.assertIsInstance(context.exception.__cause__, ValueError)


class Conversion(Testcase):
	def test_SendGetRandom1(self) -> None:
		document = Document(DIRECTORY / "TbStream_SendGetRandom1_cov.yml", analyzeAndConvert=True)
		report =   document.ConvertToFunctionalCoverageReport()

		self.assertEqual("TbStream_SendGetRandom1", report.Name)
		self.assertFalse(report["WritePassFail"])
		self.assertEqual(6, report.CovergroupCount)
		self.assertEqual(1.0, report.HitCoverage)

		for model, covergroup in zip(document.Models, report.Covergroups):
			with self.subTest(model=model.Name):
				self.assertEqual(model.Name, covergroup.Name)
				self.assertEqual(0, covergroup.Weight)
				self.assertEqual(100.0, covergroup.Goal)
				self.assertEqual(["TbStream_SendGetRandom1"], covergroup.Testcases)
				self.assertEqual(model.Settings.Seeds, covergroup["Seeds"])
				self.assertIs(WeightMode.Remain, covergroup["WeightMode"])
				self.assertAlmostEqual(model.Coverage, round(covergroup.HitCoverage * 100, 2))

		for covergroup in report.Covergroups[:4]:
			self.assertEqual(1, covergroup.CoverpointCount)
			self.assertEqual(0, covergroup.CrossCount)

		for covergroup in report.Covergroups[4:]:
			self.assertEqual(0, covergroup.CoverpointCount)
			self.assertEqual(1, covergroup.CrossCount)

		coverpoint = report.Covergroups[0].Coverpoints["DelayCov BurstLength"]
		self.assertIsInstance(coverpoint, fc_Coverpoint)
		self.assertEqual("Bin1", coverpoint.Expression)
		self.assertEqual([ValueRange(3, 11)], coverpoint.Bins[0].Ranges)
		self.assertIsNone(coverpoint.Bins[0].Name)

		cross = report.Covergroups[4].Crosses["DelayCov BurstDelay"]
		self.assertIsInstance(cross, fc_Cross)
		self.assertEqual(["Bin1", "Bin2"], cross.CrossedItems)
		self.assertEqual([(ValueRange(0, 0), ), (ValueRange(2, 8), )], cross.Bins[0].Ranges)

	def test_SendGetPacketBurst1(self) -> None:
		"""The report's hit coverage is the testcase's coverage OSVVM writes."""
		document = Document(DIRECTORY / "TbStream_SendGetPacketBurst1_cov.yml", analyzeAndConvert=True)
		report =   document.ConvertToFunctionalCoverageReport()

		self.assertEqual(50.0, document.Coverage)
		self.assertAlmostEqual(0.5, report.HitCoverage)
		self.assertEqual([1, 1], [covergroup.Weight for covergroup in report.Covergroups if covergroup.Weight > 0])

	def test_BinTypes(self) -> None:
		"""Ignore and illegal bins become bins of kind ignore and illegal; a named bin keeps its name."""
		text = (DIRECTORY / "TbStream_SendGetRandom1_cov.yml").read_text(encoding="utf-8")
		text = text.replace('Type: "COUNT"', 'Type: "IGNORE"', 1).replace('Type: "COUNT"', 'Type: "ILLEGAL"', 1)
		text = text.replace('Name: ""', 'Name: "short"', 1)

		with TemporaryDirectory() as directory:
			path = Path(directory) / "Kinds_cov.yml"
			path.write_text(text, encoding="utf-8")
			report = Document(path, analyzeAndConvert=True).ConvertToFunctionalCoverageReport()

		self.assertEqual("Kinds", report.Name)
		coverpoint = report.Covergroups[0].Coverpoints["DelayCov BurstLength"]
		self.assertEqual("short", coverpoint.Bins[0].Name)
		self.assertIs(BinKind.Ignore, coverpoint.Bins[0].Kind)
		self.assertIs(BinKind.Illegal, coverpoint.Bins[1].Kind)
		self.assertEqual(0, coverpoint.BinCount)
		self.assertEqual(3, coverpoint.IllegalHitCount)
