'''
Created on 02.08.2014

@author: Customer
'''
import unittest
from ipet.IpetApplication import IpetApplication
from ipet.IPETDataTable import IPETDataTableFrame
import pandas as pd

class IpetTest(unittest.TestCase):
    '''
    test cases to make sure that the Ipet is correctly working
    '''

    def test_constructor(self):
        '''
        test the IpetApplication constructor
        '''
        gui = IpetApplication()

    def test_datatablewidget(self):
        dtb = IPETDataTableFrame(None, None)
        singleindexdataframe = pd.DataFrame({'a':[1, 2, 3, 4], 'b':[9, 8, 7, 6]}, index=list('ABCD'))
        dtb.setDataFrame(singleindexdataframe)
        
        multiindexdataframe = pd.concat({'eins':singleindexdataframe,
                                         'zwei': singleindexdataframe + 5}).unstack(0).swaplevel(0, 1, axis=1)
        dtb.setDataFrame(multiindexdataframe)
        self.assertEqual(dtb.colwidths, [(3, 7), (9, 13), (15, 19), (21, 25)],
                         "wrong column widths in Data Table Detection:%s" % str(dtb.colwidths))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(IpetTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
