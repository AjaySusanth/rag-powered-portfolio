"""
DESIGN DECISION:
This module provides a fetch layer to download project documents from GitHub.
It parses ingest.yml configurations, queries the GitHub Git Trees API to find files
matching glob patterns, and fetches them asynchronously using HTTPX.

We implement path glob matching by recursively expanding double asterisks (**) into
varying depths of single-asterisk (*) path segments, allowing us to leverage
pathlib.PurePosixPath.match() directly as mandated by the project constraints.
We fetch raw file data using the GitHub Blobs API via the 'application/vnd.github.v3.raw'
media type, which bypasses path-encoding edge cases and base64 parsing overhead.
"""

import logging
import yaml
import httpx
import asyncio
from pathlib import Path, PurePosixPath
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from src.config import settings

# Setup logger
logger = logging.getLogger(__name__)

# Common binary file extensions to skip
BINARY_EXTENSIONS = {
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.tiff', '.webp',
    # Documents
    '.pdf', '.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp',
    # Archives/compression
    '.zip', '.tar', '.gz', '.tgz', '.bz2', '.xz', '.rar', '.7z',
    # Executables/binaries
    '.exe', '.dll', '.so', '.dylib', '.bin', '.out', '.class', '.pyc', '.pyd',
    # Audio/Video
    '.mp3', '.wav', '.mp4', '.avi', '.mkv', '.mov', '.flv', '.webm',
    # Databases/stores
    '.db', '.sqlite', '.sqlite3', '.dat',
    # Fonts
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
}


class GitHubIngestionError(Exception):
    """Raised for unrecoverable failures during GitHub ingestion."""
    pass


@dataclass
class GitHubDocument:
    """Strongly typed representation of a fetched GitHub document."""
    path: str
    content: str
    project: str
    source_type: str = "github"


def parse_ingest_yaml(yaml_path: str) -> Dict[str, Any]:
    """
    Parses the ingest.yml configuration from the filesystem.
    Extracts project name, GitHub repository, auto_ingest globs, and ignore globs.
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data:
            raise GitHubIngestionError(f"Configuration file is empty: {yaml_path}")
            
        project = data.get("project")
        github_repo = data.get("github_repo")
        
        if not project or not github_repo:
            raise GitHubIngestionError(
                f"Missing required fields 'project' or 'github_repo' in {yaml_path}"
            )
            
        # Ensure we have lists for globs
        auto_ingest = data.get("auto_ingest") or []
        ignore = data.get("ignore") or []
        
        if isinstance(auto_ingest, str):
            auto_ingest = [auto_ingest]
        if isinstance(ignore, str):
            ignore = [ignore]
            
        return {
            "project": project,
            "github_repo": github_repo,
            "auto_ingest": auto_ingest,
            "ignore": ignore
        }
    except FileNotFoundError:
        raise GitHubIngestionError(f"Configuration file not found: {yaml_path}")
    except yaml.YAMLError as e:
        raise GitHubIngestionError(f"Failed to parse YAML in {yaml_path}: {e}")
    except Exception as e:
        raise GitHubIngestionError(f"Unexpected error loading configuration: {e}")


def is_binary_file(filename: str) -> bool:
    """Checks if a file extension is in our list of common binary extensions."""
    suffix = Path(filename).suffix.lower()
    return suffix in BINARY_EXTENSIONS


def expand_pattern(pattern: str, max_depth: int) -> List[str]:
    """
    Recursively expands double asterisks (**) into different combinations of '*'
    to allow standard pathlib.PurePosixPath.match() to evaluate it correctly.
    
    Explanation of approach:
    Since Python <3.13 PurePosixPath.match() does not recursively match '**' inside paths,
    we expand any '**' in the pattern into 0 to max_depth segments of '*' (e.g. '', '*', '*/*', etc.).
    """
    if '**' not in pattern:
        return [pattern]
        
    parts = pattern.split('**', 1)
    prefix = parts[0]
    suffix = parts[1]
    
    results = []
    for k in range(max_depth + 1):
        if k == 0:
            # Collapse double asterisk
            if prefix == '':
                expanded = suffix.lstrip('/')
            elif suffix == '':
                expanded = prefix.rstrip('/')
            elif prefix.endswith('/') and suffix.startswith('/'):
                expanded = prefix + suffix[1:]
            else:
                expanded = prefix + suffix
        else:
            stars = '/'.join(['*'] * k)
            expanded = prefix + stars + suffix
            
        # Recursively expand remaining '**' in the suffix
        results.extend(expand_pattern(expanded, max_depth))
    return results


def match_pattern(path: str, pattern: str) -> bool:
    """
    Matches a path against a glob pattern using pathlib.PurePosixPath.match().
    Expands '**' recursively to support deep matching.
    """
    p = PurePosixPath(path)
    max_depth = len(p.parts)
    
    # We expand '**' in the pattern based on the path's depth
    expanded_patterns = expand_pattern(pattern, max_depth)
    
    for ep in set(expanded_patterns):
        # Normalize double slashes
        while '//' in ep:
            ep = ep.replace('//', '/')
        if p.match(ep):
            return True
            
    return False


def _match_path(path: str, includes: List[str], ignores: List[str]) -> bool:
    """
    Determines if a path matches the inclusion patterns and does not match
    any exclusion patterns.
    """
    # 1. Check ignores first
    for ignore in ignores:
        if match_pattern(path, ignore):
            return False
            
    # 2. Check inclusions
    for include in includes:
        if match_pattern(path, include):
            return True
            
    return False


async def fetch_github_repository(yaml_path: str) -> List[GitHubDocument]:
    """
    Reads ingest.yml, queries the GitHub REST API to discover matching files,
    downloads their raw contents, and returns a list of GitHubDocuments.
    """
    config = parse_ingest_yaml(yaml_path)
    project = config["project"]
    repo = config["github_repo"]
    includes = config["auto_ingest"]
    ignores = config["ignore"]
    
    # Prepare headers for GitHub API
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "antigravity-portfolio-ingester"
    }
    
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Fetch repository information to find the default branch
        repo_url = f"https://api.github.com/repos/{repo}"
        try:
            resp = await client.get(repo_url, headers=headers)
            if resp.status_code == 401:
                raise GitHubIngestionError(f"GitHub authentication failed. Check GITHUB_TOKEN.")
            elif resp.status_code == 403:
                # Check for rate limit
                rate_limit_remaining = resp.headers.get("X-RateLimit-Remaining")
                if rate_limit_remaining == "0":
                    raise GitHubIngestionError("GitHub API rate limit exceeded.")
                raise GitHubIngestionError(f"Access forbidden: {resp.text}")
            elif resp.status_code == 404:
                raise GitHubIngestionError(f"Repository not found: {repo}")
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise GitHubIngestionError(f"Failed to fetch repository metadata for {repo}: {e}")
            
        repo_data = resp.json()
        default_branch = repo_data.get("default_branch", "main")
        
        # 2. Fetch the file tree recursively
        tree_url = f"https://api.github.com/repos/{repo}/git/trees/{default_branch}?recursive=1"
        try:
            resp = await client.get(tree_url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise GitHubIngestionError(f"Failed to fetch file tree for {repo}: {e}")
            
        tree_data = resp.json()
        tree = tree_data.get("tree", [])
        
        # 3. Filter files using inclusions, ignores, and binary checks
        matched_items = []
        
        # Keep track of which inclusion patterns matched something
        matched_patterns = {pattern: False for pattern in includes}
        
        for item in tree:
            if item.get("type") != "blob":
                continue
                
            path = item.get("path", "")
            
            # Skip common binary extensions
            if is_binary_file(path):
                continue
                
            # Check pattern match
            is_matched = False
            for include in includes:
                if match_pattern(path, include):
                    # Check ignores
                    should_ignore = False
                    for ignore in ignores:
                        if match_pattern(path, ignore):
                            should_ignore = True
                            break
                    if not should_ignore:
                        is_matched = True
                        matched_patterns[include] = True
                        
            if is_matched:
                matched_items.append((path, item.get("sha")))
                
        # Log include patterns that matched zero files
        for pattern, matched in matched_patterns.items():
            if not matched:
                logger.warning(
                    f"Glob pattern '{pattern}' matched zero files in repository '{repo}'."
                )
                
        # 4. Fetch file contents concurrently using the blob API with a concurrency limit
        sem = asyncio.Semaphore(10)
        
        async def fetch_file(path: str, sha: str) -> Optional[GitHubDocument]:
            async with sem:
                blob_url = f"https://api.github.com/repos/{repo}/git/blobs/{sha}"
                # Request raw content directly
                blob_headers = headers.copy()
                blob_headers["Accept"] = "application/vnd.github.v3.raw"
                
                try:
                    resp = await client.get(blob_url, headers=blob_headers)
                    resp.raise_for_status()
                    
                    # Attempt to decode as UTF-8 (filters out binary files)
                    content = resp.content.decode('utf-8')
                    return GitHubDocument(
                        path=path,
                        content=content,
                        project=project
                    )
                except UnicodeDecodeError:
                    logger.info(f"Skipping file {path} as it could not be decoded as UTF-8 text.")
                    return None
                except Exception as e:
                    logger.error(f"Failed to fetch content for file {path} (SHA: {sha}): {e}")
                    return None
                    
        tasks = [fetch_file(path, sha) for path, sha in matched_items]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results
        documents = [doc for doc in results if doc is not None]
        return documents
