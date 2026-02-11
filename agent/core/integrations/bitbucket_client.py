import requests
import time
from typing import List, Dict, Optional
from pathlib import Path
import fnmatch

class BitbucketClient:
    def __init__(self, workspace: str, token: str, base_url: str = "https://api.bitbucket.org/2.0"):
        self.workspace = workspace
        self.token = token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        })
    
    def get_repository_tree(self, repo_slug: str, branch: str = "main", path: str = "") -> List[Dict]:
        url = f"{self.base_url}/repositories/{self.workspace}/{repo_slug}/src/{branch}/{path}"
        all_files = []
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            if 'values' in data:
                for item in data['values']:
                    if item['type'] == 'commit_file':
                        all_files.append({
                            'path': item['path'],
                            'size': item.get('size', 0),
                            'type': 'file'
                        })
                    elif item['type'] == 'commit_directory':
                        sub_files = self.get_repository_tree(
                            repo_slug, branch, item['path']
                        )
                        all_files.extend(sub_files)
            time.sleep(0.1)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repository tree: {e}")
            raise
        return all_files
    
    def get_file_content(self, repo_slug: str, file_path: str, branch: str = "main") -> str:
        url = f"{self.base_url}/repositories/{self.workspace}/{repo_slug}/src/{branch}/{file_path}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching file {file_path}: {e}")
            raise
    
    def filter_files_by_pattern(self, files: List[Dict], pattern: str) -> List[Dict]:
        filtered = []
        for file in files:
            if fnmatch.fnmatch(file['path'], pattern):
                filtered.append(file)
        return filtered
    
    def fetch_code_files(self, repo_slug: str, branch: str, path_pattern: str) -> List[Dict]:
        all_files = self.get_repository_tree(repo_slug, branch)
        matching_files = self.filter_files_by_pattern(all_files, path_pattern)
        code_files = []
        for file_meta in matching_files:
            print(f"Fetching: {file_meta['path']}")
            try:
                content = self.get_file_content(repo_slug, file_meta['path'], branch)
                code_files.append({
                    'path': file_meta['path'],
                    'content': content,
                    'size': file_meta['size']
                })
                time.sleep(0.1)
            except Exception as e:
                print(f"Warning: Could not fetch {file_meta['path']}: {e}")
        return code_files
    
    def get_readme(self, repo_slug: str, branch: str = "main", readme_path: str = "README.md") -> Optional[str]:
        try:
            return self.get_file_content(repo_slug, readme_path, branch)
        except:
            return None

if __name__ == "__main__":
    from agent.config.settings import settings
    
    client = BitbucketClient(
        workspace=settings.migration.source_workspace,
        token=settings.bitbucket.token
    )
    
    files = client.fetch_code_files(
        repo_slug=settings.migration.source_repo_slug,
        branch=settings.migration.source_branch,
        path_pattern=settings.migration.source_path_pattern
    )
    
    print(f"Fetched {len(files)} files")
