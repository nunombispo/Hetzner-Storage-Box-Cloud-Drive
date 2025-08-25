#!/usr/bin/env python3
"""
hetzner_drive_sync.py - Python-only 2-way sync with Hetzner Storage Box (WebDAV)
"""

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
    print(options)
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
            print(f"{remote_path_source}")
            print(f"{remote_path_dest}")
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

        # Start local watcher
        handler = LocalHandler(client)
        obs = Observer()
        obs.schedule(handler, str(LOCAL_DIR), recursive=True)
        obs.start()

        print("Starting file sync (Ctrl+C to stop)...")
        try:
            while True:
                # TODO: poll remote files every 30s and download if changed
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
