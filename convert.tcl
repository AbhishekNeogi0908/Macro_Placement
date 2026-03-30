# 1. Initialize the database and technology
# Since ISPD benchmarks don't have a real LEF, we create a 'dummy' tech
# or use the built-in library if available.
dbDatabase_create

# 2. Use the app-level command to read Bookshelf
# In newer versions, this is often tucked under the 'ord' namespace
ord::read_bookshelf "adaptec1/adaptec1.aux"

# 3. Save the results
exec mkdir -p odbFiles
write_db "odbFiles/adaptec1.odb"

puts "Successfully converted adaptec1 to OpenDB!"
exit
