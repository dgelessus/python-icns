python-icns
===========

TODO

Features
--------

TODO

Installation
------------

python-icns is compatible with Python 3.7 or later.
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

TODO

Changelog
---------

Changelog
---------

Version 0.0.1 (next version)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Initial development version.
