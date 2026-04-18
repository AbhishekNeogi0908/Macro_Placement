import json
import os
import sys
import kahypar
import urllib.request

# ==========================================
# Path Configuration
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "adaptec1"))

# 1. Define the main Results directory
RESULTS_DIR = os.path.join(DATA_DIR, "Results")

# 2. Define the NEW specific subfolder for this approach
PHASE1_DIR = os.path.join(RESULTS_DIR, "Phase1_Partitioning")

# 3. Create the directories safely
os.makedirs(PHASE1_DIR, exist_ok=True)

NODES_FILE = os.path.join(DATA_DIR, "adaptec1.nodes")
PL_FILE    = os.path.join(DATA_DIR, "adaptec1.pl")
NETS_FILE  = os.path.join(DATA_DIR, "adaptec1.nets")

# 4. Route the output JSON to the new folder
JSON_OUT   = os.path.join(PHASE1_DIR, "clustered_macros.json")

def verify_files_exist():
    """Safety check to ensure all input files are found before running."""
    missing = [f for f in [NODES_FILE, PL_FILE, NETS_FILE] if not os.path.exists(f)]
    if missing:
        print("❌ ERROR: Could not find the following files:")
        for m in missing:
            print(f"   - {m}")
        sys.exit(1)
    print("✅ All Bookshelf files found successfully!")

def get_kahypar_config():
    """Ensures the KaHyPar configuration file exists, saving it to the new subfolder."""
    # Route the .ini file to the new Phase1 folder
    ini_path = os.path.join(PHASE1_DIR, "cut_kKaHyPar_sea20.ini")
    
    if not os.path.exists(ini_path):
        print("📥 Downloading official KaHyPar configuration file...")
        url = "https://raw.githubusercontent.com/kahypar/kahypar/master/config/cut_kKaHyPar_sea20.ini"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(ini_path, 'wb') as out_file:
                out_file.write(response.read())
            print("✅ Configuration downloaded successfully.")
        except Exception as e:
            print(f"❌ Failed to download configuration: {e}")
            print(f"\n⚠️ WORKAROUND: Please download this file manually:")
            print(url)
            print(f"And save it exactly here: {ini_path}")
            sys.exit(1)
            
    return ini_path

def parse_bookshelf(nodes_file, pl_file, nets_file, max_fanout=500):
    """Dynamically extracts and UN-FIXES macros from the ISPD 2005 benchmark."""
    macros = {}
    macro_names = []
    hyperedges = []
    
    print("Analyzing .nodes to prove standard cell height...")
    height_counts = {}
    all_raw_nodes = {}
    
    # ---------------------------------------------------------
    # PASS 1: Statistical Analysis of Node Heights
    # ---------------------------------------------------------
    with open(nodes_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and not line.startswith(('UCLA', 'Num', '#')):
                name, w, h = parts[0], int(parts[1]), int(parts[2])
                # Check if the dataset claims this block is locked
                is_fixed = (len(parts) > 3 and parts[3] == 'terminal')
                
                all_raw_nodes[name] = {"w": w, "h": h, "fixed": is_fixed, "x": 0, "y": 0}
                
                # We only count standard cells (not terminals) to find the standard row height
                if not is_fixed:
                    height_counts[h] = height_counts.get(h, 0) + 1

    # The most frequent movable height is mathematically the Standard Cell Height
    std_cell_height = max(height_counts, key=height_counts.get)
    macro_threshold = std_cell_height * 4
    
    print(f"✅ Discovered Standard Cell Height: {std_cell_height}")
    print(f"✅ Dynamic Macro Threshold set at : Height or Width > {macro_threshold}")

    # ---------------------------------------------------------
    # PASS 2: Segregation AND "Un-Fixing" for Gurobi
    # ---------------------------------------------------------
    for name, data in all_raw_nodes.items():
        w, h, originally_fixed = data['w'], data['h'], data['fixed']
        
        # THE FIX: If it is physically massive, it is a Macro. 
        # We MUST strip the 'terminal' tag and un-fix it so Gurobi can move it!
        if h > macro_threshold or w > macro_threshold:
            macros[name] = {"w": w, "h": h, "fixed": False, "x": 0, "y": 0}
            macro_names.append(name)
            
        # If it is small and fixed, it is an actual I/O Pad. Keep it fixed.
        elif originally_fixed:
            macros[name] = {"w": w, "h": h, "fixed": True, "x": 0, "y": 0}
            macro_names.append(name)

    print("Parsing .pl...")
    with open(pl_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and not line.startswith(('UCLA', '#')):
                name = parts[0]
                if name in macros:
                    macros[name]['x'] = int(parts[1])
                    macros[name]['y'] = int(parts[2])

    print("Parsing .nets...")
    with open(nets_file, 'r') as f:
        lines = f.readlines()
        
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('NetDegree'):
            degree = int(line.split(':')[1].strip().split()[0])
            if degree <= max_fanout:
                current_net = []
                for _ in range(degree):
                    i += 1
                    node_name = lines[i].strip().split()[0]
                    if node_name in macros:
                        current_net.append(node_name)
                
                unique_net = list(set(current_net))
                
                if len(unique_net) >= 2:
                    hyperedges.append(unique_net)
            else:
                i += degree
        i += 1

    return macros, macro_names, hyperedges

def partition_with_kahypar(macros, macro_names, hyperedges, k=40, epsilon=0.03):
    """Uses the KaHyPar Python library to partition the graph in memory."""
    print(f"\n🚀 Starting KaHyPar in-memory partitioning (Clusters = {k})...")
    
    name_to_id = {name: idx for idx, name in enumerate(macro_names)}
    num_nodes = len(macro_names)
    num_edges = len(hyperedges)
    
    edge_indices = [0]
    edges_flat = []
    
    for edge in hyperedges:
        for name in edge:
            edges_flat.append(name_to_id[name])
        edge_indices.append(len(edges_flat))
        
    node_weights = [1] * num_nodes
    edge_weights = [1] * num_edges
    
    hypergraph = kahypar.Hypergraph(
        num_nodes, num_edges, edge_indices, edges_flat, k, edge_weights, node_weights
    )
    
    context = kahypar.Context()
    
    ini_path = get_kahypar_config()
    context.loadINIconfiguration(ini_path)
        
    context.setK(k)
    context.setEpsilon(epsilon)
    context.suppressOutput(True)
    
    print("🧠 Partitioning engine running (this may take a few seconds)...")
    kahypar.partition(hypergraph, context)
    
    clusters = {str(i): {} for i in range(k)}
    
    for name in macro_names:
        node_id = name_to_id[name]
        block_id = hypergraph.blockID(node_id)
        clusters[str(block_id)][name] = macros[name]
        
    return clusters

# ==========================================
# Execution Flow
# ==========================================
if __name__ == "__main__":
    verify_files_exist()

    MACROS, MACRO_NAMES, HYPEREDGES = parse_bookshelf(
        NODES_FILE, PL_FILE, NETS_FILE,
        max_fanout=500
    )
    
    print(f"\n📊 Extraction Summary:")
    print(f"   - Found {len(MACROS)} Macros/Fixed Pads")
    print(f"   - Found {len(HYPEREDGES)} valid Macro-to-Macro nets")

    FINAL_CLUSTERS = partition_with_kahypar(MACROS, MACRO_NAMES, HYPEREDGES, k=40)
    
    with open(JSON_OUT, 'w') as f:
        json.dump(FINAL_CLUSTERS, f, indent=4)
        
    print(f"\n✅ Successfully grouped macros into {len(FINAL_CLUSTERS)} clusters.")
    print(f"Saved to: {JSON_OUT}\n")