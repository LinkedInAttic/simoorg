#!/bin/bash

# This script accepts 2 arguments
#
# argument 1: Path to the PID file (mandatory)
# argument 2: Posix path
# argument 3: Install path for libfiu bin
# argument 4: Sudo user
#

if [ $# -lt "3" ]
then
  exit 255
fi

PID_PATH=$1
PID=`cat $PID_PATH`

POSIX_PATH=$2
PROBABILITY=$3
LIBFIU_BIN_PATH=$4

if [ $# -gt 3 ]
then
  SUDO_USER=$2
  COMMAND_PREFIX="sudo -u $SUDO_USER"
else
  COMMAND_PREFIX=""
fi

COMMAND_RETURN=`$COMMAND_PREFIX $LIBFIU_BIN_PATH/fiu-ctrl -c "disable name=$POSIX_PATH" $PID`

echo $COMMAND_RETURN |grep -q 'returned error'

if [ $? -eq "0" ]
then
  exit 1
fi

exit 0
