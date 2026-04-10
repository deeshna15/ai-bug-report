import sys

def process_batch(file_path: str):
    """Processes a batch of user records."""
    print(f"Starting batch processing for {file_path}...")
    valid_records = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for index, line in enumerate(lines):
        line = line.strip()
        # BUG: We don't check if the line is empty before indexing
        # If line is empty, line.split(",") returns [""] and indexing [1] throws IndexError
        parts = line.split(",")
        
        user_id = parts[0]
        email = parts[1]
        
        print(f"Processed User {user_id}: {email}")
        valid_records += 1

    print(f"Batch processing completed. Processed {valid_records} records.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_processor.py <file_path>")
        sys.exit(1)
    
    process_batch(sys.argv[1])
