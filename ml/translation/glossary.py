import re
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from backend.app.models.translation import GlossaryTerm

class GlossaryEngine:
    """
    Standardized multilingual terminology dictionary manager.
    Injects approved educational vocabulary into translation and generation pipelines.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._local_terms: Dict[str, Dict[str, str]] = {}  # {target_lang: {hindi_term: target_term}}

    def load_terms(self, terms: List[Dict[str, str]], target_lang: str = "sat"):
        if target_lang not in self._local_terms:
            self._local_terms[target_lang] = {}
        for item in terms:
            self._local_terms[target_lang][item["hindi_term"].strip()] = item["target_term"].strip()

    def find_matching_terms(self, text: str, target_lang: str = "sat") -> List[Dict[str, str]]:
        matches = []
        
        # 1. Search local memory dictionary
        if target_lang in self._local_terms:
            for h_term, t_term in self._local_terms[target_lang].items():
                if re.search(r"\b" + re.escape(h_term) + r"\b", text) or h_term in text:
                    matches.append({"hindi_term": h_term, "target_term": t_term})

        # 2. Search Database if available
        if self.db:
            terms = self.db.query(GlossaryTerm).filter_by(target_lang=target_lang).all()
            for t in terms:
                if t.hindi_term in text:
                    matches.append({
                        "hindi_term": t.hindi_term,
                        "target_term": t.target_term,
                        "domain": t.domain,
                        "pronunciation": t.pronunciation
                    })

        # Deduplicate
        seen = set()
        deduped = []
        for m in matches:
            if m["hindi_term"] not in seen:
                seen.add(m["hindi_term"])
                deduped.append(m)
        return deduped
