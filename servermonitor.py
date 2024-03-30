import os
import sqlite3
import threading
import csv
import re
import queue
import shutil
from datetime import datetime
import paramiko
import winrm
from dotenv import load_dotenv

load_dotenv()

# read servers hosts from csv
def read_hosts_from_file(filename):
    hosts = []
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file)
            print("Column Headers:")
            print(csv_reader.fieldnames) 
            for row in csv_reader:
                if 'hostname' in row and 'os' in row:
                    hosts.append({"hostname": row['hostname'], "os": row['os']})
                else:
                    print("Missing keys in row:", row)
    except Exception as e:
        log_error('', f"Error reading hosts from file: {e}")
    return hosts

# read credentials from .env file
def read_credentials_from_env():
    try:
        return {
            'windows_user': os.environ.get('windowsuser'),
            'windows_pass': os.environ.get('windowspass'),
            'linux_user': os.environ.get('linuxuser'),
            'linux_pass': os.environ.get('linuxpass')
        }
    except Exception as e:
        log_error('', f"Error reading credentials from environment variables: {e}")
        return {}
    
#Linux connection
def ssh_connection(host, username, password, command, queue):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        print(output)
        queue.put(output)
    except paramiko.AuthenticationException as e:
        log_error(host, f"Authentication failed for {host}: {e}")
    except Exception as e:
        log_error(host, f"Error executing SSH command on {host}: {e}")
    finally:
        queue.put(None)

# Windows connection
def winrm_connection(host, username, password, command, queue):
    try:
        session = winrm.Session(host, auth=(username, password))
        result = session.run_ps(command)
        output = result.std_out.decode()
        print(output)
        queue.put(output)
    except winrm.exceptions.InvalidCredentialsError as e:
        log_error(host, f"Invalid credentials for {host}: {e}")
    except Exception as e:
        log_error(host, f"Error executing WinRM command on {host}: {e}")
    finally:
        queue.put(None)

def write_to_database(data, conn):
    try:
        c = conn.cursor()
        c.executemany('''INSERT INTO network_connections 
                        (timestamp, sourceHostname, sourceIP, sourcePort,destinationPort, destinationIP, connectionState) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()
    except Exception as e:
        log_error('', f"Error writing to database: {e}")

def process_linux_console_output(output, hostname):
    processed_data = []
    lines = output.split('\n')
    for line in lines[1:]:
        if line.strip():
            parts = line.split()
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            if len(parts) >= 4 and parts[0] in ['tcp', 'udp']:
                proto = parts[0]
                if proto == 'tcp' and len(parts) >= 6:
                    source_ip, source_port = parts[3].split(':')
                    state = parts[5] if len(parts) >= 6 else ''
                elif proto == 'udp' and len(parts) >= 5:
                    source_ip, source_port = parts[3].split(':')
                    state = parts[4] if len(parts) >= 5 else ''
                else:
                    continue
                if len(parts) >= 4:
                    foreign_address = parts[4]
                    if foreign_address == '*:*':
                        destination_ip, destination_port = '', -1
                    else:
                        destination_ip, destination_port = foreign_address.rsplit(':', 1)
                else:
                    destination_ip, destination_port = '', -1
                processed_data.append((timestamp, hostname, source_ip, source_port, destination_port, destination_ip, state))
    return processed_data

def process_windows_console_output(output, hostname):
    processed_data = []
    lines = output.split('\n')
    header_lines = 3
    for i, line in enumerate(lines):
        if i < header_lines:
            continue
        if line.strip():
            pattern = r'(?P<local_address>[\w.:]+)\s+(?P<local_port>\d+)\s+(?P<remote_address>[\w.:]+)\s+(?P<remote_port>\d+)\s+(?P<state>\S.*\S|\S)'
            match = re.match(pattern, line)
            if match:
                timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                local_address, local_port = match.group('local_address'), int(match.group('local_port'))
                remote_address, remote_port = match.group('remote_address'), int(match.group('remote_port'))
                state = match.group('state')
                processed_data.append((timestamp, hostname, remote_address, remote_port, local_port, local_address, state))
    return processed_data

def backup_database():
    try:
        current_time = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        db_filename = 'server.db'
        backup_filename = f'{db_filename}_{current_time}.bak'
        shutil.copy2(db_filename, backup_filename)
        print(f"Database backup created: {backup_filename}")
    except Exception as e:
        log_error('', f"Error creating database backup: {e}")

# Error logging
def log_error(hostname, message):
    try:
        conn = sqlite3.connect('server.db')
        c = conn.cursor()
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO error_log (timestampUtc, hostname, log_message) VALUES (?, ?, ?)", (timestamp, hostname, message))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging error: {e}")

def create_error_log_table():
    try:
        conn = sqlite3.connect('server.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS error_log (
                     entry_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestampUtc TEXT,
                     log_message TEXT,
                     hostname TEXT
                     )''')
        conn.commit()
        conn.close()
    except Exception as e:
        log_error('', f"Error creating error log table: {e}")  

threads_finished = False


# Calling functions
def main():
    global threads_finished
    try:
        hosts = read_hosts_from_file("hosts.csv")
        credentials = read_credentials_from_env()
        
        windows_hosts = [host for host in hosts if host['os'] == 'Windows']
        linux_hosts = [host for host in hosts if host['os'] == 'Linux']
        create_error_log_table()
        conn = sqlite3.connect('server.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS network_connections (
                     entry_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp TEXT,
                     sourceHostname TEXT,
                     sourceIP TEXT,
                     sourcePort TEXT,
                     destinationPort TEXT,
                     destinationIP TEXT,
                     connectionState TEXT
                     )''')
        
        windows_queue = queue.Queue()
        for host in windows_hosts:
            threading.Thread(target=winrm_connection, args=(host['hostname'], credentials['windows_user'], credentials['windows_pass'], "Get-NetTCPConnection", windows_queue)).start()
        
        linux_queue = queue.Queue()
        for host in linux_hosts:
            threading.Thread(target=ssh_connection, args=(host['hostname'], credentials['linux_user'], credentials['linux_pass'], "netstat -tuln", linux_queue)).start()
        
        for thread in threading.enumerate():
            if thread != threading.current_thread():
                thread.join()
        threads_finished = True
        
        windows_data = [process_windows_console_output(data, host['hostname']) for data in iter(windows_queue.get, None) for host in windows_hosts]
        linux_data = [process_linux_console_output(data, host['hostname']) for data in iter(linux_queue.get, None) for host in linux_hosts]
        
        write_to_database(windows_data + linux_data, conn)
        
        conn.close()
        
        backup_database()
    except Exception as e:
        log_error('', f"Error in main function: {e}")

if __name__ == "__main__":
    main()
