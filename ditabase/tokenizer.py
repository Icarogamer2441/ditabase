from enum import Enum
from dataclasses import dataclass
from typing import List

class TokenType(Enum):
    # Keywords
    NEW = "NEW"
    TABLE = "TABLE"
    IF = "IF"
    EXISTS = "EXISTS"
    IS = "IS"
    FALSE = "FALSE"
    TRUE = "TRUE"
    UNIC = "UNIC"
    MAIN = "MAIN"
    UUID = "UUID"
    STR = "STR"
    PASSWORD = "PASSWORD"
    ADD = "ADD"
    ITEM = "ITEM"
    TO = "TO"
    PRINT = "PRINT"
    DELETE = "DELETE"
    FROM = "FROM"
    WHERE = "WHERE"
    REMOVE = "REMOVE"
    INT16 = "INT16"
    INT32 = "INT32"
    INT64 = "INT64"
    CHAR = "CHAR"
    BOOL = "BOOL"
    
    # Symbols
    LEFT_BRACE = "{"
    RIGHT_BRACE = "}"
    COMMA = ","
    SEMICOLON = ";"
    EQUALS = "="
    
    # Other
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    EOF = "EOF"

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class Tokenizer:
    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.current = 0
        self.start = 0
        self.line = 1
        self.column = 1
        
    def tokenize(self) -> List[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens
    
    def scan_token(self):
        char = self.advance()
        
        if char.isspace():
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            return
            
        if char.isalpha():
            self.identifier()
            return
            
        if char == '"':
            self.string()
            return
            
        # Símbolos
        symbols = {
            '{': TokenType.LEFT_BRACE,
            '}': TokenType.RIGHT_BRACE,
            ',': TokenType.COMMA,
            ';': TokenType.SEMICOLON,
            '=': TokenType.EQUALS
        }
        
        if char in symbols:
            self.add_token(symbols[char])
            self.column += 1
            return
            
        raise SyntaxError(f"Unexpected character: {char} at line {self.line}, column {self.column}")
    
    def identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
            
        text = self.source[self.start:self.current]
        
        # Keywords
        keywords = {
            'NEW': TokenType.NEW,
            'TABLE': TokenType.TABLE,
            'IF': TokenType.IF,
            'EXISTS': TokenType.EXISTS,
            'IS': TokenType.IS,
            'FALSE': TokenType.FALSE,
            'TRUE': TokenType.TRUE,
            'UNIC': TokenType.UNIC,
            'MAIN': TokenType.MAIN,
            'UUID': TokenType.UUID,
            'STR': TokenType.STR,
            'PASSWORD': TokenType.PASSWORD,
            'ADD': TokenType.ADD,
            'ITEM': TokenType.ITEM,
            'TO': TokenType.TO,
            'PRINT': TokenType.PRINT,
            'DELETE': TokenType.DELETE,
            'FROM': TokenType.FROM,
            'WHERE': TokenType.WHERE
        }
        
        # Check if it's a keyword only if text is all uppercase
        token_type = keywords.get(text) if text.isupper() else TokenType.IDENTIFIER
        self.add_token(token_type, text)
        self.column += len(text)
    
    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()
            
        if self.is_at_end():
            raise SyntaxError("Unterminated string")
            
        # Consume closing quote
        self.advance()
        
        # Remove quotes
        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING, value)
        self.column += len(value) + 2
    
    def add_token(self, type: TokenType, value: str = None):
        if value is None:
            value = self.source[self.start:self.current]
        self.tokens.append(Token(type, value, self.line, self.column))
    
    def advance(self) -> str:
        self.current += 1
        return self.source[self.current - 1]
    
    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]
    
    def is_at_end(self) -> bool:
        return self.current >= len(self.source) 