"""
Guards the embedding pipeline's imports, which broke silently when
build_card_text moved to utils.vector_helper.
"""

import unittest


class TestEmbeddingPipelineImport(unittest.TestCase):
    def test_module_imports(self):
        import database.etl.embedding_pipeline as mod
        self.assertTrue(callable(mod.build_card_text))


if __name__ == "__main__":
    unittest.main()
