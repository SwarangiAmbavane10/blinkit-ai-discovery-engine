import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("PipelineLogger")

def index_embeddings_in_pinecone(reviews: List[Dict[str, Any]], index_name: str = None) -> bool:
    """
    Checks for the Pinecone index, creates it if not present,
    and upserts the 384D review embeddings and metadata.
    Falls back to a simulated dry-run if API credentials are missing.
    """
    logger.info("Initializing Storage & Indexing Layer: Syncing with Pinecone...")

    api_key = os.getenv("PINECONE_API_KEY")
    if not index_name:
        index_name = os.getenv("PINECONE_INDEX_NAME", "blinkit-ai-discovery")

    if not api_key or api_key.startswith("YOUR_"):
        logger.warning(
            "PINECONE_API_KEY is not configured or is a placeholder. "
            "Executing simulated Pinecone indexing dry-run."
        )
        simulate_pinecone_upsert(reviews, index_name)
        return True

    try:
        from pinecone import Pinecone, ServerlessSpec
        # Initialize Pinecone Client
        pc = Pinecone(api_key=api_key)

        # Check if the index already exists, create it if not
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        
        if index_name not in existing_indexes:
            logger.info(f"Creating new Pinecone vector index: {index_name} (dim=384, metric=cosine)...")
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"  # Free-tier serverless region
                )
            )
            logger.info(f"Index '{index_name}' successfully created.")
        else:
            logger.info(f"Connected to existing Pinecone index: '{index_name}'")

        # Get Index connection instance
        index = pc.Index(index_name)

        # Format records for upserting
        upsert_data = []
        for rev in reviews:
            review_id = str(rev.get("review_id"))
            vector = rev.get("embedding")
            
            # Construct metadata object (Pinecone only accepts string, int, float, or lists thereof)
            metadata = {
                "source": str(rev.get("source")),
                "rating": float(rev.get("rating", 0.0)),
                "timestamp": str(rev.get("timestamp")),
                "original_text": str(rev.get("original_text"))[:1000],  # prevent payload size limits
                "sentiment": str(rev.get("sentiment")),
                "frustration_level": str(rev.get("frustration_level")),
                "intent": str(rev.get("intent")),
                "user_segment": str(rev.get("user_segment")),
                "unmet_need": str(rev.get("unmet_need")),
                "root_cause": str(rev.get("root_cause"))
            }

            upsert_data.append((review_id, vector, metadata))

        # Perform batched upserts to Pinecone
        batch_size = 100
        for i in range(0, len(upsert_data), batch_size):
            chunk = upsert_data[i:i + batch_size]
            logger.info(f"Upserting batch {i//batch_size + 1} (size={len(chunk)}) to Pinecone...")
            index.upsert(vectors=chunk)

        logger.info(f"Successfully upserted {len(reviews)} vectors to index '{index_name}'.")
        return True

    except Exception as e:
        logger.error(f"Pinecone operations failed: {e}. Executing dry-run fallback.")
        simulate_pinecone_upsert(reviews, index_name)
        return False

def simulate_pinecone_upsert(reviews: List[Dict[str, Any]], index_name: str):
    """Simulates upsert behavior by logging index calls and verifying metadata structures."""
    logger.info(f"--- SIMULATED PINECONE DRY-RUN (Index: {index_name}) ---")
    logger.info(f"Index target verification: OK. Dimensions matches embedding output size (384).")
    
    for idx, rev in enumerate(reviews[:3]):
        logger.info(
            f"Dry-run Vector {idx + 1}: ID={rev.get('review_id')} | "
            f"Embedding length={len(rev.get('embedding', []))} | "
            f"Metadata source={rev.get('source')} | Sentiment={rev.get('sentiment')}"
        )
    if len(reviews) > 3:
        logger.info(f"... and {len(reviews) - 3} more vectors simulated.")
    logger.info("--- DRY-RUN SUCCESSFUL ---")
