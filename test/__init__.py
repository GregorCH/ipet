from unittest import TestSuite
from .ExperimentTest import ExperimentTest
from .EvaluationTest import EvaluationTest
from .SolverTest import SolverTest
from .FormatTest import FormatTest
from .PrimalDualBoundHistoryTest import PrimalDualBoundHistoryTest
import logging


test_cases = (EvaluationTest, 
              ExperimentTest, 
              SolverTest,
              FormatTest,
              PrimalDualBoundHistoryTest,
              )

def load_tests(loader, tests, pattern):
    suite = TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
