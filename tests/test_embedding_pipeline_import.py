"""
Guards the embedding pipeline's imports, which broke silently when
build_card_text moved to utils.vector_helper.
"""

import unittest


class TestEmbeddingPipelineImport(unittest.TestCase):
    def test_module_imports(self):
        import database.etl.embedding_pipeline as mod
        self.assertTrue(callable(mod.build_card_text))

    def test_encoder_imports(self):
        # run_embedding_pipeline imports this lazily, so check it explicitly.
        from app.services.vector_service import generate_embeddings
        self.assertTrue(callable(generate_embeddings))


if __name__ == "__main__":
    unittest.main()
