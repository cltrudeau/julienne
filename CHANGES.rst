0.8.2
=====

* 2023/11/21
* Minor changes to the docs
* Really just building this so I can test my PyPI 2FA


0.8.1
=====

* 2023/07/02
* Add ability to call isort on generated content


0.8
===

* 2023/05/22
* Add ability to write a comment not included in the output code


0.7.2
=====

* Add debug command line argument that allows you to see the contents of a
file including the range of each line
* Add -p and -x debug tools for using the parser directly on a Python or XML
file
* Fixed bug in nesting code that didn't handle leaving a BLOCK_COMMENT
properly
* Fixed bug where #@- markers without text weren't leave a blank line


0.7.1
=====

* 2023/05/17
* Now supports nested markers


0.7.0
=====

* Add "#@@" tag, allowing you to comment out code in a single line
* Add ability to call black on generated output
* Add ability to remove the output directory before generating it


0.6.1
=====

* Fix bug where max chapter wasn't being found if it was on a conditional
block


0.6.0
=====

* Add ability to parse XML-style files


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
