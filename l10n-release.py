#!/usr/bin/env python

import os
import math
import argparse
import inflect
from github import Github
from jinja2 import Template

MAIN_REPO = 'kubernetes/website'
TEST_REPO = 'cstoku/kwebsite'

parser = argparse.ArgumentParser(description='Japanese l10n Release PR Submit Script.')
parser.add_argument('head_branch', help='Head branch(eg. dev-1.13-ja.1)')
parser.add_argument('base_branch', help='Base branch(eg. master)')
parser.add_argument('-s', '--submit', action='store_true')
parser.add_argument('-t', '--test', action='store_true')
args = parser.parse_args()
p = inflect.engine()

data = {}
TEMPLATE_TITLE='{{ milestone }} Japanese l10n work for release-{{ version }}'
TEMPLATE_COMMENT='''
{{ milestone }} Japanese l10n work for release-{{ version }}.

<details>
  <summary><b>Change List</b></summary>
  <ul>
    {%- for pr in prs %}
    <li>{{ pr.title }} (<a href="{{ pr.html_url }}" target="_blank">#{{ pr.number }}</a>)</li>
    {%- endfor %}
  </ul>
</details>
<br>

{% for user in coauthors -%}
Co-authored-by: {{ '@' if mention }}{{ user }}
{% endfor -%}
'''


token = os.getenv('GITHUB_API_TOKEN')

g = Github(token)
repo = g.get_repo(MAIN_REPO)

prs = repo.get_pulls(state='all', base=args.head_branch, direction='asc')

open_prs = [pr for pr in prs if pr.state == 'open']

if open_prs:
    print('There seems to be work that hasn\'t been closed yet.')

milestone_ordinal = p.ordinal(args.head_branch.split('-')[2].split('.')[1])

data['version'] = args.head_branch.split('-')[1]
data['milestone'] = p.number_to_words(milestone_ordinal).capitalize()
data['prs'] = [pr for pr in prs if pr.merged]
data['coauthors'] = set([pr.user.login for pr in data['prs'] if pr.user.login != 'cstoku'])
template_title = Template(TEMPLATE_TITLE.strip())
template_comment = Template(TEMPLATE_COMMENT.strip())
pr_title = template_title.render(data)

if args.test:
    print('test submit...')
    data['mention'] = False
    pr_comment = template_comment.render(data)
    test_repo = g.get_repo(TEST_REPO)
    test_repo.create_pull(
        title=pr_title,
        body=pr_comment,
        base=args.base_branch,
        head=args.head_branch,
        maintainer_can_modify=True
    )
elif args.submit:
    print('submit...')
    data['mention'] = True
    pr_comment = template_comment.render(data)
    main_repo = g.get_repo(MAIN_REPO)
    main_repo.create_pull(
        title=pr_title,
        body=pr_comment,
        base=args.base_branch,
        head=args.head_branch,
        maintainer_can_modify=True
    )
else:
    data['mention'] = True
    pr_comment = template_comment.render(data)
    print('Title: ')
    print('\t' + pr_title)
    print('Comment:')
    for line in pr_comment.split('\n'):
        if line:
            print('\t' + line)
        else:
            print()
