import unittest
import tempfile, os

from tests.common import createTestFile, createTestGzip, createTestDbTable, readTestDbTable
from tol_data.gen_mapping_data import \
	genData, readTaxonomyFile, readEolIdsFile, readWikidataDb, readPickedMappings, getEnwikiPageIds

class TestReadTaxonomyFile(unittest.TestCase):
	def test_read(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp taxonomy file
			taxonomyFile = os.path.join(tempDir, 'taxonomy.tsv')
			SEP = '\t|\t'
			createTestFile(taxonomyFile, ''.join([
				SEP.join(['uid', 'parent_uid', 'name', 'rank', 'sourceinfo', 'uniqueName', 'flags', '\n']),
				SEP.join(['1', '2', 'one', 'species', 'ncbi:10', '', '', '\n']),
				SEP.join(['2', '3', 'two', 'genus', 'ncbi:20,gbif:1', 'bananas', '', '\n']),
				SEP.join(['10', '20', 'ten', 'family', 'if:10,if:100', '', '', '\n']),
				SEP.join(['11', '100', 'eleven', '', 'igloo:1,ncbi:?', '', '', '\n'])
			]))
			# Run
			nodeToSrcIds = {}
			usedSrcIds = set()
			readTaxonomyFile(taxonomyFile, nodeToSrcIds, usedSrcIds)
			# Check
			self.assertEqual(nodeToSrcIds, {
				1: {'ncbi': 10},
				2: {'ncbi': 20, 'gbif': 1},
				10: {'if': 10},
			})
			self.assertEqual(usedSrcIds, {
				('ncbi', 10),
				('ncbi', 20),
				('gbif', 1),
				('if', 10)
			})
class TestReadEolIdsFile(unittest.TestCase):
	def test_read(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp EOL IDs file
			eolIdsFile = os.path.join(tempDir, 'ids.csv.gz')
			createTestGzip(eolIdsFile, (
				'node_id,resource_pk,resource_id,page_id,preferred_canonical_for_page\n'
				'0,10,676,1,rhubarb\n' # EOL ID 1 with ncbi ID 10
				'0,99,767,2,nothing\n' # EOL ID 2 with worms ID 99
				'0,234,459,100,goat\n' # EOL ID 100 with gbif ID 234
				'0,23,676,101,lemon\n' # EOL ID 101 with ncbi ID 23
			))
			# Create input maps
			nodeToSrcIds = {
				10: {'ncbi': 10},
				20: {'ncbi': 23, 'gbif': 234}
			}
			# Run
			usedSrcIds = {('ncbi', 10), ('gbif', 234), ('ncbi', 23)}
			nodeToEolId = {}
			readEolIdsFile(eolIdsFile, nodeToSrcIds, usedSrcIds, nodeToEolId)
			# Check
			self.assertEqual(nodeToEolId, {
				10: 1,
				20: 101,
			})
class TestReadWikidataDb(unittest.TestCase):
	def test_read(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp wikidata db
			wikidataDb = os.path.join(tempDir, 'taxon_srcs.db')
			createTestDbTable(
				wikidataDb,
				'CREATE TABLE src_id_to_title (src TEXT, id INT, title TEXT, PRIMARY KEY(src, id))',
				'INSERT INTO src_id_to_title VALUES (?, ?, ?)',
				[
					('ncbi', 1, 'one'),
					('ncbi', 11, 'two'),
					('gbif', 21, 'three'),
					('if', 31, 'three'),
					('ncbi', 2, 'four'),
					('gbif', 1, 'five'),
					('eol', 1, 'one'),
					('eol', 2, 'three'),
					('ncbi', 100, 'six'),
				]
			)
			createTestDbTable(
				wikidataDb,
				'CREATE TABLE title_iucn (title TEXT PRIMARY KEY, status TEXT)',
				'INSERT INTO title_iucn VALUES (?, ?)',
				[
					('one', 'least concern'),
					('three', 'vulnerable'),
					('six', 'extinct in the wild'),
				]
			)
			# Create input maps
			nodeToSrcIds = {
				10: {'ncbi': 1},
				20: {'ncbi': 11, 'gbif': 21, 'if': 31},
				30: {'ncbi': 2, 'gbif': 1},
				40: {'ncbi': 99},
			}
			usedSrcIds = {
				('ncbi', 1), ('ncbi', 2), ('gbif', 1), ('ncbi', 11), ('gbif', 21), ('if', 31),
				('eol', 10), ('ncbi', 99)
			}
			nodeToEolId = {
				20: 100,
			}
			# Run
			nodeToWikiTitle = {}
			titleToIucnStatus = {}
			readWikidataDb(wikidataDb, nodeToSrcIds, usedSrcIds, nodeToWikiTitle, titleToIucnStatus, nodeToEolId)
			# Check
			self.assertEqual(nodeToWikiTitle, {
				10: 'one',
				20: 'three',
				30: 'four',
			})
			self.assertEqual(titleToIucnStatus, {
				'one': 'least concern',
				'three': 'vulnerable',
			})
			self.assertEqual(nodeToEolId, {
				10: 1,
				20: 100,
			})
class TestReadPickedMappings(unittest.TestCase):
	def test_read(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp picked-mappings files
			pickedMappings = {'eol': ['1.txt'], 'enwiki': ['2.txt', '3.txt']}
			pickedMappingsContent = {'eol': [''], 'enwiki': ['', '']}
			pickedMappingsContent['eol'][0] = (
				'10|100\n'
				'20|202\n'
			)
			pickedMappingsContent['enwiki'][0] = (
				'12|abc\n'
				'23|def\n'
			)
			pickedMappingsContent['enwiki'][1] = (
				'15|ghi\n'
				'35|jkl\n'
			)
			for src in pickedMappings:
				for idx in range(len(pickedMappings[src])):
					pickedMappings[src][idx] = os.path.join(tempDir, pickedMappings[src][idx])
					createTestFile(pickedMappings[src][idx], pickedMappingsContent[src][idx])
			# Create input maps
			nodeToEolId = {
				1: 1,
				10: 66,
			}
			nodeToWikiTitle = {
				10: 'one',
				12: 'two',
				35: 'goanna',
			}
			# Run
			readPickedMappings(pickedMappings, nodeToEolId, nodeToWikiTitle)
			# Check
			self.assertEqual(nodeToEolId, {
				1: 1,
				10: 100,
				20: 202,
			})
			self.assertEqual(nodeToWikiTitle, {
				10: 'one',
				12: 'abc',
				23: 'def',
				15: 'ghi',
				35: 'jkl',
			})
class TestReadGetEnwikiPageIds(unittest.TestCase):
	def test_read(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp dump index
			dumpIndexDb = os.path.join(tempDir, 'dump_index.db')
			createTestDbTable(
				dumpIndexDb,
				'CREATE TABLE offsets (title TEXT PRIMARY KEY, id INT UNIQUE, offset INT, next_offset INT)',
				'INSERT INTO offsets VALUES (?, ?, ?, ?)',
				[
					('one', 1, 10, 100),
					('two', 22, 10, 100),
					('four', 3, 1000, 2000),
				]
			)
			# Create input maps
			nodeToWikiTitle = {
				10: 'one',
				20: 'two',
				30: 'three',
			}
			# Run
			titleToPageId = {}
			getEnwikiPageIds(dumpIndexDb, nodeToWikiTitle, titleToPageId)
			# Check
			self.assertEqual(titleToPageId, {
				'one': 1,
				'two': 22,
			})
class TestGenData(unittest.TestCase):
	def test_mapping(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp taxonomy file
			taxonomyFile = os.path.join(tempDir, 'taxonomy.tsv')
			SEP = '\t|\t'
			createTestFile(taxonomyFile, ''.join([
				SEP.join(['uid', 'parent_uid', 'name', 'rank', 'sourceinfo', 'uniqueName', 'flags', '\n']),
				SEP.join(['1', '', '', '', 'ncbi:10', '', '', '\n']),
				SEP.join(['2', '', '', '', 'ncbi:20,gbif:1', '', '', '\n']),
				SEP.join(['3', '', '', '', 'ncbi:30,if:2', '', '', '\n']),
			]))
			# Create temp EOL IDs file
			eolIdsFile = os.path.join(tempDir, 'ids.csv.gz')
			createTestGzip(eolIdsFile, (
				'node_id,resource_pk,resource_id,page_id,preferred_canonical_for_page\n'
				'0,10,676,1,\n' # EOL ID 1 with ncbi ID 10
				'0,30,676,2,\n' # EOL ID 2 with ncbi ID 30
			))
			# Create temp wikidata db
			wikidataDb = os.path.join(tempDir, 'taxon_srcs.db')
			createTestDbTable(
				wikidataDb,
				'CREATE TABLE src_id_to_title (src TEXT, id INT, title TEXT, PRIMARY KEY(src, id))',
				'INSERT INTO src_id_to_title VALUES (?, ?, ?)',
				[
					('ncbi', 10, 'one'),
					('gbif', 1, 'two'),
					('eol', 100, 'two'),
					('if', 2, 'three'),
				]
			)
			createTestDbTable(
				wikidataDb,
				'CREATE TABLE title_iucn (title TEXT PRIMARY KEY, status TEXT)',
				'INSERT INTO title_iucn VALUES (?, ?)',
				[
					('one', 'least concern'),
					('three', 'vulnerable'),
				]
			)
			# Create temp picked-mappings files
			pickedMappings = {'eol': [], 'enwiki': ['w_ids.txt']}
			pickedMappingsContent = {'eol': [], 'enwiki': ['']}
			pickedMappingsContent['enwiki'][0] = (
				'3|four\n'
			)
			for src in pickedMappings:
				for idx in range(len(pickedMappings[src])):
					pickedMappings[src][idx] = os.path.join(tempDir, pickedMappings[src][idx])
					createTestFile(pickedMappings[src][idx], pickedMappingsContent[src][idx])
			# Create temp dump index
			dumpIndexDb = os.path.join(tempDir, 'dump_index.db')
			createTestDbTable(
				dumpIndexDb,
				'CREATE TABLE offsets (title TEXT PRIMARY KEY, id INT UNIQUE, offset INT, next_offset INT)',
				'INSERT INTO offsets VALUES (?, ?, ?, ?)',
				[
					('one', 1000, 1, 2),
					('two', 2000, 1, 2),
					('three', 3000, 1, 2),
					('four', 4000, 1, 2),
				]
			)
			# Create temp tree-of-life db
			dbFile = os.path.join(tempDir, 'data.db')
			createTestDbTable(
				dbFile,
				'CREATE TABLE nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)',
				'INSERT INTO nodes VALUES (?, ?, ?)',
				[
					('first', 'ott1', 10),
					('second', 'ott2', 1),
					('third', 'ott3', 2),
				]
			)
			# Run
			genData(taxonomyFile, eolIdsFile, wikidataDb, pickedMappings, dumpIndexDb, dbFile)
			# Check
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, id from eol_ids'),
				{
					('first', 1),
					('second', 100),
					('third', 2),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, id from wiki_ids'),
				{
					('first', 1000),
					('second', 2000),
					('third', 4000),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT name, iucn from node_iucn'),
				{
					('first', 'least concern'),
				}
			)
