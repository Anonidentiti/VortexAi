VortexAI - AI-Powered Vulnerability Analysis Tool
VortexAI is a command-line tool that uses Google Gemini AI to analyze security scan results, providing structured insights into vulnerabilities, Metasploit modules, other tools, and exploit links.

Features
Analyzes scan results with AI, providing structured, color-coded output with Metasploit, tool, and exploit suggestions. Securely handles API keys and logs JSON responses.

Installation
Clone the repository:

`git clone github.com/Anonidentiti/VortexAi.git
cd VortexAI`

Run the automated installation script:

`python3 installation.py`

Configuration
Set your Gemini API Key
VortexAI uses your Gemini API key from the GEMINI_API_KEY environment variable or /usr/share/vortexai/apikey.txt. Get your key at Google AI Studio. The installation.py script helps set it up.

Usage
Run the tool:

`python3 vortexai.py -r <results_file_path> -q "<your_query>"`

Explanation:

`-r: Path to your scan results file.`

`-q: Your question or instruction for the AI.`

Examples
Analyze Nmap scan for vulnerabilities:

python3 vortexai.py -r nmap_scan.txt -q "identify all potential vulnerabilities"

Output
Results are printed to the console in color and saved as a .log file (e.g., nmap_scan.txt.log).

Contributing
Contributions are welcome!
