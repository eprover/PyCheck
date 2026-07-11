#!/usr/bin/env python3
# ----------------------------------
#
# Module pypcheck.py

"""
Usage: pycheck.py [options] <proof_file>

This program parses (some) TPTP-3 format proofs (FOF only, no frills -
we reuse the PyRes-Parser) and will try to proofcheck the proof, using
E as a backend for deductive steps, and smart hacks for others (I hope
;-)

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
import asyncio
import re
from resource import RLIMIT_STACK, setrlimit, getrlimit
import getopt
from version import *
from lexer import Token,Lexer
from derivations import *
from clauses import Clause
from formulas import Formula, WFormula
from formulacnf import formulaVarNormalize
from clausesets import ClauseSet
from fofspec import FOFSpec
from checkutil import VerificationStatus

def processOptions(opts):
    """
    Process the options given
    """
    global Verbose
    for opt, optarg in opts:
        if opt == "-h" or opt == "--help":
            print("pyres-fof.py "+version)
            print(__doc__)
            sys.exit()
        elif opt == "-v" or opt == "--Verbose":
            Verbose = True

res = []
res_match_re = re.compile("% SZS status (.*)")


class FileCache:
    """
    Provide access to a set of FOF problems potentially to be read
    from the file names provided.
    """
    def __init__(self, refdir = None):
        self.cache = {}
        self.refdir = refdir

    def requestSpec(self, filename):
        if not filename in self.cache:
            spec = FOFSpec()
            spec.parse(filename, self.refdir)
            self.cache[filename] = spec
        return self.cache[filename]

    def getDerivable(self, filename, name):
        spec = self.requestSpec(filename)
        return spec.getDerivable(name)



async def run_prover(step, formulas):
    job = await asyncio.create_subprocess_shell(
        "eprover --auto-schedule=8 --cpu-limit=5 -",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    prob =  "\n".join([repr(f) for f in formulas])+"\n"
    # print("Problem:\n", prob)

    prob = prob.encode('utf-8')
    res_out, res_err = await job.communicate(prob)
    res_out = res_out.decode('utf-8')
    res_err = res_err.decode('utf-8')
    mo = res_match_re.search(res_out)
    res = mo.groups()[0]
    if res == "ResourceOut":
        VerificationStatus(f"Unknown: Verifying {step.name} hit resource limit")
    elif res in ["Satisfiable", "CounterSatisfiable"]:
        VerificationStatus(f"VerifiedBad: {step.name} is unsound")
    elif res in ["Theorem", "ContradictoryAxioms"]:
        print(f"% Verified step {step.name}")
    else:
        VerificationStatus(f"Unknown: Unexpected resuls {res} for {step.name}")




def checkConjectureStructConstraints(step, problem):
    """
    Checks that only plain references of type conjecture and
    negated_conjctures with the appropriate derivation status
    reference a conjecture formula.
    """
    for f in problem.ordered_proof:
        if step in f.getParents():
            if f.type == "conjecture" and f.isSimpleQuotation():
                continue
            if f.type == "negated_conjecture" and f.derivation.status=="status(cth)":
                continue
            VerificationStatus(f"VerifiedBad: Conjecture {step.name} is used weirdly by {f.name}")


def checkInputStep(step, problem, filecache):
    print(f"% Verifying input step {step.name}")
    filename, name = step.derivation.parents
    premise = filecache.getDerivable(filename, name)
    # print(f"Input: {premise}")
    premf = premise.formula
    if isinstance(step, Clause):
        stepf = clauseToFormula(step.clause)
    else:
        stepf = step.formula
    if isinstance(premise, Clause):
        premf = clauseToFormula(premise.clause)
    else:
        stepf = step.formula
    stepf = formulaVarNormalize(stepf)
    premf = formulaVarNormalize(premf)
    # print(f"{stepf} == {premf}")
    if not stepf.isEqual(premf):
        VerificationStatus(f"VerifiedBad: Step {step.name} is not alpha-equal to {premise.name}")
    print(f"% Verified step {step.name}")


async def checkProofStep(step, problem, filecache):
    print(f"% Performing local checks on {step.name}")

    if step.type not in ["axiom",
                         "conjecture",
                         "negated_conjecture",
                         "plain",
                         "definition"]:
        VerificationStatus(f"VerifiedBad: Step {step.name} has unknown type {step.type}")
    if step.type == "conjecture":
        checkConjectureStructConstraints(step, problem)

    if step.derivation.operator == "file":
        checkInputStep(step, problem, filecache)
    else:
        statuses = step.derivation.getDerivationStatuses()
        if len(statuses) > 1:
            VerificationStatus(f"VerifiedBad: Step {step.name}'s derivation has multiple statuses: {statuses}")
        premises = step.getParents()
        if isinstance(step,Clause):
            concl = clauseToFormula(step)
        else:
            concl = step.formula
        # print("Premises:\n", premises)
        # print("Conclusion:\n", concl)
        if "status(cth)" in statuses:
            print(f"# Verifying cth step {step.name}")
            new_prem = WFormula(premises[0].formula, "plain", premises[0].name)
            premises = [new_prem]
            concl = Formula("~", concl)
            conclf = WFormula(concl, "conjecture", "prove_to_verify")
            premises.append(conclf)
            res = await run_prover(step, premises)
        elif "status(thm)" in statuses:
            print(f"# Verifying thm step {step.name}")
            conclf = WFormula(concl, "conjecture", "prove_to_verify")
            premises.append(conclf)
            res = await run_prover(step, premises)
        elif "status(esa)" in statuses:
            print("Need to verify esa step")


async def checkProofSteps(problem):
    filecache = FileCache(problem.refdir)
    for step in problem.ordered_proof:
        await checkProofStep(step, problem, filecache)




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
                                       "hv",
                                       ["help", "Verbose"])
    except getopt.GetoptError as err:
        print(sys.argv[0],":", err)
        sys.exit(1)

    processOptions(opts)

    Derivable.printDerivation = True
    for file in args:
        problem = FOFSpec()
        problem.parse(file)
        problem.resolveQuasiReferences()
        problem.checkStructure()

        print(problem)

        asyncio.run(checkProofSteps(problem))

        VerificationStatus(f"VerifiedGood: No problems found with '{file}'")
