import json
import os
import sys
import argparse
import subprocess
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Process list.json in smaller batches')
    parser.add_argument('--batch-size', type=int, default=5, help='Number of entries to process in each batch')
    parser.add_argument('--input', type=str, default='list.json', help='Input JSON file')
    parser.add_argument('--output', type=str, default='research_results.json', help='Output JSON file')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers for each batch')
    
    args = parser.parse_args()
    
    # Load the input file to get the total number of entries
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_entries = len(data)
    print(f"Total entries in {args.input}: {total_entries}")
    
    # Calculate the number of batches
    batch_size = args.batch_size
    num_batches = (total_entries + batch_size - 1) // batch_size  # Ceiling division
    
    # Check if output file exists and load existing results
    processed_entries = 0
    if os.path.exists(args.output):
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                results = json.load(f)
            processed_entries = len(results)
            print(f"Found {processed_entries} already processed entries in {args.output}")
        except Exception as e:
            print(f"Error loading existing results: {str(e)}")
    
    # Calculate the starting batch
    start_batch = processed_entries // batch_size
    start_index = start_batch * batch_size
    
    print(f"Will process entries in {num_batches - start_batch} batches of {batch_size} entries each")
    print(f"Starting from batch {start_batch + 1} (entries {start_index}-{min(start_index + batch_size - 1, total_entries - 1)})")
    
    # Process each batch
    for batch in range(start_batch, num_batches):
        start_idx = batch * batch_size
        end_idx = min(start_idx + batch_size, total_entries)
        
        print(f"\n{'=' * 80}")
        print(f"Processing batch {batch + 1}/{num_batches} (entries {start_idx}-{end_idx - 1})")
        print(f"{'=' * 80}")
        
        # Run the batch_research.py script for this batch
        cmd = [
            "python", "batch_research.py",
            "--input", args.input,
            "--output", args.output,
            "--workers", str(args.workers),
            "--start", str(start_idx),
            "--end", str(end_idx)
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        start_time = datetime.now()
        
        try:
            # Run the command and capture output
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Print output in real-time
            for line in process.stdout:
                print(line, end='')
            
            # Wait for the process to complete
            process.wait()
            
            if process.returncode != 0:
                print(f"Batch {batch + 1} failed with return code {process.returncode}")
            else:
                print(f"Batch {batch + 1} completed successfully")
        except Exception as e:
            print(f"Error processing batch {batch + 1}: {str(e)}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"Batch {batch + 1} took {duration}")
    
    print("\nAll batches completed!")
    
    # Print summary
    if os.path.exists(args.output):
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                final_results = json.load(f)
            print(f"Final results: {len(final_results)} entries processed")
        except Exception as e:
            print(f"Error loading final results: {str(e)}")

if __name__ == "__main__":
    main()