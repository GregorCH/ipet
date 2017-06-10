'''
Created on 09.06.2017

@author: Gregor Hendel
'''

TESTSET_MIPLIB2010 = "MIPLIB2010"
_testsetdict = {TESTSET_MIPLIB2010 : [\
    "30n20b8",
    "acc-tight5",
    "aflow40b",
    "air04",
    "app1-2",
    "ash608gpia-3col",
    "bab5",
    "beasleyC3",
    "biella1",
    "bienst2",
    "binkar10_1",
    "bley_xl1",
    "bnatt350",
    "core2536-691",
    "cov1075",
    "csched010",
    "danoint",
    "dfn-gwin-UUM",
    "eil33-2",
    "eilB101",
    "enlight13",
    "enlight14",
    "ex9",
    "glass4",
    "gmu-35-40",
    "iis-100-0-cov",
    "iis-bupa-cov",
    "iis-pima-cov",
    "lectsched-4-obj",
    "m100n500k4r1",
    "macrophage",
    "map18",
    "map20",
    "mcsched",
    "mik-250-1-100-1",
    "mine-166-5",
    "mine-90-10",
    "msc98-ip",
    "mspp16",
    "mzzv11",
    "n3div36",
    "n3seq24",
    "n4-3",
    "neos-1109824",
    "neos-1337307",
    "neos-1396125",
    "neos13",
    "neos-1601936",
    "neos18",
    "neos-476283",
    "neos-686190",
    "neos-849702",
    "neos-916792",
    "neos-934278",
    "net12",
    "netdiversion",
    "newdano",
    "noswot",
    "ns1208400",
    "ns1688347",
    "ns1758913",
    "ns1766074",
    "ns1830653",
    "opm2-z7-s2",
    "pg5_34",
    "pigeon-10",
    "pw-myciel4",
    "qiu",
    "rail507",
    "ran16x16",
    "reblock67",
    "rmatr100-p10",
    "rmatr100-p5",
    "rmine6",
    "rocII-4-11",
    "rococoC10-001000",
    "roll3000",
    "satellites1-25",
    "sp98ic",
    "sp98ir",
    "tanglegram1",
    "tanglegram2",
    "timtab1",
    "triptim1",
    "unitcal_7",
    "vpphard",
    "zib54-UUE",
    ]
}
def getTestSetByName(testset : str = TESTSET_MIPLIB2010):
    """Return all problem names that belong to the specified test set
    """
    try:
        return _testsetdict[testset]
    except IndexError:
        raise IndexError("Unknown test set specifier {}".format(testset))
    
def getTestSets():
    """return all valid test set identifiers
    """
    return list(_testsetdict.keys())

