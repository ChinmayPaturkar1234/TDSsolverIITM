# TDS Solver

TDS Solver is an LLM-powered application that automatically solves questions from IIT Madras' Tools in Data Science course assignments.

## Features

- API endpoint that accepts POST requests with multipart/form-data
- Processes questions and optional file attachments from 5 graded assignments
- Uses GPT-4o to generate accurate answers
- Simple web interface for easy interaction
- Handles file uploads and extractions (ZIP, CSV, etc.)

## API Usage

You can use the API by sending a POST request to the `/api/` endpoint:

```bash
curl -X POST "https://your-app-url/api/" \
  -H "Content-Type: multipart/form-data" \
  -F "question=Download and unzip file abcd.zip which has a single extract.csv file inside. What is the value in the 'answer' column of the CSV file?" \
  -F "file=@abcd.zip"
