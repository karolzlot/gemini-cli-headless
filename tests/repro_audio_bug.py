import os
import sys
import logging
from pathlib import Path

# Add parent dir to path to import the local wrapper
sys.path.append(str(Path(__file__).parent.parent))

from gemini_cli_headless import run_gemini_cli_headless

# Configure logging
logging.basicConfig(level=logging.INFO)

def run_test():
    # Use the specific audio file provided by the user
    audio_file = r"C:\Users\chojn\projects\fdds\data\user_audio\2026-04-17_08-31-45_client_x98jyph7vvl.wav"
    
    if not os.path.exists(audio_file):
        print(f"ERROR: Sample audio file not found at {audio_file}")
        return

    print(f"[TEST] Using sample audio: {audio_file}")

    # Models to test
    test_models = [
        "gemini-3-flash-preview",
        "gemini-3.1-flash-preview",
        "gemini-3.1-flash-lite-preview",
        # "gemini-3-pro-preview" # PASSES but too expensive for frequent test runs
    ]

    prompt = "Please transcribe this audio exactly. Respond ONLY with the text from the audio."

    results = {}

    for model in test_models:
        print(f"\n{'='*40}")
        print(f"TESTING MODEL: {model}")
        print(f"{'='*40}")
        
        try:
            session = run_gemini_cli_headless(
                prompt=prompt,
                model_id=model,
                files=[audio_file],
                max_retries=1,
                timeout_per_attempt=120
            )
            print(f"SUCCESS: {model} returned text: '{session.text}'")
            print("RAW DATA KEYS:", session.raw_data.keys())
            if "response" in session.raw_data:
                print("RAW RESPONSE Snippet:", str(session.raw_data["response"])[:200])
            results[model] = "SUCCESS"
        except Exception as e:
            print(f"FAILURE: {model} failed with error: {e}")
            results[model] = "FAILURE"

    print(f"\n{'='*40}")
    print("SUMMARY OF FINDINGS:")
    for model, outcome in results.items():
        print(f"  {model}: {outcome}")
    print(f"{'='*40}")

if __name__ == "__main__":
    # Load API key from standard project location if not in env
    if not os.environ.get("GEMINI_API_KEY"):
        from dotenv import load_dotenv
        load_dotenv("C:/Users/chojn/projects/fdds/config/.env")
    
    run_test()
