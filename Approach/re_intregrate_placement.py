import json
import os

# Path Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "adaptec1"))
RESULTS_DIR = os.path.join(BASE_DIR, "Results")

JSON_OPTIMIZED = os.path.join(RESULTS_DIR, "optimized_macros.json")
ORIGINAL_PL = os.path.join(BASE_DIR, "adaptec1.pl")
FINAL_PL = os.path.join(RESULTS_DIR, "Merged_optimized.pl")

def generate_exact_pl():
    # 1. Identify which nodes are ACTUALLY fixed by looking at the baseline
    fixed_nodes = set()
    with open(ORIGINAL_PL, 'r') as f:
        for line in f:
            if "/FIXED" in line:
                node_id = line.split()[0]
                fixed_nodes.add(node_id)
    print(f"✅ Found {len(fixed_nodes)} truly fixed nodes in baseline.")

    # 2. Load optimized coordinates
    opt_lookup = {}
    with open(JSON_OPTIMIZED, 'r') as f:
        data = json.load(f)
        for cluster, macros in data.items():
            for name, info in macros.items():
                opt_lookup[name] = (info['x'], info['y'])

    # 3. Generate the new placement file
    print(f"🔄 Generating optimized placement file...")
    with open(ORIGINAL_PL, 'r') as f_in, open(FINAL_PL, 'w') as f_out:
        for line in f_in:
            if line.startswith(('#', 'UCLA')):
                f_out.write(line)
                continue
            
            parts = line.strip().split()
            if not parts: continue
            
            node_id = parts[0]
            
            if node_id in opt_lookup:
                new_x, new_y = opt_lookup[node_id]
                
                # CONSISTENCY CHECK:
                # Use our self-generated 'fixed_nodes' set instead of the converter
                if node_id in fixed_nodes:
                    f_out.write(f"{node_id} {new_x} {new_y} : N /FIXED\n")
                    #count_updated+=1
                else:
                    # If it wasn't fixed before, don't fix it now.
                    # This prevents parser crashes for standard cells!
                    f_out.write(f"{node_id} {new_x} {new_y} : N\n")
                    #count_others+=1
            else:
                # Keep original line for non-optimized nodes
                f_out.write(line)

    
    #total = count_updated + count_others
    print(f"✅ Final placement created successfully.")
    #print(f"📊 Total nodes: {total} | Macros updated: {count_updated} | Standard Cells kept: {count_others}")
    print(f"📂 Saved to: {FINAL_PL}")

if __name__ == "__main__":
    generate_exact_pl()