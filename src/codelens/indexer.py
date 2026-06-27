import os
import hashlib
import click
from rich.console import Console

from codelens.chunker import Chunker
from codelens.embeddings import EmbeddingService
from codelens.store import Store

console = Console()

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_ignored(filepath: str) -> bool:
    ignored_dirs = {'node_modules', '.git', 'venv', 'dist', 'build', '__pycache__', '.pytest_cache'}
    parts = filepath.split(os.sep)
    return any(part in ignored_dirs for part in parts)

@click.group()
def cli():
    """CodeLens MCP CLI"""
    pass

@cli.command()
@click.argument('repo_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def index(repo_path: str):
    """Index a repository for semantic search."""
    console.print(f"[bold green]Indexing repository at {repo_path}...[/bold green]")
    
    store = Store()
    chunker = Chunker()
    try:
        embedding_service = EmbeddingService()
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        return
        
    existing_hashes = store.get_file_hashes()
    
    files_to_process = []
    
    # Walk the directory
    for root, _, files in os.walk(repo_path):
        if is_ignored(root):
            continue
            
        for file in files:
            # Basic check for supported extensions
            if not any(file.endswith(ext) for ext in [".py", ".js", ".ts", ".jsx", ".tsx"]):
                continue
                
            filepath = os.path.join(root, file)
            if is_ignored(filepath):
                continue
                
            files_to_process.append(filepath)
            
    processed_count = 0
    skipped_count = 0
    
    for filepath in files_to_process:
        try:
            current_hash = get_file_hash(filepath)
        except Exception:
            console.print(f"[yellow]Could not read file {filepath}, skipping.[/yellow]")
            continue
            
        rel_path = os.path.relpath(filepath, repo_path)
        
        if rel_path in existing_hashes and existing_hashes[rel_path] == current_hash:
            skipped_count += 1
            continue
            
        # File has changed or is new, delete old chunks if they exist
        if rel_path in existing_hashes:
            store.delete_file_chunks(rel_path)
            
        chunks = chunker.chunk_file(filepath)
        if not chunks:
            continue
            
        # We need to update chunks with relative paths for portability
        for chunk in chunks:
            chunk.file_path = rel_path
            
        texts_to_embed = [c.code_text for c in chunks]
        try:
            embeddings = embedding_service.embed_chunks(texts_to_embed)
            store.insert_chunks(chunks, embeddings, current_hash)
            processed_count += 1
            console.print(f"Indexed {rel_path} ({len(chunks)} chunks)")
        except Exception as e:
            console.print(f"[red]Error embedding chunks for {rel_path}: {e}[/red]")
            
    console.print(f"[bold green]Indexing complete! processed={processed_count}, skipped_unchanged={skipped_count}[/bold green]")

if __name__ == "__main__":
    cli()
