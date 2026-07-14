from google import genai
from google.genai import types
import os
import time
import PIL.Image
import warnings

# --- INITIALIZATION ---
warnings.filterwarnings("ignore", category=FutureWarning)

# --- CONFIGURATION --- 
API_KEY = "API_KEY_HERE"
client = genai.Client(api_key=API_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USB_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
MEMORY_FILE = os.path.join(BASE_DIR, "skelter_memory.txt")
MODEL_NAME = 'models/gemini-2.5-flash' 

# --- TOOLS ---
def list_usb_files(directory: str = "."):
    """Lists files and folders on the USB drive."""
    target_path = os.path.abspath(os.path.join(USB_ROOT, directory))
    try:
        items = os.listdir(target_path)
        return "\n".join([f"[{'DIR' if os.path.isdir(os.path.join(target_path, i)) else 'FILE'}] {i}" for i in items])
    except Exception as e: return str(e)

def read_usb_file(filename: str):
    """Reads a text/code file from the USB."""
    file_path = os.path.abspath(os.path.join(USB_ROOT, filename))
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e: return str(e)

def write_usb_file(filename: str, content: str):
    """Writes content to a file on the USB."""
    file_path = os.path.abspath(os.path.join(USB_ROOT, filename))
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filename}."
    except Exception as e: return f"ERROR: {e}"

def read_image(filename: str):
    """Loads an image for visual analysis."""
    file_path = os.path.abspath(os.path.join(USB_ROOT, filename))
    try: return PIL.Image.open(file_path)
    except Exception as e: return f"ERROR: {e}"

# --- MEMORY LOGIC ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[-15:]) 
    return "New session started."

def save_memory(user, ai):
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"H: {user}\nS: {ai}\n")

# --- CORE ENGINE ---
def start_skelter():
    print("Initializing SKELTER Neural Link...")
    memory_context = load_memory()

    # 1. MODE SELECTION
    print("\n[SYSTEM] SELECT NEURAL MODE:")
    print(" 1. OS MODE  (Access USB files, Code, Storage)")
    print(" 2. WEB MODE (Google Search, Live Chemistry Data)")
    mode_choice = input("\nSELECT MODE [1/2] > ")

    # 2. DEFINE SEPARATE TOOLSETS
    # OS Mode uses your custom local functions
    os_tools = [list_usb_files, read_usb_file, write_usb_file]
    
    # Web Mode uses the built-in Google Search
    web_tools = [types.Tool(google_search=types.GoogleSearch())]

    if mode_choice == "2":
        active_tools = web_tools
        mode_name = "WEB MODE (Search Enabled)"
        sys_instruct = f"You are Skelter in WEB MODE. Use Google Search for facts. USE YOUR MEMORY: {memory_context}"
    else:
        active_tools = os_tools
        mode_name = "OS MODE (File Access Enabled)"
        sys_instruct = f"You are Skelter in OS MODE. Manage the MG-OS files. USE YOUR MEMORY: {memory_context}"

    # 3. CREATE THE CHAT WITH THE SELECTED TOOLS
    try:
        chat = client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
            tools=active_tools,
            system_instruction=sys_instruct,
            # Use the full HARM_CATEGORY_ names to stop the 400 error
            safety_settings=[
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, 
                    threshold=types.HarmBlockThreshold.BLOCK_NONE
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, 
                    threshold=types.HarmBlockThreshold.BLOCK_NONE
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, 
                    threshold=types.HarmBlockThreshold.BLOCK_NONE
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, 
                    threshold=types.HarmBlockThreshold.BLOCK_NONE
                ),
            ]
        )
        )
    except Exception as e:
        print(f"[!] KERNEL ERROR: {e}")
        return

    print("\n============================================")
    print(f"          SKELTER AI ASSISTANT v3.1")
    print(f"          ACTIVE: {mode_name}")
    print("============================================\n")
    print("[SYSTEM] Neural Link Established. Ready.")

    while True:
        user_input = input("\nHUMAN > ")
        print('-' * 88)
        
        if user_input.lower() in ['exit', 'quit']:
            print("\n[SYSTEM] Going offline..."); break

        f user_input.lower() == 'reset':
            os.system('cls')
            return start_skelter()
            
        try:
            # Automated Vision Detection (Works in BOTH modes)
            content = user_input
            if any(user_input.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                img = read_image(user_input)
                if not isinstance(img, str):
                    print(f"[SYSTEM] Visual sensors active. Image '{user_input}' loaded.")
                    prompt = input("Analyze this image? > ")
                    content = [prompt, img]
                else:
                    print(f"[!] {img}")

            response = chat.send_message(message=content)
            print(f"\nSKELTER > {response.text}")

            usage = response.usage_metadata
            print("\n" + "." * 88)
            print(f" [SYSTEM RESOURCE REPORT]")
            print(f" IN: {usage.prompt_token_count} | OUT: {usage.candidates_token_count} | TOTAL: {usage.total_token_count}")
            print("—" * 88)
            
            save_memory(user_input, response.text)

        except Exception as e:
            print(f"\n[!] CONNECTION ERROR: {e}")

if __name__ == "__main__":
    start_skelter()
