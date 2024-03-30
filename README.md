Network Monitoring Script
This Python script monitors network connections on Windows and Linux servers and logs the data into a SQLite database. It supports SSH and WinRM protocols for Linux and Windows servers, respectively.

Prerequisites
Before running the script, ensure you have the following Python modules installed:

paramiko (for SSH connections)
pywinrm (for Windows Remote Management)
python-dotenv (for loading environment variables)
You can install these dependencies using pip:

bash
Copy code
pip install paramiko pywinrm python-dotenv
Installation
Clone this repository to your local machine:

bash
Copy code
git clone https://github.com/your-username/network-monitor.git
Install the required Python dependencies using pip:

bash
Copy code
pip install -r requirements.txt
Usage
Create a .env file in the root directory of the project with the following structure:

plaintext
Copy code
windowsuser=YOUR_WINDOWS_USERNAME
windowspass=YOUR_WINDOWS_PASSWORD
linuxuser=YOUR_LINUX_USERNAME
linuxpass=YOUR_LINUX_PASSWORD
Replace YOUR_WINDOWS_USERNAME, YOUR_WINDOWS_PASSWORD, YOUR_LINUX_USERNAME, and YOUR_LINUX_PASSWORD with the appropriate credentials for your Windows and Linux servers.

Prepare a CSV file named hosts.csv containing the list of hosts to monitor. The CSV file should have the following format:

plaintext
Copy code
hostname,os
server1.example.com,Windows
server2.example.com,Linux
Ensure each row includes the hostname and the corresponding operating system (either "Windows" or "Linux").

Run the script:

bash
Copy code
python network_monitor.py
The script will collect network connection data from the specified hosts, log it into the SQLite database, and create a backup of the database.

Logging
The script logs any errors encountered during execution to a log file named network_monitor.log.
Database backups are created automatically upon every script run and are named with the format server.db_TIMESTAMP.bak.
