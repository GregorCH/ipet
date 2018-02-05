'''
Created on 05.02.2018

@author: gregor
'''
import unittest
import pandas as pd
import numpy as np
from ipet.evaluation import IPETFilter

Var = "Var"
Val = "Val"
one_equal = "one_equal"
one_diff = "one_diff"
all_equal = "all_equal"
all_diff = "all_diff"

class DiffAndEqualTest(unittest.TestCase):
    """Test list operators 'diff' and 'equal' for IPETFilter class
    """


    def testFilter(self):
        #
        # construct a test data frame with no index and repeating group index column 'Var'
        #

        testdf = pd.DataFrame(
            [
                ["A", 1.0, False, True, False, True],
                ["A", 2.0, False, True, False, True],
                ["A", 3.0, False, True, False, True],
                ["B", 1.0, True, True, False, False],
                ["B", 1.0, True, True, False, False],
                ["B", 2.0, True, True, False, False],
                ["C", 1.0, True, False, True, False],
                ["C", 1.0, True, False, True, False],
                ["C", 1.0, True, False, True, False],
            ],
            columns = [Var, Val, one_equal, one_diff, all_equal, all_diff]
            )

        #
        # test all combinations of anytestrun and operator if the filtered result matches
        # the corresponding column
        #
        for combi in (one_diff, one_equal, all_diff, all_equal):
            any, op = combi.split("_")
            f = IPETFilter(operator = op, anytestrun = any, datakey = "Val")
            f_result = f.applyListOperator(testdf, ["Var"])

            self.assertTrue(np.all(f_result.values == testdf[combi].values),
                            "Wrong list operator result for combination {}:\n{}\n!=\n{}\n".format(combi, f_result, testdf[combi]))
            print()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
