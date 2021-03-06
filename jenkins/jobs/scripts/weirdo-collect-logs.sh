# weirdo-collect-logs.sh
# A script to collect logs generated by a weirdo job
pushd $WORKSPACE/weirdo
export ARA_DATABASE_NAME="$WORKSPACE/$JOB_NAME.sqlite"
# Don't fail script execution even if log collection fails -- the node needs to be destroyed afterwards
tox -e ansible-playbook -- -vv -i $WORKSPACE/hosts playbooks/logs-ci-centos.yml -e ci_environment=ci-centos || true
popd
