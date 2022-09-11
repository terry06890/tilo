import unittest
from unittest.mock import patch
import tempfile, os, shutil

from tests.common import createTestFile, createTestDbTable, readTestDbTable
from tol_data.gen_imgs import genImgs

TEST_IMG = os.path.join(os.path.dirname(__file__), 'green.png')

class TestGenImgs(unittest.TestCase):
	@patch('tol_data.gen_imgs.convertImage', autospec=True)
	def test_gen(self, convertImageMock):
		with tempfile.TemporaryDirectory() as tempDir:
			convertImageMock.side_effect = \
				lambda imgPath, outPath: shutil.copy(imgPath, outPath)
			# Create temp EOL images
			eolImgDir = os.path.join(tempDir, 'eol_imgs')
			os.mkdir(eolImgDir)
			shutil.copy(TEST_IMG, os.path.join(eolImgDir, '1 10.jpg'))
			shutil.copy(TEST_IMG, os.path.join(eolImgDir, '2 20.png'))
			shutil.copy(TEST_IMG, os.path.join(eolImgDir, '5 50.jpg'))
			# Create temp EOL image db
			eolImgDb = os.path.join(tempDir, 'eol_imgs.db')
			createTestDbTable(
				eolImgDb,
				'CREATE TABLE images (content_id INT PRIMARY KEY, page_id INT, source_url TEXT,' \
					' copy_url TEXT, license TEXT, copyright_owner TEXT)',
				'INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)',
				{
					(10, 1, 'https://example.com/1.jpg', '', 'cc-by', 'eol owner1'),
					(20, 2, 'https://example.com/2.png', '', 'cc-by-sa', 'eol owner2'),
					(50, 5, 'https://example.com/5.jpg', '', 'cc-by-sa', 'eol owner3'),
				}
			)
			# Create temp enwiki images
			enwikiImgDir = os.path.join(tempDir, 'enwiki_imgs')
			os.mkdir(enwikiImgDir)
			shutil.copy(TEST_IMG, os.path.join(enwikiImgDir, '100.jpg'))
			shutil.copy(TEST_IMG, os.path.join(enwikiImgDir, '200.jpeg'))
			shutil.copy(TEST_IMG, os.path.join(enwikiImgDir, '400.png'))
			# Create temp enwiki image db
			enwikiImgDb = os.path.join(tempDir, 'enwiki_imgs.db')
			createTestDbTable(
				enwikiImgDb,
				'CREATE TABLE page_imgs (page_id INT PRIMARY KEY, img_name TEXT)',
				'INSERT INTO page_imgs VALUES (?, ?)',
				{
					(100, 'one.jpg'),
					(200, 'two.jpeg'),
					(300, 'two.jpeg'),
					(400, 'two.jpeg'),
				}
			)
			createTestDbTable(
				enwikiImgDb,
				'CREATE TABLE imgs (' \
					'name TEXT PRIMARY KEY, license TEXT, artist TEXT, credit TEXT, restrictions TEXT, url TEXT)',
				'INSERT INTO imgs VALUES (?, ?, ?, ?, ?, ?)',
				{
					('one.jpg', 'CC BY-SA 3.0', 'author1', 'credits1', '', 'https://upload.wikimedia.org/one.jpg'),
					('two.jpeg', 'cc-by', 'author2', 'credits2', '', 'https://upload.wikimedia.org/two.jpeg'),
					('four.png', 'cc0', 'author3', '', '', 'https://upload.wikimedia.org/x.png'),
				}
			)
			# Create temp picked-images file
			pickedImgsFile = os.path.join(tempDir, 'img_data.txt')
			createTestFile(pickedImgsFile, (
				'node5.jpg|url1|cc-by-sa 4.0|artist1|credit1\n'
			))
			# Create temp picked-images
			pickedImgDir = os.path.join(tempDir, 'picked_imgs')
			os.mkdir(pickedImgDir)
			shutil.copy(TEST_IMG, os.path.join(pickedImgDir, 'node5.jpg'))
			# Create temp img-list file
			imgListFile = os.path.join(tempDir, 'img_list.txt')
			createTestFile(imgListFile, (
				'ott1 ' + os.path.join(eolImgDir, '1 10.jpg') + '\n'
				'ott2 ' + os.path.join(enwikiImgDir, '200.jpeg') + '\n'
				'ott3\n'
				'ott4 ' + os.path.join(enwikiImgDir, '400.png') + '\n'
				'ott5 ' + os.path.join(eolImgDir, '5 50.jpg') + '\n'
			))
			# Create temp tree-of-life db
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)',
				'INSERT INTO nodes VALUES (?, ?, ?)',
				{
					('node1', 'ott1', 1),
					('node2', 'ott2', 1),
					('node3', 'ott3', 2),
					('node4', 'ott4', 4),
					('node5', 'ott5', 1),
					('node6', 'ott6', 10),
				}
			)
			# Run
			outDir = os.path.join(tempDir, 'img')
			genImgs(imgListFile, eolImgDir, outDir, eolImgDb, enwikiImgDb, pickedImgDir, pickedImgsFile, dbFile)
			# Check
			self.assertEqual(set(os.listdir(outDir)), {
				'ott1.jpg',
				'ott2.jpg',
				'ott4.jpg',
				'ott5.jpg',
			})
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, img_id, src from node_imgs'),
				{
					('node1', 1, 'eol'),
					('node2', 200, 'enwiki'),
					('node4', 400, 'enwiki'),
					('node5', 1, 'picked'),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT id, src, url, license, artist, credit from images'),
				{
					(1, 'eol', 'https://example.com/1.jpg', 'cc-by', 'eol owner1', ''),
					(200, 'enwiki', 'https://en.wikipedia.org/wiki/File:two.jpeg', 'cc-by', 'author2', 'credits2'),
					(400, 'enwiki', 'https://en.wikipedia.org/wiki/File:two.jpeg', 'cc-by', 'author2', 'credits2'),
					(1, 'picked', 'url1', 'cc-by-sa 4.0', 'artist1', 'credit1'),
				}
			)
