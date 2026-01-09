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
# Copyright 2025-2026 Patrick Lehmann - Bötzingen, Germany                                                             #
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
**A Sphinx domain providing directives to add reports to the Sphinx-based documentation.**

Supported reports:

* :ref:`BUILDS`
* :ref:`ALERTLOG`
* :ref:`COVERAGE`
* :ref:`SCORE`

"""

from hashlib               import md5
from pathlib               import Path
from typing                import TYPE_CHECKING, Any, Tuple, Dict, Optional as Nullable, TypedDict, List, Callable

from docutils              import nodes
from sphinx.addnodes       import pending_xref
from sphinx.application    import Sphinx
from sphinx.builders       import Builder
from sphinx.config         import Config
from sphinx.domains        import Domain
from sphinx.environment    import BuildEnvironment
from sphinx.util.logging   import getLogger
from pyTooling.Decorators  import export
from pyTooling.Common      import readResourceFile

from sphinx_reports.Common import ReportExtensionError

from pyEDAA.OSVVM          import __version__
from pyEDAA.OSVVM          import static as ResourcePackage

@export
class OSVVMDomain(Domain):
	"""
	A Sphinx extension providing a ``osvvm`` domain to integrate reports and summaries into a Sphinx-based documentation.

	.. rubric:: New directives:

	* :rst:dir:`osvvm:testsuite-summary`

	.. rubric:: New roles:

	* *None*

	.. rubric:: New indices:

	* *None*

	.. rubric:: Configuration variables

	All configuration variables in :file:`conf.py` are prefixed with ``osvvm_*``:

	* ``osvvm_testsuites``

	"""

	name =  "osvvm"  #: The name of this domain
	label = "osvvm"  #: The label of this domain

	dependencies: List[str] = [
	]  #: A list of other extensions this domain depends on.

	from pyEDAA.OSVVM.Sphinx.Testsuites import BuildSummary

	directives = {
		BuildSummary.directiveName:     BuildSummary,
	}  #: A dictionary of all directives in this domain.

	roles = {
		# "design":   DesignRole,
	}  #: A dictionary of all roles in this domain.

	indices = [
		# LibraryIndex,
	]  #: A list of all indices in this domain.

	from pyEDAA.OSVVM.Sphinx.Testsuites import BuildSummary

	configValues: Dict[str, Tuple[Any, str, Any]] = {
		**BuildSummary.configValues,
	}  #: A dictionary of all configuration values used by this domain. (name: (default, rebuilt, type))

	del BuildSummary

	initial_data = {
		# "reports": {}
	}  #: A dictionary of all global data fields used by this domain.

	# @property
	# def Reports(self) -> Dict[str, Any]:
	# 	return self.data["reports"]

	@staticmethod
	def CheckConfigurationVariables(sphinxApplication: Sphinx, config: Config) -> None:
		"""
		Call back for Sphinx ``config-inited`` event.

		This callback will verify configuration variables used by that domain.

		.. seealso::

		   Sphinx *builder-inited* event
		     See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

		:param sphinxApplication: The Sphinx application.
		:param config:            Sphinx configuration parsed from ``conf.py``.
		"""
		from pyEDAA.OSVVM.Sphinx.Testsuites import BuildSummary

		checkConfigurations = (
			BuildSummary.CheckConfiguration,
		)

		for checkConfiguration in checkConfigurations:
			try:
				checkConfiguration(sphinxApplication, config)
			except ReportExtensionError as ex:
				logger = getLogger(__name__)
				logger.error(f"Caught {ex.__class__.__name__} when checking configuration variables.\n  {ex}")

	@staticmethod
	def AddCSSFiles(sphinxApplication: Sphinx) -> None:
		"""
		Call back for Sphinx ``builder-inited`` event.

		This callback will copy the CSS file(s) to the build directory.

		.. seealso::

		   Sphinx *builder-inited* event
		     See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

		:param sphinxApplication: The Sphinx application.
		"""
		# Create a new static path for this extension
		staticDirectory = (Path(sphinxApplication.outdir) / "_osvvm_static").resolve()
		staticDirectory.mkdir(exist_ok=True)
		sphinxApplication.config.html_static_path.append(str(staticDirectory))

		# Read the CSS content from package resources and hash it
		cssFilename = "osvvm.css"
		cssContent = readResourceFile(ResourcePackage, cssFilename)

		# Compute md5 hash of CSS file
		hash = md5(cssContent.encode("utf8")).hexdigest()

		# Write the CSS file into output directory
		cssFile = staticDirectory / f"osvvm.{hash}.css"
		sphinxApplication.add_css_file(cssFile.name)

		if not cssFile.exists():
			# Purge old CSS files
			for file in staticDirectory.glob("*.css"):
				file.unlink()

			# Write CSS content
			cssFile.write_text(cssContent, encoding="utf8")

	@staticmethod
	def ReadReports(sphinxApplication: Sphinx) -> None:
		"""
		Call back for Sphinx ``builder-inited`` event.

		This callback will read the linked report files

		.. seealso::

		   Sphinx *builder-inited* event
		     See https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

		:param sphinxApplication: The Sphinx application.
		"""
		from pyEDAA.OSVVM.Sphinx.Testsuites import BuildSummary

		BuildSummary.ReadReports(sphinxApplication)

	callbacks: Dict[str, List[Callable]] = {
		"config-inited":    [CheckConfigurationVariables],    # (app, config)
		"builder-inited":   [AddCSSFiles, ReadReports],       # (app)
	}  #: A dictionary of all events/callbacks <https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events>`__ used by this domain.

	def resolve_xref(
		self,
		env: BuildEnvironment,
		fromdocname: str,
		builder: Builder,
		typ: str,
		target: str,
		node: pending_xref,
		contnode: nodes.Element
	) -> Nullable[nodes.Element]:
		raise NotImplementedError()


if TYPE_CHECKING:
	class setup_ReturnType(TypedDict):
		version: str
		env_version: int
		parallel_read_safe: bool
		parallel_write_safe: bool


@export
def setup(sphinxApplication: Sphinx) -> "setup_ReturnType":
	"""
	Extension setup function registering the ``osvvm`` domain in Sphinx.

	It will execute these steps:

	* register domains, directives and roles.
	* connect events (register callbacks)
	* register configuration variables for :file:`conf.py`

	:param sphinxApplication: The Sphinx application.
	:returns:                 Dictionary containing the extension version and some properties.
	"""
	sphinxApplication.add_domain(OSVVMDomain)

	# Register callbacks
	for eventName, callbacks in OSVVMDomain.callbacks.items():
		for callback in callbacks:
			sphinxApplication.connect(eventName, callback)

	# Register configuration options supported/needed in Sphinx's 'conf.py'
	for configName, (configDefault, configRebuilt, configTypes) in OSVVMDomain.configValues.items():
		sphinxApplication.add_config_value(f"{OSVVMDomain.name}_{configName}", configDefault, configRebuilt, configTypes)

	return {
		"version": __version__,                          # version of the extension
		"env_version": int(__version__.split(".")[0]),   # version of the data structure stored in the environment
		'parallel_read_safe': False,                     # Not yet evaluated, thus false
		'parallel_write_safe': True,                     # Internal data structure is used read-only, thus no problems will occur by parallel writing.
	}
