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
"""Testcases for OSVVM's scoreboard YAML file format."""
from datetime                import timedelta
from pathlib                 import Path

from ruamel.yaml             import YAML

from pyTooling.Testing       import Testcase

from pyEDAA.OSVVM.Scoreboard import Document, FormatVersion, Scoreboard, ScoreboardError

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


DATA = Path("tests/data/OSVVM/Scoreboard")


class Instantiation(Testcase):
	def test_Scoreboard(self) -> None:
		scoreboard = Scoreboard("WriteFifo", "manager_1")

		self.assertIsNone(scoreboard.Parent)
		self.assertEqual("WriteFifo", scoreboard.Name)
		self.assertEqual("manager_1", scoreboard.AlertLogParentName)
		self.assertEqual(0, scoreboard.ItemCount)
		self.assertEqual(0, scoreboard.ErrorCount)
		self.assertEqual(0, scoreboard.CheckedItemCount)
		self.assertEqual(0, scoreboard.PoppedItemCount)
		self.assertEqual(0, scoreboard.DroppedItemCount)
		self.assertEqual(0, scoreboard.FifoCount)

	def test_Scoreboard_Values(self) -> None:
		scoreboard = Scoreboard("ReadSB", "manager_1", 10, 2, 9, 9, 1, 0)

		self.assertEqual(10, scoreboard.ItemCount)
		self.assertEqual(2, scoreboard.ErrorCount)
		self.assertEqual(9, scoreboard.CheckedItemCount)
		self.assertEqual(9, scoreboard.PoppedItemCount)
		self.assertEqual(1, scoreboard.DroppedItemCount)
		self.assertEqual(0, scoreboard.FifoCount)

	def test_Scoreboard_Names(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = Scoreboard(None, "manager_1")

		self.assertEqual("Parameter 'name' is None.", str(context.exception))

		with self.assertRaises(TypeError) as context:
			_ = Scoreboard("WriteFifo", 1)

		self.assertEqual("Parameter 'alertLogParentName' is not of type 'str'.", str(context.exception))

	def test_Scoreboard_Counts(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = Scoreboard("WriteFifo", "manager_1", fifoCount=None)

		self.assertEqual("Parameter 'fifoCount' is None.", str(context.exception))

		with self.assertRaises(TypeError) as context:
			_ = Scoreboard("WriteFifo", "manager_1", errorCount="0")

		self.assertEqual("Parameter 'errorCount' is not of type 'int'.", str(context.exception))

	def test_Scoreboard_Parent(self) -> None:
		document = Document(DATA / "TbEmpty_sb_slv.yml")
		scoreboard1 = Scoreboard("WriteFifo", "manager_1", parent=document)
		scoreboard2 = Scoreboard("WriteFifo", "manager_1", parent=document)

		self.assertIs(document, scoreboard1.Parent)
		self.assertListEqual([scoreboard1, scoreboard2], document.Scoreboards)

		with self.assertRaises(TypeError) as context:
			_ = Scoreboard("WriteFifo", "manager_1", parent="document")

		self.assertEqual("Parameter 'parent' is not of type 'Document'.", str(context.exception))

	def test_Document(self) -> None:
		path = DATA / "TbAxi4_TimeOut_sb_slv.yml"
		document = Document(path)

		self.assertEqual(path, document.Path)
		self.assertEqual("slv", document.Name)
		self.assertIsNone(document.Version)
		self.assertIsNone(document.TestcaseName)
		self.assertEqual(0, document.ScoreboardCount)
		self.assertIsNone(document.AnalysisDuration)
		self.assertIsNone(document.ModelConversionDuration)

	def test_Document_Analyzed(self) -> None:
		document = Document(DATA / "TbAxi4_TimeOut_sb_slv.yml")
		document.Analyze()

		self.assertGreater(document.AnalysisDuration, timedelta())
		self.assertIsNone(document.ModelConversionDuration)

	def test_Document_Name(self) -> None:
		self.assertEqual("int", Document(DATA / "Tb_xMii1_MII_INTERFACE_MII_MII_BPS_BPS_100M_sb_int.yml").Name)
		self.assertIsNone(Document(DATA / "TbDefaultName_sb.yml").Name)

	def test_Document_Path(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = Document(None)

		self.assertEqual("Parameter 'path' is None.", str(context.exception))

		with self.assertRaises(TypeError) as context:
			_ = Document("TbAxi4_TimeOut_sb_slv.yml")

		self.assertEqual("Parameter 'path' is not of type 'Path'.", str(context.exception))


class Parse(Testcase):
	def test_Errors(self) -> None:
		document = Document(DATA / "TbAxi4_TimeOut_sb_slv.yml", analyzeAndConvert=True)

		self.assertIs(FormatVersion.Version0_1, document.Version)
		self.assertEqual("TbAxi4_TimeOut", document.TestcaseName)
		self.assertEqual(13, document.ScoreboardCount)
		self.assertGreater(document.AnalysisDuration, timedelta())
		self.assertGreater(document.ModelConversionDuration, timedelta())

		for scoreboard in document.Scoreboards:
			self.assertIs(document, scoreboard.Parent)

		failed = list(document.IterateScoreboards(lambda scoreboard: scoreboard.ErrorCount > 0))
		self.assertListEqual(["WriteResp SB", "ReadResp SB"], [scoreboard.Name for scoreboard in failed])

		writeResponses = failed[0]
		self.assertEqual("manager_1", writeResponses.AlertLogParentName)
		self.assertEqual(15, writeResponses.ItemCount)
		self.assertEqual(2, writeResponses.ErrorCount)
		self.assertEqual(15, writeResponses.CheckedItemCount)
		self.assertEqual(15, writeResponses.PoppedItemCount)
		self.assertEqual(0, writeResponses.DroppedItemCount)
		self.assertEqual(0, writeResponses.FifoCount)

	def test_ItemsLeft(self) -> None:
		document = Document(DATA / "Tb_xMii1_MII_INTERFACE_MII_MII_BPS_BPS_100M_sb_int.yml", analyzeAndConvert=True)

		self.assertEqual("Tb_xMii1", document.TestcaseName)
		self.assertListEqual(
			[("xmiiphy_1.Rx", 0), ("xmiiphy_1.Tx", 24), ("xmiimac_1.Rx", 27), ("xmiimac_1.Tx", 0)],
			[(scoreboard.AlertLogParentName, scoreboard.FifoCount) for scoreboard in document.Scoreboards]
		)

	def test_SameNameAndParent(self) -> None:
		"""Two scoreboards may have the same name and the same AlertLog parent."""
		document = Document(DATA / "Tb_BasicReadWrite_sb_slv.yml", analyzeAndConvert=True)

		fifos = list(document.IterateScoreboards(lambda scoreboard: scoreboard.Name == "StartTransactionFifo"))
		self.assertEqual(2, len(fifos))
		self.assertEqual(fifos[0].AlertLogParentName, fifos[1].AlertLogParentName)
		self.assertIsNot(fifos[0], fifos[1])

	def test_ParentIsTest(self) -> None:
		document = Document(DATA / "TbUart_SingleProcess_1_sb_Uart.yml", analyzeAndConvert=True)

		self.assertEqual("Uart", document.Name)
		self.assertEqual(1, document.ScoreboardCount)
		self.assertEqual("TbUart_SingleProcess_1", document.Scoreboards[0].AlertLogParentName)

	def test_Empty(self) -> None:
		document = Document(DATA / "TbEmpty_sb_slv.yml", analyzeAndConvert=True)

		self.assertEqual("TbEmpty", document.TestcaseName)
		self.assertEqual(0, document.ScoreboardCount)
		self.assertListEqual([], list(document.IterateScoreboards()))

	def test_UnknownKeys(self) -> None:
		path = DATA / "TbUnknownKeys_sb_slv.yml"

		with self.assertRaises(ScoreboardError) as context:
			_ = Document(path, analyzeAndConvert=True)

		self.assertEqual(
			f"Validation error for OSVVM scoreboard YAML file '{path}' using JSON Schema 'OSVVM-Scoreboard-0.1.schema.json'.",
			str(context.exception)
		)
		self.assertListEqual(
			[
				"/ (line 1): Additional properties are not allowed ('Timestamp' was unexpected)",
				"/Scoreboards/0 (line 5): Additional properties are not allowed ('PeakFifoCount' was unexpected)"
			],
			context.exception.__notes__
		)

	def test_MissingKey(self) -> None:
		path = DATA / "TbMissingKey_sb_slv.yml"

		with self.assertRaises(ScoreboardError) as context:
			_ = Document(path, analyzeAndConvert=True)

		self.assertListEqual(["/Scoreboards/0 (line 4): 'ItemsPopped' is a required property"], context.exception.__notes__)

	def test_Parse_UnknownKey(self) -> None:
		node = YAML().load(DATA.joinpath("TbUnknownKeys_sb_slv.yml").read_text())["Scoreboards"][0]

		with self.assertRaises(ScoreboardError) as context:
			_ = Scoreboard.Parse(node)

		self.assertEqual("Scoreboard at line 5 has unknown key 'PeakFifoCount'.", str(context.exception))

	def test_Parse_MissingKey(self) -> None:
		node = YAML().load(DATA.joinpath("TbMissingKey_sb_slv.yml").read_text())["Scoreboards"][0]

		with self.assertRaises(ScoreboardError) as context:
			_ = Scoreboard.Parse(node)

		self.assertEqual("Scoreboard at line 4 has no key 'ItemsPopped'.", str(context.exception))

	def test_UnsupportedVersion(self) -> None:
		path = DATA / "TbUnsupportedVersion_sb_slv.yml"

		with self.assertRaises(ScoreboardError) as context:
			_ = Document(path, analyzeAndConvert=True)

		self.assertEqual(
			f"OSVVM scoreboard YAML file '{path}' states unsupported format version '1.0'.", str(context.exception)
		)
		self.assertListEqual(
			[
				"Supported format versions: 0.1.",
				"OSVVM restarted its YAML format versions at 0.1 with OSVVM 2026.01; files of older releases aren't supported."
			],
			context.exception.__notes__
		)

	def test_EmptyFile(self) -> None:
		"""OSVVM writes an empty file, if the package instance has no scoreboards."""
		document = Document(DATA / "TbNoScoreboards_sb_slv.yml", analyzeAndConvert=True)

		self.assertEqual("slv", document.Name)
		self.assertIsNone(document.Version)
		self.assertIsNone(document.TestcaseName)
		self.assertEqual(0, document.ScoreboardCount)
		self.assertGreater(document.AnalysisDuration, timedelta())
		self.assertGreater(document.ModelConversionDuration, timedelta())

	def test_FileNotFound(self) -> None:
		path = DATA / "TbMissing_sb_slv.yml"

		with self.assertRaises(ScoreboardError) as context:
			_ = Document(path, analyzeAndConvert=True)

		self.assertEqual(f"OSVVM scoreboard YAML file '{path}' does not exist.", str(context.exception))
		self.assertIsInstance(context.exception.__cause__, FileNotFoundError)

	def test_ConvertBeforeAnalyze(self) -> None:
		document = Document(DATA / "TbEmpty_sb_slv.yml")

		with self.assertRaises(ScoreboardError) as context:
			document.Convert()

		self.assertEqual(
			f"OSVVM scoreboard YAML file '{document.Path}' needs to be read and analyzed by a YAML parser.",
			str(context.exception)
		)
