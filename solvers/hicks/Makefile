
# A simple makefile (for CAAM 522)

# Lines starting with '#' are comments

# If make gives you an error message, the first thing to check is that
# the line near the end containing "LINK.cc" starts with a [tab], not
# a space.

# This improves make's behaviour
.KEEP_STATE:

# The C++ compiler to use (uncomment one of the following two lines
# and comment the other)
#CXX= CC -Dfor="if(0);else for" -Dbool=int -Dfalse=0 -Dtrue=1  
#CC= cc $(CCFLAGS)
CXX= g++ -Wall -pedantic
#CC= gcc $(CCFLAGS)
# Flags to pass to the C++ compiler

CXXFLAGS= -O3
#CCFLAGS= -xO3 
#CXXFLAGS= -pg
#CCFLAGS= -pg
# The name of the executable file you want to make
EXECUTABLE=bw

# The names of the source files (separated by spaces)
SOURCE= cut.cc bgraph.cc

# Any library commands needed to link the program
# For example, -lm
LDLIBS=

# The names of the object files
# This is automatically defined from the source files
OBJECTS=$(SOURCE:%.cc=%.o)
#OBJECTS=$(SOURCE:%.c=%.o)
# The rule for building the executable.  Instead of changing this,
# change the definition of EXECUTABLE, SOURCE, and LDLIBS.
# Also, note that the LINK.cc line starts with a [tab], not 8 spaces.
# If the LINK.cc line doesn't start with a [tab], make will get very
# confused.
$(EXECUTABLE): $(OBJECTS)
	$(LINK.cc)  -o $@ $(OBJECTS) $(LDLIBS)

# The following rule compares the executable's output on sample inputs
# against sample outputs.  The - keeps make from stopping if there are
# differences
pure:
	make
	purify $(LINK.cc)  -o $@ $(OBJECTS) $(LDLIBS)

test: $(EXECUTABLE)
	-rm -f out
	for file  in [../data/*.del ../data/tele133];\
	do (nice +19 time $(EXECUTABLE) $$file) >> out 2>>1;\
	done;



# A rule for cleaning up
cleanout:
	rm -f *.out
clean:
	rm -f *.o $(EXECUTABLE) *.out pure 

# Dependencies.  Each object file depends on its source file, and on
# each header file it includes.  It is not necessary to list system
# include files.  hello.cc does not include any non-system header
# files, so this line is boring.  If it included goodbye.h, then this
# line would read "hello.o: hello.cc goodbye.h"

ctree.o: ctree.cc graph.h








