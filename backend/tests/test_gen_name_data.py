import unittest
import tempfile, os

from tests.common import createTestFile, createTestDbTable, readTestDbTable
from tol_data.gen_name_data import genData

class TestGenData(unittest.TestCase):
	def test_gen(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp eol names file
			eolNamesFile = os.path.join(tempDir, 'vernacular_names.csv')
			createTestFile(eolNamesFile, (
				'page_id,,vernacular_string,language_code,,,is_preferred_by_eol\n'
				'10,,cat,eng,,,preferred\n'
				'10,,kitty,eng,,,\n'
				'20,,apple,eng,,,preferred\n'
				'20,,pomme,fr,,,preferred\n'
				'20,,apples,eng,,,\n'
				'30,,those things with wings,eng,,,\n'
			))
			# Create temp enwiki db
			enwikiDb = os.path.join(tempDir, 'desc_data.db')
			createTestDbTable(
				enwikiDb,
				'CREATE TABLE pages (id INT PRIMARY KEY, title TEXT UNIQUE)',
				'INSERT INTO pages VALUES (?, ?)',
				[
					(1, 'abc'),
					(2, 'def'),
					(3, 'ghi'),
				]
			)
			createTestDbTable(
				enwikiDb,
				'CREATE TABLE redirects (id INT PRIMARY KEY, target TEXT)',
				'INSERT INTO redirects VALUES (?, ?)',
				[
					(3, 'abc'),
					(4, 'def'),
				]
			)
			# Create temp picked-names file
			pickedNamesFile = os.path.join(tempDir, 'picked_names.txt')
			createTestFile(pickedNamesFile, (
				'three|xxx|1\n'
				'one|kitty|\n'
				'two|two|\n'
			))
			# Create temp db
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)',
				'INSERT INTO nodes VALUES (?, ?, ?)',
				[
					('one', 'ott1', 1),
					('two', 'ott2', 1),
					('three', 'ott3', 1),
				]
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE eol_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO eol_ids VALUES (?, ?)',
				[
					('one', 10),
					('two', 20),
					('three', 30),
				]
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE wiki_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO wiki_ids VALUES (?, ?)',
				[
					('one', 1),
					('two', 3),
					('three', 2),
				]
			)
			# Run
			genData(eolNamesFile, enwikiDb, pickedNamesFile, dbFile)
			# Check
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, alt_name, pref_alt, src FROM names'),
				{
					('one', 'cat', 1, 'eol'),
					('one', 'ghi', 0, 'enwiki'),
					('two', 'apple', 0, 'eol'),
					('two', 'apples', 0, 'eol'),
					('three', 'xxx', 1, 'picked'),
				}
			)
