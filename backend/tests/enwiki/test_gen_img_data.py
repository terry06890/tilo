import unittest
import tempfile
import os

from tests.common import createTestDbTable, readTestDbTable
from tol_data.enwiki.gen_img_data import getInputPageIdsFromDb, genData

TEST_DUMP_FILE = os.path.join(os.path.dirname(__file__), 'sample_enwiki_pages_articles.xml.bz2')

class TestGetInputPageIdsFromDb(unittest.TestCase):
	def test_get(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp tree-of-life db
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE wiki_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO wiki_ids VALUES (?, ?)',
				{
					('one', 1),
					('and another', 2),
				}
			)

			# Run
			pageIds = getInputPageIdsFromDb(dbFile)

			# Check
			self.assertEqual(pageIds, {1, 2})

class TestGenData(unittest.TestCase):
	def test_gen(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp dump-index db
			indexDb = os.path.join(tempDir, 'dump_index.db')
			createTestDbTable(
				indexDb,
				'CREATE TABLE offsets (title TEXT PRIMARY KEY, id INT UNIQUE, offset INT, next_offset INT)',
				'INSERT INTO offsets VALUES (?, ?, ?, ?)',
				{
					('AccessibleComputing',10,0,-1),
					('AfghanistanHistory',13,0,-1),
					('Autism',25,0,-1),
				}
			)

			# Run
			imgDb = os.path.join(tempDir, 'imgData.db')
			genData({10, 25}, TEST_DUMP_FILE, indexDb, imgDb)

			# Check
			self.assertEqual(
				readTestDbTable(imgDb, 'SELECT page_id, img_name from page_imgs'),
				{
					(10, None),
					(25, 'Autism-stacking-cans 2nd edit.jpg'),
				}
			)

			# Run with updated page-ids set
			genData({13, 10}, TEST_DUMP_FILE, indexDb, imgDb)

			# Check
			self.assertEqual(
				readTestDbTable(imgDb, 'SELECT page_id, img_name from page_imgs'),
				{
					(10, None),
					(13, None),
					(25, 'Autism-stacking-cans 2nd edit.jpg'),
				}
			)
