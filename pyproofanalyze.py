#!/usr/bin/env python3
# ----------------------------------
#
# Module pyproofanalyze.py

"""
Usage: pyproofanalyze.py [options] <problem_file>

This program parses (some) TPTP-3 format proofs and will provide
certain data on the different clauses.

Options:

 -h
--help
  Print this help.


Copyright 2026 Stephan Schulz, schulz@eprover.org

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program ; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston,
MA  02111-1307 USA

The original copyright holder can be contacted as

Stephan Schulz
Auf der Altenburg 7
70376 Stuttgart
Germany
Email: schulz@eprover.org

"""

import sys
import re
from resource import RLIMIT_STACK, setrlimit, getrlimit
import getopt
from version import version
from lexer import Token,Lexer
from derivations import *
from clausesets import ClauseSet
from fofspec import FOFSpec


def processOptions(opts):
    """
    Process the options given
    """

    for opt, optarg in opts:
        if opt == "-h" or opt == "--help":
            print("pyres-fof.py "+version)
            print(__doc__)
            sys.exit()


time_re = re.compile(r"[%#] Total time *: ([0-9]+\.[0-9]+) s")

count_re = re.compile(r"([0-9][0-9][0-9])\.p\.prf")

def extractSize(name):
    mr = count_re.search(name)
    if mr:
        return int(mr.group(1))
    else:
        return 0


def getRuntime(file):
    with open(file, 'r') as fp:
        data = fp.read()
    mr = time_re.search(data)
    if mr:
        return mr.group(1)
    else:
        return "unknown"


if __name__ == '__main__':
    # We try to increase stack space, since we use a lot of
    # recursion. This works differentially well on different OSes, so
    # it is a bit more complex than I would hope for.
    try:
        soft, hard = getrlimit(RLIMIT_STACK)
        soft = 10*soft
        if hard > 0 and soft > hard:
            soft = hard
        setrlimit(RLIMIT_STACK, (soft, hard))
    except ValueError:
        # For reasons nobody understands, this seems to fail on
        # OS-X. In that case, we just do our best...
        pass

    sys.setrecursionlimit(10000)

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],
                                       "h",
                                       ["help"])
    except getopt.GetoptError as err:
        print(sys.argv[0],":", err)
        sys.exit(1)

    processOptions(opts)

    for file in args:
        problem = FOFSpec()
        problem.parse(file)
        problem.resolveQuasiReferences()
        runtime = getRuntime(file)
        instsize = extractSize(file)
        print("%20s & %3d & %5d & %20d & %s \\\\"%\
              (file, instsize, problem.proofRWSteps(), problem.proofEqLen(),runtime))
        Derivable.printDerivation = True
        # print(problem)

    #Derivable.printDerivation = True
    #print(problem)
    #print("===================")
