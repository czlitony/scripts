"""
Multi-threaded file downloader with progress tracking and authentication support.

Features:
    - Multi-threaded downloading for improved speed
    - Progress tracking with real-time updates
    - Multiple authentication methods (Basic, Bearer token)
    - Range request support detection
    - Thread-safe progress monitoring
    - Interruptible downloads (Ctrl+C support)
    - Automatic cleanup of partial files on failure/interruption
    - Command-line interface support

Usage as a module:
    Basic download:
        downloader = Downloader()
        success = downloader.download(
            url="https://example.com/file.zip",
            save_path="./file.zip"
        )

    Download with authentication (Basic Auth):
        downloader = Downloader()
        success = downloader.download(
            url="https://example.com/file.zip",
            save_path="./file.zip",
            username="user",
            password="pass"
        )

    Download with Bearer token:
        downloader = Downloader()
        success = downloader.download(
            url="https://example.com/file.zip",
            save_path="./file.zip",
            token="your_bearer_token"
        )

    Custom configuration:
        config = DownloadConfig(
            num_threads=8,           # Number of parallel download threads
            chunk_size=16384,        # Chunk size in bytes (16KB)
            timeout=60               # Request timeout in seconds
        )
        downloader = Downloader(config=config, verbose=True)
        success = downloader.download(url="...", save_path="...")

    With progress callback:
        def progress_callback(progress: DownloadProgress):
            print(f"Downloaded: {progress.percentage:.1f}%")
        
        downloader = Downloader()
        success = downloader.download(
            url="...",
            save_path="...",
            progress_callback=progress_callback
        )

Usage from command line:
    Basic download:
        python downloader.py https://example.com/file.zip -o file.zip

    Download with authentication:
        python downloader.py https://example.com/file.zip -o file.zip -u user -p pass
        python downloader.py https://example.com/file.zip -o file.zip -t bearer_token

    Custom configuration:
        python downloader.py https://example.com/file.zip -o file.zip --threads 8 --chunk-size 16384

    Quiet mode (no progress bar):
        python downloader.py https://example.com/file.zip -o file.zip -q

    Show help:
        python downloader.py -h

Interruption:
    - Press Ctrl+C at any time to interrupt the download
    - Partial files will be automatically cleaned up
    - Progress bar will show the interrupted state
"""

import requests
import os
import threading
import time
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, Dict, Tuple
from dataclasses import dataclass
from requests.auth import AuthBase, HTTPBasicAuth
import urllib3

# Enable ANSI escape sequences on Windows
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass


@dataclass
class DownloadConfig:
    """Configuration for download operations.
    
    Args:
        num_threads: Number of parallel download threads (default: 4)
        chunk_size: Size of each data chunk to read from network in bytes (default: 8192 = 8KB)
                   - Smaller values (e.g., 4096): More responsive to Ctrl+C interrupts, but slightly slower
                   - Larger values (e.g., 65536): Faster download, but less responsive to interrupts
                   - Recommended range: 8192-32768 bytes
        progress_update_interval: How often to update progress display in seconds (default: 0.1)
        timeout: HTTP request timeout in seconds (default: 30)
        verify_ssl: Whether to verify SSL certificates (default: False). Set to True to enable SSL verification.
    """
    num_threads: int = 4
    chunk_size: int = 8192
    progress_update_interval: float = 0.1
    timeout: int = 30
    verify_ssl: bool = False


@dataclass
class DownloadProgress:
    """Progress information for download operations."""
    downloaded_bytes: int
    total_bytes: int
    percentage: float
    speed_bps: float

    @property
    def downloaded_mb(self) -> float:
        return self.downloaded_bytes / (1024 * 1024)

    @property
    def total_mb(self) -> float:
        return self.total_bytes / (1024 * 1024)


class ProgressTracker:
    """Thread-safe progress tracking for downloads."""

    def __init__(self, total_bytes: int):
        self.total_bytes = total_bytes
        self.downloaded_bytes = 0
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._cancelled = False

    def update(self, bytes_count: int):
        with self._lock:
            self.downloaded_bytes += bytes_count

    def get_progress(self) -> DownloadProgress:
        with self._lock:
            percentage = (self.downloaded_bytes / self.total_bytes) * 100 if self.total_bytes > 0 else 0
            elapsed_time = time.time() - self._start_time
            speed_bps = self.downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
            return DownloadProgress(
                downloaded_bytes=self.downloaded_bytes,
                total_bytes=self.total_bytes,
                percentage=percentage,
                speed_bps=speed_bps,
            )

    def is_complete(self) -> bool:
        with self._lock:
            return self.downloaded_bytes >= self.total_bytes

    def cancel(self):
        with self._lock:
            self._cancelled = True

    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled




class ProgressDisplay:
    """Handles progress display and callbacks."""

    def __init__(self, enable_console: bool = True, 
                 callback: Optional[Callable[[DownloadProgress], None]] = None):
        self.enable_console = enable_console
        self.callback = callback
        self._last_percentage = -1

    def update(self, progress: DownloadProgress):
        if self.callback:
            try:
                self.callback(progress)
            except:
                pass

        # Only update console if percentage changed significantly
        if self.enable_console and abs(progress.percentage - self._last_percentage) >= 0.1:
            self._display_progress(progress)
            self._last_percentage = progress.percentage

    def _display_progress(self, progress: DownloadProgress):
        bar_length = 50
        filled = int(bar_length * progress.percentage / 100)
        bar = "█" * filled + "-" * (bar_length - filled)
        speed_mb = progress.speed_bps / (1024 * 1024)
        
        message = (
            f"Progress: |{bar}| {progress.percentage:.1f}% "
            f"({progress.downloaded_mb:.1f}/{progress.total_mb:.1f} MB) @ {speed_mb:.1f} MB/s"
        )
        sys.stdout.write(f"\r{message}\033[K")
        sys.stdout.flush()

    def finish(self, progress: DownloadProgress, success: bool = True):
        if self.enable_console:
            bar_length = 50
            if success:
                bar = "█" * bar_length
                message = f"Progress: |{bar}| 100.0% ({progress.total_mb:.1f}/{progress.total_mb:.1f} MB)"
            else:
                filled = int(bar_length * progress.percentage / 100)
                bar = "█" * filled + "-" * (bar_length - filled)
                message = (
                    f"Progress: |{bar}| {progress.percentage:.1f}% "
                    f"({progress.downloaded_mb:.1f}/{progress.total_mb:.1f} MB) - INTERRUPTED"
                )
            sys.stdout.write(f"\r{message}\033[K\n")
            sys.stdout.flush()

        if self.callback:
            try:
                self.callback(progress)
            except:
                pass


class Downloader:
    """Main downloader class with multi-threading and progress tracking."""

    def __init__(self, config: Optional[DownloadConfig] = None, verbose: bool = True):
        self.config = config or DownloadConfig()
        self.verbose = verbose
        self._progress_tracker = None
        self._original_sigint_handler = None
        
        # Disable SSL warnings only when SSL verification is disabled
        if not self.config.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C interruption."""
        if self._progress_tracker:
            self._progress_tracker.cancel()
        print("\n\n🛑 Interrupting download...")
        if self._original_sigint_handler:
            signal.signal(signal.SIGINT, self._original_sigint_handler)

    def _create_auth(self, username, password, token, api_key, headers):
        """Create authentication objects and headers."""
        auth_obj = None
        auth_headers = {}

        if username and password:
            auth_obj = HTTPBasicAuth(username, password)
        elif token:
            auth_headers["Authorization"] = f"Bearer {token}"

        return auth_obj, auth_headers

    def download(
        self,
        url: str,
        save_path: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        display_progress: bool = True,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> bool:
        """Download a file with multi-threading support."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)
        
        try:
            start_time = time.time()
            
            # Print download URL
            if self.verbose:
                self._log(f"Download URL: {url}")

            # Setup authentication
            auth_obj, auth_headers = self._create_auth(username, password, token, None, None)

            # Get file size
            file_size = self._get_file_size(url, auth_headers, auth_obj)
            if file_size <= 0:
                self._log("Warning: Could not determine file size")
                file_size = 1

            if self.verbose:
                file_size_mb = file_size / (1024 * 1024)
                self._log(f"File size: {file_size_mb:.1f} MB")

            # Setup progress tracking
            progress_tracker = ProgressTracker(file_size)
            self._progress_tracker = progress_tracker  # Store for signal handler
            progress_display = ProgressDisplay(display_progress, progress_callback)

            # Check if we can use multi-threading
            supports_range = self._check_range_support(url, auth_headers, auth_obj)
            use_multithread = supports_range and self.config.num_threads > 1

            if self.verbose:
                if use_multithread:
                    self._log(f"Using {self.config.num_threads} threads for download")
                else:
                    reason = (
                        "server doesn't support range requests"
                        if not supports_range
                        else "single thread mode"
                    )
                    self._log(f"Using single-threaded download ({reason})")

            # Start progress monitoring
            progress_thread = threading.Thread(
                target=self._monitor_progress,
                args=(progress_tracker, progress_display),
                daemon=True,
            )
            progress_thread.start()

            # Perform download
            success = (self._download_multithread if use_multithread else self._download_singlethread)(
                url, save_path, auth_headers, auth_obj, progress_tracker
            )

            # Finish display
            progress_thread.join(timeout=1.0)
            final_progress = progress_tracker.get_progress()
            progress_display.finish(final_progress, success=success)

            if success:
                if self.verbose:
                    total_time = time.time() - start_time
                    self._log(f"Download completed in {total_time:.2f}s ({total_time/60:.1f}min)")
            else:
                # Clean up partial files on failure
                self._cleanup_partial_files(save_path, self.config.num_threads)

            return success

        except KeyboardInterrupt:
            if 'progress_thread' in locals():
                progress_thread.join(timeout=0.5)
            if 'progress_tracker' in locals() and 'progress_display' in locals():
                progress_display.finish(progress_tracker.get_progress(), success=False)
            self._log("\n❌ Download cancelled")
            self._cleanup_partial_files(save_path, self.config.num_threads)
            return False
        except Exception as e:
            self._log(f"Download failed: {str(e)}")
            self._cleanup_partial_files(save_path, self.config.num_threads)
            return False
        finally:
            if self._original_sigint_handler:
                signal.signal(signal.SIGINT, self._original_sigint_handler)
            self._progress_tracker = None

    def _get_file_size(self, url, headers, auth) -> int:
        """Get file size from server."""
        for method in [requests.head, lambda *args, **kwargs: requests.get(*args, stream=True, **kwargs)]:
            try:
                response = method(url, headers=headers, auth=auth, timeout=self.config.timeout, 
                                verify=self.config.verify_ssl)
                content_length = response.headers.get("Content-Length")
                if hasattr(response, 'close'):
                    response.close()
                if content_length:
                    return int(content_length)
            except:
                pass
        return 0

    def _check_range_support(self, url, headers, auth) -> bool:
        """Check if server supports Range requests."""
        try:
            test_headers = headers.copy()
            test_headers["Range"] = "bytes=0-1"
            response = requests.head(url, headers=test_headers, auth=auth, timeout=self.config.timeout, 
                                   verify=self.config.verify_ssl)
            return (response.headers.get("Accept-Ranges", "").lower() == "bytes" 
                    or response.status_code == 206 
                    or "Content-Range" in response.headers)
        except:
            return False

    def _download_singlethread(
        self,
        url: str,
        save_path: str,
        headers: Dict[str, str],
        auth: Optional[AuthBase],
        progress_tracker: ProgressTracker,
    ) -> bool:
        """Download file using single thread."""
        try:
            # Check cancellation before starting
            if progress_tracker.is_cancelled():
                return False
                
            # Use interruptible request method
            response = self._make_interruptible_request(
                url, headers, auth, progress_tracker, stream=True
            )
            
            if response is None:
                return False

            with open(save_path, "wb") as file:
                chunk_size = min(self.config.chunk_size, 8192)
                
                for chunk in response.iter_content(chunk_size=chunk_size, decode_unicode=False):
                    if progress_tracker.is_cancelled():
                        response.close()
                        return False
                    if chunk:
                        file.write(chunk)
                        progress_tracker.update(len(chunk))

            response.close()
            return True

        except KeyboardInterrupt:
            raise
        except Exception as e:
            self._log(f"Single-thread download error: {str(e)}")
            return False

    def _download_multithread(
        self,
        url: str,
        save_path: str,
        headers: Dict[str, str],
        auth: Optional[AuthBase],
        progress_tracker: ProgressTracker,
    ) -> bool:
        """Download file using multiple threads."""
        try:
            # Calculate ranges for each thread
            file_size = progress_tracker.total_bytes
            part_size = file_size // self.config.num_threads
            ranges = []

            for i in range(self.config.num_threads):
                start = i * part_size
                end = (
                    start + part_size - 1
                    if i < self.config.num_threads - 1
                    else file_size - 1
                )
                ranges.append((start, end, i))

            # Download parts in parallel
            with ThreadPoolExecutor(max_workers=self.config.num_threads) as executor:
                futures = [
                    executor.submit(
                        self._download_part,
                        url,
                        start,
                        end,
                        save_path,
                        part_num,
                        headers,
                        auth,
                        progress_tracker,
                    )
                    for start, end, part_num in ranges
                ]

                # Wait for all downloads to complete with periodic cancellation checks
                try:
                    all_success = True
                    for future in futures:
                        try:
                            # Check cancellation frequently while waiting
                            while not future.done():
                                if progress_tracker.is_cancelled():
                                    # Cancel all remaining futures
                                    for f in futures:
                                        f.cancel()
                                    return False
                                time.sleep(0.05)  # Check every 50ms
                            
                            # Get the result after future is done
                            result = future.result(timeout=1.0)
                            if not result:
                                all_success = False
                                break
                        except KeyboardInterrupt:
                            # Immediately cancel all futures
                            for f in futures:
                                f.cancel()
                            raise
                        except Exception as e:
                            self._log(f"Error in future: {str(e)}")
                            all_success = False
                            break
                    
                    if not all_success:
                        return False
                        
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    self._log(f"Error waiting for download parts: {str(e)}")
                    return False

            # Merge parts
            return self._merge_parts(save_path, self.config.num_threads)

        except Exception as e:
            self._log(f"Multi-thread download error: {str(e)}")
            return False

    def _download_part(
        self,
        url: str,
        start: int,
        end: int,
        save_path: str,
        part_num: int,
        headers: Dict[str, str],
        auth: Optional[AuthBase],
        progress_tracker: ProgressTracker,
    ) -> bool:
        """Download a specific part of the file."""
        try:
            # Check cancellation before starting
            if progress_tracker.is_cancelled():
                return False
                
            part_headers = headers.copy()
            part_headers["Range"] = f"bytes={start}-{end}"

            # Use interruptible request method
            response = self._make_interruptible_request(
                url, part_headers, auth, progress_tracker, stream=True
            )
            
            if response is None:
                return False

            if response.status_code != 206:
                raise Exception(
                    f"Server returned {response.status_code} instead of 206"
                )

            part_path = f"{save_path}.part{part_num}"
            with open(part_path, "wb") as file:
                chunk_size = min(self.config.chunk_size, 8192)
                
                for chunk in response.iter_content(chunk_size=chunk_size, decode_unicode=False):
                    if progress_tracker.is_cancelled():
                        response.close()
                        return False
                    if chunk:
                        file.write(chunk)
                        progress_tracker.update(len(chunk))

            response.close()
            return True

        except KeyboardInterrupt:
            raise
        except Exception as e:
            self._log(f"Error downloading part {part_num}: {str(e)}")
            return False

    def _merge_parts(self, save_path: str, num_parts: int) -> bool:
        """Merge downloaded parts into final file."""
        try:
            with open(save_path, "wb") as output_file:
                for i in range(num_parts):
                    part_path = f"{save_path}.part{i}"
                    if os.path.exists(part_path):
                        with open(part_path, "rb") as part_file:
                            output_file.write(part_file.read())
                        os.remove(part_path)
                    else:
                        self._log(f"Warning: Part file {part_path} not found")
                        return False

            return True

        except Exception as e:
            self._log(f"Error merging parts: {str(e)}")
            return False

    def _cleanup_partial_files(
        self, save_path: str, num_parts: Optional[int] = None
    ) -> None:
        """Clean up any partial files on cancellation or error."""
        try:
            # Remove main file if incomplete
            if os.path.exists(save_path):
                os.remove(save_path)

            # Remove part files
            if num_parts is not None:
                for i in range(num_parts):
                    part_path = f"{save_path}.part{i}"
                    if os.path.exists(part_path):
                        os.remove(part_path)
            else:
                # If we don't know how many parts, scan for them
                import glob
                pattern = f"{save_path}.part*"
                for part_file in glob.glob(pattern):
                    if os.path.exists(part_file):
                        os.remove(part_file)
        except Exception as e:
            self._log(f"Warning: Could not clean up partial files: {str(e)}")

    def _monitor_progress(
        self, progress_tracker: ProgressTracker, progress_display: ProgressDisplay
    ) -> None:
        """Monitor and display progress in separate thread."""
        while not progress_tracker.is_complete() and not progress_tracker.is_cancelled():
            progress = progress_tracker.get_progress()
            progress_display.update(progress)
            time.sleep(self.config.progress_update_interval)

    def _make_interruptible_request(
        self,
        url: str,
        headers: Dict[str, str],
        auth: Optional[AuthBase],
        progress_tracker: ProgressTracker,
        stream: bool = True,
    ) -> Optional[requests.Response]:
        """Make an HTTP request that can be interrupted more easily."""
        # Check cancellation before starting
        if progress_tracker.is_cancelled():
            return None
            
        try:
            # Use standard timeout for the request
            # The interruptibility comes from checking is_cancelled() during chunk iteration
            response = requests.get(
                url,
                headers=headers,
                auth=auth,
                stream=stream,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
            
            # Check cancellation right after request
            if progress_tracker.is_cancelled():
                response.close()
                return None
                
            response.raise_for_status()
            return response
            
        except KeyboardInterrupt:
            # Propagate keyboard interrupt immediately
            raise
            
        except Exception as e:
            self._log(f"Request failed: {str(e)}")
            return None

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)


def main():
    """Command-line interface for the downloader."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Multi-threaded file downloader with progress tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic download
  python downloader.py https://example.com/file.zip -o file.zip

  # Download with authentication
  python downloader.py https://example.com/file.zip -o file.zip -u user -p pass

  # Download with Bearer token
  python downloader.py https://example.com/file.zip -o file.zip -t your_token

  # Custom configuration
  python downloader.py https://example.com/file.zip -o file.zip --threads 8 --chunk-size 16384

  # Quiet mode (no progress display)
  python downloader.py https://example.com/file.zip -o file.zip -q
        '''
    )
    
    # Required arguments
    parser.add_argument('url', help='URL of the file to download')
    parser.add_argument('-o', '--output', help='Output file path (default: extract filename from URL and save to current directory)')
    
    # Authentication options
    auth_group = parser.add_argument_group('authentication options')
    auth_group.add_argument('-u', '--username', help='Username for Basic authentication')
    auth_group.add_argument('-p', '--password', help='Password for Basic authentication')
    auth_group.add_argument('-t', '--token', help='Bearer token for authentication')
    
    # Download configuration
    config_group = parser.add_argument_group('download configuration')
    config_group.add_argument('--threads', type=int, default=4, 
                             help='Number of parallel download threads (default: 4)')
    config_group.add_argument('--chunk-size', type=int, default=8192,
                             help='Chunk size in bytes (default: 8192)')
    config_group.add_argument('--timeout', type=int, default=30,
                             help='Request timeout in seconds (default: 30)')
    config_group.add_argument('--verify-ssl', action='store_true',
                             help='Enable SSL certificate verification (default: disabled)')
    
    # Display options
    display_group = parser.add_argument_group('display options')
    display_group.add_argument('-q', '--quiet', action='store_true',
                              help='Quiet mode - no progress display')
    display_group.add_argument('--no-verbose', action='store_true',
                              help='Disable verbose logging')
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Extract filename from URL
        from urllib.parse import urlparse, unquote
        parsed_url = urlparse(args.url)
        filename = os.path.basename(unquote(parsed_url.path))
        
        # If we can't extract a filename, use a default
        if not filename or filename == '/':
            filename = 'downloaded_file'
        
        output_path = os.path.join(os.getcwd(), filename)
    
    # Validate authentication options
    if args.username and not args.password:
        parser.error('--username requires --password')
    if args.password and not args.username:
        parser.error('--password requires --username')
    
    # Create configuration
    config = DownloadConfig(
        num_threads=args.threads,
        chunk_size=args.chunk_size,
        timeout=args.timeout,
        verify_ssl=args.verify_ssl
    )
    
    # Create downloader
    downloader = Downloader(config=config, verbose=not args.no_verbose)
    
    # Print download info
    if not args.quiet and not args.no_verbose:
        print("=" * 60)
        print("Multi-threaded File Downloader")
        print("=" * 60)
        print(f"URL: {args.url}")
        print(f"Output: {output_path}")
        if args.username:
            print(f"Authentication: Basic Auth (user: {args.username})")
        elif args.token:
            print(f"Authentication: Bearer Token")
        print(f"Threads: {args.threads}")
        print(f"Chunk size: {args.chunk_size} bytes")
        print("=" * 60)
        print()
    
    # Perform download
    try:
        success = downloader.download(
            url=args.url,
            save_path=output_path,
            username=args.username,
            password=args.password,
            token=args.token,
            display_progress=not args.quiet
        )
        
        if success:
            if not args.quiet:
                print(f"\n✅ Download completed successfully!")
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    file_size_mb = file_size / (1024 * 1024)
                    print(f"📁 File: {output_path}")
                    print(f"📊 Size: {file_size_mb:.1f} MB ({file_size:,} bytes)")
            return 0
        else:
            if not args.quiet:
                print("\n❌ Download failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n🛑 Download interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
