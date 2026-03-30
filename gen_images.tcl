read_db /project/odbFiles/adaptec1_baseline.odb

# Use the direct dump command which is more robust in Docker
# This fulfills Section 9.1: Baseline Placement Visualization
dump_image /project/odbFiles/adaptec1_baseline_layout.png

# Perform routing to calculate congestion for Section 9.2
predict_global_routing
# In some versions, this command can also dump a congestion map
# check if your version supports: 
# dump_congestion_image /project/odbFiles/baseline_congestion.png

exit