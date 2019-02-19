#!/bin/sh

usage="$(basename "$0") <plugin folder>"

if [ $# -ge 2 ]; then
  echo "$usage"
  exit
fi

para=$1
folder=${para%*/}
name=${folder#*/}
jarPath=$folder/target/$name-0.1.0-jar-with-dependencies.jar

for json in `ls $folder/*.json`; do
  #kill $(ps aux | grep $json | grep -v 'grep'| awk '{print $2}')
  if [ ! -f $jarPath ]; then
    echo "jar file is not exited"
    exit 1
  fi
  cp $jarPath $folder
  java -jar $folder/$name-0.1.0-jar-with-dependencies.jar $json $folder/default.conf
done


