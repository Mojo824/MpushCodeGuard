import os
import subprocess
from pathlib import Path
import json
import time


def run(command, cwd=None):
    """Run a command and return (stdout, stderr)."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", f"[ERROR] {e}"


def run_rc(command, cwd=None):
    """Run a command and return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", f"[ERROR] {e}", 1


def check_git_configured():
    """Verify git username and email are set."""
    name, err1 = run("git config user.name")
    email, err2 = run("git config user.email")
    if not name or not email:
        raise EnvironmentError("[!] Git is not configured. Please set your name and email using:\n"
                               "    git config --global user.name \"Your Name\"\n"
                               "    git config --global user.email \"you@example.com\"")


def check_gh_logged_in():
    """Check if GitHub CLI is logged in, or fallback to SSH auth."""
    out, err = run("gh auth status")
    combined = (out + "\n" + err).lower()
    if any(keyword in combined for keyword in ("logged in", "logged into", "you are logged in")):
        return

    # Fallback: check SSH authentication
    ssh_out, ssh_err = run("ssh -T -o BatchMode=yes git@github.com")
    ssh_combined = (ssh_out + "\n" + ssh_err).lower()
    if "successfully authenticated" in ssh_combined or ssh_combined.strip().startswith("hi "):
        print("[*] SSH authentication to GitHub confirmed; proceeding without gh login.")
        return

    raise EnvironmentError("[!] GitHub CLI is not logged in.\n"
                           "    Please run: gh auth login")


def init_git_repo(project_path):
    """Initialize a git repository if it doesn't exist."""
    if not Path(project_path, ".git").exists():
        print("[*] Initializing Git repository...")
        _, err = run("git init -b main", cwd=project_path)
        if err and "unknown option" in err:
            # Older git versions don't support -b flag
            _, err = run("git init", cwd=project_path)
            if err:
                raise RuntimeError(f"[!] Git init failed: {err}")
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
            _, err = run("git branch -m master main", cwd=project_path)
            if err:
                print("[!] Warning: Could not rename 'master' branch to 'main'.")
            else:
                print("[*] Renamed 'master' branch to 'main'.")

    # Ensure README.md exists
    readme_path = Path(project_path, "README.md")
    if not readme_path.exists():
        print("[*] Creating README.md file...")
        with open(readme_path, 'w') as f:
            f.write(f"# {Path(project_path).name}\n\nProject created via CodeGuard security scan and automation.\n")


def repo_exists_on_github(repo_name, github_username):
    """Check if a repository already exists on GitHub using return code."""
    out, err, rc = run_rc(f'gh repo view {github_username}/{repo_name}')
    # Return code 0 means repo exists; non-zero means it doesn't
    exists = rc == 0
    if exists:
        print(f"[✓] Confirmed: Repository {github_username}/{repo_name} exists on GitHub.")
    else:
        print(f"[!] Repository {github_username}/{repo_name} does NOT exist on GitHub yet.")
    return exists


def configure_git_remote_ssh(project_path, repo_name, github_username):
    """Configure the git remote to use SSH only."""
    ssh_url = f"git@github.com:{github_username}/{repo_name}.git"

    # Remove existing origin if present
    run(f"git remote remove origin", cwd=project_path)
    

    # Add origin with SSH URL
    out, err = run(f"git remote add origin {ssh_url}", cwd=project_path)
    out, err = run(f"git remote set-url origin {ssh_url}", cwd=project_path)
    

    # Verify
    remotes, _ = run("git remote -v", cwd=project_path)
    print(f"[*] Remote configured: {ssh_url}")
    print(remotes)


def setup_repo_with_gh(project_path, repo_name, github_username):
    """Create a GitHub repo if it doesn't exist."""
    print(f"[*] Checking if GitHub repo exists: {repo_name}...")

    if repo_exists_on_github(repo_name, github_username):
        print(f"[✓] Repository {github_username}/{repo_name} already exists on GitHub.")
        configure_git_remote_ssh(project_path, repo_name, github_username)
        return True

    print(f"[*] Repository does not exist. Creating {github_username}/{repo_name} on GitHub...")
    # Use echo "y" to auto-confirm the gh repo create prompt
    out, err, rc = run_rc(f'echo "y" | gh repo create {repo_name} --public --source=.', cwd=project_path)
    time.sleep(10)  # Wait for the repository to be created
    
    # Verify if repo was actually created by checking it again
    if repo_exists_on_github(repo_name, github_username):
        print(f"[✓] Repository {github_username}/{repo_name} created successfully on GitHub.")
        configure_git_remote_ssh(project_path, repo_name, github_username)
        return True
    
    # If repo still doesn't exist, check for auth errors
    if rc != 0:
        if "authentication" in err.lower() or "token" in err.lower():
            raise RuntimeError(f"[AUTH_FAILED] GitHub authentication failed: {err}")
        raise RuntimeError(f"[!] GitHub repo creation failed: {err}")
    
    # Repo check failed but rc was 0 - something is wrong
    raise RuntimeError(f"[!] GitHub repo creation returned success but repo still not found.")


def force_initial_commit(project_path, add_path=None):
    """Ensure the repository has at least one commit."""
    has_commits, _ = run("git rev-parse --verify HEAD 2>/dev/null || echo no", cwd=project_path)

    if has_commits == "no":
        print("[*] Creating initial commit...")
        if add_path:
            _, err, rc = run_rc(f"git add -- \"{add_path}\"", cwd=project_path)
            if rc != 0:
                raise RuntimeError(f"[!] Git add failed for {add_path}: {err}")
        else:
            _, err, rc = run_rc("git add .", cwd=project_path)
            if rc != 0:
                raise RuntimeError(f"[!] Git add failed: {err}")

        _, err, rc = run_rc('git commit -m "Initial commit from CodeGuard" --allow-empty', cwd=project_path)
        if rc != 0 and "nothing to commit" not in (err or ""):
            raise RuntimeError(f"[!] Initial commit failed: {err}")
        return True
    return False


def git_add_commit_push(project_path, commit_message="Update from CodeGuard", add_path=None):
    """Add, commit, and optionally push changes."""
    print("[*] Adding and committing changes...")
    if add_path:
        out, err, rc = run_rc(f"git add -- \"{add_path}\"", cwd=project_path)
        if rc != 0:
            raise RuntimeError(f"[!] Git add failed for {add_path}: {err}")
    else:
        out, err, rc = run_rc("git add .", cwd=project_path)
        if rc != 0:
            raise RuntimeError(f"[!] Git add failed: {err}")

    out, err, rc = run_rc(f'git commit -m "{commit_message}"', cwd=project_path)
    combined_output = (out + "\n" + (err or "")).lower()
    # Don't raise error if there's nothing to commit - that's OK
    if rc != 0 and "nothing to commit" not in combined_output:
        raise RuntimeError(f"[!] Git commit failed: {err}")

    if rc == 0:
        print("[*] Changes committed successfully.")
    elif "nothing to commit" in combined_output:
        print("[*] Nothing new to commit.")


def push_to_remote(project_path, repo_name=None, github_username=None, retry_count=1):
    """Push changes to the remote repository via SSH."""
    print("[*] Pushing to GitHub...")

    # Get current branch
    branch, err = run("git rev-parse --abbrev-ref HEAD", cwd=project_path)
    if err or not branch:
        branch = "main"

    attempt = 0
    max_attempts = retry_count + 1

    while attempt < max_attempts:
        attempt += 1
        if attempt > 1:
            print(f"[*] Retry attempt {attempt - 1} of {retry_count}...")

        # Simple push to origin
        out, err = run(f"git push -u origin {branch}", cwd=project_path)
        combined = (out + "\n" + (err or "")).lower()

        # Check for auth failure
        if any(auth_msg in combined for auth_msg in ["authentication failed", "permission denied", "401", "403", "not authorized"]):
            if attempt < max_attempts:
                print("[!] Authentication failed. Retrying...")
                _, auth_err = run("gh auth logout && gh auth login")
                continue
            else:
                raise RuntimeError(f"[AUTH_FAILED] GitHub authentication failed after {retry_count} retries.")

        # Check for other errors
        if "error" in (err or "").lower():
            if branch not in ["main", "master"]:
                print(f"[!] Push to '{branch}' failed. Trying 'main'...")
                out, err = run("git push -u origin main", cwd=project_path)
                if "error" in (err or "").lower():
                    print("[!] Push to 'main' failed. Trying 'master'...")
                    out, err = run("git push -u origin master", cwd=project_path)
                    if "error" in (err or "").lower():
                        raise RuntimeError(f"[!] Git push failed: {err}")
            else:
                other_branch = "master" if branch == "main" else "main"
                print(f"[!] Push to '{branch}' failed. Trying '{other_branch}'...")
                out, err = run(f"git push -u origin {other_branch}", cwd=project_path)
                if "error" in (err or "").lower():
                    raise RuntimeError(f"[!] Git push failed: {err}")

        print("[*] Push successful.")
        return True

    return False


def auto_push(project_path, repo_name, github_username):
    """Fully automated Git workflow to push code to GitHub.

    Returns:
        dict: {'success': bool, 'push_done': bool, 'error': str, 'auth_failed': bool, 'message': str}
    """
    try:
        check_git_configured()
        check_gh_logged_in()

        # Handle single file vs directory
        single_file = False
        add_path = None
        proj_path_obj = Path(project_path)
        if proj_path_obj.is_file():
            single_file = True
            add_path = proj_path_obj.name
            working_dir = str(proj_path_obj.parent)
        else:
            working_dir = project_path

        # Initialize repo in working_dir
        init_git_repo(working_dir)

        # Create initial commit
        is_first_commit = force_initial_commit(working_dir, add_path=add_path)

        # Add and commit changes if not first commit
        if not is_first_commit:
            git_add_commit_push(working_dir, add_path=add_path)

        # Check if repository exists on GitHub, create if it doesn't
        print(f"[*] Checking if repository {github_username}/{repo_name} exists on GitHub...")
        if repo_exists_on_github(repo_name, github_username):
            print(f"[✓] Repository already exists on GitHub.")
            configure_git_remote_ssh(working_dir, repo_name, github_username)
            print("[*] Pushing to existing GitHub repository...")
        else:
            print(f"[*] Repository does not exist. Creating {github_username}/{repo_name}...")
            setup_repo_with_gh(working_dir, repo_name, github_username)
            print("[*] Pushing to newly created GitHub repository...")

        # Push to remote
        push_to_remote(working_dir, repo_name=repo_name, github_username=github_username, retry_count=1)

        print("[*] Code successfully pushed to GitHub.")
        return {
            'success': True,
            'push_done': True,
            'error': None,
            'auth_failed': False,
            'message': 'Code successfully pushed to GitHub.'
        }

    except RuntimeError as e:
        error_msg = str(e)
        auth_failed = "[AUTH_FAILED]" in error_msg
        if auth_failed:
            error_msg = error_msg.replace("[AUTH_FAILED] ", "")

        print(f"[!] Auto-push failed: {error_msg}")
        return {
            'success': False,
            'push_done': False,
            'error': error_msg,
            'auth_failed': auth_failed,
            'message': f"Push failed: {error_msg}"
        }
    except Exception as e:
        print(f"[!] Auto-push failed: {e}")
        return {
            'success': False,
            'push_done': False,
            'error': str(e),
            'auth_failed': False,
            'message': f'Push failed: {str(e)}'
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python3 git_auto_push.py <project_path> <repo_name> <github_username>")
    else:
        result = auto_push(sys.argv[1], sys.argv[2], sys.argv[3])
        if result['success']:
            print("[✓] Push completed successfully.")
        else:
            print(f"[!] Push failed: {result['message']}")
            if result['auth_failed']:
                print("[!] Authentication was rejected.")
            exit(1)
