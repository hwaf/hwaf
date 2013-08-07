.PHONY: release dist gen-version clean

export HWAF_VERSION=`date +%Y%m%d`

MANIFEST=/afs/cern.ch/atlas/project/mana-fwk/www/hwaf-latest/MANIFEST

gen-version:
	echo "HWAF_VERSION=${HWAF_VERSION}"
	sed -e s/HWAF_VERSION/${HWAF_VERSION}/g cmd_version.go.tmpl \
	>| cmd_version.go

dist: gen-version
	git fetch --all
	git checkout master
	git pull origin master
	go get -v ./...
	hwaf self bdist
	hwaf version
	hwaf self bdist-upload

release: dist
	echo "hwaf ${HWAF_VERSION}" >> $(MANIFEST)
