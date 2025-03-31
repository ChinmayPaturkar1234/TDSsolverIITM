{
  "workflows": [
    {
      "name": "Start application",
      "command": "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"
    },
    {
      "name": "FastAPI Server",
      "command": "python student_api.py"
    }
  ]
}
