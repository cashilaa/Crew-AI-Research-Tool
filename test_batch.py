import json
import os
import sys
from batch_research import process_json_list

def main():
    # Test with a small subset of the data
    input_file = 'list.json'
    output_file = 'test_results.json'
    
    # Process only the first 3 entries
    results = process_json_list(input_file, output_file, max_workers=1, start_index=0, end_index=3)
    
    print(f"Test completed. Results saved to {output_file}")
    
    # Print the results
    print("\nResults:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()