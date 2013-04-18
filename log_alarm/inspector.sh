#!/bin/sh
#logfile = ../log/xxx_{YEAR}{MONTH}{DAY}
if [ $# -lt 7 ]; then
    echo "Usage ${0} minutes logfile greptext threshold warntext group obj"
    exit 0
fi

DC_PATH=/usr/local/services/CloudDCAgent_L5-1.0/alarm
IP_ADDR=`/sbin/ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6|awk '{print $2}'|tr -d "addr:" | head -n1`

MINUTES=$1
LOG_FILE=$2
GREP_TEXT=$3
ALARM_THRESHOLD=$4
WARN_TEXT=$5
GROUP_NAME=$6
OBJ_NAME=$7

D_HOUR=`date "+%H"`
D_DAY=`date "+%d"`
D_MONTH=`date "+%m"`
D_YEAR=`date "+%Y"`
DATE_THRESHOLD=`date -d "${MINUTES} mins ago" +%H:%M:%S`

LOG_FILE=${LOG_FILE/\{YEAR\}/${D_YEAR}}
LOG_FILE=${LOG_FILE/\{MONTH\}/${D_MONTH}}
LOG_FILE=${LOG_FILE/\{DAY\}/${D_DAY}}
LOG_FILE=${LOG_FILE/\{HOUR\}/${D_HOUR}}

GREP_NUM=`grep "${GREP_TEXT}" ${LOG_FILE} | awk -v date_t="${DATE_THRESHOLD}" '/^\[/ && $2 >= date_t {print}' | wc -l`
if [ ${GREP_NUM} -ge ${ALARM_THRESHOLD} ]; then
    WARN_MSG="${WARN_TEXT}, ${GREP_NUM} error on ${IP_ADDR}"
    ${DC_PATH}/cloud_alarm 31005 "${WARN_MSG}" -g "${GROUP_NAME}" -o "${OBJ_NAME}"
    echo ${WARN_MSG}
else
    echo "${GREP_NUM} error on ${IP_ADDR}"
fi