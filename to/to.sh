#!/bin/sh

if [ $# -lt 1 ]; then
    echo "usage: $0 remote_name"
    exit
fi

OLD_PATH=`pwd`
WORK_DIR=`dirname "$0"`
cd "${WORK_DIR}"

REMOTE_NAME="$1"
BASE_NAME=`basename "$0"`
CONF_NAME="${BASE_NAME%.*}.conf"
CONF_LINE=`grep "^${REMOTE_NAME}|" "${CONF_NAME}"`

if [ -z $CONF_LINE ]; then
    echo "no remote named $REMOTE_NAME :(, check $CONF_NAME plz"
    exit
fi

SSH_HOST=`echo "${CONF_LINE}" | awk -F'|' '{print $2}'`
SSH_USER=`echo "${CONF_LINE}" | awk -F'|' '{print $4}'`
SSH_PORT=`echo "${CONF_LINE}" | awk -F'|' '{print $3}'`

set -x
ssh -p${SSH_PORT} ${SSH_USER}@${SSH_HOST} -q
set +x

cd "${OLD_PATH}"
