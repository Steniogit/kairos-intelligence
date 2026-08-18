"""Upload files to VPS via SFTP."""
import paramiko
import os
import sys

def upload_dir(local_dir, remote_dir, host, user, password):
    transport = paramiko.Transport((host, 22))
    transport.connect(username=user, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # Create remote dir
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass  # Already exists

    for filename in os.listdir(local_dir):
        local_path = os.path.join(local_dir, filename)
        if os.path.isfile(local_path):
            remote_path = f"{remote_dir}/{filename}"
            print(f"Uploading {filename} -> {remote_path}")
            sftp.put(local_path, remote_path)
            print(f"  OK ({os.path.getsize(local_path)} bytes)")

    sftp.close()
    transport.close()
    print("All files uploaded!")

if __name__ == "__main__":
    local = sys.argv[1] if len(sys.argv) > 1 else "."
    remote = sys.argv[2] if len(sys.argv) > 2 else "/root/kairos-intelligence/clinical"
    upload_dir(local, remote, "2.24.203.81", "root", "Kairosopenclaw@2026")
