import os
import sys
import glob

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_client import LLMClient

def main():
    # 1. Initialize LLM Client
    try:
        client = LLMClient()
    except ValueError as e:
        print(f"Error: {e}")
        print("Tip: Copy .env.example to .env and fill in your API Key.")
        return

    # 2. Find input files
    input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    
    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))
    
    if not txt_files:
        print(f"No .txt files found in {input_dir}. Please add a book text file.")
        # Create a dummy file for testing if user agrees? No, just prompt user.
        return

    print(f"Found {len(txt_files)} files to process.")

    # 3. Process each file
    for file_path in txt_files:
        file_name = os.path.basename(file_path)
        print(f"Processing: {file_name}...")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Truncate content if too long for MVP (e.g., first 10k chars)
        # In a real app, we would use RAG or summary first.
        if len(content) > 10000:
            print("Content too long, using first 10000 characters for MVP analysis...")
            content = content[:10000]

        script = client.generate_script(content)
        
        if script:
            output_path = os.path.join(output_dir, f"script_{file_name}")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(script)
            print(f"Script generated and saved to: {output_path}")
        else:
            print(f"Failed to generate script for {file_name}")

if __name__ == "__main__":
    main()
