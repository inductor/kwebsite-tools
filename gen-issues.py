import os
import re
import argparse
from git import Repo
from github import Github
from jinja2 import Template

MAIN_REPO = 'kubernetes/website'
MAIN_REPO_URL = 'git@github.com:kubernetes/website.git'
TEST_REPO = 'cstoku/kwebsite'
LOCAL_REPO_PATH = './.kwebsite'

MILESTONE_NUM = 31
I18N_LABEL = 'language/ja'

MODIFY_TITLE_TEMPLATE = '''
{%- if urlpath -%}
Update k8s.io/{{ urlpath }}
{%- else -%}
Update {{ i18n_path | replace('content/ja/', '', 1) }}
{%- endif -%}
'''
MODIFY_BODY_TEMPLATE = '''
**This is a...**
- [x] Feature Request
- [ ] Bug Report

**Problem:**

Outdated content `{{ i18n_path }}`.

```
{{ orig_path }}
{%- if insertions %} {{ insertions }} insertion(+){%- endif %}
{%- if insertions and deletions %},{%- endif %}
{%- if deletions %} {{ deletions }} delettion(-){%- endif %}
```

**Proposed Solution:**

Update content `{{ i18n_path }}`.

For details, please execute the following command.

```
git diff {{ bc }} {{ hc }} -- {{ orig_path }}
```

{% if urlpath -%}
**Page to Update:**

https://kubernetes.io/{{ urlpath }}
{% endif -%}
'''
CREATE_TITLE_TEMPLATE = '''
{%- if 'docs/setup/' is in i18n_path -%}
Translate heading and subheading of {{ i18n_path | replace('content/ja/', '', 1) }} in Japanese
{%- else -%}
Translate {{ i18n_path | replace('content/ja/', '', 1) }} in Japanese
{%- endif -%}
'''
CREATE_BODY_TEMPLATE = '''
{% set repl_path = i18n_path | replace('content/ja/', '', 1) %}
**This is a...**
- [x] Feature Request
- [ ] Bug Report

**Problem:**

{% if 'docs/setup/' is in urlpath -%}
No heading and subheading of `{{ repl_path }}` in Japanese.
{% else -%}
No `{{ repl_path }}` in Japanese.
{%- endif %}

**Proposed Solution:**

{% if 'docs/setup/' is in urlpath -%}
Translate heading and subheading of `{{ repl_path }}` in Japanese.
{%- else %}
Translate `{{ repl_path }}` in Japanese.
{%- endif %}

Copy from en content and Update `{{ i18n_path }}`.


{% if urlpath -%}
**Page to Update:**

https://kubernetes.io/{{ urlpath }}
{% endif -%}
'''
REMOVE_TITLE_TEMPLATE = ''
REMOVE_BODY_TEMPLATE = '''
'''

upstream_lang_code = 'en'
localize_lang_code = 'ja'

class L10nContents:
    def __init__(self, commit, lang_code):
        pass

    def outdated_contents(self, commit, upstream_lang_code):
        pass

    def new_contents(self, commit, upstream_lang_code):
        pass

    def remove_contents(self, commit, upstream_lang_code):
        pass

    def changed_contents(self, commit):
        pass

    def contents(self):
        pass

class L10nContentDiff:
    def __init__(self, obj, lang_code):
        self.obj = obj
        self.lang_code = lang_code

    def is_update(self):
        pass

    def is_outdated(self, lang_code):
        pass

    def change_type(self):
        pass

    def __getattr__(self, name):
        return getattr(self.obj, name)

def changed_contents(diffs, lang_code, prefix=''):
    contents_path = 'content/{}/{}'.format(lang_code, prefix)
    checker = lambda x: x and x.startswith(contents_path)
    return [
        obj
        for obj in base_diff
        if checker(obj.a_path) or checker(obj.b_path)
    ]

def list_contents(commit, lang_code, prefix=''):
    contents_path = 'content/{}/{}'.format(lang_code, prefix)
    return [
        obj.path
        for obj in commit.tree.list_traverse()
        if obj.type == 'blob' and obj.path.startswith(contents_path)
    ]

def to_urlpath(content_path):
    if not (content_path.endswith('.md') or content_path.endswith('.html')):
        return None
    path = re.sub(r'^content/en/', '', content_path, 1)
    tailing_slash = re.sub(r'(/_?index)?\.(md|html)$', '/', path, 1)
    return 'ja/' + tailing_slash


parser = argparse.ArgumentParser(description='Japanese l10n Diff Detail Generator Script???')
parser.add_argument('pr_number', type=int, help='Target pull request number')
parser.add_argument('-s', '--startcommit', help='Target pull request number')
args = parser.parse_args()

token = os.getenv('GITHUB_API_TOKEN')

g = Github(token)
grepo = g.get_repo(MAIN_REPO)
trepo = g.get_repo(TEST_REPO)
milestone = grepo.get_milestone(MILESTONE_NUM)
i18n_label = grepo.get_label(I18N_LABEL)

pr = grepo.get_pull(args.pr_number)

if not pr.merged or pr.base.repo != pr.head.repo:
    print('Not Support...')
    exit(1)

if os.path.exists(LOCAL_REPO_PATH):
    repo = Repo(LOCAL_REPO_PATH)
else:
    repo = Repo.clone_from(MAIN_REPO_URL, LOCAL_REPO_PATH, bare=True)

base_ref = args.startcommit if args.startcommit else pr.merge_commit_sha
base_commit = None
try:
    base_commit = repo.commit(base_ref)
except:
    repo.remotes.origin.fetch(base_ref)
finally:
    base_commit = repo.commit(base_ref)

head_commit = None
try:
    head_commit = repo.commit(pr.head.sha)
except:
    repo.remotes.origin.fetch(pr.head.sha)
finally:
    head_commit = repo.commit(pr.head.sha)

bc = base_commit
hc = head_commit
while not bc == hc:
    if bc.committed_date < hc.committed_date:
        hc = hc.parents[0]
    else:
        bc = bc.parents[0]

branch_point = bc
base_diff = branch_point.diff(base_commit, create_patch=True)
print(branch_point)
#exit()

# Check 1. Outdated Localization Contents Check.
#print('Check 1. Outdated Localization Contents Check.')
upstream_docs_contents = changed_contents(base_diff, upstream_lang_code, 'docs/')
l10n_docs_contents = list_contents(head_commit, localize_lang_code, 'docs/')
outdated_docs_contents = [
    obj
    for obj in upstream_docs_contents
    if obj.a_path and obj.a_path.replace('content/en/', 'content/ja/', 1) in l10n_docs_contents
]

create_contents = []
modify_contents = []
remove_contents = []
for obj in outdated_docs_contents:
    diff_type = None
    modify_type = None
    if obj.a_path and obj.b_path:
        diff_type = 'modify'
        #print('Modify: ' + obj.b_path)
        modify_contents.append(obj)
        if obj.a_mode != obj.b_mode:
            #print('\tMode: {} => {}', obj.a_mode, obj.b_mode)
            modify_type = 'mode'
        if obj.a_path != obj.b_path:
            #print('\tPath: {} => {}', obj.a_path, obj.b_path)
            modify_type = 'move'
        if obj.a_blob != obj.b_blob:
            #print('\tBlob: changed')
            modify_type = 'modify'
    elif obj.b_path is None:
        #print('Remove: ' + obj.a_path)
        diff_type = 'remove'
        remove_contents.append(obj.a_path)
    else:
        #print('Create...?: ' + obj.b_path)
        diff_type = 'create'

# Check 2. Minimum Localization Check.
#print('Check 2. Minimum Localization Check.')
minimum_checker = lambda x: x.startswith('content/en/docs/home/') or  x.startswith('content/en/docs/setup/') or  x.startswith('content/en/docs/tutorials/kubernetes-basics/')

for obj in upstream_docs_contents:
    if obj.a_path is None and obj.b_path and minimum_checker(obj.b_path):
        #print('Create: ' + obj.b_path)
        create_contents.append(obj)


# Check 3. Site strings check.
#print('Check 3. Site strings check.')
for obj in base_diff:
    if obj.a_path and obj.a_path == 'i18n/en.toml':
        #print('Modify: ' + 'i18n/ja.toml')
        modify_contents.append(obj)

# Option 1. Listup new contents and remove contents.
#print('Option 1. Listup new contents and remove contents.')
for obj in upstream_docs_contents:
    if obj.a_path is None:
        #print('Create: ' + obj.b_path)
        pass
    elif obj.b_path is None:
        #print('Remove: ' + obj.a_path)
        pass



########################
# Outdated Contents... #
########################
print('\nOutdated Contents...')
template_title = Template(MODIFY_TITLE_TEMPLATE.strip())
template_body = Template(MODIFY_BODY_TEMPLATE.strip())
print(len(modify_contents))
for obj in modify_contents:
    content = obj.b_path
    patch_lines = obj.diff.decode().split('\n')
    insertions = len([line for line in patch_lines if line.startswith('+')])
    deletions = len([line for line in patch_lines if line.startswith('-')])
    i18n_path = re.sub(r'^(content|i18n)/en', r'\1/ja', content, 1)
    issue_title = template_title.render(
            i18n_path=i18n_path,
            urlpath=to_urlpath(content)
        )
    issue_body = template_body.render(
            orig_path=content,
            i18n_path=i18n_path,
            insertions=insertions,
            deletions=deletions,
            bc=branch_point.hexsha[:7],
            hc=base_commit.hexsha[:7],
            urlpath=to_urlpath(content)
        )
    #print('Issue Title: ' + issue_title)
    #print('Issue Body:\n' + issue_body)
    #print()
    grepo.create_issue(issue_title, issue_body, milestone=milestone, labels=[i18n_label])
    print('Created Issue: ' + issue_title)

#########################################
# Added Minimum Translasion Contents... #
#########################################

print('\nAdded Minimum Translasion Contents...')
template_title = Template(CREATE_TITLE_TEMPLATE.strip())
template_body = Template(CREATE_BODY_TEMPLATE.strip())
print(len(create_contents))
for obj in create_contents:
    content = obj.b_path
    i18n_path = re.sub(r'^(content|i18n)/en', r'\1/ja', content, 1)
    issue_title = template_title.render(i18n_path=i18n_path)
    issue_body = template_body.render(
            i18n_path=i18n_path,
            urlpath=to_urlpath(content)
        )
    #print('Issue Title: ' + issue_title)
    #print('Issue Body:\n' + issue_body)
    #print()
    grepo.create_issue(issue_title, issue_body, milestone=milestone, labels=[i18n_label])
    print('Created Issue: ' + issue_title)

#######################
# Removed Contents... #
#######################
#
#print('\nRemoved Contents...')
#if remove_contents:
#    print(remove_contents)

