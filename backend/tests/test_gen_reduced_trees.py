import unittest
import tempfile, os

from tests.common import createTestFile, createTestDbTable, readTestDbTable
from tol_data.gen_reduced_trees import genData

class TestGenData(unittest.TestCase):
	def test_gen(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp tree-of-life db
				# Test tree (P/I/L/D means picked/image/linked_image/desc):
					# one -> two -> threeI -> four
					#            -> fiveP
					#     -> [seven + eight] -> sevenD
					#                        -> eightP
					#     -> nine -> tenI
					#     -> elevenL
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)',
				'INSERT INTO nodes VALUES (?, ?, ?)',
				{
					('one', 'ott1', 6),
					('two', 'ott2', 2),
					('three', 'ott3', 1),
					('four', 'ott4', 1),
					('five', 'ott5', 1),
					('[seven + eight]', 'ott6', 2),
					('seven', 'ott7', 1),
					('eight', 'ott8', 1),
					('nine', 'ott9', 1),
					('ten', 'ott10', 1),
					('eleven', 'ott11', 1),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE edges (parent TEXT, child TEXT, p_support INT, PRIMARY KEY (parent, child))',
				'INSERT INTO edges VALUES (?, ?, ?)',
				{
					('one', 'two', 1),
					('two', 'three', 1),
					('three', 'four', 0),
					('two', 'five', 0),
					('one', '[seven + eight]', 1),
					('[seven + eight]', 'seven', 0),
					('[seven + eight]', 'eight', 1),
					('one', 'nine', 1),
					('nine', 'ten', 0),
					('one', 'eleven', 1),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE names(name TEXT, alt_name TEXT, pref_alt INT, src TEXT, PRIMARY KEY(name, alt_name))',
				'INSERT INTO names VALUES (?, ?, ?, ?)',
				{
					('eight', 'VIII', 1, 'eol'),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE wiki_ids (name TEXT PRIMARY KEY, id INT)',
				'INSERT INTO wiki_ids VALUES (?, ?)',
				{
					('seven', 10),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE descs (wiki_id INT PRIMARY KEY, desc TEXT, from_dbp INT)',
				'INSERT INTO descs VALUES (?, ?, ?)',
				{
					(10, 'Seven prefers orange juice', 1),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE node_imgs (name TEXT PRIMARY KEY, img_id INT, src TEXT)',
				'INSERT INTO node_imgs VALUES (?, ?, ?)',
				{
					('three', 1, 'eol'),
					('ten', 10, 'enwiki'),
				}
			)
			createTestDbTable(
				dbFile,
				'CREATE TABLE linked_imgs (name TEXT PRIMARY KEY, otol_ids TEXT)',
				'INSERT INTO linked_imgs VALUES (?, ?)',
				{
					('eleven', 'ott3'),
				}
			)
			# Create temp picked-nodes file
			pickedNodesFile = os.path.join(tempDir, 'picked_nodes.txt')
			createTestFile(pickedNodesFile, (
				'five\n'
				'VIII\n'
			))
			# Run
			genData(None, dbFile, pickedNodesFile)
			# Check
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, id, tips from nodes_p'),
				{
					('one', 'ott1', 3),
					('five', 'ott5', 1),
					('eight', 'ott8', 1),
					('eleven', 'ott11', 1),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT parent, child, p_support from edges_p'),
				{
					('one', 'five', 0),
					('one', 'eight', 1),
					('one', 'eleven', 1),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, id, tips from nodes_i'),
				{
					('one', 'ott1', 4),
					('two', 'ott2', 2),
					('three', 'ott3', 1),
					('five', 'ott5', 1),
					('eight', 'ott8', 1),
					('ten', 'ott10', 1),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT parent, child, p_support from edges_i'),
				{
					('one', 'two', 1),
					('two', 'three', 1),
					('two', 'five', 0),
					('one', 'eight', 1),
					('one', 'ten', 0),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, id, tips from nodes_t'),
				{
					('one', 'ott1', 5),
					('two', 'ott2', 2),
					('three', 'ott3', 1),
					('five', 'ott5', 1),
					('[seven + eight]', 'ott6', 2),
					('seven', 'ott7', 1),
					('eight', 'ott8', 1),
					('ten', 'ott10', 1),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT parent, child, p_support from edges_t'),
				{
					('one', 'two', 1),
					('two', 'three', 1),
					('two', 'five', 0),
					('one', '[seven + eight]', 1),
					('[seven + eight]', 'seven', 0),
					('[seven + eight]', 'eight', 1),
					('one', 'ten', 0),
				}
			)
