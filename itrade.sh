#!/bin/bash
#
# startscript for iTrade
#
# written by oc2pus
#
# Changelog:
# 20.01.2007 initial version

# activate for debugging
#set -x

# base settings
myShareDir=/usr/share/itrade
myHomeDir=~/.itrade

# creates a local working directory in user-home
function createLocalDir ()
{
 	if [ ! -d $myHomeDir ]; then
		echo "creating local working directory $myHomeDir ..."
		mkdir -p $myHomeDir

		cd $myHomeDir

		# create local directories
		for i in alerts cache data ethereal export import reports snapshots usrdata usrdata.dev; do
			mkdir -p $i
		done
		# shared data-files
		for i in images res; do
			ln -s $myShareDir/$i .
		done
		# user data files
		for i in data import usrdata; do
			cp $myShareDir/$i/* $i
		done
		# link to main programm
		ln -s /usr/lib/python/site-packages/itrade/itrade.py .

		cd ..
	fi
}

echo ""
echo "starting iTrade ..."

# creates a local working directory in user-home
createLocalDir
cd $myHomeDir

LANG=C python ./itrade.py --unicode
