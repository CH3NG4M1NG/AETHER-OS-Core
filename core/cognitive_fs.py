from __future__ import annotations

import re
from collections import defaultdict


class CognitiveFileSystemLayer:
    def __init__(self) -> None:
        self.metadata: dict[str, dict] = {}
        self.relations: dict[str, list[dict]] = defaultdict(list)

    def auto_tag(self, file_path: str, text: str = "") -> list[str]:
        low = f"{file_path} {text}".lower()
        mapping = {"frontend": ["react", "vue", "css", "ui"], "backend": ["api", "server", "auth", "jwt"], "ml": ["model", "tensor", "embedding"], "docs": ["readme", "docs", "md"]}
        tags = [tag for tag, keys in mapping.items() if any(k in low for k in keys)]
        return tags or ["general"]

    def index_file(self, file_path: str, content: str = "", project: str | None = None) -> dict:
        rec = {"path": file_path, "project": project, "tags": self.auto_tag(file_path, content)}
        self.metadata[file_path] = rec
        if project:
            self.relations[project].append({"file": file_path, "kind": "belongs_to"})
        return rec

    def semantic_search(self, query: str) -> list[dict]:
        toks = re.findall(r"[a-z0-9_]+", query.lower())
        scored = []
        for rec in self.metadata.values():
            hay = f"{rec['path']} {' '.join(rec['tags'])} {rec.get('project','')}".lower()
            score = sum(1 for t in toks if t in hay)
            if score > 0:
                scored.append((score, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:20]]
