#!/bin/bash

pushd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null
cd ..
python3 tests2/runner.py
find unitResults -name 'eclr.dot' -exec dot -Tpng '{}' -o '{}'.png -Gdpi=100 \;
rm -rf doc/unittests
mkdir -p doc/unittests
cp unitResults/index.md doc/unittests/
for name in unitResults/*; do
  if [ "$name" != "unitResults/index.md" ]; then
    JUSTNAME=$(basename $name)
    mkdir -p doc/unittests/$JUSTNAME/
    cp $name/eclr.dot.png doc/unittests/$JUSTNAME/
  fi
done
popd
