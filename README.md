This code implements simple semantic proof checker for untyped
first-order proofs in TPTP-3 syntax.

It is released as free software under the GNU GPL version 2, and
without any warranty. See the file COPYING for details and the
individual source headers for copyright information.

This recycles code from PyRes (https://github.com/eprover/PyRes) and
is currently not very clean - there is a lot of unnecessary inherited
code, because this version was built to the ProoVer competition
deadline.

Installation:
=============

Just clone the repository into a new directory, with e.g.
```
git clone https://github.com/eprover/PyCheck.git
```
No futher installation should be necessary. If you are on a UNIX-like
OS (including Linux or macOS/OS-X), and "python3" is not in your
standard search path (or not Python 3), you may need to edit the
#!-line at the beginning of the main program (see below),
or in all modules if you want to run the unit tests.

You do need E (as "eprover") in your search path. See

   https://www.eprover.org

for installation instructions.

pycheck.py:
===========

This is the main programm. To run it, call it e.g. as

```
pycheck COR001+1.prf
```

If "eprover" is not in your search path, you can provide an explicit
path to the binary via

```
pycheck -e path/to/eprover COR001+1.prf
```


The program has been designed in reply to the requirements of the
ProoVer competition, which in particular means that it cannot parse
the (older style) Skolemization steps output by E (which will be
updated soon, of course).


Information for ProoVer
=======================

The system will be delivered as a StarExec source package, including E,
with a build script that should put everything in the right place. The
script to run the system is
```
starexec_run_PyCheck
```
