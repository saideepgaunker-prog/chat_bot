import os
import glob
from typing import List, Dict, Any, Optional
from app.rag.hybrid_search import HybridSearchEngine
from app.core.logger import logger

class DocumentStore:
    def __init__(self, docs_dir: str = "app/data/platform_docs"):
        self.docs_dir = docs_dir
        self.chunks: List[Dict[str, Any]] = []
        self.search_engine = HybridSearchEngine()
        self.load_and_index()

    def load_and_index(self):
        if not os.path.exists(self.docs_dir):
            logger.warning(f"Docs directory not found: {self.docs_dir}")
            return
        
        md_files = glob.glob(os.path.join(self.docs_dir, "*.md"))
        chunks = []
        
        for file_path in md_files:
            filename = os.path.basename(file_path)
            doc_id = os.path.splitext(filename)[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Split markdown into sections by # or ##
                sections = content.split("\n## ")
                main_title = sections[0].split("\n")[0].replace("# ", "").strip()
                
                # First section
                chunks.append({
                    "id": f"{doc_id}_intro",
                    "doc_id": doc_id,
                    "title": main_title,
                    "text": sections[0].strip(),
                    "file": filename
                })

                # Subsequent sections
                for idx, sec in enumerate(sections[1:], 1):
                    lines = sec.split("\n")
                    sec_title = lines[0].strip()
                    sec_body = "\n".join(lines[1:]).strip()
                    chunks.append({
                        "id": f"{doc_id}_sec_{idx}",
                        "doc_id": doc_id,
                        "title": f"{main_title} > {sec_title}",
                        "text": f"{main_title} - {sec_title}\n{sec_body}",
                        "file": filename
                    })
            except Exception as e:
                logger.error(f"Error reading doc {file_path}: {e}")

        self.chunks = chunks
        self.search_engine.index(chunks, text_field="text")
        logger.info(f"Loaded and indexed {len(self.chunks)} markdown chunks in DocumentStore.")

    def search_docs(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.search_engine.search(query, top_k=top_k)

document_store = DocumentStore()
