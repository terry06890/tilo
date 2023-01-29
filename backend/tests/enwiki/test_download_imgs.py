import unittest
from unittest.mock import Mock, patch
import tempfile
import os

from tests.common import readTestFile, createTestDbTable
from tol_data.enwiki.download_imgs import downloadImgs

class TestDownloadInfo(unittest.TestCase):
	@patch('requests.get', autospec=True)
	def test_download(self, requestsGetMock):
		requestsGetMock.side_effect = lambda url, **kwargs: Mock(content=('img:' + url).encode())
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp image-data db
			imgDb = os.path.join(tempDir, 'img_data.db')
			createTestDbTable(
				imgDb,
				'CREATE TABLE page_imgs (page_id INT PRIMARY KEY, img_name TEXT)',
				'INSERT into page_imgs VALUES (?, ?)',
				{
					(1, 'one'),
					(2, 'two'),
					(3, 'three'),
					(4, 'four'),
					(5, 'five'),
					(6, 'six'),
					(7, 'seven'),
				}
			)
			createTestDbTable(
				imgDb,
				'CREATE TABLE imgs' \
					'(name TEXT PRIMARY KEY, license TEXT, artist TEXT, credit TEXT, restrictions TEXT, url TEXT)',
				'INSERT INTO imgs VALUES (?, ?, ?, ?, ?, ?)',
				{
					('one','cc-by','alice','anna','','https://upload.wikimedia.org/1.jpg'),
					('two','???','bob','barbara','','https://upload.wikimedia.org/2.png'),
					('three','cc-by-sa','clare','File:?','','https://upload.wikimedia.org/3.gif'),
					('four','cc-by-sa 4.0','dave','dan','all','https://upload.wikimedia.org/4.jpeg'),
					('five','cc0','eve','eric',None,'https://upload.wikimedia.org/5.png'),
					('six','cc-by','','fred','','https://upload.wikimedia.org/6.png'),
				}
			)

			# Create temp output directory
			with tempfile.TemporaryDirectory() as outDir:
				# Run
				downloadImgs(imgDb, outDir, 0)

				# Check
				expectedImgs = {
					'1.jpg': 'img:https://upload.wikimedia.org/1.jpg',
					'5.png': 'img:https://upload.wikimedia.org/5.png',
				}
				self.assertEqual(set(os.listdir(outDir)), set(expectedImgs.keys()))
				for imgName, content in expectedImgs.items():
					self.assertEqual(readTestFile(os.path.join(outDir, imgName)), content)
