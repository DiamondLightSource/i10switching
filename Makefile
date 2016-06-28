generated = i10.py matplotlib_test.py

all: $(generated)
install: $(generated)

%.py: %.ui
	pyuic4 $< > $@

clean:
	rm -rf $(generated)
	rm -rf *.pyc
