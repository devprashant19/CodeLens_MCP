import sqlite3
import json
import sqlite_vec
from typing import List, Dict, Any, Optional

from codelens.chunker import Chunk

class Store:
    def __init__(self, db_path: str = "codelens.sqlite"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        # Enable foreign keys and other pragmas if needed
        conn.execute("PRAGMA journal_mode=WAL")
        # Load sqlite-vec extension
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # Metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    code_text TEXT NOT NULL,
                    symbol_name TEXT NOT NULL,
                    symbol_type TEXT NOT NULL,
                    parent_symbol TEXT,
                    file_hash TEXT NOT NULL
                )
            """)
            
            # Create indices for exact lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON chunks(file_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_name ON chunks(symbol_name)")
            
            # Vector table (sqlite-vec uses virtual tables)
            # 768 is the default dimension for Gemini text-embedding-004
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
                    embedding float[768]
                )
            """)
            conn.commit()

    def get_file_hashes(self) -> Dict[str, str]:
        """Returns a mapping of file_path -> file_hash for incremental indexing."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT file_path, file_hash FROM chunks")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def delete_file_chunks(self, file_path: str):
        """Removes all chunks and their vectors for a given file."""
        with self._get_connection() as conn:
            # Get IDs to delete from vec_chunks
            cursor = conn.execute("SELECT id FROM chunks WHERE file_path = ?", (file_path,))
            ids = [row[0] for row in cursor.fetchall()]
            
            if ids:
                placeholders = ",".join(["?"] * len(ids))
                conn.execute(f"DELETE FROM vec_chunks WHERE rowid IN ({placeholders})", ids)
                conn.execute("DELETE FROM chunks WHERE file_path = ?", (file_path,))
            conn.commit()

    def insert_chunks(self, chunks: List[Chunk], embeddings: List[List[float]], file_hash: str):
        """Inserts new chunks and their embeddings."""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for chunk, embedding in zip(chunks, embeddings):
                # Insert metadata
                cursor.execute("""
                    INSERT INTO chunks (
                        file_path, start_line, end_line, code_text, 
                        symbol_name, symbol_type, parent_symbol, file_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk.file_path, chunk.start_line, chunk.end_line, chunk.code_text,
                    chunk.symbol_name, chunk.symbol_type, chunk.parent_symbol, file_hash
                ))
                
                chunk_id = cursor.lastrowid
                
                # Insert vector
                # sqlite-vec expects packed bytes or a JSON array string
                cursor.execute("""
                    INSERT INTO vec_chunks(rowid, embedding)
                    VALUES (?, ?)
                """, (chunk_id, json.dumps(embedding)))
                
            conn.commit()

    def vector_search(self, query_embedding: List[float], top_k: int = 5, file_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Cosine similarity search using sqlite-vec.
        Returns ranked chunks.
        """
        with self._get_connection() as conn:
            # Serialize the query embedding
            query_json = json.dumps(query_embedding)
            
            # Base query joins vec_chunks with chunks
            sql = """
                SELECT 
                    c.file_path, c.start_line, c.end_line, c.code_text, 
                    c.symbol_name, c.symbol_type, c.parent_symbol,
                    v.distance
                FROM vec_chunks v
                JOIN chunks c ON c.id = v.rowid
                WHERE v.embedding MATCH ?
            """
            
            params = [query_json]
            if file_filter:
                sql += " AND c.file_path LIKE ?"
                params.append(f"%{file_filter}%")
                
            sql += f" ORDER BY v.distance LIMIT {top_k}"
            
            cursor = conn.execute(sql, params)
            results = []
            for row in cursor.fetchall():
                results.append({
                    "file_path": row[0],
                    "start_line": row[1],
                    "end_line": row[2],
                    "code_text": row[3],
                    "symbol_name": row[4],
                    "symbol_type": row[5],
                    "parent_symbol": row[6],
                    "distance": row[7],
                    "relevance_score": max(0.0, 1.0 - row[7]) # Simple conversion of distance to score
                })
            return results

    def find_usages(self, symbol_name: str) -> List[Dict[str, Any]]:
        """
        Exact text/AST reference matching.
        For now, does a naive text search in code_text for the symbol_name, 
        but excludes the definition chunk itself (where symbol_name matches exactly).
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    file_path, start_line, end_line, code_text, 
                    symbol_name, symbol_type, parent_symbol
                FROM chunks 
                WHERE code_text LIKE ? AND symbol_name != ?
            """, (f"%{symbol_name}%", symbol_name))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "file_path": row[0],
                    "start_line": row[1],
                    "end_line": row[2],
                    "code_text": row[3],
                    "symbol_name": row[4],
                    "symbol_type": row[5],
                    "parent_symbol": row[6],
                })
            return results

    def get_chunk_by_symbol(self, file_path: str, symbol_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific chunk by its defined symbol name and file."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    file_path, start_line, end_line, code_text, 
                    symbol_name, symbol_type, parent_symbol
                FROM chunks 
                WHERE file_path = ? AND symbol_name = ?
                LIMIT 1
            """, (file_path, symbol_name))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return {
                "file_path": row[0],
                "start_line": row[1],
                "end_line": row[2],
                "code_text": row[3],
                "symbol_name": row[4],
                "symbol_type": row[5],
                "parent_symbol": row[6],
            }

    def get_calls_to(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Return chunks that contain calls to the given symbol (similar to usages)."""
        return self.find_usages(symbol_name)
