"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import unittest
import os
from ipet.parsing.Solver import GurobiSolver
from ipet import Key
from ipet.parsing.MIPCLSolver import MIPCLSolver

DATADIR = os.path.join(os.path.dirname(__file__), "data")
TMPDIR = os.path.join(os.path.dirname(__file__), ".tmp")

SOLVER = 0
NAME = 1

class GurobiBoundHistoryTest(unittest.TestCase):

    solvers = []

    fileinfo = {
        "gurobi-app1-2": [{
            Key.DualBoundHistory: [(4.0, -178.94318),
                                   (15.0, -168.87923),
                                   (16.0, -168.02564),
                                   (21.0, -167.97894),
                                   (45.0, -52.87391)]}],
        "gurobi-dfn-gwin-UUM": [{
            Key.DualBoundHistory:  [(0.0, 34399.9513), (1.0, 34932.4498), (2.0, 35224.501), (5.0, 35732.2026),
                                    (10.0, 36190.8896), (15.0, 36446.2418), (20.0, 36487.4346), (30.0, 36560.6388),
                                    (35.0, 36794.9912), (40.0, 36954.0784), (45.0, 37086.6219), (50.0, 37187.3527),
                                    (55.0, 37268.4704), (60.0, 37337.5192), (65.0, 37416.447), (70.0, 37472.5101),
                                    (75.0, 37525.486), (80.0, 37583.7266), (85.0, 37625.8314), (90.0, 37662.246),
                                    (95.0, 37693.2658), (100.0, 37724.9412), (105.0, 37763.6901), (110.0, 37793.293),
                                    (115.0, 37820.3871), (120.0, 37848.402), (125.0, 37878.662), (130.0, 37907.2466),
                                    (135.0, 37926.6135), (140.0, 37950.6336), (145.0, 37973.9575), (150.0, 37994.0912),
                                    (155.0, 38013.623), (160.0, 38031.8647), (165.0, 38047.7333), (170.0, 38062.8788),
                                    (175.0, 38081.2145), (180.0, 38097.12), (185.0, 38116.275), (190.0, 38130.2664),
                                    (195.0, 38139.2425), (200.0, 38152.9642), (205.0, 38167.2125), (210.0, 38178.8196),
                                    (215.0, 38192.8589), (220.0, 38205.1286), (225.0, 38217.4697), (230.0, 38229.8536),
                                    (235.0, 38243.2822), (240.0, 38254.3412), (245.0, 38267.1079), (250.0, 38278.5312),
                                    (256.0, 38287.0708), (260.0, 38296.7409), (265.0, 38308.8041), (270.0, 38320.4959),
                                    (275.0, 38332.0348), (280.0, 38342.8841), (285.0, 38354.8239), (290.0, 38365.8799),
                                    (295.0, 38376.0005), (300.0, 38387.0547), (305.0, 38398.2146), (310.0, 38406.3182),
                                    (315.0, 38418.1941), (320.0, 38430.3739), (325.0, 38441.6632), (330.0, 38453.5525),
                                    (335.0, 38465.6491), (340.0, 38476.7816), (345.0, 38489.4966), (350.0, 38499.8318),
                                    (355.0, 38513.6954), (360.0, 38527.5068), (365.0, 38542.3196), (370.0, 38559.6568),
                                    (375.0, 38577.8908), (380.0, 38604.4064), (385.0, 38643.6309)]}],
        "gurobi-enlight14": [{
            Key.DualBoundHistory: []}],
        "gurobi-satellites1-25": [{
            Key.DualBoundHistory: [(2.0, -20.0), (54.0, -19.99877), (55.0, -19.74946)]
        }]
    }

    def setUp(self):
        self.solvers.append([GurobiSolver(), "GUROBI"])
        self.activeSolver = self.solvers[0][SOLVER]

    def tearDown(self):
        pass

    def testData(self):
        for filename in self.fileinfo.keys():
            file = self.getFileName(filename)
            self.readFile(file)
            for key in self.fileinfo.get(filename)[0].keys():
                self.assertInfo(filename, key)

    def assertInfo(self, filename, key):
        refvalue = self.fileinfo.get(filename)[0].get(key)
        self.assertEqual(refvalue, self.activeSolver.getData(key))
    def readFile(self, filename):
        self.readSolver(filename)
        self.activeSolver.reset()
        with open(filename, "r") as f:
            for line in f:
                self.activeSolver.readLine(line)

    def readSolver(self, filename):
        with open(filename) as f:
            for i, line in enumerate(f):
                for solver, name in self.solvers:
                    if solver.recognizeOutput(line):
                        self.activeSolver = solver
                        return



    def getFileName(self, basename):
        return os.path.join(DATADIR, "{}.{}".format(basename, "out"))

if __name__ == "__main__":
    unittest.main()

