import unittest
import tempfile
import os

from tests.common import createTestBz2, readTestDbTable
from tol_data.dbpedia.gen_desc_data import genData

class TestGenData(unittest.TestCase):
	def test_gen(self):
		with tempfile.TemporaryDirectory() as tempDir:
			# Create temp labels file
			labelsFile = os.path.join(tempDir, 'labels.ttl.bz2')
			createTestBz2(labelsFile, (
				'<http://dbpedia.org/resource/One> <http://www.w3.org/2000/01/rdf-schema#label> "One"@en .\n'
				'<http://dbpedia.org/resource/Two> <http://www.w3.org/2000/01/rdf-schema#label> "II"@en .\n'
				'<http://dbpedia.org/resource/Three> <http://www.w3.org/2000/01/rdf-schema#label> "three"@en .\n'
				'<http://dbpedia.org/resource/A_Hat> <http://www.w3.org/2000/01/rdf-schema#label> "A Hat"@en .\n'
			))
			# Create temp ids file
			idsFile = f'{tempDir}ids.ttl.bz2'
			createTestBz2(idsFile, (
				'<http://dbpedia.org/resource/One> <http://dbpedia.org/ontology/wikiPageID>'
					' "1"^^<http://www.w3.org/2001/XMLSchema#integer> .\n'
				'<http://dbpedia.org/resource/Two> <http://dbpedia.org/ontology/wikiPageID>'
					' "2"^^<http://www.w3.org/2001/XMLSchema#integer> .\n'
				'<http://dbpedia.org/resource/Three> <http://dbpedia.org/ontology/wikiPageID>'
					' "3"^^<http://www.w3.org/2001/XMLSchema#integer> .\n'
				'<http://dbpedia.org/resource/A_Hat> <http://dbpedia.org/ontology/wikiPageID>'
					' "210"^^<http://www.w3.org/2001/XMLSchema#integer> .\n'
			))
			# Create temp redirects file
			redirectsFile = os.path.join(tempDir, 'redirects.ttl.bz2')
			createTestBz2(redirectsFile, (
				'<http://dbpedia.org/resource/Three> <http://dbpedia.org/ontology/wikiPageRedirects>'
					' <http://dbpedia.org/resource/A_Hat> .\n'
			))
			# Create temp disambig file
			disambigFile = os.path.join(tempDir, 'disambig.ttl.bz2')
			createTestBz2(disambigFile, (
				'<http://dbpedia.org/resource/Two> <http://dbpedia.org/ontology/wikiPageDisambiguates>'
					' <http://dbpedia.org/resource/One> .\n'
				'<http://dbpedia.org/resource/Two> <http://dbpedia.org/ontology/wikiPageDisambiguates>'
					' <http://dbpedia.org/resource/Three> .\n'
			))
			# Create temp types file
			typesFile = os.path.join(tempDir, 'types.ttl.bz2')
			createTestBz2(typesFile, (
				'<http://dbpedia.org/resource/One> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'
					' <http://dbpedia.org/ontology/Thing> .\n'
				'<http://dbpedia.org/resource/Three> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'
					' <http://dbpedia.org/ontology/Thing> .\n'
			))
			# Create temp abstracts file
			abstractsFile = os.path.join(tempDir, 'abstracts.ttl.bz2')
			createTestBz2(abstractsFile, (
				'<http://dbpedia.org/resource/One> <http://www.w3.org/2000/01/rdf-schema#comment>'
					' "One is a number."@en .\n'
				'<http://dbpedia.org/resource/A_Hat> <http://www.w3.org/2000/01/rdf-schema#comment>'
					' "Hats are not parrots, nor are they potatoes."@en .\n'
			))

			# Run
			dbFile = os.path.join(tempDir, 'descData.db')
			genData(labelsFile, idsFile, redirectsFile, disambigFile, typesFile, abstractsFile, dbFile)

			# Check
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT iri, label from labels'),
				{
					('http://dbpedia.org/resource/One', 'One'),
					('http://dbpedia.org/resource/Two', 'II'),
					('http://dbpedia.org/resource/Three', 'three'),
					('http://dbpedia.org/resource/A_Hat', 'A Hat'),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT iri, id from ids'),
				{
					('http://dbpedia.org/resource/One', 1),
					('http://dbpedia.org/resource/Two', 2),
					('http://dbpedia.org/resource/Three', 3),
					('http://dbpedia.org/resource/A_Hat', 210),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT iri, target from redirects'),
				{
					('http://dbpedia.org/resource/Three', 'http://dbpedia.org/resource/A_Hat'),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT iri from disambiguations'),
				{
					('http://dbpedia.org/resource/Two',),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT iri, type from types'),
				{
					('http://dbpedia.org/resource/One', 'http://dbpedia.org/ontology/Thing'),
					('http://dbpedia.org/resource/Three', 'http://dbpedia.org/ontology/Thing'),
				}
			)
			self.assertEqual(
				readTestDbTable(dbFile, 'SELECT iri, abstract from abstracts'),
				{
					('http://dbpedia.org/resource/One', 'One is a number.'),
					('http://dbpedia.org/resource/A_Hat', 'Hats are not parrots, nor are they potatoes.'),
				}
			)
