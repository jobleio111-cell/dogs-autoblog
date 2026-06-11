import requests
import base64
import os

TOKEN = "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"
OWNER = "jobleio111-cell"
REPO = "dogs-autoblog"
BRANCH = "main"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def update_file(local_path, repo_path):
    # 1. Read local file
    with open(local_path, "rb") as f:
        content = f.read()
    encoded_content = base64.b64encode(content).decode("utf-8")
    
    # 2. Get file SHA from GitHub (to allow update)
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{repo_path}?ref={BRANCH}"
    r = requests.get(url, headers=HEADERS)
    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]
    elif r.status_code == 404:
        pass # File doesn't exist, will create
    else:
        print(f"Error getting {repo_path}: {r.status_code} {r.text}")
        return
        
    # 3. Update/Create file
    data = {
        "message": f"Updated {repo_path} via API (Fix configs & Add Make.com Pinterest Markers)",
        "content": encoded_content,
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha
        
    put_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{repo_path}"
    put_r = requests.put(put_url, headers=HEADERS, json=data)
    
    if put_r.status_code in [200, 201]:
        print(f"✅ Success! {repo_path} pushed to GitHub!")
    else:
        print(f"❌ Failed to push {repo_path}: {put_r.status_code} {put_r.text}")

if __name__ == "__main__":
    print("Pushing files to GitHub...")
    update_file(".github/workflows/auto_blog.yml", ".github/workflows/auto_blog.yml")
    print("Done!")
