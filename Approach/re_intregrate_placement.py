import json
import os

# Path Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "adaptec1"))
RESULTS_DIR = os.path.join(BASE_DIR, "Results")

JSON_OPTIMIZED = os.path.join(RESULTS_DIR, "optimized_macros.json")
ORIGINAL_PL = os.path.join(BASE_DIR, "adaptec1.pl")
FINAL_PL = os.path.join(RESULTS_DIR, "final_full_placement.pl")

def generate_exact_pl():
    # 1. Identify which nodes were truly FIXED in the baseline
    # These are our target macros.
    fixed_nodes = set()
    with open(ORIGINAL_PL, 'r') as f:
        for line in f:
            if "/FIXED" in line:
                node_id = line.split()[0]
                fixed_nodes.add(node_id)
    print(f"✅ Found {len(fixed_nodes)} truly fixed macros in baseline.")

    # 2. Load optimized coordinates
    opt_lookup = {}
    with open(JSON_OPTIMIZED, 'r') as f:
        data = json.load(f)
        for cluster, macros in data.items():
            for name, info in macros.items():
                opt_lookup[name] = (info['x'], info['y'])

    # 3. Generate the new placement file
    print(f"🔄 Generating optimized placement file...")
    count_updated = 0
    count_skipped = 0

    with open(ORIGINAL_PL, 'r') as f_in, open(FINAL_PL, 'w') as f_out:
        for line in f_in:
            if line.startswith(('#', 'UCLA')):
                f_out.write(line)
                continue
            
            parts = line.strip().split()
            if not parts: continue
            
            node_id = parts[0]
            
            # THE FIX: Only update if it is in opt_lookup AND was originally FIXED
            if node_id in opt_lookup and node_id in fixed_nodes:
                new_x, new_y = opt_lookup[node_id]
                f_out.write(f"{node_id} {new_x} {new_y} : N /FIXED\n")
                count_updated += 1
            else:
                # Otherwise, write the line exactly as it was in the original PL
                f_out.write(line)
                count_skipped += 1

    print(f"✅ Final placement created successfully.")
    print(f"📊 Macros updated: {count_updated} | Standard Cells/Fixed Nodes kept: {count_skipped}")
    print(f"📂 Saved to: {FINAL_PL}")

if __name__ == "__main__":
    generate_exact_pl()