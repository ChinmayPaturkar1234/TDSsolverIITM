import os
import zipfile
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_zip(zip_path, extract_to):
    """
    Extract a zip file to the specified directory.
    
    Args:
        zip_path (str): Path to the zip file
        extract_to (str): Directory to extract to
    
    Returns:
        list: List of extracted file paths
    """
    try:
        extracted_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of files in the zip
            file_list = zip_ref.namelist()
            logger.debug(f"Files in zip: {file_list}")
            
            # Extract all files
            zip_ref.extractall(extract_to)
            
            # Build full paths to extracted files
            for file_name in file_list:
                # Skip directories
                if not file_name.endswith('/'):
                    extracted_path = os.path.join(extract_to, file_name)
                    if os.path.isfile(extracted_path):
                        extracted_files.append(extracted_path)
        
        return extracted_files
    except Exception as e:
        logger.error(f"Error extracting zip file: {str(e)}")
        raise

def process_files(file_paths):
    """
    Process a list of files based on their types.
    
    Args:
        file_paths (list): List of file paths to process
    
    Returns:
        dict: Dictionary of processed file contents
    """
    file_contents = {}
    
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.csv':
                # Read CSV file
                df = pd.read_csv(file_path)
                file_contents[file_name] = df
            elif file_extension == '.txt':
                # Read text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_contents[file_name] = f.read()
            # Add more file type handlers as needed
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {str(e)}")
    
    return file_contents
