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
        
        # Check if only one file was extracted and it's a ZIP file
        if len(extracted_files) == 1 and extracted_files[0].lower().endswith('.zip'):
            logger.debug("Found nested zip file, extracting it as well")
            nested_zip = extracted_files[0]
            # Create a subdirectory for the nested extraction to avoid name conflicts
            nested_extract_dir = os.path.join(extract_to, "nested_zip_contents")
            os.makedirs(nested_extract_dir, exist_ok=True)
            # Extract the nested zip and replace our list with these deeper files
            extracted_files = extract_zip(nested_zip, nested_extract_dir)
        
        # If no files were found, we should check subdirectories for files
        if not extracted_files:
            logger.debug("No files directly in zip, looking in subdirectories")
            for root, _, files in os.walk(extract_to):
                for file in files:
                    file_path = os.path.join(root, file)
                    extracted_files.append(file_path)
        
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
            if file_extension in ['.csv', '.tsv']:
                # Read CSV/TSV file
                sep = '\t' if file_extension == '.tsv' else ','
                df = pd.read_csv(file_path, sep=sep)
                
                # Convert DataFrame to string representation
                if 'answer' in df.columns:
                    answer_values = df['answer'].tolist()
                    if len(answer_values) == 1:
                        file_contents[file_name] = f"CSV contains answer column with value: {answer_values[0]}"
                    else:
                        file_contents[file_name] = f"CSV contains answer column with values: {answer_values}"
                else:
                    file_contents[file_name] = f"CSV File Contents:\n{df.to_string()}"
                
            elif file_extension in ['.txt', '.log', '.md', '.py', '.js', '.html', '.css', '.json', '.xml']:
                # Read text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Handle large files by truncating
                if len(content) > 10000:
                    file_contents[file_name] = f"{file_extension[1:].upper()} File (first 10000 chars):\n{content[:10000]}..."
                else:
                    file_contents[file_name] = f"{file_extension[1:].upper()} File:\n{content}"
            
            elif file_extension in ['.xlsx', '.xls']:
                # Read Excel file - only include if pandas is imported
                try:
                    df = pd.read_excel(file_path)
                    file_contents[file_name] = f"Excel File Contents:\n{df.to_string()}"
                except ImportError:
                    file_contents[file_name] = "Excel file detected but pandas Excel support not available."
            
            elif file_extension == '.json':
                # Read JSON file
                from processors import parse_json
                file_contents[file_name] = parse_json(file_path)
                
            else:
                # For binary or unsupported files, at least report the size
                file_size = os.path.getsize(file_path)
                file_contents[file_name] = f"File type {file_extension} not directly processable. Size: {file_size} bytes."
                logger.warning(f"Limited support for file type: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {str(e)}")
            file_contents[file_name] = f"Error processing file: {str(e)}"
    
    return file_contents
