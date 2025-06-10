import os
import subprocess
import importlib
from pathlib import Path

def run(command, cwd=None):
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", f"[ERROR] {e}"

def check_git_configured():
    # Check git username and email
    name, err1 = run("git config user.name")
    email, err2 = run("git config user.email")
    if not name or not email:
        raise EnvironmentError("[!] Git is not configured. Please set your name and email using:\n"
                               "    git config --global user.name \"Your Name\"\n"
                               "    git config --global user.email \"you@example.com\"")

def check_gh_logged_in():
    out, err = run("gh auth status")
    if "Logged in" not in out:
        raise EnvironmentError("[!] GitHub CLI is not logged in.\n"
                               "    Please run: gh auth login")

def init_git_repo(project_path):
    # Check if git repo exists
    if not Path(project_path, ".git").exists():
        print("[*] Initializing Git repository...")
        _, err = run("git init -b main", cwd=project_path)
        if err and "unknown option" in err:
            # Older git versions don't support -b flag
            _, err = run("git init", cwd=project_path)
            if err:
                raise RuntimeError(f"[!] Git init failed: {err}")
            # Set branch to main manually
            _, err = run("git checkout -b main", cwd=project_path)
            if err:
                print("[!] Warning: Could not create 'main' branch. Using default branch.")
        elif err:
            raise RuntimeError(f"[!] Git init failed: {err}")
    else:
        # Repository exists, check current branch
        current_branch, err = run("git rev-parse --abbrev-ref HEAD", cwd=project_path)
        if err:
            print("[!] Warning: Could not determine current branch.")
        elif current_branch == "master":
            # Try to rename master to main if on master branch
            _, err = run("git branch -m master main", cwd=project_path)
            if err:
                print("[!] Warning: Could not rename 'master' branch to 'main'. Continuing with 'master'.")
            else:
                print("[*] Renamed 'master' branch to 'main'.")
        
    # Create a README.md file if it doesn't exist to ensure we have something to commit
    readme_path = Path(project_path, "README.md")
    if not readme_path.exists():
        print("[*] Creating README.md file...")
        with open(readme_path, 'w') as f:
            f.write(f"# {Path(project_path).name}\n\nProject created via CodeGuard security scan and automation.\n")

def setup_repo_with_gh(project_path, repo_name, github_username):
    print(f"[*] Creating GitHub repo: {repo_name}...")
    # Create repo without --push flag to avoid issues when no commits exist
    _, err = run(f'gh repo create {github_username}/{repo_name} --public --source=. --remote=origin', cwd=project_path)
    if err and "already exists" not in err:
        raise RuntimeError(f"[!] GitHub repo creation failed: {err}")

def force_initial_commit(project_path):
    """Ensure the repository has at least one commit, even if there are no changes."""
    # Check if there are any commits already
    has_commits, _ = run("git rev-parse --verify HEAD 2>/dev/null || echo no", cwd=project_path)
    
    if has_commits == "no":
        print("[*] Creating initial commit...")
        # Add all files
        _, err = run("git add .", cwd=project_path)
        if err:
            raise RuntimeError(f"[!] Git add failed: {err}")
            
        # Force an initial commit even if there are no changes
        _, err = run('git commit -m "Initial commit from CodeGuard" --allow-empty', cwd=project_path)
        if err and "nothing to commit" not in err:
            raise RuntimeError(f"[!] Initial commit failed: {err}")
        return True
    return False

def git_add_commit_push(project_path, commit_message="Update from CodeGuard"):
    """Add all changes, commit them, and push to the remote repository."""
    print("[*] Adding and committing changes...")
    _, err = run("git add .", cwd=project_path)
    if err:
        raise RuntimeError(f"[!] Git add failed: {err}")

    _, err = run(f'git commit -m "{commit_message}"', cwd=project_path)
    if "nothing to commit" in err:
        print("[*] Nothing new to commit.")
    elif err:
        raise RuntimeError(f"[!] Git commit failed: {err}")

def push_to_remote(project_path):
    """Push changes to the remote repository, handling different branch names."""
    print("[*] Pushing to GitHub...")
    
    # Get current branch name
    branch, err = run("git rev-parse --abbrev-ref HEAD", cwd=project_path)
    if err:
        # Default to main if we can't determine branch
        branch = "main"
    
    # Try pushing to the current branch
    out, err = run(f"git push -u origin {branch}", cwd=project_path)
    if "error" in (err or "").lower():
        # If current branch failed and isn't main or master, try main
        if branch not in ["main", "master"]:
            print(f"[!] Push to '{branch}' failed. Trying 'main'...")
            out, err = run("git push -u origin main", cwd=project_path)
            
            # If main failed, try master
            if "error" in (err or "").lower():
                print("[!] Push to 'main' failed. Trying 'master'...")
                out, err = run("git push -u origin master", cwd=project_path)
                if "error" in (err or "").lower():
                    raise RuntimeError(f"[!] Git push failed: {err}")
        else:
            # Current branch is main, try master
            other_branch = "master" if branch == "main" else "main"
            print(f"[!] Push to '{branch}' failed. Trying '{other_branch}'...")
            out, err = run(f"git push -u origin {other_branch}", cwd=project_path)
            if "error" in (err or "").lower():
                raise RuntimeError(f"[!] Git push failed: {err}")
                
    print("[*] Push successful.")

def auto_push(project_path, repo_name, github_username):
    """Fully automated Git workflow to push code to GitHub."""
    try:
        # Step 1: Validate environment
        check_git_configured()
        check_gh_logged_in()

        # Step 2: Initialize repository if needed
        init_git_repo(project_path)
        
        # Step 3: Ensure there's at least one commit
        is_first_commit = force_initial_commit(project_path)
        
        # Step 4: Add and commit any changes (if not the first commit)
        if not is_first_commit:
            git_add_commit_push(project_path)
        
        # Step 5: Setup remote if needed
        remotes, _ = run("git remote", cwd=project_path)
        
        if "origin" not in remotes:
            # No remote exists, create one
            setup_repo_with_gh(project_path, repo_name, github_username)
            # Push to new remote
            print("[*] Pushing to newly created GitHub repository...")
            push_to_remote(project_path)
        else:
            # Remote exists, just push
            print("[*] Pushing to existing GitHub repository...")
            push_to_remote(project_path)
            
        print("[*] Code successfully pushed to GitHub.")
        return True
    except Exception as e:
        print(f"[!] Auto-push failed: {e}")
        return False

# For manual testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python3 git_auto_push.py <project_path> <repo_name> <github_username>")
    else:
        try:
            auto_push(sys.argv[1], sys.argv[2], sys.argv[3])
            print("[✓] Push completed.")
        except Exception as e:
            print(str(e))
            exit(1)
