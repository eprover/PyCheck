This code implements simple semantic proof checker for untyped
first-order proofs in TPTP-3 syntax.

It is released as free software under the GNU GPL version 2, and
without any warranty. See the file COPYING for details and the
individual source headers for copyright information.

Installation:
=============

Just clone the repository into a new directory, with e.g.
git clone https://github.com/eprover/PyCheck.git

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
pycheck LUSK3.prf
```



======== Information for ProoVer ==========


======== Checks ======

THM steps via ATP
CTH steps via ATP
References to input file via ATP
New symbols are only used downstream
Proof graph is a DAG
Nodes are input formulas (or references to it)
Skolemization directly
