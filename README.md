# Network Monitoring Script

## Description
This script monitors network connections on both Windows and Linux servers and logs the data into a SQLite database. It utilizes SSH for Linux servers and WinRM for Windows servers to gather network connection information.

## Requirements
- Python 3.x
- Required Python modules:
  - paramiko
  - winrm
  - dotenv
- `.env` file containing environment variables:

windowsuser=your_windows_username
windowspass=your_windows_password
linuxuser=your_linux_username
linuxpass=your_linux_password


## Installation
1. Clone the repository:
https://github.com/jamal-smg/servermonitor.git

2. Navigate to the project directory:
cd network-monitoring-script

3. Install the required Python modules:
pip install -r requirements.txt


4. Create a `.env` file with the required environment variables (see the Requirements section above for details).


## Usage
1. Prepare a CSV file named `hosts.csv` containing the list of hosts to monitor, along with their operating systems (`Windows` or `Linux`).
hostname,os
192.168.1.1,Windows
192.168.1.2,Linux

2. Run the script:
python servermonitor.py


## Additional Notes
- The script automatically creates a backup of the SQLite database (`server.db`) every time it runs.
- Ensure that SSH is enabled on Linux servers and WinRM is configured on Windows servers for the script to work properly.




