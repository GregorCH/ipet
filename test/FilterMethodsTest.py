'''
Created on 21.03.2018

@author: gregor
'''
import unittest
from ipet.evaluation import IPETFilter
from _ast import Attribute
from ipet.evaluation.IPETFilter import IPETValue


class FilterMethodsTest(unittest.TestCase):

    def assertionMessage(self, f1, f2):
        return "Filter comparison fails for the filters {} and {}".format(f1.getName(), f2.getName())

    def testFilterComparison(self):

        # test if different operators are correctly distinguished
        operatorlist = ["le", "ge", "lt", "gt", "eq", "neq"]
        for operator1 in operatorlist:
            for operator2 in operatorlist:
                f1 = IPETFilter("A", "B", operator1)
                f2 = IPETFilter("A", "B", operator2)
                eq = f1.equals(f2)
                self.assertEqual(eq, operator1 == operator2,
                                 self.assertionMessage(f1, f2))

    def testAnyAll(self):
        # test if filters that have all attributes equal except for the anytestrun attribute are distinguished
        commonattributes = dict(expression1 = "A", expression2 = "B", operator = "eq", active = True, datakey = "C")
        possiblevalues = ["one", "all"]

        for any1 in possiblevalues:
            for any2 in possiblevalues:
                f1 = IPETFilter(anytestrun = any1, **commonattributes)
                f2 = IPETFilter(anytestrun = any2, **commonattributes)

                eq = f1.equals(f2)
                self.assertEqual(eq, any1 == any2, self.assertionMessage(f1, f2))

    def testListOperators(self):
        attributes = IPETFilter.listoperators
        commonattributes = dict(datakey = "A", anytestrun = "all")
        for op1 in attributes:
            for op2 in attributes:
                f1 = IPETFilter(operator = op1, **commonattributes)
                f2 = IPETFilter(operator = op2, **commonattributes)

                eq = f1.equals(f2)
                self.assertEqual(eq, op1 == op2, self.assertionMessage(f1, f2))


    def testValueLists(self):

        valuelist1 = [
            [IPETValue("A"), IPETValue("B"), IPETValue("C")],
            [IPETValue("A"), IPETValue("B"), IPETValue("C")],
            [IPETValue("A"), ]
            ]
        valuelist2 = [
            [IPETValue("A"), IPETValue("B"), IPETValue("C")],
            [IPETValue("A"), IPETValue("B"), IPETValue("C")],
            [IPETValue("A"), IPETValue("B"), IPETValue("C")]
            ]

        operators1 = IPETFilter.valueoperators + IPETFilter.valueoperators[:1]
        operator2 = "keep"

        for op, v1list, v2list in zip(operators1, valuelist1, valuelist2):
            f1 = IPETFilter(datakey = "ABC", operator = op)
            f2 = IPETFilter(datakey = "ABC", operator = operator2)

            for v1 in v1list:
                f1.addChild(v1)
            for v2 in v2list:
                f2.addChild(v2)

            eq = f1.equals(f2)
            shouldbeequal = (op == operator2) and len(v1list) == len(v2list)

            self.assertEqual(eq, shouldbeequal, self.assertionMessage(f1, f2))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testFilterComparison']
    unittest.main()
