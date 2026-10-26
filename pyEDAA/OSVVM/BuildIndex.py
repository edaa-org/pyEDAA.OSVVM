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
A data model for OSVVM's build index file :file:`index.yml`, and its reader.

OSVVM appends an entry to the build index for every build it runs in an output directory: the build's name and
directory, its status, its test case counts, its error counts, its times and the tools it used. OSVVM's
:file:`ReportIndex2Html.tcl` renders it as :file:`index.html`. A build run twice has two entries, so the entries are a
list in the order OSVVM wrote them.

An entry links to the build's summary file :file:`<Directory>/<Name>.yml` (:data:`BuildEntry.BuildSummaryFile`), which
:class:`~pyEDAA.OSVVM.Build.BuildSummaryDocument` reads.

.. rubric:: Example

.. code-block:: Python

   from pathlib import Path
   from pyEDAA.OSVVM.BuildIndex import BuildIndexDocument

   index = BuildIndexDocument(Path("temp/index.yml"), analyzeAndConvert=True)
   for build in index.IterateBuilds():
     print(f"{build.Name}: {build.Status} - {build.PassedCount}/{build.TestcaseCount}")
"""
from __future__              import annotations

from datetime                import datetime, timedelta
from pathlib                 import Path
from re                      import fullmatch
from typing                  import Callable, ClassVar, Generator, Iterable, Optional as Nullable

from ruamel.yaml             import CommentedMap
from pyTooling.Common        import getFullyQualifiedName, StringEnum
from pyTooling.Decorators    import export, readonly
from pyTooling.MetaClasses   import ExtendedType
from pyTooling.Stopwatch     import Stopwatch
from pyTooling.Versioning    import YearMonthVersion

from pyEDAA.OSVVM            import OSVVMException, YAMLDocumentMixin


__all__ = ["SCHEMAS"]

# A class with a property named like a class - ``Path`` - can't name that class in the annotation of a field: the class
# body's namespace, where annotations are evaluated, binds the name to the property.
_Path = Path


@export
class BuildIndexError(OSVVMException):
	"""
	The exception raised by the build index model and its reader.
	"""


@export
class FormatVersion(StringEnum):
	"""
	Version of OSVVM's build index format, as a build index's ``Version`` states it.

	OSVVM writes ``OsvvmIndexYamlVersion`` of :file:`OsvvmSettingsRequired.tcl`, so far only ``0.1``.
	"""

	Version0_1 = "0.1"  #: Format version 0.1.


@export
class BuildStatus(StringEnum):
	"""
	Status of a build, as OSVVM's ``ReportBuildYaml2Dict`` determines it.
	"""

	Passed = "PASSED"  #: All test cases passed or were skipped, and the build had no analysis or simulation errors.
	Failed = "FAILED"  #: A test case failed, or the build had errors.


@export
class BuildEntry(metaclass=ExtendedType, slots=True):
	"""
	An entry of the build index (an element of ``Builds``): a build's summary.

	Paths are relative to the build index' directory. Times are as OSVVM states them, in the time zone of the machine
	that ran the build.
	"""

	_parent:             Nullable[BuildIndex]  #: The build index the entry belongs to.
	_name:               str                   #: Name of the build.
	_directory:          _Path                 #: Directory of the build's reports.
	_status:             BuildStatus           #: Status of the build.
	_passedCount:        int                   #: Number of passed test cases.
	_failedCount:        int                   #: Number of failed test cases.
	_skippedCount:       int                   #: Number of skipped test cases.
	_analyzeErrorCount:  int                   #: Number of analysis errors.
	_simulateErrorCount: int                   #: Number of simulation errors.
	_buildErrorCode:     int                   #: Error code of the build; ``0``, if the build succeeded.
	_startTime:          datetime              #: Time when the build started.
	_finishTime:         datetime              #: Time when the build finished.
	_elapsedTime:        timedelta             #: Duration of the build.
	_toolName:           str                   #: Name of the simulator, followed by its arguments, if any.
	_toolVersion:        str                   #: Version of the simulator.
	_osvvmVersion:       YearMonthVersion      #: Version of OSVVM.

	def __init__(
		self,
		name: str,
		directory: Path,
		status: BuildStatus,
		passedCount: int,
		failedCount: int,
		skippedCount: int,
		analyzeErrorCount: int,
		simulateErrorCount: int,
		buildErrorCode: int,
		startTime: datetime,
		finishTime: datetime,
		elapsedTime: timedelta,
		toolName: str,
		toolVersion: str,
		osvvmVersion: YearMonthVersion,
		*,
		parent: Nullable[BuildIndex] = None
	) -> None:
		"""
		Initializes an entry of the build index, and adds it to its build index.

		:param name:               Name of the build (``Name``).
		:param directory:          Directory of the build's reports (``Directory``).
		:param status:             Status of the build (``Status``).
		:param passedCount:        Number of passed test cases (``Passed``).
		:param failedCount:        Number of failed test cases (``Failed``).
		:param skippedCount:       Number of skipped test cases (``Skipped``).
		:param analyzeErrorCount:  Number of analysis errors (``AnalyzeErrorCount``).
		:param simulateErrorCount: Number of simulation errors (``SimulateErrorCount``).
		:param buildErrorCode:     Error code of the build (``BuildErrorCode``).
		:param startTime:          Time when the build started (``StartTime``).
		:param finishTime:         Time when the build finished (``FinishTime``).
		:param elapsedTime:        Duration of the build (``ElapsedTime``).
		:param toolName:           Name of the simulator, followed by its arguments, if any (``ToolName``).
		:param toolVersion:        Version of the simulator (``ToolVersion``).
		:param osvvmVersion:       Version of OSVVM (``OsvvmVersion``).
		:param parent:             Optional, the build index the entry belongs to.
		:raises ValueError:        If parameter 'name' is None.
		:raises ValueError:        If parameter 'directory' is None.
		:raises ValueError:        If parameter 'status' is None.
		:raises ValueError:        If parameter 'passedCount' is None.
		:raises ValueError:        If parameter 'failedCount' is None.
		:raises ValueError:        If parameter 'skippedCount' is None.
		:raises ValueError:        If parameter 'analyzeErrorCount' is None.
		:raises ValueError:        If parameter 'simulateErrorCount' is None.
		:raises ValueError:        If parameter 'buildErrorCode' is None.
		:raises ValueError:        If parameter 'startTime' is None.
		:raises ValueError:        If parameter 'finishTime' is None.
		:raises ValueError:        If parameter 'elapsedTime' is None.
		:raises ValueError:        If parameter 'toolName' is None.
		:raises ValueError:        If parameter 'toolVersion' is None.
		:raises ValueError:        If parameter 'osvvmVersion' is None.
		:raises TypeError:         If parameter 'name' is not of type :class:`str`.
		:raises TypeError:         If parameter 'toolName' is not of type :class:`str`.
		:raises TypeError:         If parameter 'toolVersion' is not of type :class:`str`.
		:raises ValueError:        If parameter 'name' is empty.
		:raises TypeError:         If parameter 'directory' is not of type :class:`~pathlib.Path`.
		:raises TypeError:         If parameter 'status' is not of type :class:`BuildStatus`.
		:raises TypeError:         If parameter 'passedCount' is not of type :class:`int`.
		:raises TypeError:         If parameter 'failedCount' is not of type :class:`int`.
		:raises TypeError:         If parameter 'skippedCount' is not of type :class:`int`.
		:raises TypeError:         If parameter 'analyzeErrorCount' is not of type :class:`int`.
		:raises TypeError:         If parameter 'simulateErrorCount' is not of type :class:`int`.
		:raises TypeError:         If parameter 'buildErrorCode' is not of type :class:`int`.
		:raises TypeError:         If parameter 'startTime' is not of type :class:`~datetime.datetime`.
		:raises TypeError:         If parameter 'finishTime' is not of type :class:`~datetime.datetime`.
		:raises TypeError:         If parameter 'elapsedTime' is not of type :class:`~datetime.timedelta`.
		:raises TypeError:         If parameter 'osvvmVersion' is not of type
		                           :class:`~pyTooling.Versioning.YearMonthVersion`.
		:raises TypeError:         If parameter 'parent' is not of type :class:`BuildIndex`.
		"""
		for parameterName, value, valueType in (
			("name",               name,               str),
			("directory",          directory,          Path),
			("status",             status,             BuildStatus),
			("passedCount",        passedCount,        int),
			("failedCount",        failedCount,        int),
			("skippedCount",       skippedCount,       int),
			("analyzeErrorCount",  analyzeErrorCount,  int),
			("simulateErrorCount", simulateErrorCount, int),
			("buildErrorCode",     buildErrorCode,     int),
			("startTime",          startTime,          datetime),
			("finishTime",         finishTime,         datetime),
			("elapsedTime",        elapsedTime,        timedelta),
			("toolName",           toolName,           str),
			("toolVersion",        toolVersion,        str),
			("osvvmVersion",       osvvmVersion,       YearMonthVersion)
		):
			if value is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(value, valueType):
				ex = TypeError(f"Parameter '{parameterName}' is not of type '{valueType.__name__}'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(value)}'.")
				raise ex

		if name == "":
			raise ValueError("Parameter 'name' is empty.")

		if parent is not None and not isinstance(parent, BuildIndex):
			ex = TypeError("Parameter 'parent' is not of type 'BuildIndex'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
			raise ex

		self._parent =             parent
		self._name =               name
		self._directory =          directory
		self._status =             status
		self._passedCount =        passedCount
		self._failedCount =        failedCount
		self._skippedCount =       skippedCount
		self._analyzeErrorCount =  analyzeErrorCount
		self._simulateErrorCount = simulateErrorCount
		self._buildErrorCode =     buildErrorCode
		self._startTime =          startTime
		self._finishTime =         finishTime
		self._elapsedTime =        elapsedTime
		self._toolName =           toolName
		self._toolVersion =        toolVersion
		self._osvvmVersion =       osvvmVersion

		if parent is not None:
			parent._builds.append(self)

	@classmethod
	def Parse(cls, node: CommentedMap, *, parent: Nullable[BuildIndex] = None) -> BuildEntry:
		"""
		Parse an entry of the build index (an element of ``Builds``).

		The mapping must be valid according to the build index' schema (:data:`SCHEMAS`). OSVVM writes the times quoted, so
		YAML reads them as strings.

		:param node:             The YAML mapping of the entry.
		:param parent:           Optional, the build index the entry belongs to.
		:returns:                The entry.
		:raises BuildIndexError: If the status is unknown. |br|
		                         The note lists the allowed values.
		:raises BuildIndexError: If ``Tests`` isn't the sum of ``Passed``, ``Failed`` and ``Skipped``.
		:raises BuildIndexError: If a time isn't an ISO 8601 timestamp.
		:raises BuildIndexError: If the OSVVM version isn't a version ``YYYY.MM``, optionally followed by a revision
		                         letter.
		"""
		line = node.lc.line + 1
		name = node["Name"]

		try:
			status = BuildStatus.Parse(node["Status"])
		except ValueError as cause:
			ex = BuildIndexError(f"Build '{name}' at line {line} has unknown status '{node['Status']}'.")
			ex.add_note(f"Allowed values: {', '.join(BuildStatus)}.")
			raise ex from cause

		if node["Tests"] != node["Passed"] + node["Failed"] + node["Skipped"]:
			ex = BuildIndexError(f"Build '{name}' at line {line} states 'Tests' unequal to passed, failed and skipped.")
			ex.add_note(f"Got {node['Tests']} tests: {node['Passed']}, {node['Failed']} and {node['Skipped']}.")
			raise ex

		try:
			startTime =  datetime.fromisoformat(node["StartTime"])
			finishTime = datetime.fromisoformat(node["FinishTime"])
		except ValueError as cause:
			raise BuildIndexError(f"Build '{name}' at line {line} states a time, which isn't ISO 8601.") from cause

		osvvmVersion = node["OsvvmVersion"]
		if (match := fullmatch(r"(\d{4})\.(\d{1,2})([a-z]?)", osvvmVersion)) is None:
			ex = BuildIndexError(f"OSVVM version of build '{name}' at line {line} is not a version YYYY.MM.")
			ex.add_note(f"Got value '{osvvmVersion}'.")
			raise ex

		return cls(
			str(name),
			Path(node["Directory"]),
			status,
			int(node["Passed"]),
			int(node["Failed"]),
			int(node["Skipped"]),
			int(node["AnalyzeErrorCount"]),
			int(node["SimulateErrorCount"]),
			int(node["BuildErrorCode"]),
			startTime,
			finishTime,
			timedelta(seconds=float(node["ElapsedTime"])),
			str(node["ToolName"]),
			str(node["ToolVersion"]),
			YearMonthVersion(int(match[1]), int(match[2]), postfix=None if match[3] == "" else match[3]),
			parent=parent
		)

	@readonly
	def Parent(self) -> Nullable[BuildIndex]:
		"""
		Read-only property to access the build index the entry belongs to (:attr:`_parent`).

		:returns: The build index, or ``None`` if the entry doesn't belong to one.
		"""
		return self._parent

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the build's name (:attr:`_name`).

		:returns: The build's name.
		"""
		return self._name

	@readonly
	def Directory(self) -> Path:
		"""
		Read-only property to access the directory of the build's reports (:attr:`_directory`).

		:returns: The directory, relative to the build index' directory.
		"""
		return self._directory

	@readonly
	def BuildSummaryFile(self) -> Path:
		"""
		Read-only property to return the build's summary file :file:`<Directory>/<Name>.yml`.

		:returns: The build summary file, relative to the build index' directory.
		"""
		return self._directory / f"{self._name}.yml"

	@readonly
	def Status(self) -> BuildStatus:
		"""
		Read-only property to access the build's status (:attr:`_status`).

		:returns: The build's status.
		"""
		return self._status

	@readonly
	def PassedCount(self) -> int:
		"""
		Read-only property to access the number of passed test cases (:attr:`_passedCount`).

		:returns: Number of passed test cases.
		"""
		return self._passedCount

	@readonly
	def FailedCount(self) -> int:
		"""
		Read-only property to access the number of failed test cases (:attr:`_failedCount`).

		:returns: Number of failed test cases.
		"""
		return self._failedCount

	@readonly
	def SkippedCount(self) -> int:
		"""
		Read-only property to access the number of skipped test cases (:attr:`_skippedCount`).

		:returns: Number of skipped test cases.
		"""
		return self._skippedCount

	@readonly
	def TestcaseCount(self) -> int:
		"""
		Read-only property to return the number of test cases (``Tests``).

		:returns: Sum of passed, failed and skipped test cases.
		"""
		return self._passedCount + self._failedCount + self._skippedCount

	@readonly
	def AnalyzeErrorCount(self) -> int:
		"""
		Read-only property to access the number of analysis errors (:attr:`_analyzeErrorCount`).

		:returns: Number of analysis errors.
		"""
		return self._analyzeErrorCount

	@readonly
	def SimulateErrorCount(self) -> int:
		"""
		Read-only property to access the number of simulation errors (:attr:`_simulateErrorCount`).

		:returns: Number of simulation errors.
		"""
		return self._simulateErrorCount

	@readonly
	def BuildErrorCode(self) -> int:
		"""
		Read-only property to access the build's error code (:attr:`_buildErrorCode`).

		:returns: The error code; ``0``, if the build succeeded.
		"""
		return self._buildErrorCode

	@readonly
	def StartTime(self) -> datetime:
		"""
		Read-only property to access the time when the build started (:attr:`_startTime`).

		:returns: The start time.
		"""
		return self._startTime

	@readonly
	def FinishTime(self) -> datetime:
		"""
		Read-only property to access the time when the build finished (:attr:`_finishTime`).

		:returns: The finish time.
		"""
		return self._finishTime

	@readonly
	def ElapsedTime(self) -> timedelta:
		"""
		Read-only property to access the build's duration (:attr:`_elapsedTime`).

		:returns: The duration.
		"""
		return self._elapsedTime

	@readonly
	def ToolName(self) -> str:
		"""
		Read-only property to access the simulator's name, followed by its arguments, if any (:attr:`_toolName`).

		:returns: The simulator.
		"""
		return self._toolName

	@readonly
	def ToolVersion(self) -> str:
		"""
		Read-only property to access the simulator's version (:attr:`_toolVersion`).

		:returns: The simulator's version.
		"""
		return self._toolVersion

	@readonly
	def OSVVMVersion(self) -> YearMonthVersion:
		"""
		Read-only property to access OSVVM's version (:attr:`_osvvmVersion`).

		:returns: OSVVM's version.
		"""
		return self._osvvmVersion


@export
class BuildIndex(metaclass=ExtendedType, slots=True):
	"""
	OSVVM's build index: the entries of the builds OSVVM ran in an output directory, in the order OSVVM wrote them.
	"""

	_builds: list[BuildEntry]  #: The entries of the builds.

	def __init__(self, builds: Nullable[Iterable[BuildEntry]] = None) -> None:
		"""
		Initializes a build index.

		:param builds:           Optional, entries of the builds.
		:raises TypeError:       If parameter 'builds' is not iterable.
		:raises TypeError:       If an element of parameter 'builds' is not of type :class:`BuildEntry`.
		:raises BuildIndexError: If an element of parameter 'builds' belongs to a build index already.
		"""
		self._builds = buildList = []
		if builds is not None:
			if not isinstance(builds, Iterable):
				ex = TypeError("Parameter 'builds' is not iterable.")
				ex.add_note(f"Got type '{getFullyQualifiedName(builds)}'.")
				raise ex

			for build in builds:
				if not isinstance(build, BuildEntry):
					ex = TypeError("Element of parameter 'builds' is not of type 'BuildEntry'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(build)}'.")
					raise ex
				elif build._parent is not None:
					raise BuildIndexError(f"Build '{build._name}' belongs to a build index already.")

				build._parent = self
				buildList.append(build)

	@readonly
	def Builds(self) -> list[BuildEntry]:
		"""
		Read-only property to access the entries of the builds (:attr:`_builds`).

		:returns: List of entries, in the order OSVVM wrote them.
		"""
		return self._builds

	@readonly
	def BuildCount(self) -> int:
		"""
		Read-only property to return the number of entries.

		:returns: Number of entries.
		"""
		return len(self._builds)

	def IterateBuilds(
		self,
		predicate: Nullable[Callable[[BuildEntry], bool]] = None
	) -> Generator[BuildEntry, None, None]:
		"""
		Iterate the entries of the builds, in the order OSVVM wrote them.

		:param predicate: Optional, a filter function; an entry is returned, if it returns ``True``.
		:returns:         A generator of entries.
		"""
		if predicate is None:
			yield from self._builds
		else:
			for build in self._builds:
				if predicate(build):
					yield build


SCHEMAS: dict[FormatVersion, str] = {
	FormatVersion.Version0_1: "OSVVM-BuildIndex-0.1.schema.json",
}  #: The JSON Schema of :mod:`pyEDAA.OSVVM.Resources` a build index is validated against, per format version.


@export
class BuildIndexDocument(BuildIndex, YAMLDocumentMixin):
	"""
	An OSVVM build index file :file:`index.yml`: read and converted to the build index.

	:meth:`Analyze` validates the file against the schema of the format version it states (:data:`SCHEMAS`),
	:meth:`Convert` converts each entry by :meth:`BuildEntry.Parse`.
	"""

	_DESCRIPTION:    ClassVar[str] =                                "OSVVM build index"  #: Format's name in messages.
	_ERROR:          ClassVar[type[BuildIndexError]] =              BuildIndexError      #: Exception of the reader.
	_FORMAT_VERSION: ClassVar[type[FormatVersion]] =                FormatVersion        #: The format's versions.
	_SCHEMAS:        ClassVar[dict[FormatVersion, str]] =           SCHEMAS              #: Schema per version.

	_path:             _Path                #: Path to the YAML file.
	_analysisDuration: Nullable[timedelta]  #: Duration of :meth:`Analyze`, or ``None`` before it ran.
	_modelConversion:  Nullable[timedelta]  #: Duration of :meth:`Convert`, or ``None`` before it ran.

	def __init__(self, yamlFile: Path, analyzeAndConvert: bool = False) -> None:
		"""
		Initializes a build index document, and optionally reads it.

		:param yamlFile:          Path to the YAML file.
		:param analyzeAndConvert: Optional, if true, analyze the file and convert its content. Default: ``False``.
		:raises ValueError:       If parameter 'yamlFile' is None.
		:raises TypeError:        If parameter 'yamlFile' is not of type :class:`~pathlib.Path`.
		"""
		super().__init__()
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

		:raises BuildIndexError: If the file doesn't exist.
		:raises BuildIndexError: If the file can't be read.
		:raises BuildIndexError: If the file isn't UTF-8 encoded.
		:raises BuildIndexError: If the file isn't valid YAML.
		:raises BuildIndexError: If the file's content isn't a YAML mapping.
		:raises BuildIndexError: If the file states no format version. |br|
		                         The note lists the supported format versions.
		:raises BuildIndexError: If the file states an unsupported format version. |br|
		                         The note lists the supported format versions.
		:raises BuildIndexError: If the JSON Schema can't be read.
		:raises BuildIndexError: If the file isn't valid according to the JSON Schema. |br|
		                         A note per violation names its path and line.
		"""
		with Stopwatch() as sw:
			self._AnalyzeYAML()

		self._analysisDuration = sw.Duration

	def Convert(self) -> None:
		"""
		Convert the analyzed YAML data structure into the build index.

		:raises BuildIndexError: If the YAML file was not analyzed before. |br|
		                         Call 'Document.Analyze()' or create the document using
		                         'Document(path, analyzeAndConvert=True)'.
		:raises BuildIndexError: If an entry's values can't be converted.
		"""
		if self._yamlDocument is None:
			ex = BuildIndexError(f"OSVVM build index '{self._path}' needs to be read and analyzed by a YAML parser.")
			ex.add_note("Call 'Document.Analyze()' or create the document using 'Document(path, analyzeAndConvert=True)'.")
			raise ex

		with Stopwatch() as sw:
			for buildNode in self._yamlDocument["Builds"]:
				BuildEntry.Parse(buildNode, parent=self)

		self._modelConversion = sw.Duration
