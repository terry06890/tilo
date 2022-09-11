import unittest
import tempfile, os

from tests.common import createTestDbTable, readTestDbTable
from tol_data.gen_pop_data import genData

class TestGenData(unittest.TestCase):
	def test_gen(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp pageviews db
			pageviewsDb = os.path.join(tempDir, 'pageview_data.db')
			createTestDbTable(
				pageviewsDb,
				'CREATE TABLE views (title TEXT PRIMARY KEY, id INT, views INT)',
				'INSERT INTO views VALUES (?, ?, ?)',
				{
					('one', 1, 10),
					('two', 2, 20),
					('three', 3, 30),
				}
			)
			# Create temp tree-of-life db
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE wiki_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO wiki_ids VALUES (?, ?)',
				{
					('node1', 1),
					('node3', 3),
				}
			)
			# Run
			genData(pageviewsDb, dbFile)
			# Check
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, pop from node_pop'),
				{
					('node1', 10),
					('node3', 30)
				}
			)
