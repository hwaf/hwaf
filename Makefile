.PHONY: release dist gen-version clean install build

export HWAF_VERSION=`date +%Y%m%d`
export HWAF_REVISION=`git rev-parse --short HEAD`

MANIFEST=/afs/cern.ch/atlas/project/hwaf/www/hwaf-latest/MANIFEST
INSTALL=/afs/cern.ch/atlas/project/hwaf/sw/install
VAULT=/afs/cern.ch/atlas/project/hwaf/www/downloads/tar

OUT=$(INSTALL)/hwaf-${HWAF_VERSION}

build: gen-version
	go get -v ./...

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

install:
	@echo ":: install hwaf: [$(OUT)]"
	mkdir -p $(OUT)/linux-amd64
	mkdir -p $(OUT)/linux-386
	mkdir -p $(OUT)/darwin-amd64

	tar -C $(OUT)/linux-amd64  -zxf $(VAULT)/hwaf-${HWAF_VERSION}-linux-amd64.tar.gz
	tar -C $(OUT)/linux-386    -zxf $(VAULT)/hwaf-${HWAF_VERSION}-linux-386.tar.gz
	tar -C $(OUT)/darwin-amd64 -zxf $(VAULT)/hwaf-${HWAF_VERSION}-darwin-amd64.tar.gz

	@echo ":: create 'latest' symlink..."
	/bin/rm $(INSTALL)/latest
	(cd $(INSTALL) && ln -s hwaf-${HWAF_VERSION} latest)

	@echo ":: bye."
