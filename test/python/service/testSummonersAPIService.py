#!/usr/bin/env/python2.7

import unittest
from mock import patch, Mock, MagicMock
from src.api.summoner.summoners import SUMMONERS

class TestSummonersAPIService(unittest.TestCase):
	@patch.object(SUMMONERS, '_getData')
	def testGetSummoners(self, getDataMock):
		# -------------------------------------------------------
		SUMMONERS.getSummoners([1, 2, 3])
		# -------------------------------------------------------
		getDataMock.assert_called_with("1,2,3")

	def testOnSuccess(self):
		# -------------------------------------------------------
		SUMMONERS._onSuccess(None)
		# -------------------------------------------------------
		self.fail("what to do")

	def testOnFail(self):
		# -------------------------------------------------------
		SUMMONERS._onFail(None)
		# -------------------------------------------------------
		self.fail("what to do")

def main():
	unittest.main()

if __name__ == '__main__':
	main()