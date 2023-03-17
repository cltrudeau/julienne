# This is a sample file

a = "In all chapters"   # inline comment
b = "In chapters 1-3"   #@= 1-3 comment on conditional
c = "In chapters 1-2"   #@= -2
d = "In chapters 2 on"  #@= 2-

#@@ 1-2 x = "In chapters 1-2"

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
