#!/usr/bin/env python3
"""Helper script to check if .env file is configured correctly"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Get backend directory
backend_dir = Path(__file__).parent
env_file = backend_dir / '.env'

print(f"🔍 Checking .env configuration...")
print(f"📍 .env file path: {env_file}")
print(f"📁 File exists: {env_file.exists()}")
print(f"📊 File size: {env_file.stat().st_size if env_file.exists() else 0} bytes")
print()

if env_file.exists():
    print("📄 File contents:")
    with open(env_file, 'r') as f:
        content = f.read()
        if content.strip():
            # Show first and last few chars of key for verification
            lines = content.split('\n')
            for line in lines:
                if 'OPENAI_API_KEY' in line and '=' in line:
                    key_part = line.split('=')[1].strip()
                    if key_part:
                        masked = key_part[:7] + '...' + key_part[-4:] if len(key_part) > 11 else '***'
                        print(f"  ✅ Found: OPENAI_API_KEY={masked}")
                    else:
                        print(f"  ⚠️  Found but empty: {line}")
                elif line.strip() and not line.strip().startswith('#'):
                    print(f"  📝 {line.split('=')[0] if '=' in line else line}")
        else:
            print("  ⚠️  File is empty!")
else:
    print("❌ .env file does not exist!")
    print()
    print("💡 To create it:")
    print("   1. Copy .env.example to .env:")
    print("      cp .env.example .env")
    print("   2. Edit .env and add your OpenAI API key:")
    print("      OPENAI_API_KEY=sk-your-actual-key-here")

print()
print("🔍 Loading environment variables...")
load_dotenv(env_file)
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ OPENAI_API_KEY is set (length: {len(api_key)} characters)")
    print(f"   Starts with: {api_key[:7]}...")
else:
    print("❌ OPENAI_API_KEY is not set!")
    print()
    print("💡 Make sure your .env file contains:")
    print("   OPENAI_API_KEY=sk-your-actual-openai-api-key")

