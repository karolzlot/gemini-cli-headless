
import subprocess
import os
import sys

def run_wsl_command(command, check=True):
    """Executes a command inside the default WSL distribution."""
    try:
        result = subprocess.run(
            ["wsl", "bash", "-c", command],
            capture_output=False,
            text=True,
            check=check
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ WSL Command Failed with exit code {e.returncode}")
        return False

if __name__ == "__main__":
    print("🚀 Starting WSL Integration Test Runner...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ FATAL: GEMINI_API_KEY must be set in your Windows environment.")
        sys.exit(1)

    # 1. Check Node.js version in WSL
    print("🟢 Checking Node.js version in WSL...")
    # gemini-cli requires Node 20+ for certain regex features (/v flag)
    node_check = "node -v"
    try:
        node_version_output = subprocess.check_output(["wsl", "bash", "-c", node_check], text=True).strip()
        print(f"Detected Node version in WSL: {node_version_output}")
        major_version = int(node_version_output.lstrip('v').split('.')[0])
        if major_version < 20:
            print(f"⚠️  Node.js version {major_version} is too old. gemini-cli requires Node 20+.")
            print("Please upgrade node inside your WSL (e.g. using nvm or nodesource).")
            # We don't auto-upgrade node as it requires sudo/user intervention
            sys.exit(1)
    except Exception as e:
        print(f"❌ Could not determine Node version in WSL: {e}")
        sys.exit(1)

    # 2. Ensure gemini-cli is installed in WSL
    print("📦 Checking gemini-cli installation in WSL...")
    if not run_wsl_command("gemini --version", check=False):
        print("⚠️  gemini-cli not found in WSL. Attempting to install...")
        if not run_wsl_command("npm install -g @google/gemini-cli"):
            print("❌ Failed to install gemini-cli in WSL. Please ensure npm/node is installed in your WSL distribution.")
            sys.exit(1)

    # 3. Run the integration tests
    print("🧪 Executing Integration Test Battery inside WSL...")
    
    current_dir = os.getcwd().replace('\\', '/').replace('C:', '/mnt/c').replace('c:', '/mnt/c')
    
    wsl_test_cmd = (
        f"export GEMINI_API_KEY='{api_key}'; "
        f"cd {current_dir}; "
        f"export PYTHONPATH='.'; "
        f"python3 tests/run_integration_tests.py gemini-3-flash-preview"
    )

    if run_wsl_command(wsl_test_cmd):
        print("\n✅ WSL Integration Tests Passed!")
        sys.exit(0)
    else:
        print("\n❌ WSL Integration Tests Failed!")
        sys.exit(1)
