import unittest
import tempfile
import os

from tests.common import createTestFile, readTestDbTable
from tol_data.gen_otol_data import genData

def runGenData(treeFileContents: str, annFileContents: str, pickedFileContents: str):
	""" Sets up files to be read by genData(), runs it, reads the output database, and returns node+edge info """
	with tempfile.TemporaryDirectory() as tempDir:
		# Create temp tree file
		treeFile = os.path.join(tempDir, 'tree.tre')
		createTestFile(treeFile, treeFileContents)
		# Create temp annotations file
		annFile = os.path.join(tempDir, 'ann.json')
		createTestFile(annFile, annFileContents)
		# Create temp picked names file
		pickedFile = os.path.join(tempDir, 'pn.txt')
		createTestFile(pickedFile, pickedFileContents)

		# Run genData()
		dbFile = os.path.join(tempDir, 'data.db')
		genData(treeFile, annFile, pickedFile, dbFile)

		# Read database
		nodes = readTestDbTable(dbFile, 'SELECT name, id, tips FROM nodes')
		edges = readTestDbTable(dbFile, 'SELECT parent, child, p_support FROM edges')
	return nodes, edges

class TestGenData(unittest.TestCase):
	def setUp(self):
		self.maxDiff = None # Remove output-diff size limit

	def test_newick(self):
		treeFileContents = """
			(
				'land plants ott2',
				(
					'TRAVELLER''s tree ott100',
					(domestic_banana_ott4, (lemon_ott6, orange_ott7)citrus_ott5)mrcaott4ott5
				) mrcaott100ott4,
				'Highly  Unu2u8| name!!  ott999',
				'citrus ott230'
			)cellular_organisms_ott1;"""
		annFileContents = '{"nodes": {}}'
		pickedFileContents = ''

		nodes, edges = runGenData(treeFileContents, annFileContents, pickedFileContents)

		self.assertEqual(nodes, {
			('land plants', 'ott2', 1),
			('traveller\'s tree', 'ott100', 1),
			('domestic banana', 'ott4', 1),
			('lemon', 'ott6', 1),
			('orange', 'ott7', 1),
			('citrus', 'ott5', 2),
			('[citrus + domestic banana]', 'mrcaott4ott5', 3),
			('[citrus + traveller\'s tree]', 'mrcaott100ott4', 4),
			('highly  unu2u8| name!! ', 'ott999', 1),
			('citrus [2]', 'ott230', 1),
			('cellular organisms', 'ott1', 7),
		})
		self.assertEqual(edges, {
			('cellular organisms', 'land plants', 0),
			('cellular organisms', '[citrus + traveller\'s tree]', 0),
			('cellular organisms', 'highly  unu2u8| name!! ', 0),
			('cellular organisms', 'citrus [2]', 0),
			('[citrus + traveller\'s tree]', 'traveller\'s tree', 0),
			('[citrus + traveller\'s tree]', '[citrus + domestic banana]', 0),
			('[citrus + domestic banana]', 'domestic banana', 0),
			('[citrus + domestic banana]', 'citrus', 0),
			('citrus', 'lemon', 0),
			('citrus', 'orange', 0),
		})

	def test_newick_invalid(self):
		with self.assertRaises(Exception):
			runGenData('(A,B,(C,D));', '{"nodes": {}}', '')

	def test_annotations(self):
		treeFileContents = '(two_ott2, three_ott3, four_ott4)one_ott1;'
		annFileContents = """
			{
				"date_completed": "xxx",
				"nodes": {
					"ott3": {
						"supported_by": {
							"tree1": "node1"
						}
					},
					"ott4": {
						"supported_by": {
							"tree1": "node2",
							"tree2": "node100"
						},
						"conflicts_with": {
							"tree3": ["x", "y"]
						}
					}
				}
			}"""

		nodes, edges = runGenData(treeFileContents, annFileContents, '')

		self.assertEqual(nodes, {
			('one', 'ott1', 3),
			('two', 'ott2', 1),
			('three', 'ott3', 1),
			('four', 'ott4', 1),
		})
		self.assertEqual(edges, {
			('one', 'two', 0),
			('one', 'three', 1),
			('one', 'four', 0),
		})

	def test_picked_names_file(self):
		treeFileContents = '(one_ott2, two_ott3)one_ott1;'
		pickedFileContents = 'one|ott2'

		nodes, edges = runGenData(treeFileContents, '{"nodes": {}}', pickedFileContents)

		self.assertEqual(nodes, {
			('one [2]', 'ott1', 2),
			('one', 'ott2', 1),
			('two', 'ott3', 1),
		})
		self.assertEqual(edges, {
			('one [2]', 'one', 0),
			('one [2]', 'two', 0),
		})
