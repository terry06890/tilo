import unittest
import tempfile, os

from tests.common import createTestDbTable
from tilo import handleReq, TolNode, SearchSuggResponse, SearchSugg, InfoResponse, NodeInfo, DescInfo, ImgInfo

def initTestDb(dbFile: str) -> None:
	# Test tree (I/D means image/desc):
		# oneI -> twoD -> threeD
		#              -> fourI
		#      -> fiveI -> sixID -> seven
	createTestDbTable(
		dbFile,
		'CREATE TABLE nodes_t (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)',
		'INSERT INTO nodes_t VALUES (?, ?, ?)',
		{
			('one', 'ott1', 3),
			('two', 'ott2', 2),
			('three', 'ott3', 1),
			('four', 'ott4', 1),
			('five', 'ott5', 1),
			('six', 'ott6', 1),
			('seven', 'ott7', 1),
		}
	)
	createTestDbTable(
		dbFile,
		'CREATE TABLE edges_t (parent TEXT, child TEXT, p_support INT, PRIMARY KEY (parent, child))',
		'INSERT INTO edges_t VALUES (?, ?, ?)',
		{
			('one', 'two', 1),
			('two', 'three', 0),
			('two', 'four', 1),
			('one', 'five', 0),
			('five', 'six', 1),
			('six', 'seven', 1),
		}
	)
	createTestDbTable(
		dbFile,
		'CREATE TABLE names(name TEXT, alt_name TEXT, pref_alt INT, src TEXT, PRIMARY KEY(name, alt_name))',
		'INSERT INTO names VALUES (?, ?, ?, ?)',
		{
			('one', 'turtle', 1, 'eol'),
			('two', 'II', 1, 'eol'),
			('five', 'V', 0, 'enwiki'),
			('six', 'VI', 1, 'enwiki'),
		}
	)
	createTestDbTable(
		dbFile,
		'CREATE TABLE node_imgs (name TEXT PRIMARY KEY, img_id INT, src TEXT)',
		'INSERT INTO node_imgs VALUES (?, ?, ?)',
		{
			('one', 1, 'eol'),
			('four', 10, 'enwiki'),
			('five', 10, 'enwiki'),
			('six', 1, 'picked'),
		}
	)
	createTestDbTable(
		dbFile,
		'CREATE TABLE linked_imgs (name TEXT PRIMARY KEY, otol_ids TEXT)',
		'INSERT INTO linked_imgs VALUES (?, ?)',
		{
			('two', 'ott4'),
		}
	)
	createTestDbTable(
		dbFile,
		'CREATE TABLE images (' \
			'id INT, src TEXT, url TEXT, license TEXT, artist TEXT, credit TEXT, PRIMARY KEY (id, src))',
		'INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)',
		{
			(1, 'eol', 'url1', 'license1', 'artist1', 'credit1'),
			(10, 'enwiki', 'url2', 'license2', 'artist2', 'credit2'),
			(1, 'picked', 'url3', 'license3', 'artist3', 'credit3'),
		}
	)
	createTestDbTable(
		dbFile,
		'CREATE TABLE node_iucn (name TEXT PRIMARY KEY, iucn TEXT)',
		'INSERT INTO node_iucn VALUES (?, ?)',
		{
			('one', 'vulnerable'),
			('six', 'endangered'),
		}
	)
	createTestDbTable(
		dbFile,
		'CREATE TABLE node_pop (name TEXT PRIMARY KEY, pop INT)',
		'INSERT INTO node_pop VALUES (?, ?)',
		{
			('one', 10),
			('two', 20),
		}
	)
	createTestDbTable(
		dbFile,
		'CREATE TABLE wiki_ids (name TEXT PRIMARY KEY, id INT)',
		'INSERT INTO wiki_ids VALUES (?, ?)',
		{
			('two', 200),
			('three', 300),
			('six', 600),
		}
	)
	createTestDbTable(
		dbFile,
		'CREATE TABLE descs (wiki_id INT PRIMARY KEY, desc TEXT, from_dbp INT)',
		'INSERT INTO descs VALUES (?, ?, ?)',
		{
			(200, 'two is 2', 1),
			(300, 'three is 3', 0),
			(600, 'six is 6', 1),
		}
	)

class TestHandleReq(unittest.TestCase):
	def setUp(self):
		self.maxDiff = None
		self.tempDir = tempfile.TemporaryDirectory()
		self.dbFile = os.path.join(self.tempDir.name, 'data.db')
		initTestDb(self.dbFile)
	def tearDown(self):
		self.tempDir.cleanup()
	def test_node_req(self):
		response = handleReq(self.dbFile, {'QUERY_STRING': 'name=two&type=node&tree=trimmed'})
		self.assertEqual(response, {
			'two': TolNode('ott2', ['three', 'four'], 'one', 2, True, 'II', 'ott4.jpg', None),
			'three': TolNode('ott3', [], 'two', 1, False, None, None, None),
			'four': TolNode('ott4', [], 'two', 1, True, None, 'ott4.jpg', None),
		})
	def test_node_toroot_req(self):
		response = handleReq(self.dbFile, {'QUERY_STRING': 'name=seven&type=node&toroot=1&excl=five&tree=trimmed'})
		self.assertEqual(response, {
			'five': TolNode('ott5', ['six'], 'one', 1, 0, None, 'ott5.jpg', None),
			'six': TolNode('ott6', ['seven'], 'five', 1, 1, 'VI', 'ott6.jpg', 'endangered'),
			'seven': TolNode('ott7', [], 'six', 1, 1, None, None, None),
		})
	def test_sugg_req(self):
		response = handleReq(self.dbFile, {'QUERY_STRING': 'name=t&type=sugg&tree=trimmed'})
		self.assertEqual(response, SearchSuggResponse(
			[
				SearchSugg('turtle', 'one', 10),
				SearchSugg('two', None, 20),
				SearchSugg('three', None, 0),
			],
			False
		))
	def test_info_req(self):
		response = handleReq(self.dbFile, {'QUERY_STRING': 'name=six&type=info&tree=trimmed'})
		self.assertEqual(response, InfoResponse(
			NodeInfo(
				TolNode('ott6', ['seven'], 'five', 1, True, 'VI', 'ott6.jpg', 'endangered'),
				DescInfo('six is 6', 600, True),
				ImgInfo(1, 'picked', 'url3', 'license3', 'artist3', 'credit3'),
			),
			[]
		))
