********
julienne
********

**very ALPHA, use at your own risk, interface may change!**

When writing code for teaching, you often need multiple versions of your code,
showing progress to your students as you introduce new concepts. Keeping
several versions is painful though, especially when you find a bug that is
common to each copy.

Enter: julienne. It slices, it dices, well... it actually only slices. This
library comes with the ``juli`` script which reads code and interprets special
directives in the comments, generating multiple versions of the code. The
directives allow you to limit which versions a block of code exists in. 

The goal for this toolset once complete is to allow you to maintain a single
version of your project in its completed state. Running ``juli`` on your
project will generate a separate copy of each version of your code.


Juli Comment Markers
--------------------

When using ``juli``, you have one copy of your code in its final state. You
mark sections of your code with comments to indicate that a line or block only
participates in certain versions. Each version is called a *chapter*. When you
run the ``juli`` command it will create a directory for each chapter found in
your code.


.. code-block:: python

    # This is a sample file

    a = "In all chapters"   # inline comment
    b = "In chapters 1-3"   #@= 1-3 comment on conditional
    c = "In chapters 1-2"   #@= -2
    d = "In chapters 2 on"  #@= 2-

    #@+ 3-4
    #@- e = "In chapters 3 to 4"  # inline comment
    #@- f = "  as a block"

    for x in range(10):
        #@+ 1-2 block header with comment
        #@- g= "In chapters 1 and 2"
        h = "In all chapters"

    #@[ 3- uncommented conditional block
    def foo():
        print("Blah de blah")
    #@]

All ``juli`` comment markers start with ``#@`` followed by the julienne type
which determines how the marker behaves. The types are as follows:

* ``#@=`` -- A single line conditional to a range of chapters
* ``#@+`` -- Start a conditional block that is commented out, applies to a range of chapters
* ``#@-`` -- Part of a conditional block that is commented out. Must appear after a ``#@+``
* ``#@[`` -- Start a conditional block that is not commented out, applies to a range of chapters
* ``#@]`` -- End a conditional block that is not commented. Must appear after a ``#@[``

The ``#@=``, ``#@+``, and ``#@[`` markers expect a range that indicates what
chapters a line or block participates within. Ranges can indicate a single
chapter, a range of chapters, up-to-and-including a chapter, and
including-and-after a chapter. A space is expected between the julienne type 
and the beginning of the range specifier. Example ranges:

* ``#@= 3`` -- this line only shows up in chapter 3
* ``#@+ 2-4`` -- the following commented block is uncommented in chapters 2, 3, and 4
* ``#@= 2-`` -- this line is in chapters 2 and above
* ``#@[ -4`` -- the following uncommented block starts appearing in chapter 4

The markers support trailing comments. Generated code will insert a comment
without the ``juli`` marker containing whatever comes after your marker.
Markers without trailing comments will not be included in the results. Any
indentation before a marker is respected if the marked line results in 
output.

The sample code above will generate four chapters. Chapter one would contain:

.. code-block:: python

    # This is a sample file

    a = "In all chapters"   # inline comment
    b = "In chapters 1-3"   # comment on conditional
    c = "In chapters 1-2"   


    for x in range(10):
        # block header with comment
        g= "In chapters 1 and 2"
        h = "In all chapters"


Chapter four would contain:

.. code-block:: python

    # This is a sample file

    a = "In all chapters"   # inline comment
    d = "In chapters 2 on"  

    e = "In chapters 3 to 4"  # inline comment
    f = "  as a block"

    for x in range(10):
        h = "In all chapters"

    # uncommented conditional block
    def foo():
        print("Blah de blah")


Note that files that contain only conditional lines will not be included if
they aren't in chapter range.


Configuring Your Project
------------------------

The ``juli`` uses a `TOML <https://toml.io>`_ file for configuration. The file
must contain two key/value pairs that indicate the source and output
directories for the parser.


.. code-block:: TOML 

    output_dir = 'last_output'
    src_dir = 'code'


The above will cause ``juli`` to look for a directory named ``code`` relative 
to the configuration file. The source found in that directory will be parsed. 
The generated chapters will be put in a directory named ``last_output``. If
your source specified two chapters, running ``juli`` will result in the 
creation of two directories: ``last_output/ch1/code`` and 
``last_output/ch2/code``.

Both the ``output_dir`` and ``src_dir`` values can be absolute paths or
relative to the TOML configuration file.

Additional, optional configuration values are:

* ``chapter_prefix`` -- Specify what the prefix part of a chapter directory is named. If not specified, defaults to "ch"
* ``active_globs`` -- A glob pattern that indicates which files participate in the parsing. Files that don't match will be copied without processing. If not specified it defaults to ``**/*.py``, meaning all files ending in "\*.py"
* ``skip_dirs`` -- A list of sub-directories that should not be processed.
* ``skip_patterns`` -- A list of strings that if they show up in the path the path is ignored. Useful for things like `__pycache__`
* ``[chapter_map]`` -- Chapter numbers are integers, but you may not always want that in your output structure. This map allows you to change the suffix part of a chapter directory name. Keys in the map are the chapter numbers while values are what should be used in the chapter suffix.
* ``[ranged_files.XYZ]`` -- Files or directories can be marked as conditional using this TOML map. This map must specify ``range`` and ``files`` attributes. The ``range`` attribute indicates what chapters this directory participates in, and ``files`` is listing of file or directory names. In the case of files they will only participate in parsing if the match the range value. If a file contains a marker outside the range it will be ignored. The ``XYZ`` portion of the TOML nested map is ignored, it is there so you can have multiple conditional directories.

Here is a full example of a configuration file:

.. code-block:: TOML 

    output_dir = 'last_output'
    src_dir = 'code'
    skip_dirs = ['bad_dir', ]
    skip_patterns = ['__pycache__', ]

    chapter_prefix = "chap"

    [chapter_map]
    4 = 'Four'
    5 = '5.0'

    [ranged_files.foo]
    range = '2-4'
    files = ['code/between24', 'only24.py']

    [ranged_files.bar]
    range = '4-'
    files = ['code/after4', ]
        

If your code directory contained:

.. code-block:: text

    code/script.py
    code/only24.py
    code/readme.txt
    code/between24/two_to_four.py
    code/after4/later_on.txt
    code/bad_dir/something.py


Then running ``juli example.toml``, the sample configuration would result
in the following:

.. code-block:: text

    last_output/chap1/code/script.py
    last_output/chap1/code/readme.txt

    last_output/chap2/code/script.py
    last_output/chap2/code/only24.py
    last_output/chap2/code/readme.txt
    last_output/chap2/code/between24/two_to_four.py

    last_output/chap3/code/script.py
    last_output/chap3/code/only24.py
    last_output/chap3/code/readme.txt
    last_output/chap3/code/between24/two_to_four.py

    last_output/chapFour/code/script.py
    last_output/chapFour/code/only24.py
    last_output/chapFour/code/readme.txt
    last_output/chapFour/code/between24/two_to_four.py
    last_output/chapFour/code/after4/later_on.txt

    last_output/chap5.0/code/script.py
    last_output/chap5.0/code/readme.txt
    last_output/chap5.0/code/after4/later_on.txt

The ``script.py``, ``two_to_four.py``, and ``only24.py``  files will be
processed for conditional content. The ``readme.txt`` and ``later_on.txt``
files will be straight copies as they aren't covered by the active glob.


Command Line Arguments
----------------------

The ``juli`` has one required argument, the name of the ``TOML`` configuration
file. It also supports the following optional arguments:

* ``--help``, ``-h``: show help info
* ``--verbose``, ``-v``: print information while processing
* ``--info``, ``-i``: only print the info don't do the processing
* ``--chapter CHAPTER``, ``-c CHAPTER``: process only the given chapter number
  (CHAPTER)


Uh, Oh
------

.. warning:: 

    There is a known bug in Python where the `shutil.copy2` method does not
    copy metadata on MacOS or Windows even though it is supposed to. This
    means group ownership flags and execution bits will get lost on those
    operating systems. See:

    https://github.com/python/cpython/issues/83087
