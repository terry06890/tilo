import unittest
from unittest.mock import Mock, patch
import tempfile, os

from tests.common import readTestFile, createTestDbTable
from tol_data.eol.download_imgs import getEolIdsFromDb, downloadImgs

class TestGetEolIdsFromDb(unittest.TestCase):
	def test_get(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp db
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE eol_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO eol_ids VALUES (?, ?)',
				{
					('one', 1),
					('a second', 2),
				}
			)
			# Run
			eolIds = getEolIdsFromDb(dbFile)
			# Check
			self.assertEqual(eolIds, {1, 2})

class TestDownloadImgs(unittest.TestCase):
	@patch('requests.get', autospec=True)
	def test_gen(self, requestsGetMock):
		requestsGetMock.side_effect = lambda url: Mock(content=('img:' + url).encode())
		with tempfile.TemporaryDirectory() as tempDir:
			eolIds = {1, 2, 4}
			# Create temp images-list db
			imagesListDb = os.path.join(tempDir, 'images_list.db')
			createTestDbTable(
				imagesListDb,
				'CREATE TABLE images (content_id INT PRIMARY KEY, page_id INT, source_url TEXT,' \
					' copy_url TEXT, license TEXT, copyright_owner TEXT)',
				'INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)',
				{
					(10, 1, '???', 'https://content.eol.org/1.jpg', 'cc-by-sa', 'owner1'),
					(20, 2, '', 'https://content.eol.org/2.jpg', 'cc-by', 'owner2'),
					(21, 2, '', 'https://content.eol.org/2b.jpg', 'public domain', 'owner2'),
					(22, 2, '', 'https://content.eol.org/2c.jpg', '???', 'owner3'),
					(23, 2, '', 'data/2d.jpg', 'cc-by-nc', 'owner5'),
					(24, 2, '', 'https://content.eol.org/2e', 'cc-by', 'owner6'),
					(25, 2, '', 'https://content.eol.org/2f.gif', 'cc-by', 'owner7'),
					(30, 3, '', 'https://content.eol.org/3.png', 'cc-by', 'owner3'),
				}
			)
			# Create temp output dir
			with tempfile.TemporaryDirectory() as outDir:
				# Run
				downloadImgs(eolIds, imagesListDb, outDir)
				# Check
				expectedImgs1 = {
					'1 10.jpg': 'img:https://content.eol.org/1.jpg',
					'2 20.jpg': 'img:https://content.eol.org/2.jpg',
					'2 23.jpg': 'img:https://content.eol.org/data/2d.jpg',
					'2 25.gif': 'img:https://content.eol.org/2f.gif',
				}
				expectedImgs2 = {
					'1 10.jpg': 'img:https://content.eol.org/1.jpg',
					'2 21.jpg': 'img:https://content.eol.org/2b.jpg',
					'2 23.jpg': 'img:https://content.eol.org/data/2d.jpg',
					'2 25.gif': 'img:https://content.eol.org/2f.gif',
				}
				outImgSet = set(os.listdir(outDir))
				expectedImgSet1 = set(expectedImgs1.keys())
				expectedImgSet2 = set(expectedImgs2.keys())
				self.assertIn(outImgSet, (expectedImgSet1, expectedImgSet2))
				matchingImgs = expectedImgs1 if outImgSet == expectedImgSet1 else expectedImgs2
				for imgName, imgContent in matchingImgs.items():
					self.assertEqual(readTestFile(os.path.join(outDir, imgName)), imgContent)
