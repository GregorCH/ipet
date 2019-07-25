from unittest import TestSuite
from .ExperimentTest import ExperimentTest
from .EvaluationTest import EvaluationTest
from .SolverTest import SolverTest
from .ReductionIndexTest import ReductionIndexTest
from .FormatTest import FormatTest
from .PrimalDualBoundHistoryTest import PrimalDualBoundHistoryTest
from .GurobiBoundHistoryTest import GurobiBoundHistoryTest
from .IndexTest import IndexTest
from .FilterDataTest import FilterDataTest
from .FillInTest import FillInTest
from .ValidationTest import ValidationTest
from .DiffAndEqualTest import DiffAndEqualTest
import logging



test_cases = (
              DiffAndEqualTest,
              EvaluationTest,
              ExperimentTest,
              SolverTest,
              FormatTest,
              PrimalDualBoundHistoryTest,
              ReductionIndexTest,
              GurobiBoundHistoryTest,
              IndexTest,
              FilterDataTest,
              ValidationTest,
              FillInTest
              )

def load_tests(loader, tests, pattern):
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    suite = TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
