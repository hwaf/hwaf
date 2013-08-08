.PHONY: release dist gen-version clean

export HWAF_VERSION=`date +%Y%m%d`
export HWAF_REVISION=`git rev-parse --short HEAD`

MANIFEST=/afs/cern.ch/atlas/project/mana-fwk/www/hwaf-latest/MANIFEST

gen-version:
	echo "HWAF_VERSION=${HWAF_VERSION}"
	echo "HWAF_REVISION=${HWAF_REVISION}"
	sed -e s/HWAF_VERSION/${HWAF_VERSION}/g cmd_version.go.tmpl \
	>| cmd_version.go.tmp
	sed -e s/HWAF_REVISION/${HWAF_REVISION}/g cmd_version.go.tmp \
	>| cmd_version.go
	/bin/rm cmd_version.go.tmp

tag: gen-version
	git add cmd_version.go
	git commit -m "version: "${HWAF_VERSION}
	git tag -f ${HWAF_VERSION}

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
