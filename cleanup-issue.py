import os
import re
import argparse
from git import Repo
from github import Github
from jinja2 import Template

TEST_REPO = 'cstoku/kwebsite'

token = os.getenv('GITHUB_API_TOKEN')
g = Github(token)
repo = g.get_repo(TEST_REPO)

for issue in repo.get_issues():
    issue.edit(state='closed')
