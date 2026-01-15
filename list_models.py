import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY not found in environment.")
else:
    try:
        client = genai.Client(api_key=api_key)
        print("Listing models...")
        # Try to list models to see what's available
        # The SDK documentation suggests client.models.list() usually
        # But let's check what the client actually exposes or if we need to access a specific service
        
        # Based on typical new SDK patterns, it might be client.models.list()
        # If that fails, I'll see the error.
        
        # The error in the user log said: "Call ListModels to see the list of available models"
        
        for model in client.models.list():
            print(f"Model: {model.name}")
            
    except Exception as e:
        print(f"Error: {e}")
