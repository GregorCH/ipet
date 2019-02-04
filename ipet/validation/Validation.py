'''
Created on 24.01.2018

@author: gregor
'''
import pandas as pd
from ipet.Key import ProblemStatusCodes, SolverStatusCodes, ObjectiveSenseCode
from ipet import Key
from ipet.misc import getInfinity as infty
from ipet.misc import isInfinite as isInf
import numpy as np
import logging
import sqlite3

logger = logging.getLogger(__name__)

DEFAULT_RELTOL = 1e-4
DEFAULT_FEASTOL = 1e-6

class SolufileMarkers:
    OPT = "=opt="
    INF = "=inf="
    BEST = "=best="
    UNKN = "=unkn="
    BESTDUAL = "=bestdual="
    FEAS = "=feas="

class DataBaseMarkers:
    OPT = "opt"
    INF = "inf"
    BEST = "best"

class Validation:
    '''
    Validation of experiments by using external solution information
    '''
    __primalidx__ = 0
    __dualidx__ = 1
    __feas__ = 1e99
    __infeas__ = 1e100


    def __init__(self, solufilename : str = None, tol : float = DEFAULT_RELTOL, feastol : float = DEFAULT_FEASTOL):
        '''
        Validation constructor

        Parameters
        ----------
        solufilename : str
            string with absolute or relative path to a solu file with reference information

        tol : float
            relative objective tolerance

        feastol : float
            relative feasibility tolerance
        '''

        if solufilename:
            if solufilename.endswith(".solu"):
                self.referencedict = self.readSoluFile(solufilename)
                self.objsensedict = {}
            else:
                self.referencedict, self.objsensedict = self.connectToDataBase(solufilename)
                logger.debug("Data base connection finished, {} items".format(len(self.referencedict.items())))
        else:
            self.referencedict, self.objsensedict = {}, {}

        self.tol = tol
        self.inconsistentset = set()

        self.feastol = feastol

    def set_tol(self, tol : float):
        """sets this validation's tol attribute

        Parameters
        ----------

        tol : float
            new value for the tol for this validation
        """
        self.tol = tol

    def set_feastol(self, feastol : float):
        """sets this validation's feastol attribute

        Parameters
        ----------

        feastol : float
            new value for the feastol for this validation
        """
        self.feastol = feastol


    def connectToDataBase(self, databasefilename):
        """connects this validation to a data base
        """

        soludict = {}
        objsensedict = {}
        with sqlite3.connect(databasefilename) as conn:
            c = conn.cursor()

            c.execute('SELECT DISTINCT name, objsense,primbound,dualbound,status FROM instances')

            for name, objsense, primbound, dualbound, status in c:

                if name in soludict:
                    logger.warning("Warning: Duplicate name {} with different data in data base".format(name))

                infotuple = [None, None]
                if status == DataBaseMarkers.OPT:
                    infotuple[self.__primalidx__] = infotuple[self.__dualidx__] = primbound

                elif status == DataBaseMarkers.BEST:
                    if primbound is not None:
                        infotuple[self.__primalidx__] = primbound
                    if dualbound is not None:
                        infotuple[self.__dualidx__] = dualbound

                elif status == DataBaseMarkers.INF:
                    infotuple[self.__primalidx__] = self.__infeas__

                objsensedict[name] = ObjectiveSenseCode.MAXIMIZE if objsense == "max" else ObjectiveSenseCode.MINIMIZE

                soludict[name] = tuple(infotuple)

        return soludict, objsensedict



    def readSoluFile(self, solufilename : str) -> dict:
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
                if line.strip() == "":
                    continue

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
            pb = infty() if objsense == ObjectiveSenseCode.MINIMIZE else -infty()
        return pb

    def getDbValue(self, db : float, objsense : int) -> float :
        """returns a floating point value computed from a given primal bound
        """
        if pd.isnull(db):
            db = -infty() if objsense == ObjectiveSenseCode.MINIMIZE else infty()
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
        return problemname in self.inconsistentset

    def isSolFeasible(self, x : pd.Series):
        """check if the solution is feasible within tolerances

        """
        #
        # respect solution checker output, if it exists
        #
        if x.get(Key.SolCheckerRead) is not None:
            #
            # if this column is not None, the solution checker output exists for at least some of the problems
            # such that it is reasonable to assume that it should exist for all parsed problems
            #
            # recall that we explicitly assume that there has been a solution reported when this function is called
            # if the solution checker failed to read in the solution, or the solution checker crashed and did
            # not report the result of the check command, the solution was most likely infeasible.
            #
            if not pd.isnull(x.get(Key.SolCheckerRead)) and x.get(Key.SolCheckerRead):
                if not pd.isnull(x.get(Key.SolCheckerFeas)) and x.get(Key.SolCheckerFeas):
                    return True
                else:
                    return False
            else:
                return False

        # compute the maximum violation of constraints, LP rows, bounds, and integrality
        maxviol = max((x.get(key, 0.0) for key in
                       [Key.ViolationBds, Key.ViolationCons, Key.ViolationInt, Key.ViolationLP]))

        return maxviol <= self.feastol




    def isSolInfeasible(self, x : pd.Series):
        """check if the solution is infeasible within tolerances

        Parameters
        ----------

        x : Series or dict
            series or dictionary representing single instance information
        """

        #
        # respect solution checker output, if it exists
        #
        if x.get(Key.SolCheckerRead) is not None:
            if x.get(Key.SolCheckerRead):
                if x.get(Key.SolCheckerFeas):
                    return False
                else:
                    return True



        # compute the maximum violation of constraints, LP rows, bounds, and integrality
        maxviol = max((x.get(key, 0.0) for key in [Key.ViolationBds, Key.ViolationCons, Key.ViolationInt, Key.ViolationLP]))

        # if no violations have been recorded, no solution was found, and the solution is not infeasible.
        if pd.isnull(maxviol):
            return False

        return maxviol > self.feastol


    def getReferencePb(self, problemname : str) -> float:
        """get the reference primal bound for this instance

        Parameters
        ----------
        problemname : str
            base name of a problem to access the reference data

        Returns
        -------
        float or None
            either a finite floating point value, or None
        """
        reference = self.referencedict.get(problemname, (None, None))

        if self.isUnkn(reference) or self.isInf(reference) or self.isFeas(reference):
            return None
        else:
            return reference[self.__primalidx__]

    def getReferenceDb(self, problemname : str) -> float:
        """get the reference primal bound for this instance

        Parameters
        ----------
        problemname : str
            base name of a problem to access the reference data

        Returns
        -------
        float or None
            either a finite floating point value, or None
        """
        reference = self.referencedict.get(problemname, (None, None))

        if self.isUnkn(reference) or self.isInf(reference) or self.isFeas(reference):
            return None
        else:
            return reference[self.__dualidx__]

    def getObjSense(self, problemname : str, x : pd.Series):
        """get the objective sense of a problem
        """
        if problemname in self.objsensedict:
            return self.objsensedict[problemname]
        elif not pd.isnull(x.get(Key.ObjectiveSense, None)):
            return x.get(Key.ObjectiveSense)
        else:
            logger.warning("No objective sense for {}, assuming minimization".format(problemname))
            return ObjectiveSenseCode.MINIMIZE

    def validateSeries(self, x : pd.Series) -> str:
        """
        validate the results of a problem

        Parameters:
        ----------
        x : Series
            Data series that represents problem information parsed by a solver

        """
        # print("{x.ProblemName} {x.PrimalBound} {x.DualBound} {x.SolverStatus}".format(x=x))
        problemname = x.get(Key.ProblemName)

        sstatus = x.get(Key.SolverStatus)

        if not problemname:
            return ProblemStatusCodes.Unknown

        if pd.isnull(sstatus):
            return ProblemStatusCodes.FailAbort


        else:
            #
            # check feasibility
            #
            pb = x.get(Key.PrimalBound)
            if self.isSolInfeasible(x) or not (pd.isnull(pb) or isInf(pb) or self.isLE(x.get(Key.ObjectiveLimit, -1e20), pb) or self.isSolFeasible(x)):
                return ProblemStatusCodes.FailSolInfeasible

            #
            # check reference consistency
            #
            psc = self.isReferenceConsistent(x)

            if psc != ProblemStatusCodes.Ok:
                return psc

            #
            # report inconsistency among solvers.
            #
            elif self.isInconsistent(problemname):
                return ProblemStatusCodes.FailInconsistent

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

    def collectInconsistencies(self, df : pd.DataFrame):
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

    def isPbReferenceConsistent(self, pb : float, referencedb : float, objsense : int) -> bool:
        """compare primal bound consistency against reference bound

        Returns
        -------

        bool
            True if the primal bound value is consistent with the reference dual bound
        """
        if objsense == ObjectiveSenseCode.MINIMIZE:
            if not self.isLE(referencedb, pb):
                return False
        else:
            if not self.isGE(referencedb, pb):
                return False
        return True

    def isDbReferenceConsistent(self, db : float, referencepb : float, objsense : int) -> bool:
        """compare dual bound consistency against reference bound

        Returns
        -------

        bool
            True if the dual bound value is consistent with the reference primal bound
        """
        if objsense == ObjectiveSenseCode.MINIMIZE:
            if not self.isGE(referencepb, db):
                return False
        else:
            if not self.isLE(referencepb, db):
                return False
        return True



    def isReferenceConsistent(self, x : pd.Series) -> str :
        """Check consistency with solution information
        """

        problemname = x.get(Key.ProblemName)
        pb = x.get(Key.PrimalBound)
        db = x.get(Key.DualBound)
        obs = self.getObjSense(problemname, x)
        sstatus = x.get(Key.SolverStatus)

        reference = self.referencedict.get(problemname, (None, None))

        logger.debug("Checking against reference {} for problem {}".format(reference, problemname))

        referencepb = self.getPbValue(reference[self.__primalidx__], obs)
        referencedb = self.getDbValue(reference[self.__dualidx__], obs)

        if self.isUnkn(reference):
            return ProblemStatusCodes.Ok

        elif self.isInf(reference):
            if sstatus != SolverStatusCodes.Infeasible and not pd.isnull(pb) and not isInf(pb):
                return ProblemStatusCodes.FailSolOnInfeasibleInstance

        elif self.isFeas(reference):
            if sstatus == SolverStatusCodes.Infeasible:
                return ProblemStatusCodes.FailDualBound

        else:

            pb = self.getPbValue(pb, obs)
            db = self.getDbValue(db, obs)
            if not self.isPbReferenceConsistent(pb, referencedb, obs):
                return ProblemStatusCodes.FailObjectiveValue
            if sstatus == SolverStatusCodes.Infeasible and abs(referencepb) < infty():
                return ProblemStatusCodes.FailDualBound
            if not self.isDbReferenceConsistent(db, referencepb, obs):
                return ProblemStatusCodes.FailDualBound

        return ProblemStatusCodes.Ok

    def updateInconsistency(self, x : pd.Series):
        """
        method that is applied to every row of a data frame to update inconsistency information
        """
        problemname = x.get(Key.ProblemName)
        pb = x.get(Key.PrimalBound)
        db = x.get(Key.DualBound)

        obs = self.getObjSense(problemname, x)

        if pd.isnull(obs):
            obs = ObjectiveSenseCode.MINIMIZE

        if not problemname:
            return


        #
        # for inconsistency checks, we only consider problems that are consistent
        # with the reference information.
        #
        if self.isReferenceConsistent(x) != ProblemStatusCodes.Ok:
            return

        # do not trust versions/settings/solvers that returned an infeasible solution
        if self.isSolInfeasible(x) or (not pd.isnull(pb) and not self.isSolFeasible(x)):
            return

        pb = self.getPbValue(pb, obs)
        db = self.getDbValue(db, obs)
        bestpb = self.bestpb.get(problemname, np.inf if obs == ObjectiveSenseCode.MINIMIZE else -np.inf)
        bestpb = min(bestpb, pb) if obs == ObjectiveSenseCode.MINIMIZE else max(bestpb, pb)

        bestdb = self.bestdb.get(problemname, -np.inf if obs == ObjectiveSenseCode.MINIMIZE else np.inf)
        if x.get(Key.SolverStatus) == SolverStatusCodes.Infeasible:
            db = infty() if obs == ObjectiveSenseCode.MINIMIZE else -infty()

        bestdb = max(bestdb, db) if obs == ObjectiveSenseCode.MINIMIZE else min(bestdb, db)

        if (obs == ObjectiveSenseCode.MINIMIZE and not self.isLE(bestdb, bestpb)) or (obs == ObjectiveSenseCode.MAXIMIZE and not self.isGE(bestdb, bestpb)):
            self.inconsistentset.add(problemname)
        else:
            self.bestdb[problemname] = bestdb
            self.bestpb[problemname] = bestpb




    def validate(self, d : pd.DataFrame):
        """validates the solutions against external information and inconsistencies

            Validation scans data twice:

            1) Collection of inconsistencies (contradicting primal and dual bounds)
            2) Comparison against external validation information from solu file

        Parameters
        d : DataFrame
            joined data from an experiment.
        """
        logger.info("Validating with a (gap) tolerance of {} and a feasibility tolerance of {}.".format(self.tol, self.feastol))

        #
        # 1) collect inconsistencies
        #
        self.collectInconsistencies(d)

        #
        # 2) validate everything considering inconsistencies and validation info from reference information.
        #
        return d.apply(self.validateSeries, axis = 1)


    def isGE(self, a : float, b : float) -> bool:
        """tolerance comparison of a >= b
        """
        return (a >= b - self.tol * max(abs(a), abs(b), 1.0)) #and (a >= b - 0.1)

    def isLE(self, a : float, b : float) -> bool:
        """tolerance comparison of a <= b
        """
        return self.isGE(b, a)
