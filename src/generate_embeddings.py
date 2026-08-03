import logging
from typing import List, Dict, Any

logger = logging.getLogger("PipelineLogger")

def generate_review_embeddings(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates 384-dimensional vector embeddings for each review's cleaned text.
    Uses sentence-transformers (all-MiniLM-L6-v2) if available.
    Falls back to generating deterministic mock 384D vectors if imports fail.
    """
    logger.info("Initializing AI Processing Layer: Generating Embeddings...")
    
    use_sentence_transformers = False
    model = None

    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers (all-MiniLM-L6-v2)...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        use_sentence_transformers = True
        logger.info("SentenceTransformer model loaded successfully.")
    except ImportError:
        logger.warning(
            "sentence-transformers or torch packages not installed. "
            "Generating high-quality deterministic mock 384D vector embeddings."
        )

    # Compile the review texts to encode
    texts = [str(r.get("cleaned_text", "")) for r in reviews]

    if use_sentence_transformers and model is not None:
        try:
            # Generate the real dense vectors
            embeddings = model.encode(texts, show_progress_bar=False)
            
            # Map embeddings back to the records as list of floats
            for idx, rev in enumerate(reviews):
                rev["embedding"] = embeddings[idx].tolist()
                
            logger.info(f"Generated {len(reviews)} real 384D embeddings via SentenceTransformer.")
            
        except Exception as e:
            logger.error(f"Failed to generate SentenceTransformer embeddings: {e}. Falling back to mock vectors.")
            use_sentence_transformers = False

    if not use_sentence_transformers:
        # Generate deterministic mock embeddings using text hashing to retain dimension consistency (384 floats)
        import hashlib
        for rev in reviews:
            text = str(rev.get("cleaned_text", ""))
            # Create a repeatable seed from the text hash
            h = hashlib.sha256(text.encode("utf-8")).digest()
            mock_emb = []
            for i in range(384):
                # Generate pseudo-random float values in range [-1.0, 1.0] from hash chunks
                val = ((h[(i % len(h))] * (i + 1)) % 1000) / 500.0 - 1.0
                mock_emb.append(round(val, 6))
            rev["embedding"] = mock_emb
            
        logger.info(f"Generated {len(reviews)} mock 384D vector embeddings.")

    return reviews
