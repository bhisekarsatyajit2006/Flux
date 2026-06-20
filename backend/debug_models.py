import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No API key found in .env")
else:
    genai.configure(api_key=api_key)
    print(f"Checking models for API Key: {api_key[:10]}...")
    try:
        models = list(genai.list_models())
        print(f"Total models found: {len(models)}")
        
        working_model = None
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"Testing {m.name}...")
                try:
                    model = genai.GenerativeModel(m.name)
                    response = model.generate_content("Hi", request_options={'timeout': 5})
                    print(f"✅ SUCCESS with {m.name}")
                    working_model = m.name
                    break
                except Exception as e:
                    print(f"❌ FAILED {m.name}: {str(e)[:100]}")
        
        if working_model:
            print(f"\nFINAL CHOICE: {working_model}")
        else:
            print("\nNo working model found with current quota.")
    except Exception as e:
        print(f"General Error: {e}")
