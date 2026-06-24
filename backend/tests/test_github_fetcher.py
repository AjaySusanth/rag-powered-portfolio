import pytest
from pathlib import PurePosixPath
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

# Import from the module we are building
from src.ingestion.github_fetcher import (
    match_pattern,
    parse_ingest_yaml,
    GitHubIngestionError,
    fetch_github_repository,
    is_binary_file
)
from src.models.document import Document, determine_document_layer

# -----------------------------------------------------------------------------
# Unit Tests for Matcher (Satisfying Rule 6)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "path,pattern,expected",
    [
        # Exact matching
        ("README.md", "README.md", True),
        # In pathlib.PurePosixPath, relative patterns match from the right side.
        # Thus, README.md matches any path ending in README.md.
        ("n8n-workflows/README.md", "README.md", True),
        ("n8n-workflows/README.md", "n8n-workflows/README.md", True),
        
        # Single wildcard matching
        ("backend/app/services/parser.py", "backend/app/services/*.py", True),
        ("backend/app/services/jd/parser.py", "backend/app/services/*.py", False), # * is non-recursive
        
        # Recursive wildcard matching (**)
        ("frontend/src/components/button.tsx", "frontend/src/components/**/*.tsx", True),
        ("frontend/src/components/common/button.tsx", "frontend/src/components/**/*.tsx", True),
        ("frontend/src/components/common/nested/button.tsx", "frontend/src/components/**/*.tsx", True),
        ("frontend/src/pages/index.tsx", "frontend/src/components/**/*.tsx", False),
        
        # Ignore pattern: node_modules
        ("node_modules/lodash/index.js", "**/node_modules/**", True),
        ("frontend/node_modules/react/index.js", "**/node_modules/**", True),
        ("src/index.js", "**/node_modules/**", False),
        
        # Ignore pattern: .git
        (".git/config", "**/.git/**", True),
        ("src/.git/config", "**/.git/**", True),
        
        # Extension and wildcard ignore
        ("infra/terraform/.terraform/providers/registry/main.tf", "infra/terraform/.terraform/**", True),
        ("infra/terraform/main.tf", "infra/terraform/.terraform/**", False),
        ("infra/terraform/main.tf", "infra/terraform/**/*.tf", True),
        
        # Suffix matching
        ("docs/resume.pdf", "**/*.pdf", True),
        ("docs/resume.pdf", "*.pdf", True), # relative match from right
        ("resume.pdf", "**/*.pdf", True),
    ]
)
def test_match_pattern(path: str, pattern: str, expected: bool):
    """
    Verifies that the glob matching using PurePosixPath.match() behaves correctly
    for various include/ignore patterns found in ingest.yml files.
    """
    assert match_pattern(path, pattern) == expected


# -----------------------------------------------------------------------------
# Unit Tests for Binary File Filtering
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "filename,expected",
    [
        ("resume.pdf", True),
        ("logo.png", True),
        ("archive.zip", True),
        ("main.py", False),
        ("README.md", False),
        ("config.json", False),
        ("NO_EXTENSION", False),
    ]
)
def test_is_binary_file(filename: str, expected: bool):
    assert is_binary_file(filename) == expected


# -----------------------------------------------------------------------------
# Unit Tests for YAML Parsing
# -----------------------------------------------------------------------------

def test_parse_ingest_yaml(tmp_path):
    yaml_content = """
project: test-project
type: fullstack
github_repo: owner/repo
auto_ingest:
  - README.md
  - "src/**/*.py"
ignore:
  - "**/node_modules/**"
  - "*.pdf"
"""
    yaml_file = tmp_path / "ingest.yml"
    yaml_file.write_text(yaml_content)

    config = parse_ingest_yaml(str(yaml_file))
    
    assert config["project"] == "test-project"
    assert config["github_repo"] == "owner/repo"
    assert config["auto_ingest"] == ["README.md", "src/**/*.py"]
    assert config["ignore"] == ["**/node_modules/**", "*.pdf"]


# -----------------------------------------------------------------------------
# Unit Tests for API Interactions
# -----------------------------------------------------------------------------

@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_fetch_github_repository_success(mock_client_class):
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client_class.return_value = mock_client
    
    # 1. Mock repo info call (to get default branch)
    mock_repo_resp = MagicMock()
    mock_repo_resp.status_code = 200
    mock_repo_resp.json.return_value = {"default_branch": "main"}
    
    # 2. Mock tree call
    mock_tree_resp = MagicMock()
    mock_tree_resp.status_code = 200
    mock_tree_resp.json.return_value = {
        "tree": [
            {"path": "README.md", "type": "blob", "sha": "sha_readme"},
            {"path": "src/main.py", "type": "blob", "sha": "sha_main"},
            {"path": "docs/resume.pdf", "type": "blob", "sha": "sha_pdf"},
            {"path": "node_modules/react/index.js", "type": "blob", "sha": "sha_react"},
        ]
    }
    
    # 3. Mock blob content calls
    mock_readme_resp = MagicMock()
    mock_readme_resp.status_code = 200
    mock_readme_resp.content = b"My Readme Content"
    
    mock_main_resp = MagicMock()
    mock_main_resp.status_code = 200
    mock_main_resp.content = b"print('Hello')"
    
    mock_client.get.side_effect = [
        mock_repo_resp,
        mock_tree_resp,
        mock_readme_resp,
        mock_main_resp
    ]
    
    # Mock settings.GITHUB_TOKEN to avoid hitting the actual settings
    with patch("src.ingestion.github_fetcher.settings") as mock_settings:
        mock_settings.GITHUB_TOKEN = "dummy_token"
        
        # Test config
        ingest_config = {
            "project": "test-project",
            "github_repo": "owner/repo",
            "auto_ingest": ["README.md", "src/**/*.py"],
            "ignore": ["**/node_modules/**", "**/*.pdf"]
        }
        
        # We patch parse_ingest_yaml to return our test config
        with patch("src.ingestion.github_fetcher.parse_ingest_yaml", return_value=ingest_config):
            docs = await fetch_github_repository("dummy_path.yml")
            
            assert len(docs) == 2
            assert docs[0].source_file == "README.md"
            assert docs[0].content == "My Readme Content"
            assert docs[0].project == "test-project"
            assert docs[0].source_type == "github"
            assert docs[0].layer == "artifact"
            
            assert docs[1].source_file == "src/main.py"
            assert docs[1].content == "print('Hello')"
            assert docs[1].layer == "artifact"


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_fetch_github_repository_rate_limit(mock_client_class):
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client_class.return_value = mock_client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {"X-RateLimit-Remaining": "0"}
    mock_resp.json.return_value = {"message": "API rate limit exceeded"}
    
    mock_client.get.return_value = mock_resp
    
    # Test config
    ingest_config = {
        "project": "test-project",
        "github_repo": "owner/repo",
        "auto_ingest": ["README.md"],
        "ignore": []
    }
    
    with patch("src.ingestion.github_fetcher.parse_ingest_yaml", return_value=ingest_config):
        with pytest.raises(GitHubIngestionError) as exc_info:
            await fetch_github_repository("dummy_path.yml")
        
    assert "rate limit" in str(exc_info.value).lower()


# -----------------------------------------------------------------------------
# Unit Tests for determine_document_layer
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source_file,source_type,expected_layer",
    [
        ("resume.md", "manual", "identity"),
        ("path/to/about-me.md", "manual", "identity"),
        ("FAQ.md", "manual", "identity"),
        ("architecture.md", "manual", "design"),
        ("decisions.md", "manual", "design"),
        ("challenges.md", "manual", "design"),
        ("lessons-learned.md", "manual", "design"),
        ("approach.md", "github", "design"),
        # README.md should be artifact!
        ("README.md", "github", "artifact"),
        ("path/to/README.md", "github", "artifact"),
        ("main.py", "github", "artifact"),
        ("frontend/src/App.tsx", "github", "artifact"),
    ]
)
def test_determine_document_layer(source_file: str, source_type: str, expected_layer: str):
    assert determine_document_layer(source_file, source_type) == expected_layer
