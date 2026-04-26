import os
import shutil
from datetime import datetime
from .toolkit import tool, toolset

# The absolute root that the AI is never allowed to escape
WORKSPACE_DIR = os.path.abspath(r"E:\_Code Projecten\api-harness\ai_env")

def _resolve_path(target_path: str) -> str:
    """Auto-prefix the workspace directory if the path doesn't start with it."""
    target_path = os.path.normpath(str(target_path))
    if not target_path.startswith(WORKSPACE_DIR):
        # Strip any accidental drive letters or leading slashes from the input to safely join it
        clean_path = os.path.splitdrive(target_path)[1].lstrip("\\/")
        target_path = os.path.join(WORKSPACE_DIR, clean_path)
    return os.path.abspath(target_path)

def _is_safe_path(target_path: str) -> bool:
    """Ensure the absolute path is inside our secure sandbox."""
    # Resolves any weird path tricks like '../../' naturally
    return target_path.startswith(WORKSPACE_DIR)

@toolset
class SystemToolset:
    @tool
    def list_items(self, path: str) -> str:
        """List files and folders in a directory."""
        path = _resolve_path(path)
        if not _is_safe_path(path):
            return "Error: Access denied. Path resolves outside the sandbox environment."
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        if not os.path.isdir(path):
            return f"Error: '{path}' is a file, not a directory."
        
        try:
            items = os.listdir(path)
            return "\n".join(items) if items else "Directory is empty."
        except Exception as e:
            return f"Error listing directory: {e}"

    @tool
    def make_file(self, path: str, content: str) -> str:
        """Create or overwrite a file with the given content."""
        path = _resolve_path(path)
        # print(f"[SystemToolset] make_file called. Resolved path: {path}")
        if not _is_safe_path(path):
            return f"Error: Access denied. Path '{path}' is outside the sandbox environment."
        
        try:
            # Ensure parent directories exist before writing
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File successfully created at: {path}"
        except Exception as e:
            return f"Error creating file: {e}"

    @tool
    def get_file(self, path: str) -> str:
        """Read the contents of a file."""
        path = _resolve_path(path)
        if not _is_safe_path(path):
            return f"Error: Access denied. Path '{path}' is outside the sandbox environment."
        
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        if not os.path.isfile(path):
            return f"Error: '{path}' is a directory, not a file."
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    @tool
    def delete_item(self, path: str) -> str:
        """Delete a file or directory and create a backup."""
        path = _resolve_path(path)
        if not _is_safe_path(path):
            return f"Error: Access denied. Path '{path}' is outside the sandbox environment."
        
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        
        try:
            # Prepare backup folder
            backup_base = os.path.abspath(os.path.join(WORKSPACE_DIR, "..", "backups"))
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.basename(path)
            backup_folder = os.path.join(backup_base, f"{filename}_{timestamp}")
            
            os.makedirs(backup_folder, exist_ok=True)
            
            # Create info.txt inside backup folder
            info_path = os.path.join(backup_folder, "info.txt")
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(f"Original path: {path}\nDeleted at: {datetime.now().isoformat()}\n")
            
            # Move the actual item into the backup directory
            backup_item_path = os.path.join(backup_folder, filename)
            shutil.move(path, backup_item_path)
            
            return f"Item '{path}' deleted. Backup created in '{backup_folder}'."
        except Exception as e:
            return f"Error deleting item: {e}"

    @tool
    def move_file(self, source_path: str, destination_path: str) -> str:
        """Move or rename a file or directory."""
        source_path = _resolve_path(source_path)
        destination_path = _resolve_path(destination_path)
        
        if not _is_safe_path(source_path) or not _is_safe_path(destination_path):
            return "Error: Access denied. Paths must be inside the sandbox environment."
            
        if not os.path.exists(source_path):
            return f"Error: Source '{source_path}' does not exist."
            
        try:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.move(source_path, destination_path)
            return f"Successfully moved to: {destination_path}"
        except Exception as e:
            return f"Error moving file: {e}"