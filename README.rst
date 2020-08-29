python-icns
===========

A cross-platform Python library/tool for reading macOS ICNS icon images.

**Note:** The PIL/Pillow library has `built-in support for reading and writing ICNS images <https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#icns>`__,
which you should use if it fits your use case.
Pillow's ICNS plugin is much more well-tested and maintained than this library,
and probably also faster.
However,
this library supports some features that Pillow's ICNS plugin does not have,
such as reading some old or unusual icon formats and resolutions,
reading nested icon families and metadata,
accessing the low-level ICNS structure and data,
and a command-line interface.

Features
--------

* Cross-platform - no native Mac APIs or tools are used.
* Almost completely pure Python - other than PIL/Pillow, no native/compiled code is required.
* Supports reading every known icon format and resolution, from Mac OS 8.5 through macOS 10.14.
  (If you find an icon type that isn't supported, please open an issue!)
* Supports reading nested icon families - alternate icon states, dark mode variants, etc.
* Supports reading metadata (although in most cases it doesn't contain any useful information).
* Includes a command-line tool for displaying the structure of an ICNS image and extracting its contents into standalone files.

Installation
------------

python-icns is compatible with Python 3.6 or later.
(If you have a need for using this library on earlier Python versions,
please open an issue -
I might support older versions if there is any interest.)

python-icns is unfinished and unreleased,
so it is not available on PyPI yet.
If you want to use it anyway,
you need to clone/download the source code and install it by running this ``pip`` command in the source directory:

.. code-block:: sh

    python3 -m pip install .

If you update your clone or otherwise modify the code,
you need to re-run the install command.
You can get around the reinstall requirement by installing the package in "editable" mode:

.. code-block:: sh

    python3 -m pip install --editable .

In editable mode,
changes to the source code take effect immediately without a reinstall.
This doesn't work perfectly in all cases though,
especially if the package metadata
(pyproject.toml, setup.cfg, setup.py, ``__version__``, etc.)
has changed.
If you're using an editable install and experience any problems with the package,
please try re-running the editable install command,
and if that doesn't help,
try using a regular (non-editable) installation instead.

Examples
--------

TODO

Limitations
-----------

* Writing ICNS images is not supported yet.
* Icon family elements of unknown/unsupported types are not always handled gracefully.
* Currently icons can only be looked up by their raw type code or exact resolution.
  There is no built-in way to request a certain resolution and automatically fall back to another resolution if the requested one doesn't exist in the family.
  At the moment you need to manually iterate over the available resolutions and choose one that fits best.

Changelog
---------

Version 0.0.1 (next version)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Initial development version.
