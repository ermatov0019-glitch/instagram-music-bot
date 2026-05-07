import google.generativeai as genai
import os
from dotenv import load_dotenv
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

load_dotenv()

# Configure API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

# Initialize Groq
if GROQ_API_KEY and AsyncGroq:
    groq_client = AsyncGroq(api_key=GROQ_API_KEY)
else:
    groq_client = None

async def get_ai_response(prompt: str) -> str:
    """
    Generates a response from Gemini or Groq and cleans it for Telegram Markdown (V1).
    """
    # Try Groq first if available
    if groq_client:
        try:
            completion = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Siz Instagram botining yordamchisisiz. Qisqa va foydali javob bering."},
                    {"role": "user", "content": prompt}
                ]
            )
            return clean_markdown(completion.choices[0].message.content)
        except Exception as e:
            print(f"Groq Error: {e}")

    # Fallback to Gemini (Try different model names)
    if GEMINI_API_KEY:
        for model_name in ['gemini-1.5-flash', 'gemini-pro', 'models/gemini-pro']:
            try:
                model = genai.GenerativeModel(model_name)
                response = await model.generate_content_async(prompt)
                return clean_markdown(response.text)
            except Exception as e:
                print(f"Gemini ({model_name}) Error: {e}")
                if "leaked" in str(e).lower():
                    return "Xatolik: Gemini API kaliti bloklangan. Iltimos, yangi kalit kiriting."
                continue # Try next model name

    return "Kechirasiz, hozircha javob bera olmayman. 😔"

def clean_markdown(text: str) -> str:
    """
    Cleans text for Telegram Markdown (V1).
    """
    # Gemini uses **bold**, Telegram V1 uses *bold*
    text = text.replace("**", "*")
    
    # Handle unclosed formatting
    if text.count("*") % 2 != 0:
        last_pos = text.rfind("*")
        text = text[:last_pos] + text[last_pos+1:]
        
    return text

if __name__ == "__main__":
    # Simple test
    import asyncio
    async def test():
        resp = await get_ai_response("Salom, kimsan?")
        print(f"AI: {resp}")
    asyncio.run(test())
