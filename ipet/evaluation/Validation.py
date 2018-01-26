'''
Created on 24.01.2018

@author: gregor
'''
from math import inf
import pandas as pd
from ipet.Key import ProblemStatusCodes, SolverStatusCodes, ObjectiveSenseCode
from ipet.Experiment import Experiment
from ipet import Key
import numpy as np
import logging

DEFAULT_RELTOL = 1e-4

class SolufileMarkers:
    OPT = "=opt="
    INF = "=inf="
    BEST = "=best="
    UNKN = "=unkn="
    BESTDUAL = "=bestdual="
    FEAS = "=feas="
    
class Interval:
    
    def __init__(self, intervaltuple, tol=DEFAULT_RELTOL):
        """
        creates an interval object of an unordered value tuple  
        """
        if type(intervaltuple) is not tuple:
            raise ValueError("Expected a tuple as 'intervaltuple', got {}".format(intervaltuple))
        if len(intervaltuple) != 2:
            raise ValueError("Expected exactly two elements as 'intervaltuple', got {}".format(len(intervaltuple)))
        
        a = min(intervaltuple)
        b = max(intervaltuple)
        
        if abs(a) != np.inf:
            tol_a = a - tol * max(abs(a), 1.0)
        else:
            tol_a = np.inf
        if abs(b) != np.inf:
            tol_b = b + tol * max(abs(b), 1.0)
        else:
            tol_b = b
        
        self.a = a
        self.b = b
        self.tol_a = tol_a
        self.tol_b = tol_b
        
    def intersects(self, other) -> bool:
        """test for intersection with another interval
        
        Parameters:
        -----------
        other : Interval
            a different interval to test
            
        Return:
        -------
        bool 
            True if the two intervals intersect, False otherwise
        """
        return self.tol_a <= other.tol_b and self.tol_b >= other.tol_a
        
    def __str__(self):
        return "[{},{}] [{},{}]".format(self.a, self.b, self.tol_a, self.tol_b)

class Validation:
    '''
    Validation of experiments by using external solution information
    '''
    __primalidx__ = 0
    __dualidx__ = 1
    __feas__ = 1e99
    __infeas__ = 1e100


    def __init__(self, solufilename : str = None, tol=DEFAULT_RELTOL):
        '''
        Validation Constructor
        '''
        if solufilename:
            self.solufiledict = self.readSoluFile(solufilename)
        else:
            self.solufiledict = {}
            
        self.tol = tol
        self.inconsistentset = set()
            
        
    def readSoluFile(self, solufilename:str) -> dict:
        """parse entire solu file into a dictionary with problem names as keys
        
        Parameters:
        -----------
        
        solufilename : str
            name of .solu file containing optimal or best known bounds for instances
            
        Return
        ------
        dict
            dictionary with problem names as keys and best known primal and dual bounds for validation as entries.
        """
        
        soludict = dict()
        with open(solufilename, "r") as solufile:
            for line in solufile:
                spline = line.split()
                marker = spline[0]
                problemname = spline[1]
                
                infotuple = list(soludict.get(problemname, (None, None)))
                if marker == SolufileMarkers.OPT:
                    infotuple[self.__primalidx__] = infotuple[self.__dualidx__] = float(spline[2])
                    
                elif marker == SolufileMarkers.BEST:
                    infotuple[self.__primalidx__] = float(spline[2])
                    
                elif marker == SolufileMarkers.BESTDUAL:
                    infotuple[self.__dualidx__] = float(spline[2])
                    
                elif marker == SolufileMarkers.FEAS:
                    infotuple[self.__primalidx__] = self.__feas__
                    
                elif marker == SolufileMarkers.INF:
                    infotuple[self.__primalidx__] = self.__infeas__
                    
                        
                soludict[problemname] = tuple(infotuple)
        return soludict
    
    def getPbValue(self, pb : float, objsense : int) -> float:
        """returns a floating point value computed from a given primal bound
        """
        if pd.isnull(pb):
            pb = np.infty if objsense == ObjectiveSenseCode.MINIMIZE else -np.infty
        return pb
    
    def getDbValue(self, db : float, objsense : int) -> float :
        """returns a floating point value computed from a given primal bound
        """
        if pd.isnull(db):
            db = -np.infty if objsense == ObjectiveSenseCode.MINIMIZE else np.infty
        return db
    
    
    def isInconsistent(self, problemname : str) -> bool:
        """are there inconsistent results for this problem
        
        Parameters
        ----------
        
        problemname : str
            name of a problem
            
        Returns
        -------
        bool
            True if inconsistent results were detected for this instance, False otherwise
        """
    
    def validateSeries(self, x : pd.Series) -> ProblemStatusCodes:
        """
        validate the results of a problem
        
        Parameters:
        ----------
        x : Series
            Data series that represents problem information parsed by a solver
        
        """
        #print("{x.ProblemName} {x.PrimalBound} {x.DualBound} {x.SolverStatus}".format(x=x))
        problemname = x.loc[Key.ProblemName]
        pb = x.loc[Key.PrimalBound]
        db = x.loc[Key.DualBound]
        sstatus = x.loc[Key.SolverStatus]
        objsense = ObjectiveSenseCode.MINIMIZE
        
        if pd.isnull(sstatus):
            return ProblemStatusCodes.FailAbort
        
        reference = self.solufiledict.get(problemname, (None, None))
        
        if self.isUnkn(reference):
            if self.isInconsistent(problemname):
                return Key.ProblemStatusCodes.FailInconsistent
            return Key.solverToProblemStatusCode(sstatus)

        elif self.isInf(reference):
            if sstatus != SolverStatusCodes.Infeasible and not pd.isnull(pb):
                return ProblemStatusCodes.FailSolOnInfeasibleInstance
            
        elif self.isFeas(reference):
            if sstatus == SolverStatusCodes.Infeasible:
                return ProblemStatusCodes.FailDualBound
        
        elif not self.validateBounds(pb, db, sstatus, objsense, reference):
            return ProblemStatusCodes.FailObjectiveValue
            
        return Key.solverToProblemStatusCode(sstatus)
        
    def isInf(self, referencetuple : tuple) -> bool:
        """is this an infeasible reference?
        
        Parameters:
        -----------
        
        referencetuple : tuple
            tuple containing a primal and dual reference bound
            
        Return:
        -------
        bool
            True if reference bound is infeasible, False otherwise
        """
        return referencetuple[self.__primalidx__] == self.__infeas__
        
    def isFeas(self, referencetuple):
        """is this a feasible reference?
        
        Parameters:
        -----------
        
        referencetuple : tuple
            tuple containing a primal and dual reference bound
            
        Return:
        -------
        bool
            True if reference bound is feasible, False otherwise
        """
        return referencetuple[self.__primalidx__] == self.__feas__ 
    
    def isUnkn(self, referencetuple):
        """is this a reference tuple of an unknown instance?
        """
        return referencetuple[self.__primalidx__] is None and referencetuple[self.__dualidx__] is None
    
    def validateBounds(self, solverpb, solverdb, solverstatus, objsense, referencetuple) -> bool: 
        """
        compares bounds against a reference tuple within tolerance
        """
        pb = self.getPbValue(solverpb, objsense)
        db = self.getDbValue(solverdb, objsense)
        
        solverinterval = Interval((pb, db), self.tol)
        referencepb = self.getPbValue(referencetuple[self.__primalidx__], objsense)
        referencedb = self.getDbValue(referencetuple[self.__dualidx__], objsense)
        
        referenceinterval = Interval((referencedb, referencepb), self.tol)
        
        if solverinterval.intersects(referenceinterval):
            return True
        else:
            return False
        
    def collectInconsistencies(self, df: pd.DataFrame):
        """collect individual results for primal and dual bounds and collect inconsistencies.
        
        Parameters
        ----------
        
        df : DataFrame
            joined data of an experiment with several test runs
        """
        
        # problems with inconsistent primal and dual bounds
        self.inconsistentset = set()
        self.bestpb = dict()
        self.bestdb = dict()
        
        df.apply(self.updateInconsistency, axis = 1)
        
    def updateInconsistency(self, x : pd.Series):
        """
        method that is applied to every row of a data frame to update inconsistency information
        """
        problemname = x.loc[Key.ProblemName]
        pb = x.loc[Key.PrimalBound]
        db = x.loc[Key.DualBound]
        obs = ObjectiveSenseCode.MINIMIZE
        
        pb = self.getPbValue(pb, obs)
        db = self.getDbValue(db, obs)
        
        bestpb = self.bestpb.get(problemname, np.inf if obs == ObjectiveSenseCode.MINIMIZE else -np.inf)
        bestpb = min(bestpb, pb) if obs == ObjectiveSenseCode.MINIMIZE else max(bestpb, pb)
        
        bestdb = self.bestdb.get(problemname, -np.inf if obs == ObjectiveSenseCode.MINIMIZE else np.inf)
        bestdb = max(bestdb, db) if obs == ObjectiveSenseCode.MINIMIZE else min(bestdb, db)
        
        if obs == ObjectiveSenseCode.MINIMIZE:
            if bestdb > bestpb + self.tol * max(1.0, abs(bestpb)):
                self.inconsistentset.add(problemname)
        else:
            if bestdb < bestpb - self.tol * max(1.0, abs(bestpb)):
                self.inconsistentset.add(problemname)
        
        
        self.bestdb[problemname] = bestdb
        self.bestpb[problemname] = bestpb
        
        
        
        
        
        
        
        
if __name__ == "__main__":
    Validation(None)
    v = Validation("/home/gregor/workspace/scip/check/testset/short.solu")
    ex = Experiment()
    ex.addOutputFile("/home/gregor/projects/ipet-github/test/data/check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.trn")
    
    d = ex.getJoinedData()
    assert type(d) is pd.DataFrame

    val = d.apply(v.validateSeries, axis = 1)
    print(val)

    i13 = Interval((1,3))
    i24 = Interval((2,4))
    i35 = Interval((3,5))
    i46 = Interval((4,6)) 
    i64 = Interval((6,4))
    # test trivial intersections:
    print(i13.intersects(i24))
    print(i24)
    print(i13.intersects(i46))
    print(i13.intersects(i35))
    print(i24.intersects(i64))
    print(i64)
    tol_0 = Interval((100,100),tol=0)
    print(tol_0)
    tol_0_2 = Interval((100+1e-8, 100+1e-8), tol=0)
    tol_normal = Interval((100+1e-8, 100+1e-8), tol=1e-6)
    print(tol_0_2)
    print(tol_0.intersects(tol_0_2))
    
    print(tol_normal.intersects(tol_0))
    
    
    
    