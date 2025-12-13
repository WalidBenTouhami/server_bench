#!/usr/bin/env python3
"""
Link Verification Script
Verifies all links in markdown files and HTML files in the repository.
Tests both external URLs and internal anchor links.
"""

import re
import sys
import os
import urllib.request
import urllib.error
from typing import List, Dict, Tuple, Set
from pathlib import Path
import time

# ANSI color codes for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class LinkVerifier:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.results = {
            'external_links': {'passed': [], 'failed': []},
            'internal_anchors': {'passed': [], 'failed': []},
            'local_urls': {'passed': [], 'failed': []},
            'badge_urls': {'passed': [], 'failed': []}
        }
        self.headers_cache = {}
        
    def log_info(self, message: str):
        """Print info message"""
        print(f"{BLUE}[INFO]{NC} {message}")
        
    def log_success(self, message: str):
        """Print success message"""
        print(f"{GREEN}[✓]{NC} {message}")
        
    def log_warning(self, message: str):
        """Print warning message"""
        print(f"{YELLOW}[⚠]{NC} {message}")
        
    def log_error(self, message: str):
        """Print error message"""
        print(f"{RED}[✗]{NC} {message}")
        
    def extract_links_from_file(self, filepath: Path) -> Dict[str, List[str]]:
        """Extract all types of links from a file"""
        links = {
            'external': set(),
            'anchors': set(),
            'local': set()
        }
        
        try:
            # Skip very large files (> 1MB) to avoid performance issues
            file_size = filepath.stat().st_size
            if file_size > 1_000_000:
                self.log_warning(f"Skipping large file ({file_size/1_000_000:.1f}MB): {filepath.name}")
                return {k: list(v) for k, v in links.items()}
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Extract external HTTP/HTTPS URLs
            # First, remove all markdown link syntax to avoid double-extraction
            # Keep only the URL part of [text](url) patterns
            cleaned_content = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r' \2 ', content)
            
            # Now extract all HTTP/HTTPS URLs from cleaned content
            external_urls = re.findall(r'https?://[^\s\)<>"\']+', cleaned_content)
            for url in external_urls:
                # Clean up URL (remove trailing punctuation)
                url = url.rstrip('.,;:)')
                links['external'].add(url)
                
            # Extract markdown anchor links from TOC
            anchor_links = re.findall(r'\[.+?\]\(#([a-z0-9\-é]+)\)', content, re.IGNORECASE)
            for anchor in anchor_links:
                links['anchors'].add(anchor)
                
            # Extract local URLs (127.0.0.1, localhost)
            local_urls = re.findall(r'http://(?:127\.0\.0\.1|localhost):[0-9]+[^\s\)<>"\']*', content)
            for url in local_urls:
                url = url.rstrip('.,;:)`|')
                links['local'].add(url)
                
        except Exception as e:
            self.log_error(f"Error reading {filepath}: {e}")
            
        return {k: list(v) for k, v in links.items()}
    
    def build_headers_index(self, filepath: Path) -> Set[str]:
        """Build index of all headers in a markdown file and their anchor equivalents"""
        anchors = set()
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Match markdown headers (## Header Text)
                    match = re.match(r'^#{2,6}\s+(.+)$', line.strip())
                    if match:
                        header_text = match.group(1)
                        # Convert to GitHub anchor format
                        anchor = self.header_to_anchor(header_text)
                        anchors.add(anchor)
                        
        except Exception as e:
            self.log_error(f"Error reading {filepath}: {e}")
            
        return anchors
    
    def header_to_anchor(self, header: str) -> str:
        """Convert markdown header to GitHub anchor format
        GitHub preserves accents but removes emojis and special chars"""
        # Remove emojis (Unicode emoji characters)
        header = re.sub(r'[\U0001F300-\U0001F9FF]', '', header)
        # Remove other special symbols and emojis
        header = re.sub(r'[🎥🚀🧠📊🛠🏗️🧪📈🧹🛑🤖⚙️📡📂👤📜⚡🔧]', '', header)
        # Convert to lowercase
        header = header.lower()
        # Remove special characters but KEEP accents (GitHub preserves them)
        # Keep: alphanumeric, spaces, hyphens, and accented characters
        header = re.sub(r'[^\w\s\-àâäéèêëïîôùûüÿæœç]', '', header)
        # Replace spaces with hyphens
        header = re.sub(r'\s+', '-', header)
        # Remove multiple consecutive hyphens
        header = re.sub(r'-+', '-', header)
        # Strip leading/trailing hyphens
        header = header.strip('-')
        return header
    
    def verify_external_url(self, url: str) -> Tuple[bool, str]:
        """Verify an external URL is accessible"""
        # Skip badge URLs with special handling
        if 'img.shields.io' in url:
            return self.verify_badge_url(url)
            
        try:
            # Create request with proper headers
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Link Checker Bot)',
                    'Accept': '*/*'
                }
            )
            
            # Set timeout to 10 seconds
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True, f"Status {response.status}"
                else:
                    return False, f"Status {response.status}"
                    
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return False, f"URL Error: {e.reason}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def verify_badge_url(self, url: str) -> Tuple[bool, str]:
        """Verify a shields.io badge URL"""
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Badge Checker)',
                    'Accept': 'image/svg+xml,image/*'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    # Verify it's an SVG
                    content_type = response.headers.get('Content-Type', '')
                    if 'svg' in content_type or 'xml' in content_type:
                        return True, f"Valid badge (Status {response.status})"
                    else:
                        return True, f"Status {response.status}"
                else:
                    return False, f"Status {response.status}"
                    
        except Exception as e:
            return False, f"Badge error: {str(e)}"
    
    def verify_anchor_link(self, anchor: str, available_anchors: Set[str]) -> Tuple[bool, str]:
        """Verify an anchor link exists in the document"""
        if anchor in available_anchors:
            return True, "Anchor exists"
        else:
            return False, f"Anchor not found (looking for: {anchor})"
    
    def verify_all_links(self):
        """Main function to verify all links"""
        self.log_info("Starting link verification...")
        
        # Find all markdown and HTML files
        md_files = list(self.repo_path.rglob('*.md'))
        html_files = list(self.repo_path.rglob('*.html'))
        all_files = md_files + html_files
        
        # Exclude certain directories
        excluded_dirs = {'.git', 'node_modules', 'venv', '__pycache__', '.github'}
        all_files = [f for f in all_files if not any(ex in str(f) for ex in excluded_dirs)]
        
        self.log_info(f"Found {len(all_files)} files to check")
        sys.stdout.flush()
        
        # Extract all links
        all_external_links = set()
        all_local_links = set()
        anchor_links_by_file = {}
        
        self.log_info("Extracting links from files...")
        sys.stdout.flush()
        
        for filepath in all_files:
            links = self.extract_links_from_file(filepath)
            all_external_links.update(links['external'])
            all_local_links.update(links['local'])
            if links['anchors']:
                anchor_links_by_file[filepath] = links['anchors']
        
        self.log_info(f"Found {len(all_external_links)} external links, {len(all_local_links)} local URLs")
        sys.stdout.flush()
        
        # Build headers index for README.md
        readme_path = self.repo_path / 'README.md'
        if readme_path.exists():
            self.headers_cache[readme_path] = self.build_headers_index(readme_path)
        
        print("\n" + "="*80)
        print("EXTERNAL LINKS VERIFICATION")
        print("="*80 + "\n")
        
        # Verify external links
        for url in sorted(all_external_links):
            # Skip local URLs (they'll be checked separately)
            if '127.0.0.1' in url or 'localhost' in url:
                continue
                
            # Add small delay to avoid rate limiting
            time.sleep(0.2)
            
            success, message = self.verify_external_url(url)
            
            if 'img.shields.io' in url:
                category = 'badge_urls'
            else:
                category = 'external_links'
                
            if success:
                self.results[category]['passed'].append((url, message))
                self.log_success(f"{url} - {message}")
            else:
                self.results[category]['failed'].append((url, message))
                self.log_error(f"{url} - {message}")
        
        print("\n" + "="*80)
        print("INTERNAL ANCHOR LINKS VERIFICATION")
        print("="*80 + "\n")
        
        # Verify anchor links
        for filepath, anchors in anchor_links_by_file.items():
            self.log_info(f"Checking anchors in {filepath.name}")
            
            if filepath in self.headers_cache:
                available_anchors = self.headers_cache[filepath]
                
                for anchor in sorted(anchors):
                    success, message = self.verify_anchor_link(anchor, available_anchors)
                    
                    if success:
                        self.results['internal_anchors']['passed'].append((anchor, filepath.name))
                        self.log_success(f"#{anchor} - {message}")
                    else:
                        self.results['internal_anchors']['failed'].append((anchor, filepath.name))
                        self.log_error(f"#{anchor} - {message}")
        
        print("\n" + "="*80)
        print("LOCAL URLs (Testing Information)")
        print("="*80 + "\n")
        
        # Report local URLs (these require servers to be running)
        if all_local_links:
            self.log_warning("Local URLs found (require running servers to test):")
            for url in sorted(all_local_links):
                self.log_warning(f"  {url}")
                self.results['local_urls']['passed'].append((url, "Requires running server"))
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80 + "\n")
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.results.items():
            passed = len(results['passed'])
            failed = len(results['failed'])
            total_passed += passed
            total_failed += failed
            
            category_name = category.replace('_', ' ').title()
            print(f"{category_name}:")
            print(f"  {GREEN}✓ Passed: {passed}{NC}")
            print(f"  {RED}✗ Failed: {failed}{NC}")
            print()
        
        print(f"{'='*80}")
        print(f"TOTAL: {GREEN}{total_passed} passed{NC}, {RED}{total_failed} failed{NC}")
        print(f"{'='*80}\n")
        
        if total_failed > 0:
            print(f"{RED}Some links failed verification!{NC}")
            return False
        else:
            print(f"{GREEN}All links verified successfully!{NC}")
            return True

def main():
    """Main entry point"""
    repo_path = os.path.dirname(os.path.abspath(__file__))
    
    verifier = LinkVerifier(repo_path)
    verifier.verify_all_links()
    success = verifier.print_summary()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
