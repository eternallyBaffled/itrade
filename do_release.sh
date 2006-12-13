#!/bin/bash
#
# 032603 phil Wrote it from scratch
# 051403 dgil Cleanup the file
# 051128 dgil Use it for iTrade project
# 060504 dgil Migrate from CVS to SVN

# put real file names or directory to be removed here
to_be_removed='do_release.sh ethereal/* data/quotes.txt.org cache/* usrdata.dev/*'

target="$HOME/itrade_snapshot_`date +'%F'`.tar.gz"
#target="$HOME/itrade_0_4_8_nausicaa2_`date +'%F'`.tar.gz"
#export SVN_RSH=ssh

cd /tmp
rm -rf itrade

echo "-------- Getting files from SVN"
# anonymous login must have been done at least once
svn export https://svn.sourceforge.net/svnroot/itrade/trunk -r HEAD itrade
svn log https://svn.sourceforge.net/svnroot/itrade/trunk > itrade/REVISION

echo "------- Removing file"
for f in $to_be_removed;
do
	echo "Removing $f"
	rm -rf itrade/$f
done

echo "------- Packaging into $target"
if [ -e $target ];
then
	echo "Removing existing $target"
	rm -f $target
fi
tar zcvf $target itrade/*
