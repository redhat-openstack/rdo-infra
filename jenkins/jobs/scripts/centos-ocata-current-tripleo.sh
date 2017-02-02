set -e
export RDO_VERSION='centos-ocata'
export DELOREAN_HOST='trunk-primary.rdoproject.org'
export DELOREAN_PUBLIC_HOST='trunk.rdoproject.org'
export DELOREAN_URL="http://$DELOREAN_HOST/centos7-ocata/current-tripleo/delorean.repo"
# The softlinks used in promotion should be cumulative. This job starts w/ current-tripleo
# If the job passes at the rdo level, rdo is appended to the new softlink name.
# End result would be two seperate softlinks e.g. current-tripleo, and current-tripleo-rdo
export LINKNAME='current-tripleo-rdo'
export LAST_PROMOTED_URL="http://$DELOREAN_HOST/centos7-ocata/$LINKNAME/delorean.repo"
export RDO_VERSION_DIR='ocata'
# The LOCATION var is handed off to the ansible-role-tripleo-image build (atrib) role to define where testing/staged images are uploaded
export LOCATION='current-tripleo'  #update to current-tripleo
# The BUILD_SYS var stores what build system was used. It becomes part of the
# path where images are stored.
export BUILD_SYS='rdo_trunk'
export HASH_FILE='/tmp/ocata_current_tripleo_hash'
