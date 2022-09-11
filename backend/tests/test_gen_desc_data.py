import unittest
import tempfile, os

from tests.common import createTestDbTable, readTestDbTable
from tol_data.gen_desc_data import genData

class TestGenData(unittest.TestCase):
	def test_gen(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp dbpedia db
			dbpediaDb = os.path.join(tempDir, 'dbp_descs.db')
			createTestDbTable(
				dbpediaDb,
				'CREATE TABLE ids (iri TEXT PRIMARY KEY, id INT)',
				'INSERT INTO ids VALUES (?, ?)',
				{
					('<http://dbpedia.org/resource/One>', 1),
					('<http://dbpedia.org/resource/Two>', 2),
					('<http://dbpedia.org/resource/Three>', 3),
				}
			)
			createTestDbTable(
				dbpediaDb,
				'CREATE TABLE redirects (iri TEXT PRIMARY KEY, target TEXT)',
				'INSERT INTO redirects VALUES (?, ?)',
				{
					('<http://dbpedia.org/resource/Two>', '<http://dbpedia.org/resource/Three>'),
				}
			)
			createTestDbTable(
				dbpediaDb,
				'CREATE TABLE abstracts (iri TEXT PRIMARY KEY, abstract TEXT)',
				'INSERT INTO abstracts VALUES (?, ?)',
				{
					('<http://dbpedia.org/resource/One>', 'One from dbp'),
					('<http://dbpedia.org/resource/Two>', 'Two from dbp'),
					('<http://dbpedia.org/resource/Three>', 'Three from dbp'),
				}
			)
			# Create temp enwiki db
			enwikiDb = os.path.join(tempDir, 'enwiki_descs.db')
			createTestDbTable(
				enwikiDb,
				'CREATE TABLE pages (id INT PRIMARY KEY, title TEXT UNIQUE)',
				'INSERT INTO pages VALUES (?, ?)',
				{
					(1, 'I'),
					(3, 'III'),
					(4, 'IV'),
					(5, 'V'),
					(6, 'VI'),
				}
			)
			createTestDbTable(
				enwikiDb,
				'CREATE TABLE redirects (id INT PRIMARY KEY, target TEXT)',
				'INSERT INTO redirects VALUES (?, ?)',
				{
					(5, 'IV'),
				}
			)
			createTestDbTable(
				enwikiDb,
				'CREATE TABLE descs (id INT PRIMARY KEY, desc TEXT)',
				'INSERT INTO descs VALUES (?, ?)',
				{
					(1, 'One from enwiki'),
					(3, 'Three from enwiki'),
					(4, 'Four from enwiki'),
					(5, 'Five from enwiki'),
				}
			)
			# Create temp tree-of-life db
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE wiki_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO wiki_ids VALUES (?, ?)',
				{
					('first', 1),
					('second', 2),
					('third', 3),
					('fourth', 4),
					('fifth', 5),
					('sixth', 6),
					('seventh', 7),
				}
			)
			# Run
			genData(dbpediaDb, enwikiDb, dbFile)
			# Check
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT wiki_id, desc, from_dbp from descs'),
				{
					(1, 'One from dbp', 1),
					(2, 'Three from dbp', 1),
					(3, 'Three from dbp', 1),
					(4, 'Four from enwiki', 0),
					(5, 'Four from enwiki', 0),
				}
			)
