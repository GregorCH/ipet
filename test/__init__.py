from unittest import TestSuite
from .ExperimentTest import ExperimentTest
from .EvaluationTest import EvaluationTest
from .SolverTest import SolverTest
from .GurobiBoundHistoryTest import GurobiBoundHistoryTest

test_cases = (EvaluationTest, ExperimentTest, SolverTest, GurobiBoundHistoryTest)

def load_tests(loader, tests, pattern):
    suite = TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
