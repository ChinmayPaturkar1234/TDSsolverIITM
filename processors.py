import pandas as pd
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_csv(file_path):
    """
    Process a CSV file and return a string representation.
    
    Args:
        file_path (str): Path to the CSV file
    
    Returns:
        str: String representation of the CSV file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Check if the CSV has an "answer" column
        if 'answer' in df.columns:
            logger.debug("Found 'answer' column in CSV")
            # Extract the value from the answer column
            answer_values = df['answer'].tolist()
            
            # If there's only one value, return it directly
            if len(answer_values) == 1:
                return f"The value in the 'answer' column is: {answer_values[0]}"
            else:
                # Otherwise, return all values
                return f"Values in the 'answer' column: {answer_values}"
        
        # If the dataframe is small, return a string representation
        if len(df) <= 100 and len(df.columns) <= 20:
            return f"CSV File Contents:\n{df.to_string()}"
        
        # For larger files, return a summary
        return (
            f"CSV File Summary:\n"
            f"Rows: {len(df)}\n"
            f"Columns: {', '.join(df.columns)}\n"
            f"First 5 rows:\n{df.head().to_string()}"
        )
    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")
        return f"Error processing CSV file: {str(e)}"

def process_text_file(file_path):
    """
    Process a text file and return its contents.
    
    Args:
        file_path (str): Path to the text file
    
    Returns:
        str: Contents of the text file
    """
    try:
        # Read the text file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # If the file is very large, return a summary
        if len(content) > 10000:
            return f"Text file (first 10000 chars):\n{content[:10000]}..."
        
        return f"Text file contents:\n{content}"
    except Exception as e:
        logger.error(f"Error processing text file: {str(e)}")
        return f"Error processing text file: {str(e)}"

def parse_json(file_path):
    """
    Parse a JSON file and return a string representation.
    
    Args:
        file_path (str): Path to the JSON file
    
    Returns:
        str: String representation of the JSON file
    """
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Return a pretty-printed version
        return f"JSON file contents:\n{json.dumps(data, indent=2)}"
    except Exception as e:
        logger.error(f"Error processing JSON file: {str(e)}")
        return f"Error processing JSON file: {str(e)}"
