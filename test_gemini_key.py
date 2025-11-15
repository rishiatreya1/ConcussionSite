"""Quick test to verify your Gemini API key works."""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in .env file")
    print("   Make sure you have: GEMINI_API_KEY=your_key_here")
    exit(1)

print(f"✓ Found API key: {GEMINI_API_KEY[:10]}...")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # First, try to list available models to see what works
    print("Checking available models...")
    try:
        models = genai.list_models()
        model_list = list(models)
        print(f"✓ Found {len(model_list)} available models")
        print("   Available models with generateContent:")
        gemini_models = []
        for m in model_list:
            if 'generateContent' in m.supported_generation_methods:
                model_name = m.name.replace('models/', '')
                print(f"   - {model_name}")
                gemini_models.append(model_name)
        
        # Try the first gemini model found
        if gemini_models:
            test_model = gemini_models[0]
            print(f"\nTrying first available model: {test_model}...")
            model = genai.GenerativeModel(test_model)
            response = model.generate_content("Say 'Hello' in one word.")
            if response and response.text:
                print(f"✅ SUCCESS! Model '{test_model}' works!")
                print(f"   Response: {response.text.strip()}")
                print(f"\n💡 Update gemini_summary.py to use: '{test_model}'")
                exit(0)
    except Exception as list_err:
        print(f"⚠️  Could not list models: {list_err}")
    
    # Try different model names
    model_names = ["gemini-1.5-flash", "gemini-pro", "gemini-1.5-pro", "models/gemini-1.5-flash"]
    
    for model_name in model_names:
        try:
            print(f"\nTrying model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'Hello' in one word.")
            
            if response and response.text:
                print(f"✅ SUCCESS! Model '{model_name}' works!")
                print(f"   Response: {response.text.strip()}")
                print(f"\n💡 Update your code to use: {model_name}")
                break
        except Exception as model_err:
            print(f"   ❌ {model_name} failed: {str(model_err)[:80]}")
            continue
    else:
        print("\n❌ None of the model names worked")
        
except Exception as e:
    error_msg = str(e)
    print(f"❌ ERROR: {error_msg}")
    
    if "API key" in error_msg or "401" in error_msg or "403" in error_msg:
        print("\n   → Your API key is invalid or incorrect")
        print("   → Make sure you got it from: https://aistudio.google.com/")
        print("   → The key should start with 'AIza'")
    elif "quota" in error_msg.lower() or "429" in error_msg:
        print("\n   → API quota/rate limit reached")
    else:
        print("\n   → Check your internet connection")
        print("   → Verify the key is from Google AI Studio (not Google Cloud)")

