import sys

def parse_pl(file_path):
    """Parses a .pl file into a dictionary: {node_id: (x, y, status_string)}"""
    data = {}
    with open(file_path, 'r') as f:
        for line in f:
            # Skip comments and header
            if line.strip().startswith(('#', 'UCLA')):
                continue
            
            parts = line.strip().split()
            if len(parts) < 3:
                continue
            
            node_id = parts[0]
            x = int(parts[1])
            y = int(parts[2])
            
            # Check for fixed status
            status = "FIXED" if "/FIXED" in line else "MOVABLE"
            data[node_id] = (x, y, status)
    return data

def compare_pl_files(base_file, opt_file):
    base_data = parse_pl(base_file)
    opt_data = parse_pl(opt_file)

    print(f"{'Node ID':<15} | {'Base (X,Y)':<15} | {'Base Status':<10} | {'Opt (X,Y)':<15} | {'Opt Status':<10}")
    print("-" * 75)

    for nid, (bx, by, bstatus) in base_data.items():
        if nid in opt_data:
            ox, oy, ostatus = opt_data[nid]

            # Case 1: Baseline (0,0) -> Optimized (!0,0)
            if bx == 0 and by == 0 and (ox != 0 or oy != 0):
                print(f"{nid:<15} | ({bx},{by}){'':<9} | {bstatus:<10} | ({ox},{oy}){'':<9} | {ostatus:<10}")

            # Case 2: Baseline (!0,0) -> Optimized (!0,0)
            elif (bx != 0 or by != 0) and (ox != 0 or oy != 0):
                print(f"{nid:<15} | ({bx},{by}){'':<9} | {bstatus:<10} | ({ox},{oy}){'':<9} | {ostatus:<10}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 compare_pl.py <baseline.pl> <optimized.pl>")
    else:
        compare_pl_files(sys.argv[1], sys.argv[2])