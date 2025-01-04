# Ditabase

A Python library for data management with support for uniqueness constraints and item limits.

## Installation

```bash
pip install .
```

## Basic Usage

### As a Python Library

```python
import ditabase
```

# Initialize the database

```python
ditabase.init("database.dtb")
```

# Create a new table

```python
ditabase.execute("""
NEW TABLE IF EXISTS IS FALSE {
    UNIC MAIN UUID id,    # Unique, maximum 1 item
    STR name,             # No restrictions
    PASSWORD password     # No restrictions
} users;
""")
```

# Insert data

```python
ditabase.execute("""
ADD ITEM { 
    name="John Doe", 
    password="12423" 
} TO TABLE users;
""")
```

# Get a reference to the table

```python
users = ditabase.get_table("users")
```

# Retrieve column information

```python
columns = users.get_columns()
for column in columns:
    print(column)  # Displays: name (type) [constraints]
```

# Retrieve all items

```python
items = users.get_items()
print(items)  # {'id': [...], 'name': [...], 'password': [...]} 
```

# Fetch a specific item

```python
user = users.get_item("name", "John Doe")
if user:
    print(user['password'])
```

### As a Command-Line Tool

# Compile a .ditabs file to .dtb

```bash
ditabase input.ditabs output.dtb
```

# Start the interactive shell

```bash
ditabase database.dtb
```

## Ditabase Syntax

### Create Table

```
NEW TABLE IF EXISTS IS FALSE {
    UNIC MAIN UUID id,    # Unique, maximum 1 item
    STR name,             # Normal string
    PASSWORD password,    # Password field
    INT32 age,            # 32-bit integer
    INT64 salary,         # 64-bit integer
    INT16 code,           # 16-bit integer
    CHAR grade,           # Single character
    BOOL is_active        # Boolean (0 for false, 1 for true)
} table_name;
```

### Insert Data

```
ADD ITEM { 
    name="John Doe", 
    password="12423" 
} TO TABLE users;
```

### Query Data

# Display the entire table

```
PRINT TABLE users;
```

# Display a specific field

```
PRINT ITEM password WHERE name="John Doe" FROM TABLE users;
```

### Delete Data

```
DELETE ITEM { name="John Doe" } FROM TABLE users;
```

### Delete Table

```
DELETE TABLE table_name;
```

### Update Data

```
CHANGE VALUE OF name="John Doe" TO "Jane Doe" FROM TABLE users;

CHANGE VALUE OF password="12423" TO "12345" FROM TABLE users WHERE name="John Doe";
```

## Constraints

- **UNIC**: Allows a maximum of 2 items with the same value
- **MAIN**: Allows a maximum of 10 items with the same value
- **UNIC MAIN**: Allows only 1 item with the same value

## Data Types

- **UUID**: Universally Unique Identifier
- **STR**: Normal string
- **PASSWORD**: Password field
- **INT32**: 32-bit integer
- **INT64**: 64-bit integer
- **INT16**: 16-bit integer
- **CHAR**: Single character
- **BOOL**: Boolean (0 for false, 1 for true)

## Python API

### Global Functions

- ditabase.init(db_file): Initializes a connection to the database
- ditabase.execute(command): Executes a Ditabase command
- ditabase.get_table(name): Retrieves a table
- ditabase.get_rows(table_name): Retrieves rows from a table
- ditabase.get_columns(table_name): Retrieves columns from a table

### Table Class

- table.get_columns(): Lists column information
- table.get_items(): Retrieves all items organized by column
- table.get_item(column, value): Fetches a specific item

## Examples

Example file example.ditabs:

```
NEW TABLE IF EXISTS IS FALSE {
    UNIC MAIN UUID id,
    STR name,
    PASSWORD password,
    INT32 age,
    INT64 salary,
    INT16 code,
    CHAR grade,
    BOOL is_active
} users;

ADD ITEM { name="John Doe", password="12423" } TO TABLE users;

PRINT ITEM password WHERE name="John Doe" FROM TABLE users;

DELETE ITEM { name="John Doe" } FROM TABLE users;

PRINT TABLE users;
```