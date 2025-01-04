from .tokenizer import Tokenizer
from .parser import Parser
from .compiler import Compiler
from typing import Optional, Dict, Any, List
from .parser import Column
import os

# Global Ditabase instance
_instance = None

def init(db_file: str) -> None:
    """
    Initializes Ditabase with a database file.
    
    Args:
        db_file (str): Path to .dtb file
    """
    global _instance
    _instance = Ditabase(db_file)

def execute_file(file_name: str) -> None:
    """
    Executes commands from a .ditabs file.
    
    Args:
        file_name (str): Path to .ditabs file
    
    Raises:
        RuntimeError: If init() was not called first
        FileNotFoundError: If file does not exist
        ValueError: If file is not a .ditabs file
    """
    if _instance is None:
        raise RuntimeError("Ditabase not initialized. Call ditabase.init() first.")
        
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"File {file_name} not found")
        
    if not file_name.endswith('.ditabs'):
        raise ValueError("File must have .ditabs extension")
        
    with open(file_name, 'r') as f:
        source = f.read()
        
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    parser = Parser(tokens)
    statements = parser.parse()
    _instance.compiler.compile(statements, _instance.db_file)

def execute(command: str) -> None:
    """
    Executes a Ditabase command.
    
    Args:
        command (str): Ditabase command to execute
    
    Raises:
        RuntimeError: If init() was not called first
    """
    if _instance is None:
        raise RuntimeError("Ditabase not initialized. Call ditabase.init() first.")
    _instance.execute(command)

class Table:
    def __init__(self, name: str, data: Dict[str, Any]):
        self.name = name
        self.columns = data['columns']
        self.data = data['data']
    
    def get_columns(self) -> List[Column]:
        """
        Returns the list of columns with their information.
        
        Returns:
            List[Column]: List of Column objects with name, type and constraints
        """
        return self.columns
    
    def get_items(self) -> Dict[str, List[str]]:
        """
        Returns a dictionary where keys are column names
        and values are lists with all values from that column.
        
        Returns:
            Dict[str, List[str]]: Dictionary with {column_name: [values...]}
        """
        result = {col.name: [] for col in self.columns}
        
        for row in self.data:
            for col_name in result:
                result[col_name].append(row[col_name])
                
        return result
    
    def get_item(self, column: str, value: str) -> Optional[Dict[str, str]]:
        """
        Returns the first item that matches the condition column=value
        
        Args:
            column (str): Column name to search
            value (str): Value to compare
            
        Returns:
            Optional[Dict[str, str]]: Found item or None if not found
        """
        for row in self.data:
            if row.get(column) == value:
                return row
        return None

def get_table(table_name: str) -> Table:
    """
    Returns a table.
    
    Args:
        table_name (str): Table name
    
    Returns:
        Table: Table object representing the table
    
    Raises:
        RuntimeError: If init() was not called first
        ValueError: If table does not exist
    """
    if _instance is None:
        raise RuntimeError("Ditabase not initialized. Call ditabase.init() first.")
    
    if table_name not in _instance.compiler.tables:
        raise ValueError(f"Table {table_name} does not exist")
        
    return Table(table_name, _instance.compiler.tables[table_name])

def get_rows(table_name: str) -> list:
    """
    Returns only the data rows from a table.
    """
    return get_table(table_name).data

def get_columns(table_name: str) -> list:
    """
    Returns only the columns from a table.
    """
    return get_table(table_name).columns

def format_column(column: Column) -> str:
    """Formats a column for display"""
    constraints = ' '.join(column.constraints)
    return f"{column.name} ({column.type}){' [' + constraints + ']' if constraints else ''}"

class Ditabase:
    def __init__(self, db_file: str):
        """
        Initializes a connection to a Ditabase database file.
        
        Args:
            db_file (str): Path to .dtb file
        """
        self.db_file = db_file if db_file.endswith('.dtb') else db_file + '.dtb'
        self.compiler = Compiler()
        
        # Load existing data if file exists
        try:
            self.compiler.load_existing_data(self.db_file)
        except Exception as e:
            print(f"Warning: Creating new file - {str(e)}")
    
    def execute(self, command: str) -> None:
        """
        Executes a Ditabase command.
        
        Args:
            command (str): Ditabase command to execute
        
        Raises:
            RuntimeError: If init() was not called first
        """
        if _instance is None:
            raise RuntimeError("Ditabase not initialized. Call ditabase.init() first.")
        _instance.execute(command)

# Library version
__version__ = "0.1.0" 