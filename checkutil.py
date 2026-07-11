#!/usr/bin/env python3
# ----------------------------------
#
# Module checkutils.py

"""
Utuility functions for the proof checker pycheck.

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
import unittest
# from fofspec import FOFSpec

def VerificationStatus(string):
    print("% SZS status:", string)
    sys.exit(1)



class TestUtils(unittest.TestCase):
    """
    """
    def setUp(self):
        print()

    def testUtil(self):
        """
        """
        pass

if __name__ == '__main__':
    unittest.main()
