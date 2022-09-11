import unittest
import tempfile, os, shutil

from tests.common import createTestDbTable
from tol_data.eol.review_imgs import reviewImgs

CLICK_IMG = os.path.join(os.path.dirname(__file__), '..', 'green.png')
AVOID_IMG = os.path.join(os.path.dirname(__file__), '..', 'red.png')

class TestReviewImgs(unittest.TestCase):
	def test_review(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create input images
			imgDir = os.path.join(tempDir, 'imgs_for_review')
			os.mkdir(imgDir)
			shutil.copy(CLICK_IMG, os.path.join(imgDir, '1 10.jpg'))
			shutil.copy(CLICK_IMG, os.path.join(imgDir, '2 20.jpeg'))
			shutil.copy(AVOID_IMG, os.path.join(imgDir, '2 21.gif'))
			shutil.copy(AVOID_IMG, os.path.join(imgDir, '2 22.jpg'))
			shutil.copy(AVOID_IMG, os.path.join(imgDir, '3 30.png'))
			shutil.copy(AVOID_IMG, os.path.join(imgDir, '3 31.jpg'))
			# Create temp extra-info db
			extraInfoDb = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				extraInfoDb,
				'CREATE TABLE eol_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO eol_ids VALUES (?, ?)',
				{
					('one', 1),
					('two', 2),
					('three', 3),
				}
			)
			createTestDbTable(
				extraInfoDb,
				'CREATE TABLE names(name TEXT, alt_name TEXT, pref_alt INT, src TEXT, PRIMARY KEY(name, alt_name))',
				'INSERT OR IGNORE INTO names VALUES (?, ?, ?, ?)',
				{
					('two','II',1,'eol'),
				}
			)
			# Run
			outDir = os.path.join(tempDir, 'imgs')
			reviewImgs(imgDir, outDir, extraInfoDb)
			# Check
			self.assertEqual(set(os.listdir(outDir)), {'1 10.jpg', '2 20.jpeg'})
