#!/usr/bin/env python3
"""Check if Ollama is running and what models are available."""

import httpx
import sys

OLLAMA_URL = "http://localhost:11434"

def check_ollama():
    """Check Ollama status and available models."""
    print("Checking Ollama status...")
    print(f"URL: {OLLAMA_URL}")
    print()
    
    try:
        with httpx.Client(timeout=5.0) as client:
            # Check if Ollama is running
            try:
                response = client.get(f"{OLLAMA_URL}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    print("✅ Ollama is running!")
                    print()
                    
                    if models:
                        print(f"Available models ({len(models)}):")
                        for model in models:
                            name = model.get("name", "unknown")
                            size = model.get("size", 0)
                            size_gb = size / (1024**3) if size else 0
                            print(f"  - {name} ({size_gb:.2f} GB)")
                    else:
                        print("⚠️  No models found. Pull a model with:")
                        print("   ollama pull llama3")
                    
                    return True
                else:
                    print(f"❌ Ollama responded with status {response.status_code}")
                    return False
            except httpx.ConnectError:
                print("❌ Cannot connect to Ollama")
                print()
                print("Make sure Ollama is running:")
                print("  ollama serve")
                return False
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
    except ImportError:
        print("❌ httpx not installed. Install it with:")
        print("  pip install httpx")
        return False

if __name__ == "__main__":
    success = check_ollama()
    sys.exit(0 if success else 1)
