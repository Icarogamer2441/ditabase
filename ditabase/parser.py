from dataclasses import dataclass
from typing import List, Dict, Any
from .tokenizer import Token, TokenType

@dataclass
class Column:
    name: str
    type: str
    constraints: List[str]
    
    def __str__(self) -> str:
        constraints = ' '.join(self.constraints)
        return f"{self.name} ({self.type}){' [' + constraints + ']' if constraints else ''}"

@dataclass
class Table:
    name: str
    columns: List[Column]

@dataclass
class CreateTableStatement:
    table: Table
    if_not_exists: bool

@dataclass
class InsertStatement:
    table_name: str
    values: Dict[str, Any]

@dataclass
class PrintTableStatement:
    table_name: str

@dataclass
class DeleteStatement:
    table_name: str
    conditions: Dict[str, Any]

@dataclass
class DeleteTableStatement:
    table_name: str

@dataclass
class PrintItemStatement:
    table_name: str
    column: str
    conditions: Dict[str, Any]

@dataclass
class RemoveTableStatement:
    table_name: str

@dataclass
class ChangeValueStatement:
    table_name: str
    column_name: str
    old_value: str
    new_value: str
    condition_column: str | None = None
    condition_value: str | None = None

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        
    def parse(self):
        statements = []
        
        while not self.is_at_end():
            if self.match(TokenType.NEW):
                statements.append(self.create_table_statement())
            elif self.match(TokenType.ADD):
                statements.append(self.insert_statement())
            elif self.match(TokenType.DELETE):
                if self.check(TokenType.TABLE):
                    statements.append(self.delete_table_statement())
                else:
                    statements.append(self.delete_statement())
            elif self.match(TokenType.REMOVE):
                statements.append(self.remove_table_statement())
            elif self.match(TokenType.PRINT):
                if self.check(TokenType.ITEM):
                    statements.append(self.print_item_statement())
                else:
                    statements.append(self.print_statement())
            elif self.match(TokenType.CHANGE):
                statements.append(self.change_value_statement())
            else:
                raise SyntaxError(f"Unexpected command: {self.peek().value}")
                
        return statements
    
    def create_table_statement(self) -> CreateTableStatement:
        self.consume(TokenType.TABLE, "Expected 'TABLE' after 'NEW'")
        
        if_not_exists = False
        if self.match(TokenType.IF):
            self.consume(TokenType.EXISTS, "Expected 'EXISTS' after 'IF'")
            self.consume(TokenType.IS, "Expected 'IS' after 'EXISTS'")
            if self.match(TokenType.FALSE):
                if_not_exists = True
            elif self.match(TokenType.TRUE):
                if_not_exists = False
            else:
                raise SyntaxError("Expected 'TRUE' or 'FALSE' after 'IS'")
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after table declaration")
        
        columns = []
        while not self.check(TokenType.RIGHT_BRACE):
            constraints = []
            if self.match(TokenType.UNIC):
                constraints.append("UNIQUE")
            if self.match(TokenType.MAIN):
                constraints.append("PRIMARY")
                
            type_token = self.advance()
            valid_types = ["UUID", "STR", "PASSWORD", "INT16", "INT32", "INT64", "CHAR", "BOOL"]
            if type_token.value not in valid_types:
                raise SyntaxError(f"Invalid column type: {type_token.value}")
                
            name_token = self.consume(TokenType.IDENTIFIER, "Expected column name")
            
            columns.append(Column(name_token.value, type_token.value, constraints))
            
            if not self.check(TokenType.RIGHT_BRACE):
                self.consume(TokenType.COMMA, "Expected ',' between columns")
                
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after column definitions")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value
        self.consume(TokenType.SEMICOLON, "Expected ';' after table name")
        
        return CreateTableStatement(Table(table_name, columns), if_not_exists)
    
    def insert_statement(self) -> InsertStatement:
        self.consume(TokenType.ITEM, "Expected 'ITEM' after 'ADD'")
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after 'ITEM'")
        
        values = {}
        while not self.check(TokenType.RIGHT_BRACE):
            name = self.consume(TokenType.IDENTIFIER, "Expected field name").value
            self.consume(TokenType.EQUALS, "Expected '=' after field name")
            value = self.consume(TokenType.STRING, "Expected string value").value
            
            # Get column type for validation
            column_types = self._get_column_types()
            if name in column_types:
                col_type = column_types[name]
                
                # Validate BOOL values
                if col_type == "BOOL":
                    try:
                        num = int(value)
                        if num not in [0, 1]:
                            raise ValueError
                    except ValueError:
                        raise ValueError(f"BOOL type only accepts '0' or '1', got '{value}'")
                
                # Validate CHAR values
                elif col_type == "CHAR":
                    if len(value) != 1:
                        raise ValueError(f"CHAR type only accepts single character, got '{value}'")
                
                # Validate integer types
                elif col_type == "INT16":
                    try:
                        num = int(value)
                        if num < -32768 or num > 32767:
                            raise ValueError(f"INT16 value must be between -32768 and 32767, got {value}")
                    except ValueError:
                        raise ValueError(f"Invalid INT16 value: {value}")
                
                elif col_type == "INT32":
                    try:
                        num = int(value)
                        if num < -2147483648 or num > 2147483647:
                            raise ValueError(f"INT32 value must be between -2147483648 and 2147483647, got {value}")
                    except ValueError:
                        raise ValueError(f"Invalid INT32 value: {value}")
                
                elif col_type == "INT64":
                    try:
                        num = int(value)
                        if num < -9223372036854775808 or num > 9223372036854775807:
                            raise ValueError(f"INT64 value must be between -9223372036854775808 and 9223372036854775807, got {value}")
                    except ValueError:
                        raise ValueError(f"Invalid INT64 value: {value}")
            
            values[name] = value
            
            if not self.check(TokenType.RIGHT_BRACE):
                self.consume(TokenType.COMMA, "Expected ',' between values")
                
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after values")
        self.consume(TokenType.TO, "Expected 'TO' after values")
        self.consume(TokenType.TABLE, "Expected 'TABLE' after 'TO'")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value
        self.consume(TokenType.SEMICOLON, "Expected ';' after table name")
        
        return InsertStatement(table_name, values)
    
    def print_statement(self) -> PrintTableStatement:
        self.consume(TokenType.TABLE, "Expected 'TABLE' after 'PRINT'")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value
        self.consume(TokenType.SEMICOLON, "Expected ';' after table name")
        
        return PrintTableStatement(table_name)
    
    def delete_statement(self) -> DeleteStatement:
        self.consume(TokenType.ITEM, "Expected 'ITEM' after 'DELETE'")
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after 'ITEM'")
        
        conditions = {}
        while not self.check(TokenType.RIGHT_BRACE):
            name = self.consume(TokenType.IDENTIFIER, "Expected field name").value
            self.consume(TokenType.EQUALS, "Expected '=' after field name")
            value = self.consume(TokenType.STRING, "Expected string value").value
            
            conditions[name] = value
            
            if not self.check(TokenType.RIGHT_BRACE):
                self.consume(TokenType.COMMA, "Expected ',' between conditions")
                
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after conditions")
        self.consume(TokenType.FROM, "Expected 'FROM' after conditions")
        self.consume(TokenType.TABLE, "Expected 'TABLE' after 'FROM'")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value
        self.consume(TokenType.SEMICOLON, "Expected ';' after table name")
        
        return DeleteStatement(table_name, conditions)
    
    def print_item_statement(self) -> PrintItemStatement:
        self.advance()  # Consome ITEM
        column = self.consume(TokenType.IDENTIFIER, "Expected column name").value
        self.consume(TokenType.WHERE, "Expected 'WHERE' after column name")
        
        conditions = {}
        name = self.consume(TokenType.IDENTIFIER, "Expected field name").value
        self.consume(TokenType.EQUALS, "Expected '=' after field name")
        value = self.consume(TokenType.STRING, "Expected string value").value
        conditions[name] = value
        
        self.consume(TokenType.FROM, "Expected 'FROM' after condition")
        self.consume(TokenType.TABLE, "Expected 'TABLE' after 'FROM'")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value
        self.consume(TokenType.SEMICOLON, "Expected ';' after table name")
        
        return PrintItemStatement(table_name, column, conditions)
    
    def remove_table_statement(self) -> RemoveTableStatement:
        self.consume(TokenType.TABLE, "Expected 'TABLE' after 'REMOVE'")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value
        self.consume(TokenType.SEMICOLON, "Expected ';' after table name")
        return RemoveTableStatement(table_name)
    
    def delete_table_statement(self) -> DeleteTableStatement:
        self.consume(TokenType.TABLE, "Expected 'TABLE' after 'DELETE'")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value
        self.consume(TokenType.SEMICOLON, "Expected ';' after table name")
        return DeleteTableStatement(table_name)
    
    def change_value_statement(self) -> ChangeValueStatement:
        self.consume(TokenType.VALUE, "Expected 'VALUE' after 'CHANGE'")
        self.consume(TokenType.OF, "Expected 'OF' after 'VALUE'")
        column = self.consume(TokenType.IDENTIFIER, "Expected column name").value
        self.consume(TokenType.EQUALS, "Expected '=' after column name")
        old_value = self.consume(TokenType.STRING, "Expected old value").value
        self.consume(TokenType.TO, "Expected 'TO' after old value")
        new_value = self.consume(TokenType.STRING, "Expected new value").value
        self.consume(TokenType.FROM, "Expected 'FROM' after new value")
        self.consume(TokenType.TABLE, "Expected 'TABLE' after 'FROM'")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value
        
        # Check for optional WHERE clause
        condition_column = None
        condition_value = None
        if self.match(TokenType.WHERE):
            condition_column = self.consume(TokenType.IDENTIFIER, "Expected condition column name").value
            self.consume(TokenType.EQUALS, "Expected '=' after condition column name")
            condition_value = self.consume(TokenType.STRING, "Expected condition value").value
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after table name")
        
        return ChangeValueStatement(table_name, column, old_value, new_value, condition_column, condition_value)
    
    def match(self, *types) -> bool:
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False
    
    def check(self, type) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == type
    
    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()
    
    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF
    
    def peek(self) -> Token:
        return self.tokens[self.current]
    
    def previous(self) -> Token:
        return self.tokens[self.current - 1]
    
    def consume(self, type: TokenType, message: str) -> Token:
        if self.check(type):
            return self.advance()
        raise SyntaxError(f"{message} at line {self.peek().line}") 
    
    def _get_column_types(self) -> Dict[str, str]:
        """Helper method to get column types from current context"""
        for stmt in reversed(self.tokens):
            if isinstance(stmt, CreateTableStatement):
                return {col.name: col.type for col in stmt.table.columns}
        return {} 