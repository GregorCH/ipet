'''
Created on 02.08.2014

@author: Customer
'''
import unittest
from ipet.IpetApplication import IpetApplication

class IpetTest(unittest.TestCase):
    '''
    test cases to make sure that the Ipet is correctly working
    '''

    def test_constructor(self):
        '''
        test the IpetApplication constructor
        '''
        gui = IpetApplication()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(IpetTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
