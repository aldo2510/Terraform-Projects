import base64
import os
from urllib.parse import quote
import requests

class GitHubClient:
    def __init__(self):
        self.token = os.environ["GITHUB_TOKEN"]
        self.repo = os.environ["GITHUB_REPOSITORY"]
        self.base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(self, method, path, **kwargs):
        r = requests.request(method, f"{self.base}{path}", headers=self.headers, timeout=30, **kwargs)
        if not r.ok:
            raise RuntimeError(f"GitHub API {r.status_code}: {r.text[:1000]}")
        return r.json()

    def get_file(self, path, ref):
        return self._request("GET", f"/repos/{self.repo}/contents/{quote(path, safe='/')}", params={"ref": ref})

    def create_branch(self, branch, base):
        ref = self._request("GET", f"/repos/{self.repo}/git/ref/heads/{quote(base, safe='')}")
        sha = ref["object"]["sha"]
        self._request("POST", f"/repos/{self.repo}/git/refs", json={"ref": f"refs/heads/{branch}", "sha": sha})
        return sha

    def upsert_file(self, path, content, branch, message):
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch,
        }
        try:
            payload["sha"] = self.get_file(path, branch)["sha"]
        except RuntimeError as exc:
            if "404" not in str(exc):
                raise
        result = self._request("PUT", f"/repos/{self.repo}/contents/{quote(path, safe='/')}", json=payload)
        return result["commit"]["sha"]

    def create_pull_request(self, head, base, title, body):
        return self._request(
            "POST",
            f"/repos/{self.repo}/pulls",
            json={"title": title, "head": head, "base": base, "body": body, "draft": True},
        )
