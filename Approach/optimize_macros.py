import json
import os
import gurobipy as gp
from gurobipy import GRB

# ==========================================
# Path Configuration - CHECK THESE!
# Ensure these match where your JSON files actually reside
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: If your files are in Phase1_Partitioning, make sure this path reflects that!
RESULTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "adaptec1", "Results", "Phase1_Partitioning"))

JSON_IN = os.path.join(RESULTS_DIR, "clustered_macros.json")
JSON_OUT = os.path.join(RESULTS_DIR, "optimized_macros.json")
JSON_ANCHORS = os.path.join(RESULTS_DIR, "cluster_anchors.json")

# Define how much 'leash' we give Gurobi (in microns/units)
TETHER_BUFFER = 2000

# 1. FIXED: Added 'anchor' as the third argument here
def optimize_cluster(cluster_id, macros_dict, anchor):
    print(f"\n🚀 Launching Gurobi for Cluster {cluster_id} tethered at ({anchor['x']}, {anchor['y']})")
    
    m = gp.Model(f"Cluster_{cluster_id}")
    m.setParam('OutputFlag', 1)
    m.setParam('TimeLimit', 60)

    # 1. Variables: X and Y coordinates
    x = {}
    y = {}
    for name in macros_dict.keys():
        x[name] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{name}")
        y[name] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"y_{name}")

    # 2. NEW: Tether Constraints (Using the anchor)
    for name in macros_dict.keys():
        m.addConstr(x[name] >= anchor['x'] - TETHER_BUFFER, name=f"tether_x_min_{name}")
        m.addConstr(x[name] <= anchor['x'] + TETHER_BUFFER, name=f"tether_x_max_{name}")
        m.addConstr(y[name] >= anchor['y'] - TETHER_BUFFER, name=f"tether_y_min_{name}")
        m.addConstr(y[name] <= anchor['y'] + TETHER_BUFFER, name=f"tether_y_max_{name}")

    # 3. Non-Overlap Constraints (Big-M)
    BigM_X = sum(data['w'] for data in macros_dict.values()) * 2
    BigM_Y = sum(data['h'] for data in macros_dict.values()) * 2
    macro_names = list(macros_dict.keys())
    
    for i in range(len(macro_names)):
        for j in range(i + 1, len(macro_names)):
            n1, n2 = macro_names[i], macro_names[j]
            w1, h1 = macros_dict[n1]['w'], macros_dict[n1]['h']
            w2, h2 = macros_dict[n2]['w'], macros_dict[n2]['h']

            b_l = m.addVar(vtype=GRB.BINARY)
            b_r = m.addVar(vtype=GRB.BINARY)
            b_d = m.addVar(vtype=GRB.BINARY)
            b_u = m.addVar(vtype=GRB.BINARY)

            m.addConstr(b_l + b_r + b_d + b_u >= 1)
            m.addConstr(x[n1] + w1 <= x[n2] + BigM_X * (1 - b_l))
            m.addConstr(x[n2] + w2 <= x[n1] + BigM_X * (1 - b_r))
            m.addConstr(y[n1] + h1 <= y[n2] + BigM_Y * (1 - b_d))
            m.addConstr(y[n2] + h2 <= y[n1] + BigM_Y * (1 - b_u))

    # 4. Objective
    m.setObjective(sum(x.values()) + sum(y.values()), GRB.MINIMIZE)

    # 5. Optimize
    m.optimize()

    if m.status in [GRB.OPTIMAL, GRB.TIME_LIMIT]:
        for name in macros_dict.keys():
            macros_dict[name]['x'] = round(x[name].X)
            macros_dict[name]['y'] = round(y[name].X)
        return macros_dict
    else:
        return macros_dict

if __name__ == "__main__":
    # Check paths
    if not os.path.exists(JSON_IN) or not os.path.exists(JSON_ANCHORS):
        print(f"❌ ERROR: Check paths!")
        print(f"JSON_IN: {JSON_IN} exists? {os.path.exists(JSON_IN)}")
        print(f"JSON_ANCHORS: {JSON_ANCHORS} exists? {os.path.exists(JSON_ANCHORS)}")
        exit()

    with open(JSON_IN, 'r') as f: clusters = json.load(f)
    with open(JSON_ANCHORS, 'r') as f: anchors = json.load(f)

    optimized_clusters = {}

    for c_id, macros in clusters.items():
        if c_id in anchors:
            optimized_clusters[c_id] = optimize_cluster(c_id, macros, anchors[c_id])
    
    with open(JSON_OUT, 'w') as f:
        json.dump(optimized_clusters, f, indent=4)
        
    print(f"\n💾 Saved all results to: {JSON_OUT}")