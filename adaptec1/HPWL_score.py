import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

# --- STEP 1: DEFINE HELPER FUNCTIONS FIRST ---

def compute_net_hpwl(pins):
    """Calculates HPWL for a single list of (x, y) coordinates."""
    if len(pins) < 2:
        return 0
    x_coords = [p[0] for p in pins]
    y_coords = [p[1] for p in pins]
    return (max(x_coords) - min(x_coords)) + (max(y_coords) - min(y_coords))

def calculate_total_hpwl(nets_path, node_positions):
    """Parses .nets file and calculates the sum of all net HPWLs."""
    total_hpwl = 0
    try:
        with open(nets_path, 'r') as f:
            current_net_pins = []
            pins_to_read = 0
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or "UCLA" in line:
                    continue
                
                if "NetDegree" in line:
                    if current_net_pins:
                        total_hpwl += compute_net_hpwl(current_net_pins)
                    parts = line.split()
                    pins_to_read = int(parts[2])
                    current_net_pins = []
                elif pins_to_read > 0:
                    parts = line.split()
                    node_name = parts[0]
                    off_x, off_y = float(parts[-2]), float(parts[-1])
                    
                    if node_name in node_positions:
                        base_x, base_y = node_positions[node_name]
                        current_net_pins.append((base_x + off_x, base_y + off_y))
                    pins_to_read -= 1
            
            if current_net_pins:
                total_hpwl += compute_net_hpwl(current_net_pins)
        return total_hpwl
    except Exception as e:
        print(f"Error calculating HPWL: {e}")
        return None

# --- STEP 2: DEFINE THE MAIN VISUALIZATION FUNCTION ---

# def visualize_and_score(node_dir,pl_dir,nets_dir):
#     # Construct correct file paths
#     nodes_path = os.path.join(node_dir,"adaptec1.nodes")
#     pl_path = os.path.join(pl_dir,"adaptec1.pl")
#     nets_path = os.path.join(nets_dir,"adaptec1.nets")

#     node_dims = {}
#     node_positions = {}
    
#     try:
#         # 1. Parse Dimensions from .nodes
#         with open(nodes_path, 'r', encoding='utf-8') as f:
#             for line in f:
#                 line = line.strip()
#                 if not line or line.startswith('#') or "UCLA" in line or "Num" in line:
#                     continue
#                 parts = line.split()
#                 if len(parts) >= 3:
#                     name = parts[0]
#                     w, h = int(parts[1]), int(parts[2])
#                     node_dims[name] = (w, h, 'terminal' in line)

#         # 2. Parse Positions from .pl (Needed for BOTH plotting and HPWL)
#         with open(pl_path, 'r', encoding='utf-8') as f:
#             for line in f:
#                 line = line.strip()
#                 if not line or line.startswith('#') or "UCLA" in line:
#                     continue
#                 parts = line.split()
#                 if len(parts) >= 3:
#                     name, x, y = parts[0], int(parts[1]), int(parts[2])
#                     node_positions[name] = (x, y)

#         # 3. Calculate the HPWL Score
#         print("Calculating HPWL...")
#         hpwl_score = calculate_total_hpwl(nets_path, node_positions)
#         print(f"Baseline HPWL Score: {hpwl_score}")

#         # 4. Draw the Plot
#         print("Generating Plot...")
#         fig, ax = plt.subplots(figsize=(10, 10))
#         for name, (x, y) in node_positions.items():
#             if name in node_dims and node_dims[name][2]: # Plot only Macros
#                 w, h = node_dims[name][0], node_dims[name][1]
#                 color = 'royalblue' if (w > 50 and h > 50) else 'crimson'
#                 rect = patches.Rectangle((x, y), w, h, linewidth=0.5, 
#                                        edgecolor='black', facecolor=color, alpha=0.7)
#                 ax.add_patch(rect)

#         ax.set_title(f"Baseline Visualization: adaptec1\nHPWL: {hpwl_score}")
#         ax.autoscale_view()
#         plt.grid(True, linestyle='--', alpha=0.3)
#         plt.savefig("baseline_visualization.png", dpi=300, bbox_inches='tight')
#         plt.show()
#         check_macro_overlaps(node_dims, node_positions)
#     except Exception as e:
#         print(f"An error occurred: {e}")




def check_macro_overlaps(node_dims, node_positions):
    overlap_count = 0
    total_overlap_area = 0
    macro_names = [name for name, info in node_dims.items() if info[2]] # Only Terminals
    
    for i in range(len(macro_names)):
        for j in range(i + 1, len(macro_names)):
            m1, m2 = macro_names[i], macro_names[j]
            
            # Get Coordinates and Dimensions
            x1, y1 = node_positions[m1]
            w1, h1 = node_dims[m1][0], node_dims[m1][1]
            x2, y2 = node_positions[m2]
            w2, h2 = node_dims[m2][0], node_dims[m2][1]
            
            # Intersection Boundaries
            ix1, ix2 = max(x1, x2), min(x1 + w1, x2 + w2)
            iy1, iy2 = max(y1, y2), min(y1 + h1, y2 + h2)
            
            if ix1 < ix2 and iy1 < iy2:
                overlap_area = (ix2 - ix1) * (iy2 - iy1)
                total_overlap_area += overlap_area
                overlap_count += 1
                print(f"OVERLAP: {m1} and {m2} (Area: {overlap_area})")

    print(f"\n--- Legalization Report ---")
    print(f"Total Overlapping Pairs: {overlap_count}")
    print(f"Total Overlap Area: {total_overlap_area}")
    return total_overlap_area

# --- STEP 3: RUN EVERYTHING ---
# visualize_and_score("adaptec1.nodes","adaptec1.pl","adaptec1.nets")
