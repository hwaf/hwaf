.PHONY: release dist gen-version clean

export HWAF_VERSION=`date +%Y%m%d`
export HWAF_REVISION=`git rev-parse --short HEAD`

MANIFEST=/afs/cern.ch/atlas/project/hwaf/www/hwaf-latest/MANIFEST

gen-version:
	echo "HWAF_VERSION=${HWAF_VERSION}"
	echo "HWAF_REVISION=${HWAF_REVISION}"
	sed -e s/HWAF_VERSION/${HWAF_VERSION}/g hwaflib/version.go.tmpl \
	>| hwaflib/version.go.tmp
	sed -e s/HWAF_REVISION/${HWAF_REVISION}/g hwaflib/version.go.tmp \
	>| hwaflib/version.go
	/bin/rm hwaflib/version.go.tmp

tag: gen-version
	git add hwaflib/version.go
	git commit -m "version: "${HWAF_VERSION}
	git tag -f ${HWAF_VERSION}
	git push --tags

dist:
	git fetch --all
	git checkout master
	git pull origin master
	go get -v ./...
	hwaf self bdist
	hwaf version
	hwaf self bdist-upload

release: dist
	echo "hwaf ${HWAF_VERSION}" >> $(MANIFEST)
