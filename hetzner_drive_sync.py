import time
import os
from pathlib import Path
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from webdav3.client import Client

LOCAL_DIR = Path("./HetznerDrive").resolve()
REMOTE_DIR = "/HetznerDrive"

# Load environment variables from .env file
load_dotenv()

# --- Helpers -----------------------------------------------------------------

def load_config():
    """Load configuration from environment variables"""
    # Convert to webdavclient3 format
    options = {
        'webdav_hostname': os.getenv('HETZNER_BASE_URL'),
        'webdav_login': os.getenv('HETZNER_USERNAME'),
        'webdav_password': os.getenv('HETZNER_PASSWORD'),
        'webdav_timeout': 30
    }
    return options

def create_webdav_client(config_options):
    """Create and configure WebDAV client"""
    client = Client(config_options)
    client.verify = True
    return client

# --- Watchdog Local Event Handler --------------------------------------------

class LocalHandler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client

    def on_modified(self, event):
        if not event.is_directory:
            try:
                self.upload(Path(event.src_path))
            except Exception as e:
                print(f"Error handling file modification for {event.src_path}: {e}")

    def on_moved(self, event):
        try:
            rel_source = str(Path(event.src_path).relative_to(LOCAL_DIR))
            remote_path_source = f"{REMOTE_DIR}/{rel_source}".replace("\\", "/")
            rel_dest = str(Path(event.dest_path).relative_to(LOCAL_DIR))
            remote_path_dest = f"{REMOTE_DIR}/{rel_dest}".replace("\\", "/")
            print(f"Moving {rel_source} to {rel_dest}")
            self.client.move(remote_path_source, remote_path_dest)
            print(f"Moved {remote_path_source} to {remote_path_dest}")
        except Exception as e:
            print(f"Error handling file move for {remote_path_source}: {e}")

    def on_created(self, event):
        if not event.is_directory:
            try:
                self.upload(Path(event.src_path))
            except Exception as e:
                print(f"Error handling file creation for {event.src_path}: {e}")
        else:
            try:
                rel = str(Path(event.src_path).relative_to(LOCAL_DIR))
                remote_path = f"{REMOTE_DIR}/{rel}".replace("\\", "/")
                self.client.mkdir(remote_path)
                print(f"Created remote directory: {remote_path}")
            except Exception as e:
                print(f"Error handling directory creation for {event.src_path}: {e}")

    def on_deleted(self, event):
        if not event.is_directory:
            try:
                rel = str(Path(event.src_path).relative_to(LOCAL_DIR))
                remote_path = f"{REMOTE_DIR}/{rel}".replace("\\", "/")
                self.client.clean(remote_path)
                print(f"Deleted remote: {rel}")
            except Exception as e:
                print(f"Error handling file deletion for {event.src_path}: {e}")

    def upload(self, path: Path):
        try:
            rel = str(path.relative_to(LOCAL_DIR)).replace("\\", "/")
            remote_path = f"{REMOTE_DIR}/{rel}"
            print(f"Uploading {rel} -> {remote_path}")
            self.client.upload_sync(remote_path=remote_path, local_path=str(path))
            print(f"Successfully uploaded: {rel}")
        except Exception as e:
            print(f"Error uploading {path}: {e}")
            # Don't re-raise - we want to continue monitoring other files

# --- Startup Sync -------------------------------------------------------------
def startup_sync(client):
    """Perform initial sync: upload local files to remote and delete remote files not present locally"""
    print("Starting initial sync...")
    
    # Get list of all local files and directories
    local_files = set()
    local_dirs = set()
    
    for root, dirs, files in os.walk(LOCAL_DIR):
        root_path = Path(root)
        for file in files:
            rel_path = str(root_path.joinpath(file).relative_to(LOCAL_DIR)).replace("\\", "/")
            local_files.add(rel_path)
        for dir_name in dirs:
            rel_path = str(root_path.joinpath(dir_name).relative_to(LOCAL_DIR)).replace("\\", "/")
            local_dirs.add(rel_path)
    
    print(f"Found {len(local_files)} local files and {len(local_dirs)} local directories")
    
    # Get list of all remote files and directories
    remote_files = set()
    remote_dirs = set()
    
    try:
        def list_remote_recursive(path):
            try:
                items = client.list(path)
                for item in items:
                    if item.endswith('/'):
                        # Directory
                        dir_name = item.rstrip('/').split('/')[-1]
                        if dir_name:  # Skip root path
                            rel_path = path.replace(REMOTE_DIR, '').lstrip('/')
                            if rel_path:
                                remote_dirs.add(f"{rel_path}/{dir_name}")
                            else:
                                remote_dirs.add(dir_name)
                            # Recursively list subdirectories
                            list_remote_recursive(f"{path}/{dir_name}")
                    else:
                        # File
                        rel_path = path.replace(REMOTE_DIR, '').lstrip('/')
                        if rel_path:
                            remote_files.add(f"{rel_path}/{item}")
                        else:
                            remote_files.add(item)
            except Exception as e:
                print(f"Warning: Could not list remote directory {path}: {e}")
        
        list_remote_recursive(REMOTE_DIR)
        print(f"Found {len(remote_files)} remote files and {len(remote_dirs)} remote directories")
        
    except Exception as e:
        print(f"Warning: Could not list remote files: {e}")
        print("Proceeding with upload only...")
    
    # Delete remote files that don't exist locally
    deleted_count = 0
    for remote_file in remote_files:
        if remote_file not in local_files:
            try:
                remote_path = f"{REMOTE_DIR}/{remote_file}"
                print(f"Deleting remote file (not in local): {remote_file}")
                client.clean(remote_path)
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting remote file {remote_file}: {e}")
    
    print(f"Deleted {deleted_count} remote files")
    
    # Delete remote directories that don't exist locally
    deleted_dirs = 0
    for remote_dir in sorted(remote_dirs, key=len, reverse=True):  # Delete deepest dirs first
        if remote_dir not in local_dirs:
            try:
                remote_path = f"{REMOTE_DIR}/{remote_dir}"
                print(f"Deleting remote directory (not in local): {remote_dir}")
                client.clean(remote_path)
                deleted_dirs += 1
            except Exception as e:
                print(f"Error deleting remote directory {remote_dir}: {e}")
    
    print(f"Deleted {deleted_dirs} remote directories")
    
    # Create remote directories that don't exist
    created_dirs = 0
    for local_dir in local_dirs:
        try:
            remote_path = f"{REMOTE_DIR}/{local_dir}"
            client.mkdir(remote_path)
            created_dirs += 1
        except Exception as e:
            # Directory might already exist
            pass
    
    print(f"Created {created_dirs} remote directories")

    # Upload local files that don't exist remotely or are newer
    uploaded_count = 0
    for local_file in local_files:
        try:
            local_path = LOCAL_DIR / local_file
            remote_path = f"{REMOTE_DIR}/{local_file}"
            
            # Check if remote file exists and compare modification times
            should_upload = True
            try:
                remote_info = client.info(remote_path)
                if remote_info:
                    # File exists remotely, check if local is newer
                    local_mtime = local_path.stat().st_mtime
                    remote_mtime = float(remote_info.get('modified', 0))
                    if local_mtime <= remote_mtime:
                        should_upload = False
            except:
                # Remote file doesn't exist or can't get info
                pass
            
            if should_upload:
                print(f"Uploading: {local_file}")
                client.upload_sync(remote_path=remote_path, local_path=str(local_path))
                uploaded_count += 1
            else:
                print(f"Skipping (up to date): {local_file}")
                
        except Exception as e:
            print(f"Error uploading {local_file}: {e}")
    
    print(f"Uploaded {uploaded_count} files")
    
    print("Initial sync completed!")

# --- Main Sync Loop ----------------------------------------------------------
def main():
    try:
        config_options = load_config()
        client = create_webdav_client(config_options)

        print(f"Local directory: {LOCAL_DIR}")
        print(f"Remote directory: {REMOTE_DIR}")
        
        LOCAL_DIR.mkdir(exist_ok=True)
        
        # Ensure remote base directory exists
        try:
            print(f"Ensuring remote directory exists: {REMOTE_DIR}")
            client.mkdir(REMOTE_DIR)
        except Exception as e:
            print(f"Warning: Could not create remote directory {REMOTE_DIR}: {e}")
            print("This might be normal if the directory already exists or if you don't have write permissions")

        # Perform initial sync
        startup_sync(client)

        # Start local watcher
        handler = LocalHandler(client)
        obs = Observer()
        obs.schedule(handler, str(LOCAL_DIR), recursive=True)
        obs.start()

        print("Starting file sync (Ctrl+C to stop)...")
        try:
            while True:
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nStopping sync...")
            obs.stop()
        finally:
            obs.join()
            print("Sync stopped.")
            
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    main()
