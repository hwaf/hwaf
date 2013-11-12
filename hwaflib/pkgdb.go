package hwaflib

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"sort"
)

type VcsPackage struct {
	Type    string // type of remote VCS (svn, git, ...)
	Repo    string // remote repository URL
	RepoDir string // local repository directory
	Path    string // path under which the package is locally checked out
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

func (db *PackageDb) Add(vcs, pkguri, repodir, pkgname string) error {
	_, has := db.db[pkgname]
	if has {
		return fmt.Errorf("hwaf.pkgdb: package [%s] already in db", pkgname)
	}
	db.db[pkgname] = VcsPackage{
		Type:    vcs,
		Repo:    pkguri,
		RepoDir: repodir,
		Path:    pkgname,
	}

	err := db.sync()
	if err != nil {
		return err
	}
	// FIXME: should this return an error ?
	exec.Command("git", "add", db.fname).Run()
	exec.Command(
		"git", "commit",
		"-m", fmt.Sprintf("adding package [%s] to pkgdb", pkgname),
	).Run()
	return nil
}

func (db *PackageDb) Remove(pkgname string) error {
	_, ok := db.db[pkgname]
	if !ok {
		return fmt.Errorf("hwaf.pkgdb: package [%s] not in db", pkgname)
	}
	delete(db.db, pkgname)

	err := db.sync()
	if err != nil {
		return err
	}

	// FIXME: should this return an error ?
	exec.Command("git", "add", db.fname).Run()
	exec.Command(
		"git", "commit",
		"-m", fmt.Sprintf("removing package [%s] from pkgdb", pkgname),
	).Run()
	return nil
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
	sort.Strings(pkgs)
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

	data, err := json.MarshalIndent(&db.db, "", "    ")
	if err != nil {
		return err
	}

	_, err = f.Write(data)
	if err != nil {
		return err
	}
	fmt.Fprintf(f, "\n")

	err = f.Sync()
	if err != nil {
		return err
	}
	return f.Close()
}

// EOF
