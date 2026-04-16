# import odb
# import sys
# import os


# libs = odb.getLibs()
# for lib in libs:
#     lef_path = os.path.join(output_dir, f"{lib.getName()}_macros.lef")
#     # This writes the physical data back to a LEF file
#     odb.write_lef(lib, lef_path)
#     print(f"Generated Custom LEF at: {lef_path}")

# # 1. Setup paths
# sys.path.append('RosettaStone/benchGen')
# import BookshelfToOdb as b2o

# os.chdir('adaptec1')
# db = odb.dbDatabase.create()

# # 2. Hardcode the path to the newly downloaded LEF
# # tech_lef = './tech/Nangate45.lef'
# tech_lef = '/mnt/c/Users/abhis/OneDrive/Desktop/Macro_Placement_WSL/tech/Nangate45.lef'
# print(f"Loading Technology LEF: {tech_lef}")
# odb.read_lef(db, tech_lef)


# # Insert this after odb.read_lef(db, tech_lef)
# libs = db.getLibs()
# for lib in libs:
#     for master in lib.getMasters():
#         # This is the exact property the script checks
#         if master.isSequential():
#             print(f"DEBUG: Found Sequential Cell: {master.getName()}")
            
# # 3. Auto-detect the Site Name from the loaded LEF
# libs = db.getLibs()
# site_name = "unithx" # Fallback
# if libs and libs[0].getSites():
#     site_name = libs[0].getSites()[0].getName()
# print(f"Auto-detected Site Name: {site_name}")

# # 4. Run the Conversion
# # Added: ffClkPinList=['CLK'] to help the script identify sequential cells
# converter = b2o.BookshelfToOdb(
#     opendbpy=odb,
#     opendb=db,
#     auxName="adaptec1.aux", 
#     siteName=site_name,
#     ffClkPinList=['CLK'],  # CRITICAL: Nangate45 uses 'CLK' for flip-flops
#     customFPRatio=1.0
# )

# # 5. Save the Output
# output_dir = "odbFiles"
# if not os.path.exists(output_dir):
#     os.makedirs(output_dir)

# odb.write_db(db, os.path.join(output_dir, "adaptec1_baseline.odb"))

# # ADD THIS: Save the ASCII DEF file
# def_path = os.path.join(output_dir, "adaptec1_baseline.def")
# odb.write_def(db.getChip().getBlock(), def_path)

# print(f"\nSuccess! Baseline created at {output_dir}/adaptec1_baseline.odb")




import odb
import sys
import os

# 1. Setup paths
sys.path.append('RosettaStone/benchGen')
import BookshelfToOdb as b2o

# 2. Change directory
os.chdir('adaptec1')

# 3. Create database
db = odb.dbDatabase.create()

# 4. Read technology LEF
tech_lef = '/mnt/c/Users/abhis/OneDrive/Desktop/Macro_Placement_WSL/tech/Nangate45.lef'
print(f"Loading Technology LEF: {tech_lef}")
odb.read_lef(db, tech_lef)

# 5. Detect site name
site_name = "FreePDK45_38x28_10R_NP_162NW_34O"
libs = db.getLibs()

if libs:
    for lib in libs:
        sites = lib.getSites()
        if sites:
            site_name = sites[0].getName()
            break

print(f"Auto-detected Site Name: {site_name}")

# 6. Run Bookshelf conversion
converter = b2o.BookshelfToOdb(
    opendbpy=odb,
    opendb=db,
    auxName="adaptec1.aux",
    siteName=site_name,
    ffClkPinList=['CLK'],
    customFPRatio=1.0
)

# 7. Output folder
output_dir = "odbFiles"
os.makedirs(output_dir, exist_ok=True)

# 8. Save ODB
odb_path = os.path.join(output_dir, "adaptec1_baseline.odb")
odb.write_db(db, odb_path)

# 9. Save DEF
block = db.getChip().getBlock()
def_path = os.path.join(output_dir, "adaptec1_baseline.def")
odb.write_def(block, def_path)

# 10. Save LEF
for lib in db.getLibs():
    lef_path = os.path.join(output_dir, f"{lib.getName()}.lef")
    odb.write_lef(lib, lef_path)
    print(f"Generated LEF: {lef_path}")

print("\nSUCCESS!")
print(f"ODB: {odb_path}")
print(f"DEF: {def_path}")