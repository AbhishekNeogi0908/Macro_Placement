import odb
import sys
import os

# 1. Setup paths
sys.path.append('RosettaStone/benchGen')
import BookshelfToOdb as b2o

os.chdir('adaptec1')
db = odb.dbDatabase.create()

# 2. Hardcode the path to the newly downloaded LEF
# tech_lef = './tech/Nangate45.lef'
tech_lef = '/mnt/c/Users/abhis/OneDrive/Desktop/Macro_Placement_WSL/tech/Nangate45.lef'
print(f"Loading Technology LEF: {tech_lef}")
odb.read_lef(db, tech_lef)


# Insert this after odb.read_lef(db, tech_lef)
libs = db.getLibs()
for lib in libs:
    for master in lib.getMasters():
        # This is the exact property the script checks
        if master.isSequential():
            print(f"DEBUG: Found Sequential Cell: {master.getName()}")
            
# 3. Auto-detect the Site Name from the loaded LEF
libs = db.getLibs()
site_name = "unithx" # Fallback
if libs and libs[0].getSites():
    site_name = libs[0].getSites()[0].getName()
print(f"Auto-detected Site Name: {site_name}")

# 4. Run the Conversion
# Added: ffClkPinList=['CLK'] to help the script identify sequential cells
converter = b2o.BookshelfToOdb(
    opendbpy=odb,
    opendb=db,
    auxName="adaptec1.aux", 
    siteName=site_name,
    ffClkPinList=['CLK'],  # CRITICAL: Nangate45 uses 'CLK' for flip-flops
    customFPRatio=1.0
)

# 5. Save the Output
output_dir = "odbFiles"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

odb.write_db(db, os.path.join(output_dir, "adaptec1_baseline.odb"))
print(f"\nSuccess! Baseline created at {output_dir}/adaptec1_baseline.odb")


