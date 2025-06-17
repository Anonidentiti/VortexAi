import argparse
import os
import json
import requests # Ensure this is installed: pip install requests

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
    UNDERLINE = '\033[4m'

def main():
    """
    Main function to parse arguments, read file, query Gemini AI, and print structured results with colors.
    """
    parser = argparse.ArgumentParser(
        description="Query Gemini AI with content from a file and a custom query string for structured vulnerability analysis."
    )
    parser.add_argument(
        "-r", "--results_file",
        required=True,
        help="Path to the file containing results/content to analyze (e.g., Nmap scan)."
    )
    parser.add_argument(
        "-q", "--query",
        required=True,
        help="The specific question or instruction for the AI (e.g., 'look for vulnerabilities here')."
    )

    args = parser.parse_args()

    # --- 1. Load API Key securely ---
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        # Fallback: Attempt to read API key from a local file
        api_key_file_path = "/usr/share/vortexai/apikey.txt"
        print(f"{Colors.YELLOW}GEMINI_API_KEY environment variable not set. Checking '{api_key_file_path}'...{Colors.RESET}")
        try:
            if os.path.exists(api_key_file_path) and os.path.isfile(api_key_file_path):
                with open(api_key_file_path, 'r', encoding='utf-8') as f:
                    api_key = f.read().strip()
                if not api_key:
                    print(f"{Colors.RED}Error: API key file '{api_key_file_path}' is empty.{Colors.RESET}")
                    return
                else:
                    print(f"{Colors.GREEN}API key successfully loaded from '{api_key_file_path}'.{Colors.RESET}")
            else:
                print(f"{Colors.RED}Error: API key file not found at '{api_key_file_path}'.{Colors.RESET}")
                print(f"{Colors.YELLOW}Please set GEMINI_API_KEY environment variable OR create '{api_key_file_path}' with your API key.{Colors.RESET}")
                return
        except Exception as e:
            print(f"{Colors.RED}Error reading API key from file '{api_key_file_path}': {e}{Colors.RESET}")
            return

    if not api_key: # Final check if key is still not found/loaded
        print(f"{Colors.RED}Fatal Error: No Gemini API key found. Exiting.{Colors.RESET}")
        print(f"{Colors.YELLOW}Please set GEMINI_API_KEY environment variable OR create /usr/share/vortexai/apikey.txt with your API key.{Colors.RESET}")
        return

    # --- 2. Read the content from the specified file ---
    file_path = args.results_file
    if not os.path.exists(file_path):
        print(f"{Colors.RED}Error: File not found at '{file_path}'{Colors.RESET}")
        return
    if not os.path.isfile(file_path):
        print(f"{Colors.RED}Error: Path '{file_path}' is not a file.{Colors.RESET}")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        print(f"{Colors.RED}Error reading file '{file_path}': {e}{Colors.RESET}")
        return

    # --- 3. Prepare the prompt for the AI and define the expected JSON structure ---
    prompt = f"""
Analyze the following content and {args.query}.
Provide your analysis in a structured JSON format. The JSON should be an array of vulnerability objects.
Each vulnerability object must contain:
- "name": A concise name for the vulnerability.
- "description": A short, parsed explanation of the vulnerability.
- "metasploit_modules": An array of suggested Metasploit module paths (e.g., "exploit/windows/smb/ms17_010_eternalblue"). If none, use an empty array.
- "exploit_links": An array of relevant URLs for exploit details or PoCs. If none, use an empty array.
- "other_tools_and_formats": An array of other relevant tools and their likely output formats (e.g., "Nessus (HTML, XML, CSV)", "Nmap (XML, Nmap Script Output)", "Nikto (TXT, HTML)"). If none, use an empty array.

--- Content Start ---
{file_content}
--- Content End ---
"""

    print(f"{Colors.CYAN}Sending structured query to Gemini AI. Please wait...{Colors.RESET}")

    # --- 4. Interact with the Gemini AI with a specific response schema ---
    try:
        chat_history = []
        chat_history.append({"role": "user", "parts": [{"text": prompt}]})

        generation_config = {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "description": {"type": "STRING"},
                        "metasploit_modules": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "exploit_links": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "other_tools_and_formats": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        }
                    },
                    "required": ["name", "description", "metasploit_modules", "exploit_links", "other_tools_and_formats"]
                }
            }
        }

        payload = {
            "contents": chat_history,
            "generationConfig": generation_config
        }
        
        apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}" # Use loaded API key

        response = requests.post(apiUrl, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        ai_response_json = json.loads(result_text)

        # --- Save raw JSON to a .log file ---
        log_file_path = file_path + ".log"
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(ai_response_json, indent=2))
            print(f"{Colors.BLUE}Raw JSON response saved to: {log_file_path}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not save JSON to log file {log_file_path}: {e}{Colors.RESET}")


        # --- Print the AI's structured response in a non-JSON format ---
        print(f"\n{Colors.GREEN}--- Gemini AI Vulnerability Analysis ---{Colors.RESET}")
        if not ai_response_json:
            print(f"{Colors.YELLOW}No vulnerabilities identified or structured response received.{Colors.RESET}")
            return

        for i, vuln in enumerate(ai_response_json):
            print(f"\n{Colors.BOLD}{Colors.GREEN}Vulnerability {i+1}: {vuln.get('name', 'N/A')}{Colors.RESET}")
            print(f"{Colors.CYAN}  Description:{Colors.RESET} {vuln.get('description', 'N/A')}")

            metasploit_modules = vuln.get('metasploit_modules')
            if metasploit_modules:
                print(f"{Colors.MAGENTA}  Metasploit Modules:{Colors.RESET}")
                for module in metasploit_modules:
                    print(f"    - {module}")
            else:
                print(f"{Colors.MAGENTA}  Metasploit Modules:{Colors.RESET} None suggested.")

            other_tools_and_formats = vuln.get('other_tools_and_formats')
            if other_tools_and_formats:
                print(f"{Colors.BLUE}  Other Suggested Tools & Formats:{Colors.RESET}")
                for tool_info in other_tools_and_formats:
                    print(f"    - {tool_info}")
            else:
                print(f"{Colors.BLUE}  Other Suggested Tools & Formats:{Colors.RESET} None suggested.")

            exploit_links = vuln.get('exploit_links')
            if exploit_links:
                print(f"{Colors.YELLOW}  Exploit Links:{Colors.RESET}")
                for link in exploit_links:
                    print(f"    - {link}")
            else:
                print(f"{Colors.YELLOW}  Exploit Links:{Colors.RESET} None provided.")
        
        print(f"\n{Colors.GREEN}--- Analysis Complete ---{Colors.RESET}")


    except requests.exceptions.RequestException as req_err:
        print(f"{Colors.RED}\nError communicating with Gemini API: {req_err}{Colors.RESET}")
        print(f"{Colors.YELLOW}Please check your internet connection or API key.{Colors.RESET}")
    except json.JSONDecodeError as json_err:
        print(f"{Colors.RED}\nError parsing API response JSON: {json_err}{Colors.RESET}")
        print(f"{Colors.YELLOW}Raw response: {response.text}{Colors.RESET}")
    except KeyError as key_err:
        print(f"{Colors.RED}\nError: Missing expected key in API response - {key_err}{Colors.RESET}")
        print(f"{Colors.YELLOW}Full API response: {json.dumps(response.json(), indent=2) if response else 'No response'}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}\nAn unexpected error occurred: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()

