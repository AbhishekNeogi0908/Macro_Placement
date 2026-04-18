import json
import os
import gurobipy as gp
from gurobipy import GRB

# ==========================================
# Path Configuration
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: Ensure these paths match your Ubuntu 20 structure
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "adaptec1"))
RESULTS_DIR = os.path.join(BASE_DIR, "Results", "Phase1_Partitioning")

JSON_CLUSTERS = os.path.join(RESULTS_DIR, "clustered_macros.json")
JSON_ANCHORS = os.path.join(RESULTS_DIR, "cluster_anchors.json")
JSON_OUT = os.path.join(RESULTS_DIR, "optimized_macros_final.json")

# The "Tether" - How much freedom do we give Gurobi?
# Start with 2000 units. If it fails to solve, increase this.
TETHER_BUFFER = 2000 

def optimize_cluster(cluster_id, macros_dict, anchor):
    print(f"\n🚀 Launching Gurobi for Cluster {cluster_id} tethered at ({anchor['x']}, {anchor['y']})")
    
    m = gp.Model(f"Cluster_{cluster_id}")
    m.setParam('OutputFlag', 1)
    m.setParam('TimeLimit', 120) # Given 2 mins per cluster

    x = {}
    y = {}
    for name in macros_dict.keys():
        x[name] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{name}")
        y[name] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"y_{name}")

    # 1. Tether Constraints (The "Anchor" logic)
    # Macros must stay within anchor_x +/- buffer
    for name in macros_dict.keys():
        m.addConstr(x[name] >= anchor['x'] - TETHER_BUFFER, name=f"tether_x_min_{name}")
        m.addConstr(x[name] <= anchor['x'] + TETHER_BUFFER, name=f"tether_x_max_{name}")
        m.addConstr(y[name] >= anchor['y'] - TETHER_BUFFER, name=f"tether_y_min_{name}")
        m.addConstr(y[name] <= anchor['y'] + TETHER_BUFFER, name=f"tether_y_max_{name}")

    # 2. Non-Overlap Constraints (The Big-M logic)
    BigM_X = sum(d['w'] for d in macros_dict.values()) * 2
    BigM_Y = sum(d['h'] for d in macros_dict.values()) * 2
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

    # 3. Objective: Compact the cluster
    m.setObjective(sum(x.values()) + sum(y.values()), GRB.MINIMIZE)

    m.optimize()

    if m.status in [GRB.OPTIMAL, GRB.TIME_LIMIT]:
        for name in macros_dict.keys():
            macros_dict[name]['x'] = round(x[name].X)
            macros_dict[name]['y'] = round(y[name].X)
        return macros_dict
    return None

if __name__ == "__main__":
    with open(JSON_CLUSTERS, 'r') as f: clusters = json.load(f)
    with open(JSON_ANCHORS, 'r') as f: anchors = json.load(f)

    optimized_clusters = {}
    for c_id, macros in clusters.items():
        if c_id in anchors:
            result = optimize_cluster(c_id, macros, anchors[c_id])
            if result: optimized_clusters[c_id] = result

    with open(JSON_OUT, 'w') as f: json.dump(optimized_clusters, f, indent=4)
    print(f"\n✅ Phase 4 Complete. Final placement in {JSON_OUT}")