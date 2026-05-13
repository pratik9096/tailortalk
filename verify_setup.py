"""
TailorTalk - Setup Verification Script
Run this to check if everything is configured correctly
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🔍 TailorTalk Setup Verification")
print("=" * 60)

# Track results
checks_passed = 0
checks_failed = 0

# ============ CHECK 1: Python Version ============
print("\n1️⃣  Python Version")
print("-" * 40)
py_version = sys.version_info
required_version = (3, 8)
if py_version >= required_version:
    print(f"✅ Python {py_version.major}.{py_version.minor} (Required: 3.8+)")
    checks_passed += 1
else:
    print(f"❌ Python {py_version.major}.{py_version.minor} (Required: 3.8+)")
    checks_failed += 1

# ============ CHECK 2: Required Packages ============
print("\n2️⃣  Required Packages")
print("-" * 40)
required_packages = [
    'fastapi',
    'streamlit',
    'langchain',
    'langchain_core',
    'google',
    'dotenv'
]

for package in required_packages:
    try:
        __import__(package)
        print(f"✅ {package}")
        checks_passed += 1
    except ImportError:
        print(f"❌ {package} - Run: pip install -r requirements.txt")
        checks_failed += 1

# ============ CHECK 3: Environment Variables ============
print("\n3️⃣  Environment Variables")
print("-" * 40)

required_vars = {
    'GROQ_API_KEY': 'Groq API Key (from https://console.groq.com)',
    'DRIVE_FOLDER_ID': 'Google Drive Folder ID',
    'GOOGLE_SERVICE_ACCOUNT_JSON': 'Service Account JSON (from Google Cloud Console)'
}

for var, description in required_vars.items():
    value = os.getenv(var)
    if value:
        if var == 'GOOGLE_SERVICE_ACCOUNT_JSON':
            # Validate it's valid JSON
            try:
                json.loads(value)
                print(f"✅ {var}")
                print(f"   └─ Valid JSON format")
                checks_passed += 1
            except:
                print(f"❌ {var}")
                print(f"   └─ Invalid JSON format")
                checks_failed += 1
        else:
            # Just check it's not empty
            if len(value) > 5:
                print(f"✅ {var}")
                print(f"   └─ {description}")
                checks_passed += 1
            else:
                print(f"❌ {var}")
                print(f"   └─ Value too short")
                checks_failed += 1
    else:
        print(f"❌ {var}")
        print(f"   └─ {description}")
        print(f"   └─ Add to .env file")
        checks_failed += 1

# ============ CHECK 4: .env File ============
print("\n4️⃣  Configuration File")
print("-" * 40)
if Path('.env').exists():
    print(f"✅ .env file found")
    with open('.env', 'r') as f:
        env_lines = len([l for l in f if l.strip() and not l.startswith('#')])
    print(f"   └─ {env_lines} configuration(s) set")
    checks_passed += 1
else:
    print(f"❌ .env file not found")
    print(f"   └─ Copy .env.example to .env")
    print(f"   └─ Fill in your API keys")
    checks_failed += 1

# ============ CHECK 5: Google Drive Connection ============
print("\n5️⃣  Google Drive Connection")
print("-" * 40)
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    if service_account_json:
        try:
            service_account_info = json.loads(service_account_json)
            credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Try to list files in the target folder
            folder_id = os.getenv("DRIVE_FOLDER_ID")
            if folder_id:
                try:
                    results = service.files().list(
                        q=f"'{folder_id}' in parents and trashed=false",
                        spaces='drive',
                        pageSize=1,
                        fields='files(id, name)'
                    ).execute()
                    
                    file_count = len(results.get('files', []))
                    print(f"✅ Connected to Google Drive")
                    print(f"   └─ Folder accessible")
                    print(f"   └─ Found {file_count} file(s) in folder")
                    checks_passed += 1
                except Exception as e:
                    print(f"❌ Cannot access folder")
                    print(f"   └─ Error: {str(e)}")
                    print(f"   └─ Verify:")
                    print(f"      - DRIVE_FOLDER_ID is correct")
                    print(f"      - Service account is shared on folder")
                    print(f"      - Folder has files")
                    checks_failed += 1
            else:
                print(f"❌ DRIVE_FOLDER_ID not set")
                checks_failed += 1
        
        except json.JSONDecodeError:
            print(f"❌ GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON")
            checks_failed += 1
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            checks_failed += 1
    else:
        print(f"❌ GOOGLE_SERVICE_ACCOUNT_JSON not set")
        checks_failed += 1

except ImportError as e:
    print(f"⚠️  Cannot check (missing package: {str(e)})")
    print(f"   └─ Run: pip install -r requirements.txt")

# ============ CHECK 6: LLM API ============
print("\n6️⃣  LLM API Connection")
print("-" * 40)
try:
    from langchain_groq import ChatGroq
    
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            llm = ChatGroq(
                model="mixtral-8x7b-32768",
                api_key=groq_key,
                temperature=0.3,
            )
            
            # Try to invoke the model
            response = llm.invoke("What is 2+2?")
            
            print(f"✅ Groq API Connected")
            print(f"   └─ Model: mixtral-8x7b-32768")
            print(f"   └─ Test response: {str(response.content)[:50]}...")
            checks_passed += 1
        
        except Exception as e:
            print(f"❌ Groq API Error")
            print(f"   └─ {str(e)}")
            print(f"   └─ Verify GROQ_API_KEY is valid")
            checks_failed += 1
    else:
        print(f"❌ GROQ_API_KEY not set")
        checks_failed += 1

except ImportError:
    print(f"⚠️  Cannot check (missing package)")
    print(f"   └─ Run: pip install langchain-groq")

# ============ CHECK 7: File Structure ============
print("\n7️⃣  Project Structure")
print("-" * 40)
required_files = {
    'main.py': 'FastAPI Backend',
    'streamlit_app.py': 'Streamlit Frontend',
    'requirements.txt': 'Dependencies',
    'README.md': 'Documentation',
}

for filename, description in required_files.items():
    if Path(filename).exists():
        print(f"✅ {filename}")
        print(f"   └─ {description}")
        checks_passed += 1
    else:
        print(f"❌ {filename}")
        print(f"   └─ Missing: {description}")
        checks_failed += 1

# ============ SUMMARY ============
print("\n" + "=" * 60)
print("📊 SUMMARY")
print("=" * 60)

total = checks_passed + checks_failed
percentage = (checks_passed / total * 100) if total > 0 else 0

print(f"\n✅ Passed:  {checks_passed}")
print(f"❌ Failed:  {checks_failed}")
print(f"📈 Score:   {percentage:.0f}%")

if checks_failed == 0:
    print("\n🎉 All checks passed! You're ready to go!")
    print("\nNext steps:")
    print("1. Terminal 1: python main.py")
    print("2. Terminal 2: streamlit run streamlit_app.py")
    print("3. Test at http://localhost:8501")
    sys.exit(0)
else:
    print(f"\n⚠️  {checks_failed} issue(s) to fix before proceeding")
    print("\nFix the issues above, then run this script again")
    sys.exit(1)
