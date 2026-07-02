import os
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.database import get_db

VECTOR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vector_data")
os.makedirs(VECTOR_DIR, exist_ok=True)

class VectorStoreManager:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        # Lazy initialization of sentence-transformers model
        self._model = None
        self.candidate_index_path = os.path.join(VECTOR_DIR, "candidates.index")
        self.candidate_metadata_path = os.path.join(VECTOR_DIR, "candidates_meta.pkl")
        self.policy_index_path = os.path.join(VECTOR_DIR, "policy.index")
        self.policy_metadata_path = os.path.join(VECTOR_DIR, "policy_meta.pkl")
        
        # Populate initial mock company policy if not existing
        self._ensure_mock_policy()
        
    @property
    def model(self):
        if self._model is None:
            print("Loading SentenceTransformer model...")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _ensure_mock_policy(self):
        policy_file = os.path.join(VECTOR_DIR, "company_policy.txt")
        if not os.path.exists(policy_file):
            policies = [
                "Equal Opportunity Hiring: HireGenie AI is committed to providing equal employment opportunities to all applicants.",
                "Interview Reimbursement: Candidates travelling more than 50 miles for onsite interviews are eligible for up to $200 travel reimbursement.",
                "Background Checks: All employment offers are contingent on a successful criminal background check and education verification.",
                "Referral Bonus: Employees who refer candidates that are hired and stay for 6 months receive a $1000 referral bonus.",
                "Probation Period: New hires undergo a 90-day introductory performance review period.",
                "Work Authorization: Candidates must be legally authorized to work in the country of application without sponsorship requirements, unless specified."
            ]
            with open(policy_file, "w") as f:
                f.write("\n".join(policies))
            
            # Embed policies
            embeddings = self.model.encode(policies)
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings).astype('float32'))
            
            # Save policy index
            faiss.write_index(index, self.policy_index_path)
            with open(self.policy_metadata_path, "wb") as f:
                pickle.dump(policies, f)

    def add_candidate(self, candidate_id: str, text: str):
        """Adds a candidate's text resume to the FAISS index."""
        # 1. Generate Embedding
        emb = self.model.encode([text])[0]
        
        # 2. Load existing index or create new one
        index = None
        metadata = []
        
        if os.path.exists(self.candidate_index_path) and os.path.exists(self.candidate_metadata_path):
            try:
                index = faiss.read_index(self.candidate_index_path)
                with open(self.candidate_metadata_path, "rb") as f:
                    metadata = pickle.load(f)
            except Exception as e:
                print(f"Error loading FAISS index: {e}, creating fresh index.")
                
        if index is None:
            dimension = len(emb)
            index = faiss.IndexFlatL2(dimension)
            
        # Check if candidate_id is already indexed, if so replace or ignore
        if candidate_id in metadata:
            idx_pos = metadata.index(candidate_id)
            # Rebuilding FAISS is cleaner for deletion/replacement since IndexFlatL2 doesn't support easy update
            # We will just append for now or do a rebuild
            metadata.append(candidate_id)
            index.add(np.array([emb]).astype('float32'))
        else:
            metadata.append(candidate_id)
            index.add(np.array([emb]).astype('float32'))
            
        # Save
        faiss.write_index(index, self.candidate_index_path)
        with open(self.candidate_metadata_path, "wb") as f:
            pickle.dump(metadata, f)
            
        print(f"Indexed candidate {candidate_id} in FAISS vector store.")

    def search_candidates(self, query: str, top_k: int = 5) -> list:
        """Searches the candidate FAISS index for candidates matching query."""
        if not os.path.exists(self.candidate_index_path) or not os.path.exists(self.candidate_metadata_path):
            return []
            
        try:
            index = faiss.read_index(self.candidate_index_path)
            with open(self.candidate_metadata_path, "rb") as f:
                metadata = pickle.load(f)
                
            q_emb = self.model.encode([query])
            distances, indices = index.search(np.array(q_emb).astype('float32'), top_k)
            
            results = []
            db = get_db()
            candidates_coll = db["candidates"]
            
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(metadata) and idx >= 0:
                    cand_id = metadata[idx]
                    cand = candidates_coll.find_one({"_id": cand_id})
                    if cand:
                        results.append({
                            "candidate": cand,
                            "distance": float(dist)
                        })
            return results
        except Exception as e:
            print(f"Error searching candidates: {e}")
            return []

    def search_company_policy(self, query: str, top_k: int = 2) -> list:
        """RAG tool: searches company policies based on search query."""
        if not os.path.exists(self.policy_index_path) or not os.path.exists(self.policy_metadata_path):
            return ["No policies available."]
            
        try:
            index = faiss.read_index(self.policy_index_path)
            with open(self.policy_metadata_path, "rb") as f:
                policies = pickle.load(f)
                
            q_emb = self.model.encode([query])
            distances, indices = index.search(np.array(q_emb).astype('float32'), top_k)
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(policies) and idx >= 0:
                    results.append(policies[idx])
            return results
        except Exception as e:
            print(f"Error searching policy: {e}")
            return ["Error retrieving policy data."]

# Singleton Instance
vector_store = VectorStoreManager()
