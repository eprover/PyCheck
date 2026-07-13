#!/usr/bin/env python3
# ----------------------------------
#
# Module fofspec.py

"""
This module implements parsing and processing for full first-order
logic, in mixed TPTP FOF and CNF format.

Copyright 2011-2023 Stephan Schulz, schulz@eprover.org

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

import unittest
import errno
import os
import os.path

from lexer import Lexer, Token
from signature import Signature
from clauses import Clause, parseClause
from clausesets import ClauseSet
from formulas import WFormula, parseWFormula, negateConjecture
from formulacnf import wFormulaClausify
from eqaxioms import generateEquivAxioms, generateCompatAxioms
from checkutil import VerificationStatus
from version import Verbose

def tptpLexer(source, refdir):
    """
    Create a lexer for reading a file using the TPTP convention. If
    refdir exists, interpret name relative to it. If this does not
    exist, interpret it relative to $TPTP. Return lexer, new refdir.
    """
    lex = None

    if not refdir:
        refdir = os.getcwd()

    name = os.path.join(refdir, source)
    try:
        fp = open(name, "r")
        lex = Lexer(fp.read(), name)
        fp.close()
        refdir = os.path.dirname(name)
    except IOError: # pragma: nocover
        tptp = os.getenv("TPTP")
        if tptp:
            name = os.path.join(tptp, source)
            fp = open(name, "r")
            lex = Lexer(fp.read()), name
            fp.close()
            refdir = os.path.dirname(name)
        else:
            raise IOError(errno.ENOENT, "File not found", name)
    return lex, refdir



class FOFSpec(object):
    """
    A datastructure for representing a mixed set of clauses and
    formulas, with support for clausification of the clauses.
    """

    def __init__(self):
        """
        Initialize the specification.
        """
        self.clauses  = []
        self.formulas = []
        self.refdir = None
        self.isFof    = False
        self.hasConj  = False
        self.deriv_index = {}
        self.ordered_proof = None
        self.sig = Signature()

    def __repr__(self):
        """
        Return a string representation of the spec.
        """
        res= "\n".join([repr(c) for c in self.clauses]+
                       [repr(f) for f in self.formulas])
        return res

    def indexDerivable(self, derivable):
        """
        Try to add a clause or formula to the name->derivable index.
        Terminate with an error if the name is already in use.
        """
        if derivable.name in self.deriv_index:
            VerificationStatus(f"VerifiedBad: Identifier '{derivable.name}' is not unique")
        self.deriv_index[derivable.name] = derivable

    def getDerivable(self, name):
        """
        Return clause or formula with name, if it exists, None
        otherwise.
        """
        if name in self.deriv_index:
            return self.deriv_index[name]
        return None

    def addClause(self,clause):
        """
        Add a clause to the specification.
        """
        if clause.type == "negated_conjecture":
            self.hasConj = True
        self.clauses.append(clause)
        self.indexDerivable(clause)
        if clause.derivation and clause.derivation.operator == "file":
            clause.collectSig(self.sig)

    def addFormula(self,formula):
        """
        Add a clause to the specification.
        """
        if formula.type in ["conjecture", "negated_conjecture"] :
            self.hasConj = True
        self.isFof = True
        self.formulas.append(formula)
        self.indexDerivable(formula)
        if formula.derivation and formula.derivation.operator == "file":
            formula.collectSig(self.sig)

    def findEmpty(self):
        """
        Return the empty clause or formula (if any).
        """
        for c in self.clauses:
            if c.isEmpty():
                return c
        for f in self.formulas:
            if f.formula.isPropConst(False):
                return f
        return None

    def parse(self, source, refdir=None):
        """
        Parse a mixed FOF/CNF specification with includes. "source" is
        either a filename or a lexer initialized with the input
        text. "refdir" is the reference directory for TPTP includes.
        """

        if not isinstance(source, Lexer):
            source, refdir = tptpLexer(source, refdir)

        while not source.TestTok(Token.EOFToken):
            source.CheckLit(["cnf", "fof", "include"])
            if source.TestLit("cnf"):
                clause = parseClause(source)
                self.addClause(clause)
            elif source.TestLit("fof"):
                formula = parseWFormula(source)
                self.addFormula(formula)
            else:
                source.AcceptLit("include")
                source.AcceptTok(Token.OpenPar)
                name = source.LookLit()[1:-1]
                source.AcceptTok(Token.SQString)
                source.AcceptTok(Token.ClosePar)
                source.AcceptTok(Token.FullStop)
                self.parse(name, refdir)
        self.refdir = refdir

    def clausify(self):
        """
        Convert all formulas in the spec into clauses, add them to
        self.clauses, and return the resulting set of all clauses.
        """
        while self.formulas:
            form = self.formulas.pop()
            form = negateConjecture(form)
            tmp = wFormulaClausify(form)
            self.clauses.extend(tmp)

        return ClauseSet(self.clauses)

    def addEqAxioms(self):
        """
        Add equality axioms (if necessary). Return True if equality
        is present, false otherwise.
        """
        sig = Signature()
        for c in self.clauses:
            c.collectSig(sig)

        for f in self.formulas:
            f.collectSig(sig)

        if sig.isPred("="):
            res = generateEquivAxioms()
            res.extend(generateCompatAxioms(sig))
            self.clauses.extend(res)
            return True
        return False

    def resolveQuasiReferences(self):
        """
        Replace quasi-references (names) with proper references (to
        other clauses or formulas).
        """
        for c in self.clauses:
            c.derivation.resolveQuasiReferences(self.deriv_index)
        for f in self.formulas:
            f.derivation.resolveQuasiReferences(self.deriv_index)

    def checkStructure(self):
        """
        Perform structural tests:
        - check if there is an explicit $false clause or formula
        - linearize the proof
        - check for forward-references
        If successful, the linearized proof is returned and stored
        in self.ordered_proof.
        """
        deriv_root = self.findEmpty()
        if  deriv_root==None:
            VerificationStatus(f"VerifiedBad: No explicit witness of contradiction")
        if Verbose:
            print("% Proof has explicit witness for contradiction")
        res = deriv_root.orderedDerivation()
        count = 0
        # print(res)
        for step in res:
            step.setNumber(count)
            count+=1
        for step in res:
            step.checkForwardReferences()
        if Verbose:
            print("% Proof structure is sound (no cyclical references)")
        self.ordered_proof = res
        return res



    def computeEqLen(self):
        for c in self.clauses:
            c.computeEqLen()
        for f in self.formulas:
            f.computeEqLen()

    def proofEqLen(self):
        for c in self.clauses:
            if c.isEmpty():
                return c.computeEqLen()
        return 0

    def proofRWSteps(self):
        res = 0
        for c in self.clauses:
            res += c.computeRWSteps()
        for f in self.formulas:
            res += f.computeRWSteps()
        return res


# ------------------------------------------------------------------
#                  Unit test section
# ------------------------------------------------------------------

class TestFormulas(unittest.TestCase):
    """
    Unit test class for clauses. Test clause and literal
    functionality.
    """
    def setUp(self):
        """
        Setup function for clause/literal unit tests. Initialize
        variables needed throughout the tests.
        """
        print()

        self.seed = """
        cnf(agatha,plain,lives(agatha)).
        cnf(butler,plain,lives(butler)).
        cnf(charles,negated_conjecture,lives(charles)).
        include('includetest.txt').
        """
        inctext = """
        fof(dt_m1_filter_2,axiom,(
        ! [A] :
        ( ( ~ v3_struct_0(A)
        & v10_lattices(A)
        & l3_lattices(A) )
        => ! [B] :
        ( m1_filter_2(B,A)
        => ( ~ v1_xboole_0(B)
        & m2_lattice4(B,A) ) ) ) )).
        """
        fp = open("includetest.txt", "w")
        fp.write(inctext)
        fp.close()

        self.testeq = """
        cnf(clause, axiom, a=b).
        fof(eqab, axiom, a=b).
        fof(pa, axiom, p(a)).
        fof(fb, axiom, ![X]:f(X)=b).
        fof(pa, conjecture, ?[X]:p(f(X))).
        """

    def testParse(self):
        """
        Test the parsing and printing of a FOF spec.
        """

        lex = Lexer(self.seed)
        spec = FOFSpec()

        spec.parse(lex)
        print("MIX:\n===")
        print(spec)

    def testCNF(self):
        """
        Test CNFization.
        """

        lex = Lexer(self.seed)
        spec = FOFSpec()
        spec.parse(lex)
        spec.clausify()
        print("CNF:\n===")
        print(spec)

    def testEqAxioms(self):
        """
        Test equality handling.
        """
        lex = Lexer(self.testeq)
        spec = FOFSpec()
        spec.parse(lex)

        spec.addEqAxioms()

        print("EQ:\n===")
        print(spec)


if __name__ == '__main__':
    unittest.main()
