import unittest
import tempfile, os, json, bz2, pickle, indexed_bzip2

from tests.common import readTestDbTable
from tol_data.wikidata.gen_taxon_src_data import genData

def runGenData(wikiItemArray: str, preGenOffsets: bool, nProcs: int):
	""" Sets up wikidata file to be read by genData(), runs it, reads the output database, and returns src+iucn info.
		If 'preGenOffsets' is True, generates a bz2 offsets file before running genData(). """
	with tempfile.TemporaryDirectory() as tempDir:
		# Create temp wikidata file
		wikidataFile = os.path.join(tempDir, 'dump.json.bz2')
		with bz2.open(wikidataFile, mode='wb') as file:
			file.write(b'[\n')
			for i in range(len(wikiItemArray)):
				file.write(json.dumps(wikiItemArray[i], separators=(',',':')).encode())
				if i < len(wikiItemArray) - 1:
					file.write(b',')
				file.write(b'\n')
			file.write(b']\n')
		# Create temp offsets file if requested
		offsetsFile = os.path.join(tempDir, 'offsets.dat')
		if preGenOffsets:
			with indexed_bzip2.open(wikidataFile) as file:
				with open(offsetsFile, 'wb') as file2:
					pickle.dump(file.block_offsets(), file2)
		# Run genData()
		dbFile = os.path.join(tempDir, 'data.db')
		genData(wikidataFile, offsetsFile, dbFile, nProcs)
		# Read db
		srcRows = readTestDbTable(dbFile, 'SELECT src, id, title FROM src_id_to_title')
		iucnRows = readTestDbTable(dbFile, 'SELECT title, status FROM title_iucn')
		return srcRows, iucnRows

class TestGenData(unittest.TestCase):
	def setUp(self):
		self.maxDiff = None # Remove output-diff size limit
		self.testWikiItems = [
			{
				'id': 'Q1',
				'claims': {
					'P31': [{'mainsnak': {'datavalue': {'value': {'id': 'Q16521'}}}}], # instance-of 'taxon'
					'P830': [{'mainsnak': {'datavalue': {'value': 100}}}], # EOL ID 100
					'P685': [{'mainsnak': {'datavalue': {'value': 200}}}], # NCBI ID 200
					'P141': [{'mainsnak': {'datavalue': {'value': {'id': 'Q211005'}}}}], # IUCN 'least concern'
				},
				'sitelinks': {'enwiki': {'title': 'eucalyptus'}},
			},
			{
				'id': 'Q2',
				'claims': {
					'P685': [{'mainsnak': {'datavalue': {'value': 101}}}], # NCBI ID 101
					'P31': [{'mainsnak': {'datavalue': {'value': {'id': 'Q23038290'}}}}], # fossil taxon
				},
				'sitelinks': {'enwiki': {'title': 'dolphin'}},
			},
			{
				'id': 'Q30',
				'claims': {
					'P31': [{'mainsnak': {'datavalue': {'value': {'id': 'Q502895'}}}, # instance-of common name
						'qualifiers': {'P642': [{'datavalue': {'value': {'numeric-id': 100}}}]}}], # of Q100
					'P685': [{'mainsnak': {'datavalue': {'value': 333}}}], # NCBI ID 333
				},
				'sitelinks': {'enwiki': {'title': 'dog'}},
			},
			{
				'id': 'Q100',
				'claims': {
					'P31': [{'mainsnak': {'datavalue': {'value': {'id': 'Q16521'}}}}], # instance-of taxon
					'P5055': [{'mainsnak': {'datavalue': {'value': 9}}}], # IRMNG ID 9
					'P141': [{'mainsnak': {'datavalue': {'value': {'id': 'Q11394'}}}}], # IUCN endangered
				},
			},
			{
				'id': 'Q1',
				'claims': {
					'P31': [{'mainsnak': {'datavalue': {'value': {'id': 'Q16521'}}}}], # instance-of taxon
				}
				# No title
			},
			{'id': 'Q932', 'claims': {}},
		]
		self.expectedSrcRows = {
			('eol', 100, 'eucalyptus'),
			('ncbi', 200, 'eucalyptus'),
			('ncbi', 101, 'dolphin'),
			('ncbi', 333, 'dog'),
			('irmng', 9, 'dog'),
		}
		self.expectedIucnRows = {
			('eucalyptus', 'least concern'),
			('dog', 'endangered'),
		}
	def test_wikiItems(self):
		srcRows, iucnRows = runGenData(self.testWikiItems, False, 1)
		self.assertEqual(srcRows, self.expectedSrcRows)
		self.assertEqual(iucnRows, self.expectedIucnRows)
	def test_empty_dump(self):
		srcRows, iucnRows = runGenData([{}], False, 1)
		self.assertEqual(srcRows, set())
		self.assertEqual(iucnRows, set())
	def test_multiprocessing(self):
		srcRows, iucnRows = runGenData(self.testWikiItems, False, 4)
		self.assertEqual(srcRows, self.expectedSrcRows)
		self.assertEqual(iucnRows, self.expectedIucnRows)
	def test_existing_offsets(self):
		srcRows, iucnRows = runGenData(self.testWikiItems, True, 3)
		self.assertEqual(srcRows, self.expectedSrcRows)
		self.assertEqual(iucnRows, self.expectedIucnRows)
