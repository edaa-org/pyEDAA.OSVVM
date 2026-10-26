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
Testcases for the Sphinx extension :mod:`pyEDAA.OSVVM.Sphinx`, each built in a small Sphinx project.

The projects read the hand-written build :file:`tests/data/OSVVM/Sphinx/Demo`: a build summary, the settings of its
testcases, and the AlertLog, functional coverage and scoreboard reports of a testcase.
"""
from io                   import StringIO
from pathlib              import Path
from re                   import sub
from tempfile             import TemporaryDirectory
from typing               import Any, Optional as Nullable

from sphinx.testing.util  import SphinxTestApp

from pyTooling.Testing    import Testcase

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


DEMO =       (Path(__file__).parent.parent.parent / "data" / "OSVVM" / "Sphinx" / "Demo").resolve()
DEMO_BUILD = DEMO / "Demo.yml"


class Project(Testcase):
	"""Base-class of the testcases: a temporary directory holding a Sphinx project per testcase."""

	_directory: TemporaryDirectory
	_path:      Path
	_warnings:  StringIO

	def setUp(self) -> None:
		self._directory = TemporaryDirectory()
		self._path = Path(self._directory.name)
		(self._path / "src").mkdir()

	def tearDown(self) -> None:
		self._directory.cleanup()

	def _build(
		self,
		index: str,
		builder: str = "html",
		documents: Nullable[dict[str, str]] = None,
		**config: Any
	) -> SphinxTestApp:
		"""
		Write the documents and build the project, with the demo build declared as ``demo``, unless overridden.

		:param index:     Content of the document ``index``.
		:param builder:   Optional, name of the builder. Default: ``"html"``.
		:param documents: Optional, more documents, keyed by name; ``index`` lists them in a hidden toctree.
		:param config:    Configuration values overriding the defaults.
		:returns:         The Sphinx application after the build.
		"""
		source = self._path / "src"
		(source / "conf.py").write_text('extensions = ["pyTooling.Sphinx", "pyEDAA.OSVVM.Sphinx"]\n', encoding="utf-8")
		if documents is not None:
			index += "\n.. toctree::\n   :hidden:\n\n" + "".join(f"   {name}\n" for name in documents)
			for name, content in documents.items():
				(source / f"{name}.rst").write_text(content, encoding="utf-8")

		(source / "index.rst").write_text(index, encoding="utf-8")

		overrides = {"osvvm_build_summaries": {"demo": {"yaml_report": str(DEMO_BUILD)}}}
		overrides.update(config)

		self._warnings = StringIO()
		app = SphinxTestApp(
			builder, source, self._path / "build", freshenv=True, confoverrides=overrides, status=StringIO(),
			warning=self._warnings
		)
		try:
			app.build()
		finally:
			app.cleanup()

		return app

	def _html(self, name: str) -> str:
		"""
		Read a built page.

		:param name: Name of the document.
		:returns:    The page's HTML.
		"""
		return (self._path / "build" / "html" / f"{name}.html").read_text(encoding="utf-8")

	def _warningLines(self) -> list[str]:
		"""
		Return the warnings of the last build, without colours and without the temporary directory's path.

		:returns: One line per warning.
		"""
		lines = []
		for line in self._warnings.getvalue().splitlines():
			line = sub(r"\x1b\[[0-9;]*m", "", line)
			lines.append(line.replace(f"{self._path}/", "").replace(f"{DEMO}/", ""))

		return lines
