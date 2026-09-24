import json
import os
import re
import unicodedata
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.song_embedding import SongEmbedding, HAS_PGVECTOR
from app.models.song import Song

logger = logging.getLogger(__name__)

# Global model cache to avoid re-loading weights on every HTTP request
_MODEL_CACHE: Dict[str, Any] = {}
DEFAULT_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")


def get_embedding_model(model_name: Optional[str] = None):
    """
    Singleton factory for loading sentence-transformer models once per process.
    """
    if model_name is None:
        model_name = DEFAULT_MODEL_NAME

    if model_name not in _MODEL_CACHE:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
        except Exception as e:
            raise RuntimeError(f"Failed to load sentence-transformer model '{model_name}': {str(e)}")
            
    return _MODEL_CACHE[model_name]


def normalize_lyrics(lyrics: str) -> str:
    """
    Deterministic lyric normalization for search & fingerprinting.
    Strips accents, lowercases, removes non-alphanumeric chars except space/newlines, normalizes whitespace.
    """
    if not lyrics:
        return ""
    # Normalize unicode (NFKD)
    normalized = unicodedata.normalize('NFKD', lyrics)
    # Remove accents/diacritics
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    # Convert to lowercase
    normalized = normalized.lower()
    # Normalize whitespace while preserving line structure for chunking
    lines = [re.sub(r'[^\w\s]', '', line).strip() for line in normalized.split('\n')]
    lines = [re.sub(r'\s+', ' ', line) for line in lines if line]
    return "\n".join(lines)


def chunk_lyrics(lyrics: str) -> List[str]:
    """
    Splits song lyrics into chunks (stanzas or fixed line blocks).
    Always returns full normalized lyrics as chunk 0, followed by sub-chunks.
    """
    norm_lyrics = normalize_lyrics(lyrics)
    if not norm_lyrics:
        return [""]

    chunks = [norm_lyrics]

    # Try splitting by double newline (stanzas)
    stanzas = [s.strip() for s in lyrics.split("\n\n") if s.strip()]
    if len(stanzas) > 1:
        for stanza in stanzas:
            cleaned_stanza = normalize_lyrics(stanza)
            if cleaned_stanza and cleaned_stanza not in chunks:
                chunks.append(cleaned_stanza)
    else:
        # Split into blocks of 4 lines
        lines = norm_lyrics.split("\n")
        if len(lines) > 4:
            for i in range(0, len(lines), 4):
                block = "\n".join(lines[i:i+4]).strip()
                if block and block not in chunks:
                    chunks.append(block)

    return chunks


def compute_vector(text_input: str, model_name: Optional[str] = None) -> List[float]:
    """
    Computes a 384-dimensional normalized dense embedding for a given text snippet.
    """
    model = get_embedding_model(model_name)
    vector = model.encode(text_input, normalize_embeddings=True)
    return vector.tolist()


def store_song_embeddings(
    db: Session,
    song_id: Any,
    lyrics: str,
    model_name: Optional[str] = None,
    commit: bool = True
) -> List[SongEmbedding]:
    """
    Deletes old embeddings for a song and generates new whole-song & verse chunk embeddings.
    If commit=False, flushes the session instead of committing, allowing atomic transaction management.
    """
    if model_name is None:
        model_name = DEFAULT_MODEL_NAME

    # Remove existing embeddings for song_id
    db.query(SongEmbedding).filter(SongEmbedding.song_id == song_id).delete()

    chunks = chunk_lyrics(lyrics)
    stored_records = []

    for idx, chunk in enumerate(chunks):
        vector_list = compute_vector(chunk, model_name=model_name)
        embedding_record = SongEmbedding(
            song_id=song_id,
            embedding=vector_list if HAS_PGVECTOR else json.dumps(vector_list),
            embedding_json=json.dumps(vector_list),
            model_name=model_name,
            model_version="v1",
            embedding_dimension=len(vector_list),
            chunk_index=idx,
            chunk_text=chunk[:500]  # Store preview snippet of chunk
        )
        db.add(embedding_record)
        stored_records.append(embedding_record)

    if commit:
        db.commit()
    else:
        db.flush()

    return stored_records


def classify_similarity_level(score: float) -> str:
    """
    Classifies cosine similarity score into qualitative match levels:
    - >= 0.95: likely_duplicate
    - >= 0.80: high_similarity
    - >= 0.65: possible_similarity
    - < 0.65: low_similarity
    """
    if score >= 0.95:
        return "likely_duplicate"
    elif score >= 0.80:
        return "high_similarity"
    elif score >= 0.65:
        return "possible_similarity"
    else:
        return "low_similarity"


def find_similar_songs(
    db: Session,
    target_song_id: Any,
    limit: int = 10,
    min_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Finds top similar songs using vector cosine similarity.
    Uses pgvector HNSW distance on PostgreSQL, or numpy cosine similarity fallback on SQLite.
    """
    target_embeddings = db.query(SongEmbedding).filter(
        SongEmbedding.song_id == target_song_id,
        SongEmbedding.chunk_index == 0
    ).all()

    # FINDING-03 FIX: Safely handle missing/null target embeddings without AttributeError
    if not target_embeddings:
        target_song = db.query(Song).filter(Song.id == target_song_id).first()
        if not target_song:
            return []
        
        lyrics_text = getattr(target_song, 'lyrics', None) or getattr(target_song, 'lyrics_preview', None)
        if not lyrics_text:
            return []
        
        try:
            target_embeddings = store_song_embeddings(db, target_song_id, lyrics_text, commit=True)
        except Exception as e:
            logger.warning(f"Failed auto-generating embedding for song {target_song_id}: {str(e)}")
            return []

    if not target_embeddings or not target_embeddings[0].embedding_json:
        return []

    try:
        target_vec = json.loads(target_embeddings[0].embedding_json)
    except Exception:
        return []

    # FINDING-01 FIX: Index-friendly HNSW query structure using subquery/CTE
    db_bind = db.get_bind()
    if db_bind and db_bind.dialect.name == "postgresql" and HAS_PGVECTOR:
        candidate_limit = max(limit * 10, 100)
        query_sql = text("""
            WITH top_candidate_chunks AS (
                SELECT se.song_id,
                       (1 - (se.embedding <=> :vec::vector)) AS chunk_score
                FROM song_embeddings se
                WHERE se.song_id != :target_id
                ORDER BY se.embedding <=> :vec::vector ASC
                LIMIT :candidate_limit
            )
            SELECT s.id AS song_id, s.title, s.artist_id,
                   MAX(tc.chunk_score) AS similarity_score
            FROM top_candidate_chunks tc
            JOIN songs s ON s.id = tc.song_id
            GROUP BY s.id, s.title, s.artist_id
            HAVING MAX(tc.chunk_score) >= :threshold
            ORDER BY similarity_score DESC
            LIMIT :limit
        """)
        vec_str = "[" + ",".join(map(str, target_vec)) + "]"
        result = db.execute(query_sql, {
            "vec": vec_str,
            "target_id": target_song_id,
            "threshold": min_threshold,
            "candidate_limit": candidate_limit,
            "limit": limit
        }).fetchall()

        similar_songs = []
        for row in result:
            score = float(row.similarity_score)
            similar_songs.append({
                "song_id": str(row.song_id),
                "title": row.title,
                "artist_id": str(row.artist_id),
                "similarity_score": round(score, 4),
                "match_level": classify_similarity_level(score)
            })
        return similar_songs

    # Strategy 2: Python / SQLite fallback for in-memory testing or standard SQLite
    all_embeddings = db.query(SongEmbedding, Song).join(
        Song, Song.id == SongEmbedding.song_id
    ).filter(SongEmbedding.song_id != target_song_id).all()

    target_array = np.array(target_vec)
    target_norm = np.linalg.norm(target_array)
    if target_norm == 0:
        return []

    song_scores: Dict[str, Dict[str, Any]] = {}

    for emb, song in all_embeddings:
        if not emb or not emb.embedding_json:
            continue
        try:
            vec = np.array(json.loads(emb.embedding_json))
        except Exception:
            continue

        vec_norm = np.linalg.norm(vec)
        if vec_norm == 0:
            continue
        sim = float(np.dot(target_array, vec) / (target_norm * vec_norm))

        sid = str(song.id)
        if sid not in song_scores or sim > song_scores[sid]["similarity_score"]:
            song_scores[sid] = {
                "song_id": sid,
                "title": song.title,
                "artist_id": str(song.artist_id),
                "similarity_score": sim,
                "match_level": classify_similarity_level(sim)
            }

    filtered = [
        item for item in song_scores.values()
        if item["similarity_score"] >= min_threshold
    ]
    filtered.sort(key=lambda x: x["similarity_score"], reverse=True)
    return filtered[:limit]
