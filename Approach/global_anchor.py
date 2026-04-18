import json
import os
import argparse
import numpy as np

# Path Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "adaptec1"))
RESULTS_DIR = os.path.join(DATA_DIR, "Results", "Phase1_Partitioning")
CLUSTERS_FILE = os.path.join(RESULTS_DIR, "clustered_macros.json")
PL_FILE = os.path.join(DATA_DIR, "adaptec1.pl")
ANCHORS_FILE = os.path.join(RESULTS_DIR, "cluster_anchors.json")

def load_pl_data(pl_file):
    """Parses the .pl file into a dictionary of {name: (x, y)}."""
    pl_data = {}
    with open(pl_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and not line.startswith(('UCLA', '#')):
                pl_data[parts[0]] = (int(parts[1]), int(parts[2]))
    return pl_data

def get_centroids(clusters, pl_data):
    """Calculates the center of gravity for each cluster."""
    anchors = {}
    for c_id, macros in clusters.items():
        x_coords = []
        y_coords = []
        for name in macros:
            if name in pl_data:
                x_coords.append(pl_data[name][0])
                y_coords.append(pl_data[name][1])
        
        if x_coords:
            anchors[c_id] = {
                "x": int(np.mean(x_coords)),
                "y": int(np.mean(y_coords))
            }
    return anchors

def run_simulated_annealing(clusters, pl_data):
    """Placeholder for your Phase 3 SA research implementation."""
    print("🧠 [SA Mode] Initializing Simulated Annealing engine...")
    # TODO: Implement your cost function (HPWL + Overlap)
    # TODO: Implement cooling schedule (move clusters, accept/reject)
    print("⚠️ Simulated Annealing is currently a stub. Implementing logic...")
    return get_centroids(clusters, pl_data) # Defaulting to centroids until SA is coded

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 3: Global Anchor Placement")
    parser.add_argument("--mode", choices=['centroid', 'sa'], required=True, help="Mode for anchor calculation")
    args = parser.parse_args()

    # Load inputs
    with open(CLUSTERS_FILE, 'r') as f:
        clusters = json.load(f)
    pl_data = load_pl_data(PL_FILE)

    # Execution
    if args.mode == 'centroid':
        print("📍 Mode: Centroid Calculation")
        anchors = get_centroids(clusters, pl_data)
    else:
        print("🔥 Mode: Simulated Annealing")
        anchors = run_simulated_annealing(clusters, pl_data)

    # Save output
    with open(ANCHORS_FILE, 'w') as f:
        json.dump(anchors, f, indent=4)
        
    print(f"✅ Success! Anchors saved to: {ANCHORS_FILE}")