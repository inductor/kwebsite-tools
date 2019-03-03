from git import Repo

repo = Repo('./website')
origin = repo.remote()
#origin.fetch()

print(origin.refs.master)
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
        #print('{}({} > {}): {}'.format(head_ref, bc.committed_date, hc.committed_date, hc))
        hc = hc.parents[0]
    else:
        #print('{}({} < {}): {}'.format(origin.refs.master, bc.committed_date, hc.committed_date, bc))
        bc = bc.parents[0]

branch_point = bc
base_diff = branch_point.diff(base_commit, create_patch=True)

for obj in base_diff[:10]:
    print(obj.change_type)
    print('Path: {} => {}'.format(obj.a_path, obj.b_path))
    print('Blob: {} => {}'.format(obj.a_blob, obj.b_blob))
    print(obj.diff.decode())

