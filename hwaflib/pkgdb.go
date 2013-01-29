package hwaflib

import (
	"encoding/json"
	"fmt"
	"os"
)

type VcsPackage struct {
	Type string // type of remote VCS (svn, git, ...)
	Repo string // remote repository URL
	Path string // path under which the package is locally checked out
}

type PackageDb struct {
	db    map[string]VcsPackage
	fname string // file name where the db is backed up
}

func NewPackageDb(fname string) *PackageDb {
	return &PackageDb{
		db:    make(map[string]VcsPackage),
		fname: fname,
	}
}

func (db *PackageDb) Load(fname string) error {
	f, err := os.Open(fname)
	if err != nil {
		return err
	}
	defer f.Close()
	err = json.NewDecoder(f).Decode(&db.db)
	return err
}

func (db *PackageDb) Add(vcs, pkguri, pkgname string) error {
	_, has := db.db[pkgname]
	if has {
		return fmt.Errorf("hwaf.pkgdb: package [%s] already in db", pkgname)
	}
	db.db[pkgname] = VcsPackage{vcs, pkguri, pkgname}

	return db.sync()
}

func (db *PackageDb) Remove(pkgname string) error {
	_, ok := db.db[pkgname]
	if !ok {
		return fmt.Errorf("hwaf.pkgdb: package [%s] not in db", pkgname)
	}
	delete(db.db, pkgname)

	return db.sync()
}

func (db *PackageDb) HasPkg(pkgname string) bool {
	_, ok := db.db[pkgname]
	return ok
}

func (db *PackageDb) GetPkg(pkgname string) (VcsPackage, error) {
	pkg, ok := db.db[pkgname]
	if !ok {
		return pkg, fmt.Errorf("hwaf.pkgdb: package [%s] not in db", pkgname)
	}
	return pkg, nil
}

// Pkgs returns the list of packages this db holds
func (db *PackageDb) Pkgs() []string {
	if db == nil || db.db == nil {
		return []string{}
	}

	pkgs := make([]string, 0, len(db.db))
	for k, _ := range db.db {
		pkgs = append(pkgs, k)
	}
	return pkgs
}

func (db *PackageDb) sync() error {
	if path_exists(db.fname) {
		os.RemoveAll(db.fname)
	}
	f, err := os.Create(db.fname)
	if err != nil {
		return err
	}
	defer f.Close()

	err = json.NewEncoder(f).Encode(&db.db)
	if err != nil {
		return err
	}
	err = f.Sync()
	if err != nil {
		return err
	}
	return f.Close()
}

// EOF
