import unittest
import tempfile, os, shutil

from tests.common import readTestFile, createTestDbTable
from tol_data.review_imgs_to_gen import reviewImgs

CLICK_IMG = os.path.join(os.path.dirname(__file__), 'green.png')
AVOID_IMG = os.path.join(os.path.dirname(__file__), 'red.png')

class TestReviewImgs(unittest.TestCase):
	def test_review(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp eol imgs
			eolImgDir = os.path.join(tempDir, 'eol_imgs')
			os.mkdir(eolImgDir)
			shutil.copy(CLICK_IMG, os.path.join(eolImgDir, '1 10.jpg'))
			shutil.copy(AVOID_IMG, os.path.join(eolImgDir, '2 20.gif'))
			shutil.copy(AVOID_IMG, os.path.join(eolImgDir, '4 40.jpg'))
			# Create temp enwiki imgs
			enwikiImgDir = os.path.join(tempDir, 'enwiki_imgs')
			os.mkdir(enwikiImgDir)
			shutil.copy(AVOID_IMG, os.path.join(enwikiImgDir, '1.jpg'))
			shutil.copy(CLICK_IMG, os.path.join(enwikiImgDir, '3.png'))
			shutil.copy(CLICK_IMG, os.path.join(enwikiImgDir, '4.png'))
			# Create temp tree-of-life db
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)',
				'INSERT INTO nodes VALUES (?, ?, ?)',
				{
					('one', 'ott1', 1),
					('two', 'ott2', 10),
					('three', 'ott3', 2),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE names(name TEXT, alt_name TEXT, pref_alt INT, src TEXT, PRIMARY KEY(name, alt_name))',
				'INSERT OR IGNORE INTO names VALUES (?, ?, ?, ?)',
				{
					('two', 'II', 1, 'eol'),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE eol_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO eol_ids VALUES (?, ?)',
				{
					('one', 1),
					('two', 2),
					('four', 4),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE wiki_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO wiki_ids VALUES (?, ?)',
				{
					('one', 1),
					('three', 3),
					('four', 4),
				}
			)
			# Run
			outFile = os.path.join(tempDir, 'imgList.txt')
			reviewImgs(eolImgDir, enwikiImgDir, dbFile, outFile, 'all')
			# Check
			self.assertEqual(set(readTestFile(outFile).splitlines()), {
				'ott1 ' + os.path.join(eolImgDir, '1 10.jpg'),
				'ott2',
				'ott3 ' + os.path.join(enwikiImgDir, '3.png'),
			})
			# Add extra data
			createTestDbTable(dbFile, None, 'INSERT INTO nodes VALUES (?, ?, ?)',{('four', 'ott4', 2)})
			# Run
			reviewImgs(eolImgDir, enwikiImgDir, dbFile, outFile, 'all')
			# Check
			self.assertEqual(set(readTestFile(outFile).splitlines()), {
				'ott1 ' + os.path.join(eolImgDir, '1 10.jpg'),
				'ott2',
				'ott3 ' + os.path.join(enwikiImgDir, '3.png'),
				'ott4 ' + os.path.join(enwikiImgDir, '4.png'),
			})
