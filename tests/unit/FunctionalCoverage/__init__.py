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
"""Testcases for OSVVM's functional coverage YAML file format: enumerations, settings and bins."""
from pyTooling.Testing                 import Testcase

from pyEDAA.Reports.FunctionalCoverage import ValueRange

from pyEDAA.OSVVM.FunctionalCoverage   import Bin, BinType, CountMode, FormatVersion, IllegalMode, ModelSettings, \
                                              WeightMode


if __name__ == "__main__":  # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unittest <testcase module>'")
	exit(1)


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
