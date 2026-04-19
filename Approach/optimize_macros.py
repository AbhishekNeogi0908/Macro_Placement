import json
import os
import gurobipy as gp
from gurobipy import GRB

# ==========================================
# Path Configuration
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "adaptec1", "Results"))
JSON_IN = os.path.join(RESULTS_DIR, "clustered_macros.json")
JSON_OUT = os.path.join(RESULTS_DIR, "optimized_macros.json")

def optimize_cluster(cluster_id, macros_dict):
    """
    Uses Gurobi to pack a cluster of macros tightly without overlapping.
    """
    print(f"\n🚀 Launching Gurobi for Cluster {cluster_id} ({len(macros_dict)} macros)...")
    
    # Create an empty model
    m = gp.Model(f"Cluster_{cluster_id}")
    
    # Suppress heavy Gurobi console logging
    m.setParam('OutputFlag', 1)
    # Set a time limit in case the math gets stuck (60 seconds max per cluster)
    m.setParam('TimeLimit', 60)

    # 1. Variables: X and Y coordinates for each macro
    x = {}
    y = {}
    for name in macros_dict.keys():
        # Coordinates must be positive
        x[name] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{name}")
        y[name] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"y_{name}")

    # Variables for the total Bounding Box of the cluster
    max_w = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="max_w")
    max_h = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="max_h")

    # 2. Bounding Box Constraints
    # The bounding box must encapsulate the top-right corner of every macro
    for name, data in macros_dict.items():
        m.addConstr(x[name] + data['w'] <= max_w, name=f"bound_w_{name}")
        m.addConstr(y[name] + data['h'] <= max_h, name=f"bound_h_{name}")

    # 3. Non-Overlap Constraints (The Big-M formulation)
    # Calculate a safe 'Big M' (Sum of all widths/heights is guaranteed to be larger than any distance)
    BigM_X = sum(data['w'] for data in macros_dict.values())
    BigM_Y = sum(data['h'] for data in macros_dict.values())

    macro_names = list(macros_dict.keys())
    
    # Loop through every unique pair of macros
    for i in range(len(macro_names)):
        for j in range(i + 1, len(macro_names)):
            name1 = macro_names[i]
            name2 = macro_names[j]
            w1, h1 = macros_dict[name1]['w'], macros_dict[name1]['h']
            w2, h2 = macros_dict[name2]['w'], macros_dict[name2]['h']

            # Binary variables for spatial relationship
            b_left  = m.addVar(vtype=GRB.BINARY, name=f"left_{name1}_{name2}")
            b_right = m.addVar(vtype=GRB.BINARY, name=f"right_{name1}_{name2}")
            b_below = m.addVar(vtype=GRB.BINARY, name=f"below_{name1}_{name2}")
            b_above = m.addVar(vtype=GRB.BINARY, name=f"above_{name1}_{name2}")

            # At least one spatial relationship MUST be true (they cannot overlap)
            m.addConstr(b_left + b_right + b_below + b_above >= 1, name=f"no_overlap_{name1}_{name2}")

            # The actual spatial constraints activated by the binary variables
            m.addConstr(x[name1] + w1 <= x[name2] + BigM_X * (1 - b_left))
            m.addConstr(x[name2] + w2 <= x[name1] + BigM_X * (1 - b_right))
            m.addConstr(y[name1] + h1 <= y[name2] + BigM_Y * (1 - b_below))
            m.addConstr(y[name2] + h2 <= y[name1] + BigM_Y * (1 - b_above))

    # 4. Objective: Minimize the bounding box (Perimeter proxy for Area)
    # Packing them into the smallest possible square footprint
    m.setObjective(max_w + max_h, GRB.MINIMIZE)

    # 5. Optimize!
    m.optimize()

    # 6. Extract Results
    if m.status == GRB.OPTIMAL or m.status == GRB.TIME_LIMIT:
        print(f"✅ Solved! Bounding Box Size: {max_w.X} x {max_h.X}")
        # Update our dictionary with the new optimal coordinates
        for name in macros_dict.keys():
            macros_dict[name]['x'] = round(x[name].X)
            macros_dict[name]['y'] = round(y[name].X)
        return macros_dict
    else:
        print(f"❌ Optimization failed for Cluster {cluster_id}. Status: {m.status}")
        return macros_dict

# ==========================================
# Execution Flow
# ==========================================
if __name__ == "__main__":
    if not os.path.exists(JSON_IN):
        print(f"❌ ERROR: Cannot find {JSON_IN}")
        exit()

    with open(JSON_IN, 'r') as f:
        clusters = json.load(f)

    # Dictionary to hold the new coordinates
    optimized_clusters = {}

    # -------------------------------------------------------------
    # TEST MODE: We are only running Cluster "0" to test the math
    # -------------------------------------------------------------
    test_cluster = "0"
    if test_cluster in clusters:
        optimized_clusters[test_cluster] = optimize_cluster(test_cluster, clusters[test_cluster])
    
    # Save the output
    with open(JSON_OUT, 'w') as f:
        json.dump(optimized_clusters, f, indent=4)
        
    print(f"\n💾 Saved optimized coordinates to: {JSON_OUT}")