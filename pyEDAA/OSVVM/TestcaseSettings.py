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
A data model for OSVVM's test case settings file :file:`<TestCaseFileName>_run.yml`, and its reader.

OSVVM writes the settings of a test case (``WriteTestCaseSettingsYaml``) after its simulation, into the reports
directory of its test suite, e.g. :file:`reports/<testsuite>/<test>_run.yml`. OSVVM's :file:`ReportSimulate2Html.tcl`
reads it to write the test case's HTML report from its other report files.

Most of the file repeats the build summary: the test's and the test suite's name, the generics and OSVVM's settings.
What it adds are the links to the test case's files:

* the test case's VHDL source file (``TestCaseFile``),
* its AlertLog report (``AlertYamlFile``), see :mod:`pyEDAA.OSVVM.AlertLog`,
* its functional coverage report (``CovYamlFile``),
* its scoreboard reports, one per scoreboard package instance (``ScoreboardDict``),
* its requirements report (``RequirementsYamlFile``),
* its transcripts (``TranscriptFiles``).

A :class:`~pyEDAA.OSVVM.Build.Testcase` of a build summary links to its settings via
:data:`~pyEDAA.OSVVM.Build.Testcase.TestcaseSettings`, after
:meth:`~pyEDAA.OSVVM.Build.BuildSummaryDocument.ReadTestcaseSettings` read them.

.. rubric:: Example

.. code-block:: Python

   from pathlib import Path
   from pyEDAA.OSVVM.TestcaseSettings import TestcaseSettingsDocument

   settings = TestcaseSettingsDocument(Path("reports/Axi4Full/TbAxi4_BasicReadWrite_run.yml"), analyzeAndConvert=True)
   print(f"{settings.TestName}: {settings.AlertLogFile}")
"""
from __future__              import annotations

from datetime                import timedelta
from pathlib                 import Path
from re                      import finditer
from typing                  import ClassVar, Iterable, Mapping, Optional as Nullable

from pyTooling.Common        import getFullyQualifiedName, StringEnum
from pyTooling.Decorators    import export, readonly
from pyTooling.MetaClasses   import ExtendedType
from pyTooling.Stopwatch     import Stopwatch

from pyEDAA.OSVVM            import OSVVMException, YAMLDocumentMixin
from pyEDAA.OSVVM.Build      import Settings


__all__ = ["SCHEMAS"]

# A class with a property named like a class - ``Path``, ``Settings`` - can't name that class in the annotation of a
# field: the class body's namespace, where annotations are evaluated, binds the name to the property.
_Path =     Path
_Settings = Settings


@export
class TestcaseSettingsError(OSVVMException):
	"""
	The exception raised by the test case settings model and its reader.
	"""


@export
class FormatVersion(StringEnum):
	"""
	Version of OSVVM's test case settings format, as a settings file's ``Version`` states it.

	OSVVM writes ``OsvvmTestCaseYamlVersion`` of :file:`OsvvmSettingsRequired.tcl`, so far only ``0.1``.
	"""

	Version0_1 = "0.1"  #: Format version 0.1.


@export
class TestcaseSettings(metaclass=ExtendedType, slots=True):
	"""
	The settings of a test case, as OSVVM states them after its simulation: names, generics and the test case's files.

	Paths are relative to the build's directory, except :data:`TestcaseFile`, which is relative to the test suite's
	reports directory (:data:`ReportsTestsuiteDirectory`). OSVVM writes an empty string for a file it didn't write; it
	is ``None`` here.
	"""

	_testName:                  str                   #: Name of the test, without the generics' values.
	_testcaseFileName:          str                   #: Base name of the test case's report files.
	_testsuiteName:             str                   #: Name of the test suite.
	_buildName:                 str                   #: Name of the build.
	_genericNames:              str                   #: The generics' names and values, appended to the test's name.
	_generics:                  dict[str, str]        #: Generics the test case was simulated with.
	_testcaseFile:              Nullable[_Path]       #: VHDL source file of the test case.
	_reportsTestsuiteDirectory: _Path                 #: Reports directory of the test suite.
	_alertLogFile:              Nullable[_Path]       #: AlertLog report of the test case.
	_functionalCoverageFile:    Nullable[_Path]       #: Functional coverage report of the test case.
	_requirementsFile:          Nullable[_Path]       #: Requirements report of the test case.
	_scoreboardFiles:           dict[str, _Path]      #: Scoreboard report per scoreboard package instance.
	_transcriptFiles:           list[_Path]           #: Transcripts of the test case.
	_settings:                  Nullable[_Settings]   #: OSVVM's settings of the build.

	def __init__(
		self,
		testName: str,
		testcaseFileName: str,
		testsuiteName: str,
		buildName: str,
		reportsTestsuiteDirectory: Path,
		genericNames: str = "",
		generics: Nullable[Mapping[str, str]] = None,
		testcaseFile: Nullable[Path] = None,
		alertLogFile: Nullable[Path] = None,
		functionalCoverageFile: Nullable[Path] = None,
		requirementsFile: Nullable[Path] = None,
		scoreboardFiles: Nullable[Mapping[str, Path]] = None,
		transcriptFiles: Nullable[Iterable[Path]] = None
	) -> None:
		"""
		Initializes the settings of a test case.

		OSVVM's settings of the build are added by creating them with the test case settings as parent.

		:param testName:                  Name of the test, without the generics' values (``TestCaseName``).
		:param testcaseFileName:          Base name of the test case's report files (``TestCaseFileName``).
		:param testsuiteName:             Name of the test suite (``TestSuiteName``).
		:param buildName:                 Name of the build (``BuildName``).
		:param reportsTestsuiteDirectory: Reports directory of the test suite (``ReportsTestSuiteDirectory``).
		:param genericNames:              Optional, the generics' names and values, as appended to the test's name
		                                  (``GenericNames``). Default: ``""``.
		:param generics:                  Optional, generics the test case was simulated with (``Generics``).
		:param testcaseFile:              Optional, VHDL source file of the test case (``TestCaseFile``).
		:param alertLogFile:              Optional, AlertLog report of the test case (``AlertYamlFile``).
		:param functionalCoverageFile:    Optional, functional coverage report of the test case (``CovYamlFile``).
		:param requirementsFile:          Optional, requirements report of the test case (``RequirementsYamlFile``).
		:param scoreboardFiles:           Optional, scoreboard report per scoreboard package instance
		                                  (``ScoreboardDict``).
		:param transcriptFiles:           Optional, transcripts of the test case (``TranscriptFiles``).
		:raises ValueError:               If parameter 'testName' is None.
		:raises ValueError:               If parameter 'testcaseFileName' is None.
		:raises ValueError:               If parameter 'testsuiteName' is None.
		:raises ValueError:               If parameter 'buildName' is None.
		:raises ValueError:               If parameter 'reportsTestsuiteDirectory' is None.
		:raises TypeError:                If parameter 'testName' is not of type :class:`str`.
		:raises TypeError:                If parameter 'testcaseFileName' is not of type :class:`str`.
		:raises TypeError:                If parameter 'testsuiteName' is not of type :class:`str`.
		:raises TypeError:                If parameter 'buildName' is not of type :class:`str`.
		:raises TypeError:                If parameter 'genericNames' is not of type :class:`str`.
		:raises TypeError:                If parameter 'reportsTestsuiteDirectory' is not of type :class:`~pathlib.Path`.
		:raises TypeError:                If parameter 'testcaseFile' is not of type :class:`~pathlib.Path`.
		:raises TypeError:                If parameter 'alertLogFile' is not of type :class:`~pathlib.Path`.
		:raises TypeError:                If parameter 'functionalCoverageFile' is not of type :class:`~pathlib.Path`.
		:raises TypeError:                If parameter 'requirementsFile' is not of type :class:`~pathlib.Path`.
		:raises TypeError:                If parameter 'generics' is not a mapping.
		:raises TypeError:                If parameter 'scoreboardFiles' is not a mapping.
		:raises TypeError:                If a value of parameter 'scoreboardFiles' is not of type :class:`~pathlib.Path`.
		:raises TypeError:                If parameter 'transcriptFiles' is not iterable.
		:raises TypeError:                If an element of parameter 'transcriptFiles' is not of type
		                                  :class:`~pathlib.Path`.
		"""
		for parameterName, text in (
			("testName",         testName),
			("testcaseFileName", testcaseFileName),
			("testsuiteName",    testsuiteName),
			("buildName",        buildName)
		):
			if text is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(text, str):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'str'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(text)}'.")
				raise ex

		if reportsTestsuiteDirectory is None:
			raise ValueError("Parameter 'reportsTestsuiteDirectory' is None.")

		if not isinstance(genericNames, str):
			ex = TypeError("Parameter 'genericNames' is not of type 'str'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(genericNames)}'.")
			raise ex

		for parameterName, path in (
			("reportsTestsuiteDirectory", reportsTestsuiteDirectory),
			("testcaseFile",              testcaseFile),
			("alertLogFile",              alertLogFile),
			("functionalCoverageFile",    functionalCoverageFile),
			("requirementsFile",          requirementsFile)
		):
			if path is not None and not isinstance(path, Path):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'Path'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(path)}'.")
				raise ex

		for parameterName, mapping in (
			("generics",        generics),
			("scoreboardFiles", scoreboardFiles)
		):
			if mapping is not None and not isinstance(mapping, Mapping):
				ex = TypeError(f"Parameter '{parameterName}' is not a mapping.")
				ex.add_note(f"Got type '{getFullyQualifiedName(mapping)}'.")
				raise ex

		self._scoreboardFiles = scoreboardFileDict = {}
		if scoreboardFiles is not None:
			for scoreboardName, scoreboardFile in scoreboardFiles.items():
				if not isinstance(scoreboardFile, Path):
					ex = TypeError(f"Value '{scoreboardName}' of parameter 'scoreboardFiles' is not of type 'Path'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(scoreboardFile)}'.")
					raise ex

				scoreboardFileDict[scoreboardName] = scoreboardFile

		self._transcriptFiles = transcriptFileList = []
		if transcriptFiles is not None:
			if not isinstance(transcriptFiles, Iterable):
				ex = TypeError("Parameter 'transcriptFiles' is not iterable.")
				ex.add_note(f"Got type '{getFullyQualifiedName(transcriptFiles)}'.")
				raise ex

			for transcriptFile in transcriptFiles:
				if not isinstance(transcriptFile, Path):
					ex = TypeError("Element of parameter 'transcriptFiles' is not of type 'Path'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(transcriptFile)}'.")
					raise ex

				transcriptFileList.append(transcriptFile)

		self._testName =                  testName
		self._testcaseFileName =          testcaseFileName
		self._testsuiteName =             testsuiteName
		self._buildName =                 buildName
		self._genericNames =              genericNames
		self._generics =                  {} if generics is None else dict(generics)
		self._testcaseFile =              testcaseFile
		self._reportsTestsuiteDirectory = reportsTestsuiteDirectory
		self._alertLogFile =              alertLogFile
		self._functionalCoverageFile =    functionalCoverageFile
		self._requirementsFile =          requirementsFile
		self._settings =                  None

	@readonly
	def TestName(self) -> str:
		"""
		Read-only property to access the name of the test, without the generics' values (:attr:`_testName`).

		:returns: The test's name.
		"""
		return self._testName

	@readonly
	def TestcaseFileName(self) -> str:
		"""
		Read-only property to access the base name of the test case's report files (:attr:`_testcaseFileName`).

		It's the name of the test case in the build summary.

		:returns: The base name.
		"""
		return self._testcaseFileName

	@readonly
	def TestsuiteName(self) -> str:
		"""
		Read-only property to access the name of the test suite (:attr:`_testsuiteName`).

		:returns: The test suite's name.
		"""
		return self._testsuiteName

	@readonly
	def BuildName(self) -> str:
		"""
		Read-only property to access the name of the build (:attr:`_buildName`).

		:returns: The build's name.
		"""
		return self._buildName

	@readonly
	def GenericNames(self) -> str:
		"""
		Read-only property to access the generics' names and values, as appended to the test's name (:attr:`_genericNames`).

		:returns: The generics' names and values, e.g. ``_MII_BPS_BPS_1G``; empty, if the test has no generics.
		"""
		return self._genericNames

	@readonly
	def Generics(self) -> dict[str, str]:
		"""
		Read-only property to access the generics the test case was simulated with (:attr:`_generics`).

		:returns: Dictionary of generic names and values.
		"""
		return self._generics

	@readonly
	def TestcaseFile(self) -> Nullable[Path]:
		"""
		Read-only property to access the test case's VHDL source file (:attr:`_testcaseFile`).

		OSVVM states the last file analyzed before the simulation.

		:returns: The source file, relative to :data:`ReportsTestsuiteDirectory`, or ``None`` if OSVVM states none.
		"""
		return self._testcaseFile

	@readonly
	def ReportsTestsuiteDirectory(self) -> Path:
		"""
		Read-only property to access the reports directory of the test suite (:attr:`_reportsTestsuiteDirectory`).

		:returns: The directory, e.g. :file:`reports/<testsuite>`.
		"""
		return self._reportsTestsuiteDirectory

	@readonly
	def AlertLogFile(self) -> Nullable[Path]:
		"""
		Read-only property to access the test case's AlertLog report (:attr:`_alertLogFile`).

		:returns: The AlertLog report :file:`<TestCaseFileName>_alerts.yml`, or ``None`` if OSVVM wrote none.
		"""
		return self._alertLogFile

	@readonly
	def FunctionalCoverageFile(self) -> Nullable[Path]:
		"""
		Read-only property to access the test case's functional coverage report (:attr:`_functionalCoverageFile`).

		:returns: The coverage report :file:`<TestCaseFileName>_cov.yml`, or ``None`` if the test case has no coverage
		          model.
		"""
		return self._functionalCoverageFile

	@readonly
	def RequirementsFile(self) -> Nullable[Path]:
		"""
		Read-only property to access the test case's requirements report (:attr:`_requirementsFile`).

		:returns: The requirements report :file:`<TestCaseFileName>_req.yml`, or ``None`` if the test case has no
		          requirements.
		"""
		return self._requirementsFile

	@readonly
	def ScoreboardFiles(self) -> dict[str, Path]:
		"""
		Read-only property to access the test case's scoreboard reports (:attr:`_scoreboardFiles`).

		:returns: Dictionary of scoreboard package instance names, e.g. ``slv``, and their reports
		          :file:`<TestCaseFileName>_sb_<name>.yml`.
		"""
		return self._scoreboardFiles

	@readonly
	def TranscriptFiles(self) -> list[Path]:
		"""
		Read-only property to access the test case's transcripts (:attr:`_transcriptFiles`).

		:returns: List of transcripts, e.g. :file:`results/<testsuite>/<test>.log`.
		"""
		return self._transcriptFiles

	@readonly
	def Settings(self) -> Nullable[Settings]:
		"""
		Read-only property to access OSVVM's settings of the build (:attr:`_settings`).

		:returns: The settings, or ``None`` if they weren't recorded.
		"""
		return self._settings


SCHEMAS: dict[FormatVersion, str] = {
	FormatVersion.Version0_1: "OSVVM-TestcaseSettings-0.1.schema.json",
}  #: The JSON Schema of :mod:`pyEDAA.OSVVM.Resources` a test case settings file is validated against, per version.


@export
class TestcaseSettingsDocument(TestcaseSettings, YAMLDocumentMixin):
	"""
	An OSVVM test case settings file :file:`<TestCaseFileName>_run.yml`: read and converted to the test case settings.

	:meth:`Analyze` validates the file against the schema of the format version it states (:data:`SCHEMAS`),
	:meth:`Convert` converts it.
	"""

	_DESCRIPTION:    ClassVar[str] =                                "OSVVM test case settings"  #: Format's name.
	_ERROR:          ClassVar[type[TestcaseSettingsError]] =        TestcaseSettingsError       #: Reader's exception.
	_FORMAT_VERSION: ClassVar[type[FormatVersion]] =                FormatVersion               #: Format's versions.
	_SCHEMAS:        ClassVar[dict[FormatVersion, str]] =           SCHEMAS                     #: Schema per version.

	_path:             _Path                #: Path to the YAML file.
	_analysisDuration: Nullable[timedelta]  #: Duration of :meth:`Analyze`, or ``None`` before it ran.
	_modelConversion:  Nullable[timedelta]  #: Duration of :meth:`Convert`, or ``None`` before it ran.

	def __init__(self, yamlFile: Path, analyzeAndConvert: bool = False) -> None:
		"""
		Initializes a test case settings document, and optionally reads it.

		:param yamlFile:          Path to the YAML file.
		:param analyzeAndConvert: Optional, if true, analyze the file and convert its content. Default: ``False``.
		:raises ValueError:       If parameter 'yamlFile' is None.
		:raises TypeError:        If parameter 'yamlFile' is not of type :class:`~pathlib.Path`.
		"""
		super().__init__("Unprocessed", "Unprocessed", "Unprocessed", "Unprocessed", Path("."))
		YAMLDocumentMixin.__init__(self)

		if yamlFile is None:
			raise ValueError("Parameter 'yamlFile' is None.")
		elif not isinstance(yamlFile, Path):
			ex = TypeError("Parameter 'yamlFile' is not of type 'Path'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(yamlFile)}'.")
			raise ex

		self._path =             yamlFile
		self._analysisDuration = None
		self._modelConversion =  None

		if analyzeAndConvert:
			self.Analyze()
			self.Convert()

	@readonly
	def Path(self) -> Path:
		"""
		Read-only property to access the path to the YAML file (:attr:`_path`).

		:returns: The path to the YAML file.
		"""
		return self._path

	@readonly
	def AnalysisDuration(self) -> Nullable[timedelta]:
		"""
		Read-only property to access the analysis duration (:attr:`_analysisDuration`).

		:returns: Duration to analyze the file, or ``None`` if it wasn't analyzed yet.
		"""
		return self._analysisDuration

	@readonly
	def ModelConversionDuration(self) -> Nullable[timedelta]:
		"""
		Read-only property to access the conversion duration (:attr:`_modelConversion`).

		:returns: Duration to convert the file, or ``None`` if it wasn't converted yet.
		"""
		return self._modelConversion

	def Analyze(self) -> None:
		"""
		Analyze the YAML file: parse it, read its format version and validate it against the version's JSON Schema.

		The schema is chosen from :data:`SCHEMAS` by the format version the file states. A key the schema doesn't define
		is an error.

		:raises TestcaseSettingsError: If the file doesn't exist.
		:raises TestcaseSettingsError: If the file can't be read.
		:raises TestcaseSettingsError: If the file isn't UTF-8 encoded.
		:raises TestcaseSettingsError: If the file isn't valid YAML.
		:raises TestcaseSettingsError: If the file's content isn't a YAML mapping.
		:raises TestcaseSettingsError: If the file states no format version. |br|
		                               The note lists the supported format versions.
		:raises TestcaseSettingsError: If the file states an unsupported format version. |br|
		                               The note lists the supported format versions.
		:raises TestcaseSettingsError: If the JSON Schema can't be read.
		:raises TestcaseSettingsError: If the file isn't valid according to the JSON Schema. |br|
		                               A note per violation names its path and line.
		"""
		with Stopwatch() as sw:
			self._AnalyzeYAML()

		self._analysisDuration = sw.Duration

	def Convert(self) -> None:
		"""
		Convert the analyzed YAML data structure into the test case settings.

		``TranscriptFiles`` is a Tcl list: paths are separated by spaces, a path with spaces is braced.

		:raises TestcaseSettingsError: If the YAML file was not analyzed before. |br|
		                               Call 'Document.Analyze()' or create the document using
		                               'Document(path, analyzeAndConvert=True)'.
		"""
		if self._yamlDocument is None:
			ex = TestcaseSettingsError(f"OSVVM test case settings '{self._path}' need to be analyzed by a YAML parser.")
			ex.add_note("Call 'Document.Analyze()' or create the document using 'Document(path, analyzeAndConvert=True)'.")
			raise ex

		with Stopwatch() as sw:
			root = self._yamlDocument

			self._testName =                  str(root["TestCaseName"])
			self._testcaseFileName =          str(root["TestCaseFileName"])
			self._testsuiteName =             str(root["TestSuiteName"])
			self._buildName =                 str(root["BuildName"])
			self._genericNames =              str(root["GenericNames"])
			self._generics =                  {} if (generics := root["Generics"]) is None else {
				str(key): str(value) for key, value in generics.items()
			}
			self._testcaseFile =              None if (path := root["TestCaseFile"]) == "" else Path(path)
			self._reportsTestsuiteDirectory = Path(root["ReportsTestSuiteDirectory"])
			self._alertLogFile =              None if (path := root["AlertYamlFile"]) == "" else Path(path)
			self._functionalCoverageFile =    None if (path := root["CovYamlFile"]) == "" else Path(path)
			self._requirementsFile =          None if (path := root["RequirementsYamlFile"]) == "" else Path(path)
			self._scoreboardFiles =           {} if (scoreboards := root["ScoreboardDict"]) is None else {
				str(name): Path(path) for name, path in scoreboards.items()
			}
			self._transcriptFiles =           [
				Path(match[1] if match[1] is not None else match[2])
				for match in finditer(r"\{([^}]*)\}|(\S+)", root["TranscriptFiles"])
			]

			Settings.Parse(root["OsvvmSettingsInfo"], parent=self)

		self._modelConversion = sw.Duration
