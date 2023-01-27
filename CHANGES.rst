0.5.1
=====

* Fixed problem where ranged files wasn't working for copy-only files


0.5.0
=====

* Once again modified a bunch of the keys in the TOML configuration file; you
were warned it is ALPHA :)
* Added command line arguments for verbose mode, info only mode, and to
generate only a single chapter
* Refactored a bunch of the file stuff into a class to make the above args
change easier


0.4.0
=====

* Added `ignore_substrings` feature allowing you to specify a partial name of
a path to ignore, useful for things like `__pycache__`
* Found bug where file metadata isn't maintained during a copy, updated to use
the right `shutil` call only to find out there is a Python bug in that library
for MacOS and Windows since 3.8


0.3.0
=====

* BREAKING CHANGE!!! Juli token markers have been changed to be more
consistent
* Add ability to have a block of code that is conditional but not commented
out in the main version
* Change the conditional directory handling mechanism to handle both files and
directories, renamed the part of the TOML file from "srcdir" to "ranged_files"
* Large refactor of the parser, cleaning it up and making it possible to
implement the open block feature


0.2.1
=====

* Fix bug where conditional directory limits weren't always detected


0.2.0
=====

* Add ability to ignore directories
* Add some error handling to indicate what file has a problem for certain
parsing errors
* Change juli token marker from "#:" and "#::" to "#@" and "#@@" after
discovering some code using the original in the wild


0.1.0
=====

* Initial release to pypi
