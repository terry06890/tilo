import unittest
import tempfile
import os

from tests.common import createTestFile, readTestDbTable
from tol_data.eol.gen_images_list_db import genData

class TestGenData(unittest.TestCase):
	def test_gen(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp images-list files
			imageListsGlob = os.path.join(tempDir, 'imgs-*.csv')
			createTestFile(os.path.join(tempDir, 'imgs-1.csv'), (
				'EOL content ID,EOL page ID,Medium Source URL,EOL Full-Size Copy URL,License Name,Copyright Owner\n'
				'1,10,https://example.com/1/,https://content.eol.org/1.jpg,cc-by,owner1\n'
				'2,20,https://example2.com/2/,https://content.eol.org/2.jpg,cc-by-sa,owner2\n'
			))
			createTestFile(os.path.join(tempDir, 'imgs-2.csv'), (
				'3,30,https://example.com/3/,https://content.eol.org/3.png,public,owner3\n'
			))

			# Run
			dbFile = os.path.join(tempDir, 'imagesList.db')
			genData(imageListsGlob, dbFile)

			# Check
			self.assertEqual(
				readTestDbTable(
					dbFile, 'SELECT content_id, page_id, source_url, copy_url, license, copyright_owner from images'),
				{
					(1, 10, 'https://example.com/1/', 'https://content.eol.org/1.jpg', 'cc-by', 'owner1'),
					(2, 20, 'https://example2.com/2/', 'https://content.eol.org/2.jpg', 'cc-by-sa', 'owner2'),
					(3, 30, 'https://example.com/3/', 'https://content.eol.org/3.png', 'public', 'owner3'),
				}
			)
