import subprocess
import os
import tempfile
import logging
import time
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CodeExecutor:
    """
    Class to safely execute code snippets for generating answers
    """
    
    SUPPORTED_LANGUAGES = {
        'python': {
            'extension': '.py',
            'command': 'python',
            'comment': '#'
        },
        'javascript': {
            'extension': '.js',
            'command': 'node',
            'comment': '//'
        }
    }
    
    def __init__(self, timeout=5):
        """
        Initialize the code executor
        
        Args:
            timeout (int): Maximum execution time in seconds
        """
        self.timeout = timeout
    
    def detect_language(self, code):
        """
        Detect the programming language from the code
        
        Args:
            code (str): Code snippet to analyze
            
        Returns:
            str: Detected language or None if not detected
        """
        # Check for Python syntax patterns
        python_patterns = [
            r'^\s*def\s+\w+\s*\(',  # Function definition
            r'^\s*import\s+\w+',    # Import statement
            r'^\s*from\s+\w+\s+import',  # From import
            r'print\(',             # Print function call
            r'^\s*class\s+\w+:',    # Class definition
        ]
        
        for pattern in python_patterns:
            if re.search(pattern, code, re.MULTILINE):
                return 'python'
        
        # Check for JavaScript syntax patterns
        js_patterns = [
            r'^\s*function\s+\w+\s*\(',  # Function declaration
            r'^\s*const\s+\w+\s*=',      # Const declaration
            r'^\s*let\s+\w+\s*=',        # Let declaration
            r'^\s*var\s+\w+\s*=',        # Var declaration
            r'console\.log\(',           # Console.log
            r'^\s*export',               # Export statement
            r'^\s*import.*from',         # ES6 import
        ]
        
        for pattern in js_patterns:
            if re.search(pattern, code, re.MULTILINE):
                return 'javascript'
        
        # Default to Python if no clear indicators
        return 'python'
    
    def execute_code(self, code, language=None):
        """
        Execute a code snippet and return the result
        
        Args:
            code (str): Code to execute
            language (str, optional): Language of the code. If None, will be auto-detected.
            
        Returns:
            tuple: (success, output/error message)
        """
        # Auto-detect language if not specified
        if not language:
            language = self.detect_language(code)
            logger.debug(f"Auto-detected language: {language}")
        
        # Ensure language is supported
        if language not in self.SUPPORTED_LANGUAGES:
            return False, f"Unsupported language: {language}"
        
        # Create a temporary file
        language_info = self.SUPPORTED_LANGUAGES[language]
        extension = language_info['extension']
        
        try:
            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Add output capturing code
                if language == 'python':
                    # For Python, add import sys capture to ensure we capture all output
                    capture_header = (
                        "import sys, io\n"
                        "original_stdout = sys.stdout\n"
                        "sys.stdout = io.StringIO()\n\n"
                        "try:\n"
                    )
                    
                    # Indent the code
                    indented_code = "\n".join([f"    {line}" for line in code.split("\n")])
                    
                    # Add footer to print captured output
                    capture_footer = (
                        "\nexcept Exception as e:\n"
                        "    print(f'Error: {str(e)}')\n"
                        "finally:\n"
                        "    output = sys.stdout.getvalue()\n"
                        "    sys.stdout = original_stdout\n"
                        "    print(output)"
                    )
                    
                    # Write the modified code
                    temp_file.write((capture_header + indented_code + capture_footer).encode('utf-8'))
                
                elif language == 'javascript':
                    # For JS, wrap in try/catch with console.log capturing
                    temp_file.write(code.encode('utf-8'))
                
                temp_file.flush()
            
            # Execute the code
            cmd = [language_info['command'], temp_path]
            logger.debug(f"Executing command: {cmd}")
            
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    errors='replace'
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=self.timeout)
                    
                    if process.returncode != 0:
                        logger.warning(f"Code execution failed with return code {process.returncode}")
                        return False, f"Execution failed: {stderr}"
                    
                    # Combine stdout and stderr for the complete output
                    output = stdout
                    if stderr:
                        output += f"\nStderr: {stderr}"
                    
                    return True, output.strip()
                    
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.warning("Code execution timed out")
                    return False, f"Execution timed out after {self.timeout} seconds"
            
            except Exception as e:
                logger.error(f"Error executing code: {str(e)}")
                return False, f"Execution error: {str(e)}"
            
        except Exception as e:
            logger.error(f"Error setting up code execution: {str(e)}")
            return False, f"Setup error: {str(e)}"
        
        finally:
            # Clean up the temporary file
            if 'temp_path' in locals():
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception as cleanup_err:
                    logger.warning(f"Error cleaning up temporary file: {str(cleanup_err)}")
    
    def extract_code_blocks(self, text):
        """
        Extract code blocks from markdown text
        
        Args:
            text (str): Text containing code blocks
            
        Returns:
            list: List of (language, code) tuples
        """
        # Match ```language ... ``` blocks
        pattern = r'```(\w+)?\s*([\s\S]*?)\s*```'
        matches = re.findall(pattern, text)
        
        # Process matches
        code_blocks = []
        for language, code in matches:
            # Default to python if language not specified
            if not language:
                language = 'python'
            
            language = language.lower()
            code_blocks.append((language, code.strip()))
        
        # If no code blocks with ``` found, look for indented blocks
        if not code_blocks:
            # Look for lines with 4-space or tab indents that look like code
            lines = text.split('\n')
            current_block = []
            
            for line in lines:
                if line.startswith('    ') or line.startswith('\t'):
                    # Add to current block with indent removed
                    if line.startswith('    '):
                        current_block.append(line[4:])
                    else:
                        current_block.append(line[1:])
                elif current_block:
                    # End of a block, save it if it's not empty
                    if current_block:
                        # Try to auto-detect language
                        code = '\n'.join(current_block)
                        language = self.detect_language(code)
                        code_blocks.append((language, code))
                    current_block = []
            
            # Add final block if exists
            if current_block:
                code = '\n'.join(current_block)
                language = self.detect_language(code)
                code_blocks.append((language, code))
        
        return code_blocks
    
    def execute_and_get_result(self, text):
        """
        Extract code blocks from text and execute them
        
        Args:
            text (str): Text containing code blocks
            
        Returns:
            str: Execution results
        """
        code_blocks = self.extract_code_blocks(text)
        
        if not code_blocks:
            return "No code blocks found to execute"
        
        results = []
        
        for i, (language, code) in enumerate(code_blocks):
            logger.debug(f"Executing code block {i+1}/{len(code_blocks)}")
            
            # Only execute if language is supported
            if language in self.SUPPORTED_LANGUAGES:
                success, output = self.execute_code(code, language)
                
                if success:
                    results.append(f"Result of {language} code execution:\n{output}")
                else:
                    results.append(f"Error executing {language} code: {output}")
            else:
                results.append(f"Skipped execution: Unsupported language '{language}'")
        
        return "\n\n".join(results)