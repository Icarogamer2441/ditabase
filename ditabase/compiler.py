import struct
import uuid
from typing import List, Any
from .parser import CreateTableStatement, InsertStatement, PrintTableStatement, Column, DeleteStatement, PrintItemStatement, RemoveTableStatement, DeleteTableStatement
import os

class Compiler:
    def __init__(self):
        self.tables = {}
        
    def load_existing_data(self, file_path: str):
        """Loads existing data from .dtb file if it exists"""
        if not os.path.exists(file_path):
            return
            
        with open(file_path, 'rb') as f:
            # Check signature
            signature = f.read(4)
            if signature != b'DTB1':
                raise ValueError("Invalid .dtb file")
                
            # Read number of tables
            num_tables = struct.unpack('!I', f.read(4))[0]
            
            # Read each table
            for _ in range(num_tables):
                # Table name
                name_len = struct.unpack('!H', f.read(2))[0]
                table_name = f.read(name_len).decode('utf-8')
                
                # Number of columns
                num_cols = struct.unpack('!H', f.read(2))[0]
                columns = []
                
                # Read column information
                for _ in range(num_cols):
                    # Column name
                    col_name_len = struct.unpack('!H', f.read(2))[0]
                    col_name = f.read(col_name_len).decode('utf-8')
                    
                    # Column type
                    type_len = struct.unpack('!H', f.read(2))[0]
                    col_type = f.read(type_len).decode('utf-8')
                    
                    # Constraints
                    num_constraints = struct.unpack('!H', f.read(2))[0]
                    constraints = []
                    for _ in range(num_constraints):
                        const_len = struct.unpack('!H', f.read(2))[0]
                        constraint = f.read(const_len).decode('utf-8')
                        constraints.append(constraint)
                        
                    columns.append(Column(col_name, col_type, constraints))
                
                # Lê dados da tabela
                num_rows = struct.unpack('!I', f.read(4))[0]
                rows = []
                
                for _ in range(num_rows):
                    row = {}
                    for col in columns:
                        value_len = struct.unpack('!I', f.read(4))[0]
                        value = f.read(value_len).decode('utf-8')
                        row[col.name] = value
                    rows.append(row)
                
                self.tables[table_name] = {
                    'columns': columns,
                    'data': rows
                }
        
    def compile(self, statements: List[Any], output_file: str):
        # Carrega dados existentes
        try:
            self.load_existing_data(output_file)
        except Exception as e:
            print(f"Aviso: Criando novo arquivo - {str(e)}")
        
        # Processa as declarações
        for stmt in statements:
            if isinstance(stmt, CreateTableStatement):
                if stmt.table.name in self.tables:
                    if not stmt.if_not_exists:
                        raise ValueError(f"Table {stmt.table.name} already exists")
                else:
                    self.tables[stmt.table.name] = {
                        'columns': stmt.table.columns,
                        'data': []
                    }
            elif isinstance(stmt, InsertStatement):
                self.insert_data(stmt)
            elif isinstance(stmt, DeleteStatement):
                self.delete_data(stmt)
            elif isinstance(stmt, DeleteTableStatement):
                self.remove_table(stmt.table_name)
            elif isinstance(stmt, PrintTableStatement):
                self.print_table(stmt.table_name)
            elif isinstance(stmt, PrintItemStatement):
                self.print_item(stmt)
            elif isinstance(stmt, RemoveTableStatement):
                self.remove_table(stmt.table_name)
                
        # Salva tudo no arquivo binário
        self.save_to_file(output_file)
    
    def insert_data(self, stmt: InsertStatement):
        if stmt.table_name not in self.tables:
            raise ValueError(f"Table {stmt.table_name} does not exist")
            
        table = self.tables[stmt.table_name]
        
        # Validate data types before inserting
        for column in table['columns']:
            if column.name in stmt.values:
                value = stmt.values[column.name]
                
                # Validate BOOL values
                if column.type == "BOOL":
                    try:
                        num = int(value)
                        if num not in [0, 1]:
                            raise ValueError
                    except ValueError:
                        raise ValueError(f"BOOL type only accepts '0' or '1', got '{value}'")
                
                # Validate CHAR values
                elif column.type == "CHAR":
                    if len(value) != 1:
                        raise ValueError(f"CHAR type only accepts single character, got '{value}'")
                
                # Validate integer types
                elif column.type == "INT16":
                    try:
                        num = int(value)
                        if num < -32768 or num > 32767:
                            raise ValueError(f"INT16 value must be between -32768 and 32767, got {value}")
                    except ValueError:
                        raise ValueError(f"Invalid INT16 value: {value}")
                
                elif column.type == "INT32":
                    try:
                        num = int(value)
                        if num < -2147483648 or num > 2147483647:
                            raise ValueError(f"INT32 value must be between -2147483648 and 2147483647, got {value}")
                    except ValueError:
                        raise ValueError(f"Invalid INT32 value: {value}")
                
                elif column.type == "INT64":
                    try:
                        num = int(value)
                        if num < -9223372036854775808 or num > 9223372036854775807:
                            raise ValueError(f"INT64 value must be between -9223372036854775808 and 9223372036854775807, got {value}")
                    except ValueError:
                        raise ValueError(f"Invalid INT64 value: {value}")
        
        # Verifica restrições antes de inserir
        for column in table['columns']:
            if column.name in stmt.values:
                value = stmt.values[column.name]
                existing_count = sum(1 for row in table['data'] 
                                   if row.get(column.name) == value)
                
                is_unic = 'UNIQUE' in column.constraints
                is_main = 'PRIMARY' in column.constraints
                
                if is_unic and is_main and existing_count >= 1:
                    raise ValueError(f"UNIC MAIN constraint violation: '{value}' already exists in column {column.name}")
                elif is_unic and existing_count >= 2:
                    raise ValueError(f"UNIC constraint violation: '{value}' already exists 2 times in column {column.name}")
                elif is_main and existing_count >= 10:
                    raise ValueError(f"MAIN constraint violation: 10 items limit reached for '{value}' in column {column.name}")
        
        # Gera UUID para campos UNIC MAIN UUID
        row_data = {}
        for column in table['columns']:
            if 'UUID' in column.type and 'PRIMARY' in column.constraints:
                row_data[column.name] = str(uuid.uuid4())
            elif column.name in stmt.values:
                row_data[column.name] = stmt.values[column.name]
            else:
                raise ValueError(f"Valor não fornecido para a coluna {column.name}")
                
        table['data'].append(row_data)
    
    def save_to_file(self, output_file: str):
        with open(output_file, 'wb') as f:
            # Cabeçalho do arquivo
            f.write(b'DTB1')  # Assinatura do formato
            
            # Número de tabelas
            f.write(struct.pack('!I', len(self.tables)))
            
            # Escreve cada tabela
            for table_name, table_data in self.tables.items():
                # Nome da tabela
                name_bytes = table_name.encode('utf-8')
                f.write(struct.pack('!H', len(name_bytes)))
                f.write(name_bytes)
                
                # Número de colunas
                columns = table_data['columns']
                f.write(struct.pack('!H', len(columns)))
                
                # Informações das colunas
                for col in columns:
                    # Nome da coluna
                    col_name_bytes = col.name.encode('utf-8')
                    f.write(struct.pack('!H', len(col_name_bytes)))
                    f.write(col_name_bytes)
                    
                    # Tipo da coluna
                    col_type_bytes = col.type.encode('utf-8')
                    f.write(struct.pack('!H', len(col_type_bytes)))
                    f.write(col_type_bytes)
                    
                    # Constraints
                    f.write(struct.pack('!H', len(col.constraints)))
                    for constraint in col.constraints:
                        const_bytes = constraint.encode('utf-8')
                        f.write(struct.pack('!H', len(const_bytes)))
                        f.write(const_bytes)
                
                # Dados da tabela
                rows = table_data['data']
                f.write(struct.pack('!I', len(rows)))
                
                for row in rows:
                    for col in columns:
                        value = row[col.name]
                        value_bytes = value.encode('utf-8')
                        f.write(struct.pack('!I', len(value_bytes)))
                        f.write(value_bytes) 
    
    def print_table(self, table_name: str):
        """Prints data from a table"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
            
        table = self.tables[table_name]
        columns = table['columns']
        rows = table['data']
        
        # Print header
        headers = [col.name for col in columns]
        print("\n" + " | ".join(headers))
        print("-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1)))
        
        # Print data
        for row in rows:
            print(" | ".join(row[col.name] for col in columns))
        print() 
    
    def delete_data(self, stmt: DeleteStatement):
        if stmt.table_name not in self.tables:
            raise ValueError(f"Table {stmt.table_name} does not exist")
            
        table = self.tables[stmt.table_name]
        rows = table['data']
        
        # Remove rows that match conditions
        table['data'] = [
            row for row in rows 
            if not all(row.get(k) == v for k, v in stmt.conditions.items())
        ]
    
    def print_item(self, stmt: PrintItemStatement):
        if stmt.table_name not in self.tables:
            raise ValueError(f"Table {stmt.table_name} does not exist")
            
        table = self.tables[stmt.table_name]
        rows = table['data']
        
        # Find rows that match conditions
        for row in rows:
            if all(row.get(k) == v for k, v in stmt.conditions.items()):
                if stmt.column in row:
                    print(f"\n{stmt.column}: {row[stmt.column]}\n")
                else:
                    print(f"\nColumn {stmt.column} not found\n")
                return
        
        print(f"\nNo items found matching the specified conditions\n") 
    
    def remove_table(self, table_name: str):
        """Removes a table from the database"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        del self.tables[table_name] 