"""
Created on Apr 27, 2017

@author: Franziska Schlösser
"""

from ipet.parsing.Solver import Solver
import re
from ipet import Key
from ipet import misc

class MIPCLSolver(Solver):
	solverId = "MIPCL"
	recognition_expr = re.compile("Reading data")
	primalbound_expr = re.compile("Objective value: (\S*)")
	dualbound_expr = re.compile("^(?:\s*lower-bound: |Objective value: )(\S+)")
	solvingtime_expr = re.compile("Solution time: (\S*)")
	version_expr = re.compile("MIPCL version (\S*)")

	solverstatusmap = {"Objective value: (\S*) - optimality proven" : Key.SolverStatusCodes.Optimal,
			"This problem is infeasible" : Key.SolverStatusCodes.Infeasible,
			"Time limit reached" : Key.SolverStatusCodes.TimeLimit}
	
	# variables needed for primal bound history
	inTable = False
	primalboundhistory_exp = re.compile("^      Time     Nodes    Leaves   Sols       Best Solution         Lower Bound     Gap%")
	endtable = re.compile('^===========================================')

	def __init__(self, **kw):
		super(MIPCLSolver, self).__init__(**kw)

	def extracHistory(self, line : str):
		""" Extract the sequence of primal bounds  
		"""
		if not self.isTableLine(line):
			return 
		
		# history reader should be in a table. check if a display char indicates a new primal bound
		if self.inTable:
			allmatches = misc.numericExpressionOrInf.findall(line)
			if len(allmatches) == 0:
				return

			pointInTime = allmatches[0]
			pb = allmatches[4]
			db = allmatches[5]
			# in the case of ugscip, we reacted on a disp char, so no problem at all.
			self.addHistoryData(Key.PrimalBoundHistory, pointInTime, pb)
			self.addHistoryData(Key.DualBoundHistory, pointInTime, db)
	
	def isTableLine(self, line):
		if self.primalboundhistory_exp.match(line):
			self.inTable = True
			return False
		elif self.inTable and self.endtable.match(line):
			self.inTable = False
			return False
		return self.inTable

