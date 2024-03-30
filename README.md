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
