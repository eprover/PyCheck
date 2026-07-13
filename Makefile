#------------------------------------------------------------------------
#
# File  : Makefile for PyCheck
#
# Author: Stephan Schulz
#
# Changes
#
# <1> Mon Sep 19 13:50:35 CEST 2011
#     New
#
#------------------------------------------------------------------------

STAREXECPATH=$(HOME)/StarExecPyBuild
VERSION=


all:

clean:
	-rm -f *.pyc *~


testcov: *.py
	-rm -r .coverage COVERAGE
	for f in *.py ;do coverage-3.8 run -a $$f; done
	coverage-3.8 report > testcov
	mkdir COVERAGE
	coverage-3.8 annotate -d COVERAGE
	cat testcov


tags: TAGS

TAGS: *.py
	etags-emacs *.py


distrib: clean
	cd ..; tar czf PyCheck.tgz PyCheck


starexec-src:
	echo $(STAREXECPATH)
	rm -rf $(STAREXECPATH)
	mkdir $(STAREXECPATH)
	find . -name ".#*"  -exec rm {} \;
	make distrib
	cp ../PyCheck.tgz $(STAREXECPATH)
	cd ~/tmp/E; git pull; make distrib;cp ../E.tgz $(STAREXECPATH)

	mkdir $(STAREXECPATH)/bin
	cp starexec_run* $(STAREXECPATH)/bin
	cp starexec_build $(STAREXECPATH)
	$(eval VERSION=`grep "version =" /Users/schulz/SOURCES/Projects/PyCheck/version.py | cut -d' ' -f3  |cut -d'"' -f2`)
	cd $(STAREXECPATH); zip -r PyCheck-$(VERSION)_src.zip bin E.tgz PyCheck.tgz starexec_build
