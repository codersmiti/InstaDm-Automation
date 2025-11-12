# Instagram Multi-Account DM Automation

This project automates personalized Instagram DMs across multiple accounts using **OpenAI GPT** for natural, human-like message generation.  
It logs into each account, reads target lists, sends DMs (optionally with images), and mimics real user activity with random cooldowns.

---

## Setup

```bash
1️. Clone the repo
git clone https://github.com/codersmiti/InstaDm-Automation.git
cd InstaDm-Automation

2️. Create a virtual environment
python -m venv venv
venv\Scripts\activate     # On Windows

3️. Install dependencies
pip install -r requirements.txt

4. Add your OpenAI API key
Create a .env file in the root folder:
OPENAI_API_KEY=your_openai_api_key_here

5. Prepare input files
accounts.csv          # username,password
lists/<username>.txt  # usernames to DM (one per line)
media/                # optional images to attach

6. Run the script
python multiaccount.py
