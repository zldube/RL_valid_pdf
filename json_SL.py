import json
import os
import sys

def save_json(data, filename):
    #Save data as JSON file.
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON saved to {filename}", file=sys.stderr)

def load_json(filename):
    #Load JSON if it exists, otherwise return None.

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
