#import google
import google.generativeai as genai
#import genai
import os
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# --- CONFIGURATION ---
API_KEY = "YOUR_API_KEY_HERE"
genai.configure(api_key=API_KEY)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USB_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
MEMORY_FILE = os.path.join(BASE_DIR, "skelter_memory.txt")
MODEL_NAME = 'models/gemini-2.5-flash'
MAX_CONTEXT = 1000000 

# --- TOOLS ---
def list_usb_files(directory: str = "."):
    """Lists files and folders on the USB drive."""
    target_path = os.path.abspath(os.path.join(USB_ROOT, directory))
    #if not target_path.startswith(USB_ROOT):
        #return "ERROR: Access Denied. I stay on the USB."
    try:
        items = os.listdir(target_path)
        return "\n".join([f"[{'DIR' if os.path.isdir(os.path.join(target_path, i)) else 'FILE'}] {i}" for i in items])
    except Exception as e:
        return str(e)

def read_usb_file(filename: str):
    """Reads a file from the USB."""
    file_path = os.path.abspath(os.path.join(USB_ROOT, filename))

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return str(e)

def write_usb_file(filename: str, content: str):
        """Writes content to a specified file on the USB drive. Creates the file if it doesn't exist, overwrites it if it does.

        Args:
            filename: The path and name of the file to write to (e.g., 'MG/skelter-notes.txt').
            content: The string content to write into the file.
        """
        file_path = os.path.abspath(os.path.join(USB_ROOT, filename))
        # No restriction check here, as per your previous modification
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {filename}."
        except Exception as e:
            return f"ERROR writing file: {e}"

# --- MEMORY LOGIC ---
def load_memory():
    """Loads only the most recent part of the conversation to save tokens."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
            # --- THE TOKEN SAVER ---
            # Instead of reading the whole file, we only take the last 10-15 lines.
            # This covers about 5-7 full interactions. 
            # It's enough for context but keeps 'Spent Tokens' very low.
            recent_memory = "".join(lines[-15:]) 
            return recent_memory
            
    return "No previous memories. This is a new session."

def save_memory(user, ai):
    """Saves conversation in a compact format to keep the file clean."""
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        # We use short labels (H/S) instead of HUMAN/SKELTER to save a few more tokens
        f.write(f"H: {user}\nS: {ai}\n")
# --- INITIALIZATION ---
model = genai.GenerativeModel(
    model_name= MODEL_NAME,
    tools=[list_usb_files, read_usb_file, write_usb_file],
    safety_settings={
        genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
    }
)

# --- INITIALIZATION ---

def start_skelter():
    print("Initializing SKELTER Neural Link...")
    
    # 1. Load memory first (Local and fast)
    memory_context = load_memory()
    
    # 2. Define Skelter's personality AND memory in the System Instruction
    # This is the most efficient way to give an AI context in 2026.
    system_prompt = (
        "You are Skelter, the AI assistant for MG-OS. "
        "Maintain a technical, helpful and direct terminal-assistant persona. "
        "You may also be a funny guy so that you don't sound too boring"
        f"Your memory of past interactions is: {memory_context}"
    )

    # 3. Create the model with the prompt built-in
    # Use 'gemini-1.5-flash-latest' for the best free-tier speed
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        tools=[list_usb_files, read_usb_file, write_usb_file],
        system_instruction=system_prompt
    )
    
    print("\n============================================")
    print("          SKELTER AI ASSISTANT v2.2")
    print("============================================\n")
    
    # 4. Start the chat (This is now instant)
    chat = model.start_chat(enable_automatic_function_calling=True)
    
    print("[SYSTEM] Neural Link Established. Ready for input.")

    while True:
        user_input = input("\nHUMAN > ")
        print('-' * 88)
        
        if user_input.lower() in ['exit', 'quit']:
            print("\n[SYSTEM] Saving logs and going offline...")
            break
            
        try:
            # 1. Get the response from Google
            response = chat.send_message(
            user_input,
            safety_settings={
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # 2. Extract the token data (New Lines)
            usage = response.usage_metadata
            
            prompt_t = usage.prompt_token_count 
            reply_t = usage.candidates_token_count
            total_t = usage.total_token_count

            # Uses the dynamic limit we fetched at the start
            remaining_context = MAX_CONTEXT - total_t

            print(f"\nSKELTER > {response.text}")

            print("\n" + "." * 88)
            print(f" [SYSTEM RESOURCE REPORT - {MODEL_NAME}]")
            print(f" INPUT  (Prompt): {prompt_t:>6} tokens")
            print(f" OUTPUT (Reply) : {reply_t:>6} tokens")
            print(f" TOTAL SESSION  : {total_t:>6} tokens")
            #print(f" CONTEXT FREE   : {remaining_context:,} tokens")
            print("—" * 88)
            
            save_memory(user_input, response.text)

        except Exception as e:
            print(f"\n[!] CONNECTION ERROR: {e}")

if __name__ == "__main__":
    start_skelter()
