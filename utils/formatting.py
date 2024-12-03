from datetime import datetime
from typing import Optional

def format_file_size(size_in_bytes: int) -> str:
    """Format file size to human readable format."""
    if size_in_bytes >= 1_000_000:
        return f"{size_in_bytes / 1_000_000:.2f} MB"
    else:
        return f"{size_in_bytes / 1_000:.2f} KB"

def format_date(date_string: str) -> str:
    """Format date string to readable format."""
    date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    return date.strftime('%m/%d/%y - %H:%M:%S UTC')

def parse_size_string(size_str: Optional[str]) -> Optional[int]:
    """
    Parse size string (e.g., '2mb', '500kb') to bytes.
    Returns None if invalid format.
    """
    if not size_str:
        return None

    size_str = size_str.lower()
    try:
        value = float(size_str[:-2])
        unit = size_str[-2:]

        if unit == 'mb':
            return int(value * 1_000_000)
        elif unit == 'kb':
            return int(value * 1_000)
        else:
            return None
    except (ValueError, IndexError):
        return None

def get_progress_message(current: int, total: int, status: str = "Working on it") -> str:
    """Generate a progress message."""
    return f"{status}... (Attempt {current}/{total})"

def format_file_details(asset_info: dict, file_size_bytes: int) -> str:
    """Format file details for Discord message."""
    return (
        f"**File Details:**\n"
        f"ID: {asset_info['id']}\n"
        f"Original File Name: {asset_info.get('originalFileName', 'Unknown')}\n"
        f"Size: {format_file_size(file_size_bytes)}\n"
        f"Resolution: {asset_info['exifInfo']['exifImageWidth']}x{asset_info['exifInfo']['exifImageHeight']}\n"
        f"Downloaded: {format_date(asset_info['fileCreatedAt'])}"
    )