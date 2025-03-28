import os
import logging
from utils import extract_zip, process_files
from processors import process_csv, process_text_file
import tempfile
import openai
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def process_request(question, files):
    """
    Process the request by analyzing the question and files.
    
    Args:
        question (str): The question to answer
        files (list): List of uploaded files
    
    Returns:
        str: The answer to the question
    """
    logger.debug(f"Processing request with question: {question}")
    
    # Process any uploaded files
    file_contents = {}
    extracted_files = []
    
    # Create a temporary directory for file processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Process uploaded files
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            
            # Check if the file is a zip file
            if file.filename.endswith('.zip'):
                logger.debug(f"Extracting zip file: {file.filename}")
                extracted_files = extract_zip(file_path, temp_dir)
                logger.debug(f"Extracted files: {extracted_files}")
            else:
                extracted_files.append(file_path)
        
        # Process extracted files based on type
        for file_path in extracted_files:
            file_content = None
            
            if file_path.endswith('.csv'):
                logger.debug(f"Processing CSV file: {file_path}")
                file_content = process_csv(file_path)
            elif file_path.endswith('.txt'):
                logger.debug(f"Processing text file: {file_path}")
                file_content = process_text_file(file_path)
            # Add more file type handlers as needed
            
            if file_content:
                file_name = os.path.basename(file_path)
                file_contents[file_name] = file_content
    
    # Generate answer using LLM
    answer = generate_answer(question, file_contents)
    return answer

def generate_answer(question, file_contents):
    """
    Generate an answer using the OpenAI GPT model.
    
    Args:
        question (str): The question to answer
        file_contents (dict): Dictionary of file contents
    
    Returns:
        str: The answer generated by the model
    """
    logger.debug("Generating answer with GPT-4o")
    
    # Construct the prompt with file contents if available
    prompt = f"Question: {question}\n\n"
    
    if file_contents:
        prompt += "File contents:\n"
        for file_name, content in file_contents.items():
            prompt += f"File: {file_name}\n{content}\n\n"
    
    prompt += (
        "You are an expert in Tools in Data Science. The user has provided a question from a graded assignment. "
        "Analyze the question and any provided file contents, and provide the exact answer that should be submitted. "
        "The answer should be concise and direct - just the value or text that needs to be entered, "
        "without any explanation or additional text. "
        "If the question requires extracting a value from a CSV file's 'answer' column, return only that value."
    )
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a Tools in Data Science expert. Provide direct, concise answers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Lower temperature for more deterministic answers
            max_tokens=500
        )
        
        # Extract the answer from the response
        answer = response.choices[0].message.content.strip()
        
        # Clean up the answer - remove any explanations
        lines = answer.split('\n')
        if len(lines) > 1:
            # If there are multiple lines, try to find the most relevant one
            # which is usually the shortest line that contains substantive content
            # or the line that appears to be just the value
            valid_lines = [line.strip() for line in lines if line.strip()]
            if valid_lines:
                # Sort by length and take the shortest non-empty line
                answer = min(valid_lines, key=len)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        raise
