import subprocess
import sys

def run_git_command(command, ignore_errors=False):
    """Runs a terminal command and stops the script if it fails."""
    try:
        # Using shell=True for simple string commands
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"\n❌ My guy, something broke while running: {command}")
            print(f"Error details: {e}")
            sys.exit(1)

def main():
    print("🚀 HemLex Auto-Git Pusher 🚀\n")
    
    # 1. Get the Repo URL
    repo_url = input("Drop your GitHub Repo URL here: ").strip()
    if not repo_url:
        print("Bruh, I need a URL to know where to send this. Try again.")
        sys.exit(1)

    # 2. Get the Commit Message
    commit_msg = input("Commit message (press Enter for 'Auto-commit'): ").strip()
    if not commit_msg:
        commit_msg = "Auto-commit: grinding on the code"

    print("\n🔥 Firing up the git commands...")

    # 3. Execute the Git workflow
    run_git_command("git init")
    run_git_command("git add .")
    
    # We ignore errors on commit just in case there are no new changes to commit
    run_git_command(f'git commit -m "{commit_msg}"', ignore_errors=True)
    
    run_git_command("git branch -M main")
    
    # Remove existing origin just in case you ran this before and made a mistake
    run_git_command("git remote remove origin", ignore_errors=True)
    
    # Link the new URL and push
    run_git_command(f"git remote add origin {repo_url}")
    
    print("\n⏳ Pushing code to the cloud...")
    run_git_command("git push -u origin main")

    print("\n✅ Code shipped successfully. Safe and sound!")

if __name__ == "__main__":
    main()