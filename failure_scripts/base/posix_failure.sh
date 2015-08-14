#!/bin/bash

# This script accepts 2 arguments
#
# argument 1: Path to the PID file (mandatory)
# argument 2: Posix path
# argument 3: Probability for failure
# argument 4: Install path for libfiu bin
# argument 5: Sudo user
#

if [ $# -lt "4" ]
then
  exit 255
fi

PID_PATH=$1
PID=`cat $PID_PATH`

POSIX_PATH=$2
PROBABILITY=$3
LIBFIU_BIN_PATH=$4

if [ $# -gt 4 ]
then
  SUDO_USER=$2
  COMMAND_PREFIX="sudo -u $SUDO_USER"
else
  COMMAND_PREFIX=""
fi

COMMAND_RETURN=`$COMMAND_PREFIX $LIBFIU_BIN_PATH/fiu-ctrl -c "enable_random name=$POSIX_PATH,probability=$PROBABILITY" $PID`

echo $COMMAND_RETURN |grep -q 'returned error'

if [ $? -eq "0" ]
then
  exit 1
fi

exit 0
