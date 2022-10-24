********
julienne
********

**very ALPHA, use at your own risk**

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
project will generate a separate copy of each generation of your code.
