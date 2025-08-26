# Hetzner Storage Box Cloud Drive

A Python-based two-way synchronization tool for Hetzner Storage Box using WebDAV protocol. 

This tool provides real-time file synchronization between your local machine and Hetzner's cloud storage, with automatic conflict resolution and efficient change detection.

If these scripts were useful to you, consider donating to support the Developer Service Blog: https://buy.stripe.com/bIYdTrggi5lZamkdQW

## Features

- **Real-time synchronization**: Monitors local file system changes and automatically syncs with remote storage
- **Automatic conflict resolution**: Compares file modification times to determine which version is newer
- **File system events**: Handles file creation, modification, deletion, and movement
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Efficient**: Only syncs changed files, reducing bandwidth usage
- **Robust error handling**: Continues operation even if individual file operations fail

## Prerequisites

- Python 3.7 or higher
- Hetzner Storage Box account with WebDAV access
- Network connection to Hetzner servers

## Installation

1. **Clone or download this repository:**

   ```bash
   git clone https://github.com/nunombispo/Hetzner-Storage-Box-Cloud-Drive
   cd Hetzner-Storage-Box-Cloud-Drive
   ```

2. **Install required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file in the project root with your Hetzner credentials:**
   ```env
   HETZNER_BASE_URL=https://your-username.your-storage-box.de
   HETZNER_USERNAME=your-username
   HETZNER_PASSWORD=your-password
   ```

## Configuration

### Environment Variables

The following environment variables are required in your `.env` file:

- `HETZNER_BASE_URL`: Your Hetzner Storage Box WebDAV URL
- `HETZNER_USERNAME`: Your Hetzner username
- `HETZNER_PASSWORD`: Your Hetzner password

### Directory Structure

- **Local Directory**: `./HetznerDrive/` (automatically created if it doesn't exist)
- **Remote Directory**: `/HetznerDrive/` (on your Hetzner Storage Box, automatically created if it doesn't exist)

You can modify these paths in the respective Python files if needed.

## Usage

### Basic Synchronization

Run the main synchronization script:

```bash
python hetzner_drive_sync.py
```

This will:

1. Perform an initial sync (upload local files, delete remote files not present locally)
2. Start monitoring local file system changes
3. Automatically sync changes in real-time

### File Operations

The tool automatically handles:

- **File Creation**: New files are immediately uploaded to remote storage
- **File Modification**: Modified files are uploaded with newer timestamps
- **File Deletion**: Deleted files are removed from remote storage
- **File Movement**: Files moved/renamed are handled as move operations
- **Directory Operations**: Directory creation and deletion are synced

### Stopping the Sync

Press `Ctrl+C` to gracefully stop the synchronization process.

## Scripts

### `hetzner_drive_sync.py`

The main synchronization script that provides:

- Initial startup synchronization
- Real-time file monitoring
- Two-way sync capabilities
- Comprehensive error handling

### `hetzner_drive_changes.py`

A simplified version focused on change detection and upload operations.

## Dependencies

- **webdavclient3**: WebDAV client for Python
- **watchdog**: File system monitoring and event handling
- **python-dotenv**: Environment variable management

## Troubleshooting

### Common Issues

1. **Connection Errors**

   - Verify your Hetzner credentials in the `.env` file
   - Verify that your Hetzner Storage Box as External Access and WebDAV active
   - Check your internet connection

2. **Permission Errors**

   - Verify you have write permissions to the local `HetznerDrive` directory
   - Check your Hetzner account permissions

3. **Sync Issues**
   - Check the console output for specific error messages
   - Verify file paths and permissions
   - Restart the sync process if needed

### Logs

The tool provides detailed console output for:

- File operations (upload, download, delete, move)
- Error messages and warnings
- Sync progress and statistics

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.
