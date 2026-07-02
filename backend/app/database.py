import os
import json
import logging
from pymongo import MongoClient
import mongomock
from app.config import settings

logger = logging.getLogger("hiregenie.database")
logging.basicConfig(level=logging.INFO)

class JSONPersistedMockCollection:
    """A mock MongoDB collection that persists to a JSON file for local dev without MongoDB"""
    def __init__(self, db_dir, name):
        self.db_dir = db_dir
        self.name = name
        self.file_path = os.path.join(db_dir, f"{name}.json")
        self._ensure_file()
        
    def _ensure_file(self):
        os.makedirs(self.db_dir, exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)
                
    def _read(self):
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except Exception:
            return []
            
    def _write(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def find(self, query=None):
        query = query or {}
        docs = self._read()
        if not query:
            return docs
        
        # Simple match engine
        results = []
        for doc in docs:
            match = True
            for k, v in query.items():
                # Support simple equality
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(doc)
        return results

    def find_one(self, query=None):
        query = query or {}
        results = self.find(query)
        return results[0] if results else None

    def insert_one(self, document):
        docs = self._read()
        if "_id" not in document:
            document["_id"] = str(len(docs) + 1)
        docs.append(document)
        self._write(docs)
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertResult(document["_id"])

    def update_one(self, query, update, upsert=False):
        docs = self._read()
        query = query or {}
        target_idx = -1
        
        for idx, doc in enumerate(docs):
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                target_idx = idx
                break
                
        # Handle update operations ($set)
        set_data = update.get("$set", {}) if isinstance(update, dict) else update
        
        if target_idx != -1:
            for k, v in set_data.items():
                docs[target_idx][k] = v
            self._write(docs)
        elif upsert:
            new_doc = query.copy()
            for k, v in set_data.items():
                new_doc[k] = v
            self.insert_one(new_doc)
            
        class UpdateResult:
            def __init__(self, matched_count, modified_count):
                self.matched_count = matched_count
                self.modified_count = modified_count
        return UpdateResult(1 if target_idx != -1 else 0, 1 if target_idx != -1 else 0)

    def delete_one(self, query):
        docs = self._read()
        query = query or {}
        target_idx = -1
        
        for idx, doc in enumerate(docs):
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                target_idx = idx
                break
                
        if target_idx != -1:
            docs.pop(target_idx)
            self._write(docs)
            
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        return DeleteResult(1 if target_idx != -1 else 0)

    def count_documents(self, query=None):
        return len(self.find(query))

class JSONPersistedMockDatabase:
    def __init__(self, db_dir):
        self.db_dir = db_dir
        self.collections = {}
        
    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = JSONPersistedMockCollection(self.db_dir, name)
        return self.collections[name]

from bson import ObjectId

def parse_id_query(query):
    if not isinstance(query, dict):
        if isinstance(query, str):
            val = query
            if ObjectId.is_valid(val):
                return {"_id": {"$in": [val, ObjectId(val)]}}
            else:
                return {"_id": val}
        return query
        
    query = query.copy()
    if "_id" in query:
        val = query["_id"]
        if isinstance(val, str):
            if ObjectId.is_valid(val):
                query["_id"] = {"$in": [val, ObjectId(val)]}
    return query

class MongoCollectionWrapper:
    def __init__(self, real_coll):
        self.real_coll = real_coll
        
    def __getattr__(self, name):
        return getattr(self.real_coll, name)
        
    def find(self, query=None, *args, **kwargs):
        query = parse_id_query(query or {})
        return self.real_coll.find(query, *args, **kwargs)
        
    def find_one(self, query=None, *args, **kwargs):
        query = parse_id_query(query or {})
        return self.real_coll.find_one(query, *args, **kwargs)
        
    def update_one(self, query, update, *args, **kwargs):
        query = parse_id_query(query or {})
        return self.real_coll.update_one(query, update, *args, **kwargs)
        
    def delete_one(self, query, *args, **kwargs):
        query = parse_id_query(query or {})
        return self.real_coll.delete_one(query, *args, **kwargs)
        
    def count_documents(self, query=None, *args, **kwargs):
        query = parse_id_query(query or {})
        return self.real_coll.count_documents(query, *args, **kwargs)

class MongoDatabaseWrapper:
    def __init__(self, real_db):
        self.real_db = real_db
        
    def __getitem__(self, name):
        return MongoCollectionWrapper(self.real_db[name])
        
    def __getattr__(self, name):
        return getattr(self.real_db, name)

# Initialize MongoDB Client or Local Fallback
db = None
is_mock = False

if settings.MONGODB_URI:
    try:
        logger.info("Attempting to connect to MongoDB...")
        client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
        # Verify connection
        client.admin.command('ping')
        raw_db = client[settings.DATABASE_NAME]
        db = MongoDatabaseWrapper(raw_db)
        logger.info("Successfully connected to MongoDB and initialized query wrapper!")
    except Exception as e:
        logger.warning(f"Failed to connect to MongoDB: {e}. Falling back to file-based database storage.")
        is_mock = True
else:
    logger.info("No MONGODB_URI provided. Using file-based database storage.")
    is_mock = True

if is_mock:
    fallback_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db_fallback")
    db = JSONPersistedMockDatabase(fallback_dir)
    logger.info(f"Initialized local JSON database at {fallback_dir}")

def get_db():
    return db
