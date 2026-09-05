import os
import subprocess

BASE_DIR = r"c:\Users\ksvik\Projects\Agam-Lang"

repos = [
    'agam',
    '.github',
    'agamlab',
    'agam-lang.github.io',
    'std',
    'registry-index',
    'sdk-packs',
    'rfcs',
    'agam-vscode',
    'agam-intellij',
    'playground',
    'examples',
    'benchmarks',
    'governance'
]

for local_dir in repos:
    repo_path = os.path.join(BASE_DIR, local_dir)
    git_dir = os.path.join(repo_path, '.git')
    
    if not os.path.exists(repo_path) or not os.path.exists(git_dir):
        continue
        
    print(f"==========================================")
    print(f"Syncing & Pushing {local_dir}...")
    
    try:
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        commit_res = subprocess.run(["git", "commit", "-m", "docs: update documentation & agent literature rules"], cwd=repo_path, capture_output=True, text=True)
        if "nothing to commit" in commit_res.stdout or "nothing to commit" in commit_res.stderr:
            print(f"  {local_dir}: Nothing new to commit.")
        else:
            print(f"  {local_dir}: Committed changes.")
            
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=repo_path, capture_output=True, text=True)
        if push_res.returncode == 0:
            print(f"  {local_dir}: Successfully pushed to origin/main.")
        else:
            print(f"  {local_dir}: Push output: {push_res.stdout.strip()} {push_res.stderr.strip()}")
            
    except Exception as e:
        print(f"Error processing {local_dir}: {e}")

print("==========================================")
print("Finished remote sync process across all organization repositories.")
