import os
import logging
import json
import google.generativeai as genai
import openai
from code_executor import CodeExecutor
from code_question_handlers import CodeQuestionHandler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages interactions with different AI models (Gemini and OpenAI)
    """
    
    def __init__(self):
        """Initialize the model manager with available API keys"""
        self.executor = CodeExecutor(timeout=10)
        self.code_handler = CodeQuestionHandler()
        self.available_models = []
        
        # Initialize Google Gemini if available
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.available_models.append("gemini")
                logger.debug("Gemini API configured successfully")
            except Exception as e:
                logger.error(f"Error configuring Gemini API: {str(e)}")
        
        # Initialize OpenAI if available - either direct API or AI Proxy
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.aiproxy_token = os.environ.get("AIPROXY_TOKEN")
        
        # Prioritize using AI Proxy if token is available
        if self.aiproxy_token:
            try:
                # Configure OpenAI client to use AI Proxy
                self.client = openai.OpenAI(
                    api_key=self.aiproxy_token,
                    base_url="https://aiproxy.sanand.workers.dev/openai/v1"
                )
                self.available_models.append("openai")
                logger.debug("OpenAI API configured successfully using AI Proxy")
            except Exception as e:
                logger.error(f"Error configuring OpenAI API via AI Proxy: {str(e)}")
        # Fall back to direct OpenAI API if proxy token not available
        elif self.openai_api_key:
            try:
                openai.api_key = self.openai_api_key
                self.client = openai.OpenAI(api_key=self.openai_api_key)
                self.available_models.append("openai")
                logger.debug("OpenAI API configured successfully using direct API")
            except Exception as e:
                logger.error(f"Error configuring OpenAI API: {str(e)}")
        
        if not self.available_models:
            logger.error("No available models configured")
        else:
            logger.debug(f"Available models: {self.available_models}")
    
    def select_model_for_question(self, question):
        """
        Select the best model for a given question type
        
        Args:
            question (str): The question text
            
        Returns:
            str: Model name to use
        """
        # Default to Gemini if available
        if not self.available_models:
            logger.warning("No models available")
            return None
        
        # Prioritize model selection based on question type
        question_lower = question.lower()
        
        # For coding questions, prefer OpenAI if available
        coding_indicators = [
            "code", "function", "algorithm", "programming", 
            "python", "javascript", "compute", "calculate",
            "implement", "script", "function", "class", "method",
            "syntax", "compiler", "interpreter", "runtime"
        ]
        
        # For data analysis questions, prefer Gemini
        data_indicators = [
            "data frame", "pandas", "csv", "dataset", "data set",
            "visualization", "plot", "graph", "chart", "analysis",
            "statistics", "regression", "prediction", "machine learning"
        ]
        
        # Count indicators for each category
        coding_score = sum(1 for indicator in coding_indicators if indicator in question_lower)
        data_score = sum(1 for indicator in data_indicators if indicator in question_lower)
        
        if coding_score > data_score and "openai" in self.available_models:
            logger.debug(f"Selected OpenAI for coding question (scores: coding={coding_score}, data={data_score})")
            return "openai"
        elif "gemini" in self.available_models:
            logger.debug(f"Selected Gemini (scores: coding={coding_score}, data={data_score})")
            return "gemini"
        
        # Fallback to first available model
        return self.available_models[0]
    
    def get_system_prompt(self, is_coding=False):
        """
        Get the appropriate system prompt for the question type
        
        Args:
            is_coding (bool): Whether this is a coding question
            
        Returns:
            str: System prompt
        """
        base_prompt = (
            "You are an expert in Tools in Data Science from IIT Madras' Online Degree program. "
            "The user has provided a question from one of the 5 graded assignments. "
            "Follow these strict rules when providing your answer:\n"
            "1. Analyze the question and any provided file contents carefully.\n"
            "2. Provide ONLY the exact answer value that should be submitted - nothing else.\n"
            "3. Do not include explanations or any additional text.\n"
            "4. If the question requires extracting a value from a CSV file's 'answer' column, return only that value.\n"
            "5. If the question asks for a code output or terminal command output, provide only that exact output text.\n"
            "6. For questions about command outputs like 'code -s', be very specific and factual.\n"
            "7. Provide the complete output when requested for command results.\n"
            "8. Make sure your answer can be directly entered in the assignment submission field.\n"
            "9. If the answer is a number, provide just the number without units unless explicitly requested.\n"
            "10. Your response must directly answer the assignment question."
        )
        
        coding_prompt = (
            "You are an expert programming instructor specializing in data science tools and languages. "
            "The user has provided a coding question from a data science assignment. "
            "Follow these strict rules when providing your answer:\n"
            "1. For coding questions, focus on producing the exact output that the code would generate.\n"
            "2. If you need to write code to solve a problem, ensure it is correct and efficient.\n"
            "3. When asked for the output of code, execute the code mentally and provide ONLY the exact output.\n"
            "4. For complex calculations, work through them step by step to ensure accuracy.\n"
            "5. If asked for specific command outputs, provide the exact expected format.\n"
            "6. For algorithmic problems, ensure your solution has the correct time and space complexity.\n"
            "7. Provide ONLY the final answer with no explanations or additional text.\n"
            "8. If extracting from provided files, ensure you use the correct data parsing techniques.\n"
            "9. Make sure numeric answers have the correct precision and format.\n"
            "10. Your response must be the exact answer that would be submitted for the assignment."
        )
        
        return coding_prompt if is_coding else base_prompt
    
    def get_response_from_gemini(self, prompt, system_prompt):
        """
        Get a response from the Gemini model
        
        Args:
            prompt (str): The user prompt
            system_prompt (str): The system prompt
            
        Returns:
            str: The model's response
        """
        try:
            combined_prompt = system_prompt + "\n\n" + prompt
            
            # Configure the model
            gemini_model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Generate the response
            response = gemini_model.generate_content(
                combined_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Low temperature for deterministic answers
                    max_output_tokens=1024,
                    top_p=0.95,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating response from Gemini: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_response_from_openai(self, prompt, system_prompt, is_coding=False):
        """
        Get a response from the OpenAI model
        
        Args:
            prompt (str): The user prompt
            system_prompt (str): The system prompt
            is_coding (bool): Whether this is a coding question
            
        Returns:
            str: The model's response
        """
        try:
            # Use appropriate model based on whether we're using AI Proxy or direct OpenAI
            if hasattr(self, 'aiproxy_token') and self.aiproxy_token:
                # AI Proxy only supports gpt-4o-mini
                model = "gpt-4o-mini"
                logger.debug("Using gpt-4o-mini model via AI Proxy")
            else:
                # Direct OpenAI API - use the newest model
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                # do not change this unless explicitly requested by the user
                model = "gpt-4o"
                logger.debug("Using gpt-4o model via direct OpenAI API")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for deterministic answers
                max_tokens=1024,
                top_p=0.95,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            return f"Error: {str(e)}"
    
    def is_code_execution_needed(self, question, response):
        """
        Determine if code execution is needed based on the question and response
        
        Args:
            question (str): The question text
            response (str): The model's response
            
        Returns:
            bool: Whether code execution is needed
        """
        question_lower = question.lower()
        
        # Check if the response contains code blocks
        contains_code_blocks = "```" in response
        
        # Check if question indicates code execution
        execution_indicators = [
            "what is the output of", "run this code", "execute this code",
            "what will be the result", "what does this code print",
            "compute the result", "calculate", "the output is",
            "run the following", "execute the following"
        ]
        
        needs_execution = any(indicator in question_lower for indicator in execution_indicators)
        
        # If both indicators are present, code execution is needed
        if contains_code_blocks and needs_execution:
            logger.debug("Code execution needed based on question and response")
            return True
        
        return False
    
    def clean_response(self, response, question):
        """
        Clean up the response to get only the exact answer value
        
        Args:
            response (str): The raw model response
            question (str): The question text
            
        Returns:
            str: The cleaned response
        """
        # First, split into lines and remove any empty ones
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        # Check for multi-line command output questions
        if "code -s" in question.lower() and "output" in question.lower():
            # Special case for 'code -s' command output question
            # Preserve multi-line output for command results
            if any(line.lower().startswith(('version:', 'os version:')) for line in lines):
                # This appears to be the correct format for code -s output, return as is
                return '\n'.join(lines)
        
        # For other types of questions
        if len(lines) > 1:
            # If there are multiple lines, apply heuristics to find the actual answer
            
            # Check for common answer patterns
            for line in lines:
                # Check if line starts with "Answer:" or similar
                if line.lower().startswith(('answer:', 'the answer is:', 'result:')):
                    response = line.split(':', 1)[1].strip()
                    break
            else:
                # Specific check for command outputs that might have "Version:" format
                if any(line.lower().startswith(('version:', 'os version:')) for line in lines):
                    # This appears to be command output, return the full output
                    return '\n'.join(lines)
                    
                # If no specific format is detected, use the default approach
                # Filter out very short lines (less than 1 char) which might be punctuation
                valid_lines = [line for line in lines if len(line) >= 1]
                if valid_lines:
                    # For most questions, take the shortest line as it's likely the direct answer
                    # But check if it looks like we need the full multi-line output first
                    if "command" in question.lower() or "output" in question.lower():
                        # For command output questions, return all lines
                        return '\n'.join(valid_lines)
                    else:
                        # For other questions, default to the shortest line
                        response = min(valid_lines, key=len)
        else:
            # If only one line, use it directly
            response = lines[0]
        
        # Additional cleaning: remove quotes, if they're wrapping the entire answer
        response = response.strip('"\'')
        
        # Remove "The answer is: " or similar prefixes if they exist
        common_prefixes = [
            "the answer is ", "answer: ", "result: ", "value: ", 
            "the value is ", "output: ", "the output is "
        ]
        for prefix in common_prefixes:
            if response.lower().startswith(prefix):
                response = response[len(prefix):].strip()
        
        return response
    
    def generate_answer(self, question, file_contents=None):
        """
        Generate an answer using the appropriate AI model
        
        Args:
            question (str): The question to answer
            file_contents (dict, optional): Dictionary of file contents
            
        Returns:
            str: The generated answer
        """
        # First, check if we can handle this with our specialized code question handler
        handled, special_result = self.code_handler.handle_question(question)
        if handled and special_result:
            logger.debug("Question handled by specialized code question handler")
            return special_result
        
        # Construct the prompt with file contents if available
        prompt = f"Question: {question}\n\n"
        
        if file_contents:
            prompt += "File contents:\n"
            for file_name, content in file_contents.items():
                prompt += f"File: {file_name}\n{content}\n\n"
        
        # Determine if this appears to be a coding question
        question_lower = question.lower()
        is_coding = any(term in question_lower for term in [
            "code", "function", "algorithm", "programming", 
            "python", "javascript", "output", "compute", "calculate"
        ])
        
        # Select the appropriate model
        model_name = self.select_model_for_question(question)
        if not model_name:
            return "Error: No AI models are available"
        
        # Get appropriate system prompt
        system_prompt = self.get_system_prompt(is_coding=is_coding)
        
        # Generate response using selected model
        if model_name == "gemini":
            logger.debug("Using Gemini model for response")
            response = self.get_response_from_gemini(prompt, system_prompt)
        elif model_name == "openai":
            logger.debug("Using OpenAI model for response")
            response = self.get_response_from_openai(prompt, system_prompt, is_coding)
        else:
            return "Error: Invalid model selection"
        
        # Check if we should execute code in the response
        if is_coding and self.is_code_execution_needed(question, response):
            logger.debug("Executing code in response")
            execution_result = self.executor.execute_and_get_result(response)
            
            # If execution was successful, replace response with execution result
            if execution_result and "No code blocks found" not in execution_result:
                logger.debug("Using code execution result")
                response = execution_result
        
        # Clean up and return the response
        cleaned_response = self.clean_response(response, question)
        return cleaned_response