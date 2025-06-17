import os
import sys
import subprocess
import json # Import json for proper string escaping

# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m' # Corrected and ensured this is present

def run_command(command, check_error=True, admin_needed=False):
    """
    Executes a shell command and prints its output.
    If admin_needed is True, it tries to use sudo on Linux/macOS,
    correctly handling redirections by wrapping the command in 'sh -c'.
    """
    full_command = command
    if admin_needed and (sys.platform.startswith('linux') or sys.platform == 'darwin'):
        # For commands requiring sudo with redirections/pipes, wrap in 'sh -c'.
        # json.dumps will correctly escape the command string for shell interpretation.
        full_command = f"sudo sh -c {json.dumps(command)}"
        print(f"{Colors.YELLOW}Administrative privileges may be required for: {full_command}{Colors.RESET}")

    try:
        print(f"{Colors.BLUE}Executing: {full_command}{Colors.RESET}")
        process = subprocess.run(full_command, shell=True, check=check_error, text=True, capture_output=True)
        print(f"{Colors.GREEN}Output:\n{process.stdout}{Colors.RESET}")
        if process.stderr:
            print(f"{Colors.YELLOW}Error Output:\n{process.stderr}{Colors.RESET}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Command failed with error code {e.returncode}:{Colors.RESET}")
        print(f"{Colors.RED}{e.stderr}{Colors.RESET}")
        return False
    except FileNotFoundError:
        print(f"{Colors.RED}Error: Command '{full_command.split()[0]}' not found. Is it in your PATH?{Colors.RESET}")
        return False

def install_dependencies():
    """Installs required Python packages."""
    print(f"\n{Colors.CYAN}--- Installing Python Dependencies ---{Colors.RESET}")
    required_packages = ["requests"]
    for package in required_packages:
        try:
            __import__(package)
            print(f"{Colors.GREEN}'{package}' is already installed.{Colors.RESET}")
        except ImportError:
            print(f"{Colors.YELLOW}'{package}' not found. Installing now...{Colors.RESET}")
            if run_command(f"{sys.executable} -m pip install {package}"):
                print(f"{Colors.GREEN}'{package}' installed successfully!{Colors.RESET}")
            else:
                print(f"{Colors.RED}Failed to install '{package}'. Please try installing it manually: 'pip install {package}'{Colors.RESET}")
                return False
    return True

def setup_api_key():
    """Guides the user to set up their Gemini API key."""
    print(f"\n{Colors.CYAN}--- Setting up Gemini API Key ---{Colors.RESET}")
    print(f"You can get your Gemini API key from: {Colors.UNDERLINE}https://aistudio.google.com/{Colors.RESET}")
    print(f"Please log in with your Google account and follow the prompts to create a new API key.")

    api_key = input(f"{Colors.BOLD}Paste your Gemini API key here: {Colors.RESET}").strip()

    if not api_key:
        print(f"{Colors.RED}API key cannot be empty. Please restart the script and provide a key.{Colors.RESET}")
        return False

    # --- Attempt to set environment variable (cross-platform persistent where possible) ---
    if sys.platform.startswith('linux') or sys.platform == 'darwin': # Linux or macOS
        shell_profile = os.path.expanduser("~/.bashrc")
        if os.path.exists(os.path.expanduser("~/.zshrc")): # Prefer zshrc if it exists
            shell_profile = os.path.expanduser("~/.zshrc")

        print(f"\n{Colors.CYAN}Attempting to set GEMINI_API_KEY persistently in {shell_profile}...{Colors.RESET}")
        try:
            # Using 'a' mode to append, preventing overwriting if it already exists
            with open(shell_profile, 'a') as f:
                f.write(f'\nexport GEMINI_API_KEY="{api_key}"\n')
            print(f"{Colors.GREEN}API key added to {shell_profile}.{Colors.RESET}")
            print(f"{Colors.YELLOW}Please run '{Colors.BOLD}source {shell_profile}{Colors.RESET}{Colors.YELLOW}' or restart your terminal for changes to take effect.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Failed to write to {shell_profile}: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}You might need to set the environment variable manually for each session:{Colors.RESET}")
            print(f"{Colors.YELLOW}export GEMINI_API_KEY='{api_key}'{Colors.RESET}")

    elif sys.platform == 'win32': # Windows
        print(f"\n{Colors.CYAN}Attempting to set GEMINI_API_KEY as a persistent user environment variable (Windows)...{Colors.RESET}")
        if run_command(f'setx GEMINI_API_KEY "{api_key}"'):
            print(f"{Colors.GREEN}API key set persistently for your user.{Colors.RESET}")
            print(f"{Colors.YELLOW}You may need to restart your command prompt/PowerShell for changes to take effect.{Colors.RESET}")
        else:
            print(f"{Colors.RED}Failed to set API key persistently using setx.{Colors.RESET}")
            print(f"{Colors.YELLOW}You'll need to set it manually for each session (or through System Properties):{Colors.RESET}")
            print(f"{Colors.YELLOW}set GEMINI_API_KEY='{api_key}' (CMD){Colors.RESET}")
            print(f"{Colors.YELLOW}$env:GEMINI_API_KEY='{api_key}' (PowerShell){Colors.RESET}")
    else:
        print(f"{Colors.RED}Unsupported operating system for automated environment variable setup.{Colors.RESET}")
        print(f"{Colors.YELLOW}Please set the GEMINI_API_KEY environment variable manually.{Colors.RESET}")
        print(f"{Colors.YELLOW}Example: export GEMINI_API_KEY='{api_key}'{Colors.RESET}")


    # --- Attempt to save API key to /usr/share/vortexai/apikey.txt as fallback ---
    api_key_dir = "/usr/share/vortexai"
    api_key_file_path = os.path.join(api_key_dir, "apikey.txt")

    print(f"\n{Colors.CYAN}Attempting to save API key to fallback file: {api_key_file_path}{Colors.RESET}")

    # Create directory if it doesn't exist, requires admin on /usr/share
    if not os.path.exists(api_key_dir):
        print(f"{Colors.YELLOW}Creating directory '{api_key_dir}'...{Colors.RESET}")
        # mkdir -p already handles existing dirs and parent creation
        if not run_command(f"mkdir -p {api_key_dir}", admin_needed=True):
            print(f"{Colors.RED}Failed to create directory '{api_key_dir}'. Please create it manually with sufficient permissions.{Colors.RESET}")
            return False
    
    # Write API key to file, requires admin for /usr/share
    # Use echo to file with sudo for reliability, escaping the key to prevent shell injection
    # The 'echo' command within 'sh -c' correctly handles the redirection.
    # The API key itself is directly placed into the string without needing replace, as json.dumps
    # will handle the necessary quoting/escaping for the outer shell command.
    if run_command(f"echo \"{api_key}\" > {api_key_file_path}", admin_needed=True):
        print(f"{Colors.GREEN}API key successfully saved to '{api_key_file_path}'.{Colors.RESET}")
        # Set less restrictive permissions (read-only for group/others)
        # Change chmod 600 to chmod 644
        if run_command(f"chmod 644 {api_key_file_path}", admin_needed=True): # Changed to 644
            print(f"{Colors.GREEN}Permissions for '{api_key_file_path}' set to 644 (owner read/write, others read).{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}Warning: Failed to set permissions for '{api_key_file_path}'. Please set them manually to 644 for security.{Colors.RESET}")
    else:
        print(f"{Colors.RED}Failed to save API key to '{api_key_file_path}'.{Colors.RESET}")
        print(f"{Colors.YELLOW}VortexAI will rely solely on the environment variable if this failed.{Colors.RESET}")
        return False # Indicate that file-based setup might not be fully successful.

    return True # Indicate overall success of API key setup (env var or file).


def main_installation():
    print(f"{Colors.BOLD}{Colors.MAGENTA}--- VortexAI Installation Script ---{Colors.RESET}")

    if not install_dependencies():
        print(f"\n{Colors.RED}Installation failed due to dependency issues. Please resolve them and try again.{Colors.RESET}")
        sys.exit(1)

    api_key_setup_successful = setup_api_key()

    if not api_key_setup_successful:
        print(f"\n{Colors.RED}API Key setup encountered issues. VortexAI may not function correctly without a valid API key.{Colors.RESET}")
        # Do not exit here; the user might fix it manually or env var might still work.
    else:
        print(f"\n{Colors.BOLD}{Colors.GREEN}VortexAI installation complete!{Colors.RESET}")
        print(f"{Colors.GREEN}You can now run the main tool using: python3 vortexai.py -r <file> -q \"<query>\"{Colors.RESET}")
        print(f"{Colors.YELLOW}Remember to restart your terminal if you set the API key persistently.{Colors.RESET}")

if __name__ == "__main__":
    main_installation()

