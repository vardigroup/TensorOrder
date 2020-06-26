appname := portfolio

CXX := g++
CXXFLAGS := -std=c++17 -O3 -DNDEBUG -I. -pedantic
LDLIBS := -lpthread

srcfiles := $(shell find . -name "*.cc" -or -name "*.cpp")
objects  := $(patsubst ./%.cpp, ./%.o, $(patsubst ./%.cc, ./%.o, $(srcfiles)))

all: build/$(appname)

build/$(appname): $(objects)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o build/$(appname) $(objects) $(LDLIBS)

build/.depend: $(srcfiles)
	rm -f ./build/.depend
	mkdir -p ./build/
	$(CXX) $(CXXFLAGS) -MM $^>>./build/.depend;

clean:
	rm -f $(objects)

dist-clean: clean
	rm -f *~ ./build/depend

include build/.depend