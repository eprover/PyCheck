#!/usr/bin/env python3
# ----------------------------------
#
# Module derivations.py

"""
A datatype for representing derivations, i.e. jusifications for
clauses and formulas. Derivations are recursively defined: A
derivation can be the trivial derivation (the clause or formula is
read directly from the input), or it consists of an operator (the
inference rule) and a list of parents.

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

from lexer import Token,Lexer
import unittest


class Derivable(object):
    """
    This class represents "derivable" objects. Derivable objects have
    a name and a justification. Names can be generated
    automatically. They are not strictly required to be different for
    different objects, but will usually be (this makes live easier for
    users). Derivable objects will typically be logical formulas,
    either full FOF formulas, or clauses.
    """
    derivedIdCounter = 0
    """
    Counter for generating new clause names.
    """
    printDerivation = False
    """
    Indicate if derivations shouldbe printed as part of Derivable
    objects. It's up to the concrete classes to support this.
    """
    def __init__(self, name=None, derivation = None):
        """
        Initialize the object..
        """
        self.setName(name)
        self.derivation = derivation
        self.refCount = 0
        self.eqLen = None # How many applications of original axioms
                          # lead to this? Probably only useful in a
                          # purely UEQ setting.
        self.rwSteps = None

    def __repr__(self):
        return self.name

    def setName(self, name = None):
        """
        Set the name. If no name is given, generate a default name.
        """
        if name:
            self.name = name
        else:
            self.name = "c%d"%(Derivable.derivedIdCounter,)
            Derivable.derivedIdCounter=Derivable.derivedIdCounter+1

    def setDerivation(self, derivation):
        """
        Set the derivation that created this derivable.
        """
        self.derivation = derivation

    def setInputDeriv(self, filename, name):
        """
        Special case: It's an input object.
        """
        self.derivation = Derivation("file('%s', %s)"%(filename,name))

    def getParents(self):
        """
        Return a list of all ancestors of this node in the derivation
        graph.
        """
        if self.derivation:
            return self.derivation.getParents()
        else:
            return []

    def incRefCount(self):
        """
        Increase reference counter (counts virtual edges in the
        derivation graph coming from the children).
        """
        self.refCount = self.refCount+1

    def decRefCount(self):
        """
        See above.
        """
        self.refCount = self.refCount-1

    def strDerivation(self):
        """
        If printing of derivations is enabled, return a string
        representartion suitable as part of TPTP-3 output. Otherwise
        return the empty string.
        """
        if not self.derivation:
            return ""
        if Derivable.printDerivation:
            return ","+repr(self.derivation)
        return ""

    def annotateDerivationGraph(self):
        """
        Compute and set the number of virtual edges in all descendents
        of self. The root node has one "virtual" edge.
        """
        if self.refCount == 0:
            parents = self.getParents()
            for p in parents:
                p.annotateDerivationGraph()
        self.incRefCount()

    def linearizeDerivation(self, res = None):
        """
        Return linearized derivation.
        """
        if res == None:
            res = list()
        self.decRefCount()
        if self.refCount==0:
            res.append(self)
            parents = self.getParents()
            for p in parents:
                p.linearizeDerivation(res)
        return res

    def orderedDerivation(self):
        self.annotateDerivationGraph()
        res = self.linearizeDerivation()
        res.reverse()
        return res

    def computeEqLen(self):
        if self.derivation.isInputDeriv() and "conjecture" in self.type:
            self.eqLen = 0
        if self.eqLen == None:
            self.eqLen = self.derivation.computeEqLen()
        return self.eqLen

    def computeRWSteps(self):
        if self.derivation.isInputDeriv() and "conjecture" in self.type:
            self.rwSteps = 0
        if self.rwSteps == None:
            self.rwSteps = self.derivation.computeRWSteps()
        return self.rwSteps


def enableDerivationOutput():
    Derivable.printDerivation = True

def disableDerivationOutput():
    Derivable.printDerivation = False

def toggleDerivationOutput():
     Derivable.printDerivation = not Derivable.printDerivation

class Derivation(object):
    """
    A derivation object. A derivation is either trivial ("input"), a
    reference to an existing Derivable object ("reference"), or an
    inference with a list of premises.
    """
    def __init__(self, operator, parents=None, status="status(thm)"):
        """
        Initialize  a derivation object with the operator and a list
        of parents (which can be Derivations or, in the case of
        "reference", Derivables).
        """
        self.operator = operator
        self.parents  = parents
        self.status   = status

    def __repr__(self):
        """
        Return a string for the derivation in TPTP-3 format.
        """
        if self.isInputDeriv():
            return self.operator
        elif self.operator.startswith("theory("):
            return self.operator
        elif self.operator == "reference":
            assert(len(self.parents)==1)
            return self.parents[0].name
        elif self.operator == "quasi_ref":
            assert(len(self.parents)==1)
            return self.parents[0]+"q"
        else:
            return "inference(%s,[%s],%s)"%\
                   (self.operator, self.status, repr(self.parents))

    def isInputDeriv(self):
        """
        Return true if this derivation corresponds to an input
        clause/formula, i.e. it is justified simply by pointing to its
        origin.
        """
        return self.operator.startswith("file(")

    def getParents(self):
        """
        Return a list of all derived objects that are used in this
        derivation.
        """
        if self.isInputDeriv():
            return []
        elif self.operator.startswith("theory("):
            return []
        elif self.operator == "reference":
            assert(len(self.parents)==1)
            return self.parents
        else:
            res = []
            for p in self.parents:
                res.extend(p.getParents())
            return res

    def resolveQuasiReferences(self, index):
        if self.operator == "quasi_ref":
            self.operator = "reference"
            parents = [index[p] for p in self.parents]
            self.parents = parents
        else:
            # print(self.parents)
            if self.parents:
                for p in self.parents:
                    p.resolveQuasiReferences(index)

    def computeEqLen(self):
        if self.isInputDeriv():
            return 1
        elif self.operator == "reference":
            return self.parents[0].computeEqLen()
        else:
            # print(self.operator, len(self.parents))
            res = 0
            if self.parents:
                for p in self.parents:
                    res += p.computeEqLen()
            return res

    def computeRWSteps(self):
        if self.isInputDeriv():
            return 0
        elif self.operator == "reference":
            return 0
        else:
            res = 0
            if(self.operator in ["rw", "sr"]):
                res = 1
            if self.parents:
                for p in self.parents:
                    res += p.computeRWSteps()
            return res



def parseRecDerivation(lexer):
    if lexer.TestLit("inference"):
        lexer.AcceptLit("inference")
        lexer.AcceptTok(Token.OpenPar)
        operator = lexer.LookLit()
        lexer.AcceptTok(Token.IdentLower)
        lexer.AcceptTok(Token.Comma)
        lexer.AcceptTok(Token.OpenSquare)
        lexer.AcceptLit("status")
        lexer.AcceptTok(Token.OpenPar)
        status = "status(%s)"%(lexer.LookLit(),)
        lexer.AcceptTok(Token.IdentLower)
        lexer.AcceptTok(Token.ClosePar)
        lexer.AcceptTok(Token.CloseSquare)
        lexer.AcceptTok(Token.Comma)
        lexer.AcceptTok(Token.OpenSquare)
        parents = []
        if not lexer.TestTok(Token.CloseSquare):
            parent = parseRecDerivation(lexer)
            parents.append(parent)
            while lexer.TestTok(Token.Comma):
                lexer.AcceptTok(Token.Comma)
                parent = parseRecDerivation(lexer)
                parents.append(parent)
        lexer.AcceptTok(Token.CloseSquare)
        lexer.AcceptTok(Token.ClosePar)
        return Derivation(operator, parents, status)
    elif lexer.TestTok(Token.IdentLower):
        name = lexer.LookLit()
        lexer.AcceptTok(Token.IdentLower)
        return Derivation("quasi_ref", [name])

def parseDerivation(lexer):
    if lexer.TestLit("file"):
        lexer.AcceptLit("file")
        lexer.AcceptTok(Token.OpenPar)
        filename = lexer.LookLit()
        lexer.AcceptTok(Token.SQString)
        lexer.AcceptTok(Token.Comma)
        name = lexer.LookLit()
        lexer.AcceptTok([Token.IdentLower,Token.SQString])
        lexer.AcceptTok(Token.ClosePar)
        return Derivation("file(%s, %s)"%(filename,name))
    else:
        return parseRecDerivation(lexer)


def flatDerivation(operator, parents, status="status(thm)"):
    """
    Simple convenience function: Create a derivation which directly
    references all parents.
    """
    parentlist = [Derivation("reference", [p]) for p in parents]
    return Derivation(operator, parentlist, status)



class TestDerivations(unittest.TestCase):
    """
    """
    def setUp(self):
        print()

    def testDerivable(self):
        """
        Test basic properties of derivations.
        """
        o1 = Derivable()
        o2 = Derivable()
        o3 = Derivable()
        o3.setDerivation(flatDerivation("resolution", [o1, o2]))
        self.assertEqual(o1.getParents(),[])
        self.assertEqual(o2.getParents(),[])
        self.assertEqual(len(o3.getParents()), 2)
        print(o3)
        print(o3.derivation)
        o3.setDerivation(flatDerivation("factor", [o1]))
        print(o3.derivation)
        self.assertEqual(len(o3.getParents()), 1)

    def testProofExtraction(self):
        """
        Test basic proof extraction.
        """
        o1 = Derivable()
        o2 = Derivable()
        o3 = Derivable()
        o4 = Derivable()
        o5 = Derivable()
        o6 = Derivable()
        o7 = Derivable()
        o1.setDerivation(Derivation("theory(equality)"))
        print(repr(o1.derivation))
        o2.setDerivation(Derivation("file('fake', fake')"))
        o3.setDerivation(flatDerivation("factor", [o1]))
        o4.setDerivation(flatDerivation("factor", [o3]))
        o5.setDerivation(flatDerivation("resolution", [o1,o2]))
        o6.setDerivation(Derivation("reference", [o5]))
        o7.setDerivation(flatDerivation("resolution", [o5,o1]))
        proof = o7.orderedDerivation()
        print(proof)
        self.assertEqual(len(proof),4)
        self.assertTrue(o1 in proof)
        self.assertTrue(o2 in proof)
        self.assertTrue(o5 in proof)
        self.assertTrue(o7 in proof)

    def testOutput(self):
        """
        Test derivation output functions.
        """
        o1 = Derivable()
        o2 = Derivable()
        o3 = Derivable()
        o4 = Derivable()
        o1.setDerivation(Derivation("theory(equality)"))
        o2.setDerivation(Derivation("input"))
        o3.setDerivation(flatDerivation("resolution", [o1, o2]))
        enableDerivationOutput()
        self.assertTrue(o2.strDerivation()!="")
        self.assertTrue(o3.strDerivation()!="")
        self.assertTrue(o4.strDerivation()=="")
        disableDerivationOutput()
        self.assertTrue(o3.strDerivation()=="")
        self.assertTrue(o4.strDerivation()=="")
        toggleDerivationOutput()
        self.assertTrue(o3.strDerivation()!="")
        self.assertTrue(o4.strDerivation()=="")



if __name__ == '__main__':
    unittest.main()
