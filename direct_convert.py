import odb

# 1. Create a new database
db = odb.dbDatabase.create()

# 2. Use the internal parser to read the .aux file
# This is exactly what RosettaStone tries to do, but simplified.
odb.read_bookshelf(db, "adaptec1/adaptec1.aux")

# 3. Verify it loaded
block = db.getChip().getBlock()
print(f"Loaded block: {block.getName()}")
print(f"Instances: {len(block.getInsts())}")

# 4. Save
import os
if not os.path.exists('odbFiles'):
    os.makedirs('odbFiles')
    
odb.write_db(db, "odbFiles/adaptec1.odb")
print("Conversion Complete!")
