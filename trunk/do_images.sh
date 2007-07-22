#!/bin/bash
#
# build the /images folder package
#
# 070405 dgil Wrote it from scratch
# 070722 dgil fix itrade. prefix for svn

# put real file names or directory to be removed here
to_be_removed=''

target="$HOME/itrade_images_`date +'%F'`.tar.gz"

cd /tmp
rm -rf itrade

echo "-------- Getting files from SVN"
# anonymous login must have been done at least once
svn export https://itrade.svn.sourceforge.net/svnroot/itrade/trunk/images -r HEAD itrade

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
cd itrade
tar zcvf $target *
cd ..
