import os
import shutil

def reset_demo_data():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(project_root, "backend", "db_fallback")
    vector_dir = os.path.join(project_root, "backend", "vector_data")
    uploads_dir = os.path.join(project_root, "backend", "uploads")
    
    print("="*50)
    print("        HIREGENIE AI - DEMO DATA RESETTER        ")
    print("="*50)
    
    # 1. Clear database JSON files (keeping users and jobs)
    files_to_remove = ["candidates.json", "interviews.json", "emails.json", "activity_logs.json"]
    for file in files_to_remove:
        filepath = os.path.join(db_dir, file)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Cleared database collection: {file}")
            except Exception as e:
                print(f"Could not clear {file}: {e}")
                
    # 2. Reset FAISS candidate vector store (keeping policy)
    candidate_index = os.path.join(vector_dir, "candidates.index")
    candidate_meta = os.path.join(vector_dir, "candidates_meta.pkl")
    for file in [candidate_index, candidate_meta]:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Cleared vector file: {os.path.basename(file)}")
            except Exception as e:
                print(f"Could not clear vector file: {e}")
                
    # 3. Clean uploaded PDF files
    if os.path.exists(uploads_dir):
        for filename in os.listdir(uploads_dir):
            filepath = os.path.join(uploads_dir, filename)
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                print(f"Removed uploaded resume file: {filename}")
            except Exception as e:
                print(f"Could not remove upload {filename}: {e}")

    print("="*50)
    print("Success! Demo reset completed. Refresh your browser to start fresh.")
    print("="*50)

if __name__ == "__main__":
    reset_demo_data()
