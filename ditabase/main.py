from .tokenizer import Tokenizer
from .parser import Parser
from .compiler import Compiler
import sys
import os
import cmd

class DitabaseShell(cmd.Cmd):
    intro = 'Welcome to Ditabase. Type help or ? to list commands.\n'
    prompt = 'ditabase> '
    
    def __init__(self, db_file: str):
        super().__init__()
        self.db_file = db_file
        self.multiline_buffer = []
        self.in_multiline = False
        
    def default(self, line: str):
        if self.in_multiline:
            self.multiline_buffer.append(line)
            if line.strip().endswith(';'):
                # Execute the complete command
                full_command = '\n'.join(self.multiline_buffer)
                self.execute_command(full_command)
                self.multiline_buffer = []
                self.in_multiline = False
            return
            
        if '{' in line:
            self.in_multiline = True
            self.multiline_buffer.append(line)
            return
            
        self.execute_command(line)
        
    def execute_command(self, command: str):
        try:
            tokenizer = Tokenizer(command)
            tokens = tokenizer.tokenize()
            parser = Parser(tokens)
            statements = parser.parse()
            compiler = Compiler()
            compiler.compile(statements, self.db_file)
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_exit(self, arg):
        """Exit the interpreter"""
        return True
        
    def do_quit(self, arg):
        """Exit the interpreter"""
        return True

def compile_ditabase(input_file: str, output_file: str):
    # Read input file
    with open(input_file, 'r') as f:
        source = f.read()
    
    # Tokenize
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    statements = parser.parse()
    
    # Compile
    compiler = Compiler()
    # Try to load existing data before compiling
    try:
        compiler.load_existing_data(output_file)
    except Exception as e:
        print(f"Warning: Creating new file - {str(e)}")
    
    compiler.compile(statements, output_file)

def main():
    if len(sys.argv) == 1:
        print("Usage: python -m ditabase <file.dtb>")
        print("   or: python -m ditabase <input.ditabs> <output.dtb>")
        sys.exit(1)
        
    # If only one file is specified, assume it's .dtb and start shell
    if len(sys.argv) == 2:
        db_file = sys.argv[1]
        if not db_file.endswith('.dtb'):
            db_file += '.dtb'
        DitabaseShell(db_file).cmdloop()
        return
        
    # If two files are specified, compile .ditabs to .dtb
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        compile_ditabase(input_file, output_file)
        print(f"File {output_file} generated successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 