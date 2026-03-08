import os
import sys
import subprocess
import time

def test_startup():
    print("Testing backend startup...")
    # Add root to python path to find 'app'
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    # Try starting uvicorn on a random port
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8002", "--host", "127.0.0.1"],
        cwd=os.path.join(os.getcwd(), "backend"),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(3) # Wait for it to crash or start
    
    if process.poll() is not None:
        # It crashed
        stdout, stderr = process.communicate()
        print("Backend failed to start!")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        sys.exit(1)
    else:
        print("Backend started successfully on port 8002!")
        process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    test_startup()
