from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List, Optional

# Create FastAPI app
app = FastAPI(title="Student API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET"],  # Only allow GET requests
    allow_headers=["*"],  # Allow all headers
)

# Load the data from CSV file
try:
    # Try to load the CSV file - adjust the filename as needed
    students_df = pd.read_csv("q-fastapi.csv")
    # Convert student IDs to integers
    students_df["studentId"] = students_df["studentId"].astype(int)
    print(f"Successfully loaded data with {len(students_df)} students")
except Exception as e:
    print(f"Error loading CSV: {e}")
    # Create empty dataframe with required columns if file doesn't exist
    students_df = pd.DataFrame(columns=["studentId", "class"])

@app.get("/api")
async def get_students(class_filter: Optional[List[str]] = Query(None, alias="class")):
    """
    Get student data, optionally filtered by class.
    
    Args:
        class_filter: Optional list of classes to filter by.
        
    Returns:
        JSON with student data.
    """
    # If no class filter is provided, return all students
    if class_filter is None:
        result_df = students_df
    else:
        # Filter students by the specified classes
        result_df = students_df[students_df["class"].isin(class_filter)]
    
    # Convert the DataFrame to a list of dictionaries
    students_list = result_df.to_dict(orient="records")
    
    # Return the data in the required format
    return {"students": students_list}

if __name__ == "__main__":
    import uvicorn
    # Run the server when the script is executed directly
    uvicorn.run("student_api:app", host="0.0.0.0", port=8000, reload=True)