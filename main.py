from git import Repo

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

l10n_contents = [blob.path.replace('content/ja/', '', 1) for blob in head_commit.tree.list_traverse() if blob.path.startswith('content/ja/')]

for obj in base_diff:
    if obj.a_path and obj.a_path.startswith('content/en/'):
        print('{} => {}'.format(obj.a_path, obj.b_path))

