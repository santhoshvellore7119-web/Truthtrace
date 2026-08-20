"""
Source snapshotting using Wayback Machine and local fallback.
"""
import hashlib
import httpx
from typing import Optional
from datetime import datetime
import os

# Import cost tracker for observability
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
from observability.cost_tracker import cost_tracker

# We'll store snapshots in a local directory if we can't use Wayback
SNAPSHOT_DIR = os.getenv("TRUTHTRACE_SNAPSHOT_DIR", "./snapshots")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

class Snapshotter:
    def __init__(self):
        self.wayback_save_url = "https://web.archive.org/save/"
        self.wayback_available_url = "http://archive.org/wayback/available"
        # Use shorter timeout for testing; can be overridden by environment variable
        timeout = float(os.getenv("TRUTHTRACE_SNAPSHOT_TIMEOUT", "10.0"))
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)

    def snapshot(self, url: str) -> Optional[str]:
        """
        Attempt to snapshot the URL using Wayback Machine.
        If that fails, fall back to saving locally.
        Returns a snapshot URL (either a Wayback URL or a local file URL).
        """
        # Check if we are in mock mode (for testing)
        if os.getenv("TRUTHTRACE_SNAPSHOTTER_MOCK") == "1":
            # Return a mock snapshot URL without making HTTP requests
            return f"mock://snapshot/{hashlib.md5(url.encode()).hexdigest()}"

        # Try Wayback Machine save
        try:
            call_id = f"wayback_save_{int(datetime.now().timestamp())}_{hashlib.md5(url.encode()).hexdigest()[:8]}"
            cost_tracker.start_call(call_id, "wayback_save")
            response = self.client.post(
                self.wayback_save_url,
                params={"url": url}
            )
            cost_tracker.end_call(call_id, "wayback_save", cost=0.01)  # Estimated cost

            if response.status_code in [200, 201, 202]:
                # The Wayback Machine returns a job ID in the response headers
                # The snapshot URL can be constructed from the job ID
                # Or we can check the Content-Location header
                content_location = response.headers.get("Content-Location")
                if content_location:
                    # This is the URL to check for snapshot completion
                    # For now, we'll return the original URL with a timestamp parameter
                    # to indicate we requested a snapshot
                    return f"{url}?{response.headers.get('X-Wayback-Trackback-Id', '')}"
                else:
                    # Fallback: construct the expected snapshot URL
                    # Wayback Machine snapshots are available at:
                    # https://web.archive.org/web/<timestamp>/<original_url>
                    # We don't know the timestamp yet, so we'll return a placeholder
                    # that indicates a snapshot was requested
                    return url  # Placeholder - in production we'd poll for completion
            elif response.status_code == 302:
                # Redirect to snapshot
                snapshot_url = response.headers.get("Location")
                if snapshot_url:
                    return snapshot_url
                else:
                    return str(response.url)  # The final URL after redirects
        except Exception as e:
            print(f"Wayback Machine save failed: {e}")
            # Still end the call even if it failed
            if 'call_id' in locals():
                cost_tracker.end_call(call_id, "wayback_save", cost=0.0)

        # Fallback: save locally
        try:
            call_id = f"local_save_{int(datetime.now().timestamp())}_{hashlib.md5(url.encode()).hexdigest()[:8]}"
            cost_tracker.start_call(call_id, "local_save")
            response = self.client.get(url)
            cost_tracker.end_call(call_id, "local_save", cost=0.005)  # Estimated cost

            if response.status_code == 200:
                content = response.content
                # Create a filename based on URL hash
                url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                filename = f"{url_hash}_{timestamp}.html"
                filepath = os.path.join(SNAPSHOT_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(content)
                # Return a file:// URL
                return f"file://{os.path.abspath(filepath)}"
        except Exception as e:
            print(f"Local snapshot failed: {e}")
            if 'call_id' in locals():
                cost_tracker.end_call(call_id, "local_save", cost=0.0)

        return None

    def is_snapshot_available(self, original_url: str, snapshot_url: str) -> bool:
        """
        Check if a snapshot is available at the given snapshot_url.
        For Wayback, we can check the availability API.
        For local files, we just check if the file exists.
        """
        if snapshot_url.startswith("file://"):
            filepath = snapshot_url[8:]
            return os.path.exists(filepath)
        elif "web.archive.org" in snapshot_url:
            # We'll check the Wayback availability API
            try:
                response = self.client.get(
                    self.wayback_available_url,
                    params={"url": original_url},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    # Check if there's a snapshot closest to now
                    snapshots = data.get("archived_snapshots", {})
                    closest = snapshots.get("closest")
                    if closest and closest.get("available"):
                        return True
            except Exception:
                pass
            return False
        else:
            # Assume it's a direct URL and we can HEAD it
            try:
                response = self.client.head(snapshot_url, timeout=10.0)
                return response.status_code == 200
            except Exception:
                return False

# Global snapshotter instance
snapshotter = Snapshotter()

def snapshot_source(url: str) -> Optional[str]:
    """Convenience function to snapshot a URL."""
    return snapshotter.snapshot(url)