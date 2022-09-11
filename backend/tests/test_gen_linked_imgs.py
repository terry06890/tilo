import unittest
import tempfile, os

from tests.common import createTestDbTable, readTestDbTable
from tol_data.gen_linked_imgs import genData

class TestGenData(unittest.TestCase):
	def test_gen(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp tree-of-life db
				# Test tree ('I' means a node has an image):
					# one -> two -> sixI
					#            -> seven
					#            -> eight
					#     -> threeI
					#     -> [nine + ten] -> nineI
					#                     -> ten
					#     -> fiveI -> [twelve + thirteen] -> twelveI
					#                                     -> thirteenI
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)',
				'INSERT INTO nodes VALUES (?, ?, ?)',
				{
					('one', 'ott1', 8),
					('two', 'ott2', 3),
					('three', 'ott3', 1),
					('[nine + ten]', 'ott4', 2),
					('five', 'ott5', 2),
					('six', 'ott6', 1),
					('seven', 'ott7', 1),
					('eight', 'ott8', 1),
					('nine', 'ott9', 1),
					('ten', 'ott10', 1),
					('[twelve + thirteen]', 'ott11', 2),
					('twelve', 'ott12', 1),
					('thirteen', 'ott13', 1),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE edges (parent TEXT, child TEXT, p_support INT, PRIMARY KEY (parent, child))',
				'INSERT INTO edges VALUES (?, ?, ?)',
				{
					('one', 'two', 1),
					('one', 'three', 1),
					('one', '[nine + ten]', 0),
					('one', 'five', 1),
					('two', 'six', 1),
					('two', 'seven', 1),
					('two', 'eight', 0),
					('[nine + ten]', 'nine', 0),
					('[nine + ten]', 'ten', 1),
					('five', '[twelve + thirteen]', 1),
					('[twelve + thirteen]', 'twelve', 1),
					('[twelve + thirteen]', 'thirteen', 0),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE node_imgs (name TEXT PRIMARY KEY, img_id INT, src TEXT)',
				'INSERT INTO node_imgs VALUES (?, ?, ?)',
				{
					('six', 1, 'eol'),
					('three', 10, 'enwiki'),
					('nine', 1, 'picked'),
					('five', 2, 'eol'),
					('twelve', 11, 'enwiki'),
					('thirteen', 12, 'enwiki'),
				}
			)
			# Run
			genData(dbFile)
			# Check
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, otol_ids from linked_imgs'),
				{
					('one', 'ott6'),
					('two', 'ott6'),
					('[nine + ten]', 'ott9,'),
					('[twelve + thirteen]', 'ott12,ott13'),
				}
			)
