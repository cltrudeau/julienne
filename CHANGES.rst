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
