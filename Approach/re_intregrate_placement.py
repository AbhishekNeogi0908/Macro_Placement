import json
import os

# Path Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "adaptec1"))
RESULTS_DIR = os.path.join(BASE_DIR, "Results", "Phase1_Partitioning")

JSON_OPTIMIZED = os.path.join(RESULTS_DIR, "optimized_macros_final.json")
ORIGINAL_PL = os.path.join(BASE_DIR, "adaptec1.pl")
FINAL_PL = os.path.join(RESULTS_DIR, "final_full_placement.pl")

def generate_exact_pl():
    # 1. Load optimized coordinates into a flat lookup dictionary
    opt_lookup = {}
    with open(JSON_OPTIMIZED, 'r') as f:
        data = json.load(f) # Loading optimized macros
        for cluster, macros in data.items():
            for name, info in macros.items():
                opt_lookup[name] = (info['x'], info['y'])

    # 2. Reintegration Pass
    print(f"🔄 Generating optimized placement file...")
    count_updated = 0
    count_others = 0
    
    with open(ORIGINAL_PL, 'r') as f_in, open(FINAL_PL, 'w') as f_out:
        for line in f_in:
            # Preserve headers and comments
            if line.startswith(('#', 'UCLA')):
                f_out.write(line)
                continue
            
            parts = line.strip().split()
            if not parts: continue # Skip empty lines
            
            node_id = parts[0]
            
            # Logic: If ID is in our optimized lookup, it is an optimized Macro
            if node_id in opt_lookup:
                new_x, new_y = opt_lookup[node_id]
                # Write in the exact format required: name x y : N /FIXED
                f_out.write(f"{node_id} {new_x} {new_y} : N /FIXED\n")
                count_updated += 1
            else:
                # Logic: Standard Cell or other component
                # Preserve the original line structure
                f_out.write(line)
                count_others += 1
    
    total = count_updated + count_others
    print(f"✅ Final placement created successfully.")
    print(f"📊 Total nodes: {total} | Macros updated: {count_updated} | Standard Cells kept: {count_others}")
    print(f"📂 Saved to: {FINAL_PL}")

if __name__ == "__main__":
    generate_exact_pl()