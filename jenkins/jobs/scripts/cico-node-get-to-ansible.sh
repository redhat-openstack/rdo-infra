# cico-node-get-to-ansible.sh
# A script that provisions nodes and writes them to an Ansible inventory file
NODE_COUNT=${NODE_COUNT:-1}
ANSIBLE_HOSTS=${ANSIBLE_HOSTS:-$WORKSPACE/hosts}
SSID_FILE=${SSID_FILE:-$WORKSPACE/cico-ssid}

CPU_ARCH=${CPU_ARCH:-x86_64}
CICO_FLAVOR=${CICO_FLAVOR:-small}

# Write the header of the hosts file
cat << EOF > ${ANSIBLE_HOSTS}
localhost ansible_connection=local

[openstack_nodes]
EOF

# Get nodes
nodes=$(cico -q node get --arch $CPU_ARCH --flavor $CICO_FLAVOR --retry-count 6 --retry-interval 60  --count ${NODE_COUNT} --column hostname --column ip_address --column comment -f value)

# Write nodes to inventory file and persist the SSID separately for simplicity
touch ${SSID_FILE}
IFS=$'\n'
for node in ${nodes}
do
    host=$(echo "${node}" |cut -f1 -d " ")
    address=$(echo "${node}" |cut -f2 -d " ")
    ssid=$(echo "${node}" |cut -f3 -d " ")

    line="${host} ansible_host=${address} ansible_user=root cico_ssid=${ssid}"
    echo "${line}" >> ${ANSIBLE_HOSTS}

    # Write unique SSIDs to the SSID file
    if ! grep -q ${ssid} ${SSID_FILE}; then
        echo ${ssid} >> ${SSID_FILE}
    fi
done
