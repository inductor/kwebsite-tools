from git import Repo

upstream_lang_code = 'en'
localize_lang_code = 'ja'

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



repo = Repo('./website')
origin = repo.remote()
#origin.fetch()

head_ref = None
for ref in origin.refs:
    if ref.remote_head == 'dev-1.13-ja.1':
        head_ref = ref
        break

if head_ref is None:
    print('Not found ref.')
    exit(1)

base_commit = origin.refs.master.commit
head_commit = head_ref.commit

bc = base_commit
hc = head_commit
while not bc == hc:
    if bc.committed_date < hc.committed_date:
        hc = hc.parents[0]
    else:
        bc = bc.parents[0]

branch_point = bc
base_diff = branch_point.diff(base_commit, create_patch=True)

upstream_docs_contents = changed_contents(base_diff, upstream_lang_code, 'docs/')
l10n_docs_contents = list_contents(head_commit, localize_lang_code, 'docs/')
outdated_docs_contents = [
    obj
    for obj in upstream_docs_contents
    if obj.a_path and obj.a_path.replace('content/en/', 'content/ja/', 1) in l10n_docs_contents
]

for obj in outdated_docs_contents:
    if obj.a_path and obj.b_path:
        if obj.a_path == obj.b_path:
            print('Modify: ' + obj.a_path)
        else:
            print('Move: {} => {}'.format(obj.a_path, obj.b_path))
    elif obj.a_path is None:
        print('Create: ' + obj.b_path)
    else:
        print('Remove: ' + obj.a_path)

