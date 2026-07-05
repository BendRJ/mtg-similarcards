import unittest
from training.generate_training_data import _supertype, _parse_subtypes

class TestTypeExtraction(unittest.TestCase):


    def test_supertype_extraction(self):
        self.assertEqual(_supertype("Artifact Creature - Golem"), "Creature")

    def test_subtype_extraction(self):
        self.assertEqual(_parse_subtypes("Artifact Creature - Golem"), {"Golem"})

    def test_subtype_extraction_mutliple(self):
            self.assertEqual(_parse_subtypes("Artifact Creature - Golem Myr"), {"Golem", "Myr"})