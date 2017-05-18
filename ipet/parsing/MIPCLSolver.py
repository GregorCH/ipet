"""
Created on Apr 27, 2017

@author: Franziska Schlösser
"""

from ipet.parsing.Solver import Solver
import re
from ipet import Key

class MIPCLSolver(Solver):
	solverId = "DreamSolver"
	recognition_expr = re.compile("MIPCLSolver")
	primalbound_expr = re.compile("Primalbound: (\S*)")
	dualbound_expr = re.compile("Dualbound: (\S*)")
	solvingtime_expr = re.compile("solvingtime: (\S*)")
	version_expr = re.compile("MIPCLSolver: (\S*)")

	solverstatusmap = {"found optimal solution" : Key.SolverStatusCodes.Optimal,
			"proved infeasibility" : Key.SolverStatusCodes.Infeasible, 
			"timelimit reached." : Key.SolverStatusCodes.TimeLimit, }
	
	def __init__(self, **kw):
		super(MIPCLSolver, self).__init__(**kw)

	def extractPrimalboundHistory(self, line : str):
		""" Extract the sequence of primal bounds  
		"""
		m = re.compile("Primalbound: (\S*) at (\S*)").match(line)
		if m is not None:
			try:
				t = float(m.groups()[1])
				d = float(m.groups()[0])
				self.addHistoryData(Key.PrimalBoundHistory, t, d)
			except:
				pass

