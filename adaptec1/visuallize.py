import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

import HPWL_score 
from HPWL_score import check_macro_overlaps

def visualize_and_score(node_dir,pl_dir,nets_dir):
    # Construct correct file paths
    nodes_path = os.path.join(node_dir,"adaptec1.nodes")
    pl_path = os.path.join(pl_dir,"adaptec1.pl")
    nets_path = os.path.join(nets_dir,"adaptec1.nets")

    node_dims = {}
    node_positions = {}
    
    try:
        # 1. Parse Dimensions from .nodes
        with open(nodes_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or "UCLA" in line or "Num" in line:
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    w, h = int(parts[1]), int(parts[2])
                    node_dims[name] = (w, h, 'terminal' in line)

        # 2. Parse Positions from .pl (Needed for BOTH plotting and HPWL)
        with open(pl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or "UCLA" in line:
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    name, x, y = parts[0], int(parts[1]), int(parts[2])
                    node_positions[name] = (x, y)

        # 3. Calculate the HPWL Score
        print("Calculating HPWL...")
        hpwl_score = HPWL_score.calculate_total_hpwl(nets_path, node_positions)
        print(f"Baseline HPWL Score: {hpwl_score}")

        # 4. Draw the Plot
        print("Generating Plot...")
        fig, ax = plt.subplots(figsize=(10, 10))
        for name, (x, y) in node_positions.items():
            if name in node_dims and node_dims[name][2]: # Plot only Macros
                w, h = node_dims[name][0], node_dims[name][1]
                color = 'royalblue' if (w > 50 and h > 50) else 'crimson'
                rect = patches.Rectangle((x, y), w, h, linewidth=0.5, 
                                       edgecolor='black', facecolor=color, alpha=0.7)
                ax.add_patch(rect)

        ax.set_title(f"Baseline Visualization: adaptec1\nHPWL: {hpwl_score}")
        ax.autoscale_view()
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.savefig("baseline_visualization.png", dpi=300, bbox_inches='tight')
        #plt.show()
        HPWL_score.check_macro_overlaps(node_dims, node_positions)
    except Exception as e:
        print(f"An error occurred: {e}")

visualize_and_score("adaptec1.nodes","adaptec1.pl","adaptec1.nets")
