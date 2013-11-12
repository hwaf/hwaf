package vcs

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"io/ioutil"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

func path_exists(name string) bool {
	_, err := os.Stat(name)
	if err == nil {
		return true
	}
	if os.IsNotExist(err) {
		return false
	}
	return false
}

type Helper struct {
	Uri     *url.URL
	TmpDir  string
	PkgUri  string
	PkgName string // full package name (relative to repo root)
	PkgId   string // tag, branch or revision,... of package
	PkgDir  string

	Type    string // type of repository
	Repo    string // origin of repository
	RepoDir string // local directory for the repository
}

func NewHelper(pkguri, pkgname, pkgid, pkgdir string) (*Helper, error) {
	var err error

	pkguri = os.ExpandEnv(pkguri)

	// FIXME: shouldn't this be refactorized ?
	if strings.HasPrefix(pkguri, "git@github.com:") {
		pkguri = strings.Replace(
			pkguri,
			"git@github.com:",
			"git+ssh://git@github.com/",
			1)
	}

	uri, err := url.Parse(pkguri)
	if err != nil {
		return nil, err
	}

	// FIXME: hack. we need a better "plugin architecture" for this...
	if uri.Scheme == "" {
		if !path_exists(uri.Path) {
			if svnroot := os.Getenv("SVNROOT"); svnroot != "" {
				pkguri = svnroot + "/" + pkguri
				pkguri = os.ExpandEnv(pkguri)
				uri, err = url.Parse(pkguri)
				if err != nil {
					return nil, err
				}
			}
		} else {
			// check whether this is a local xyz-repo
			for _, vcs := range List {
				if vcs.Ping("file", uri.Path) == nil {
					uri.Scheme = vcs.cmd
					break
				}
			}
			if uri.Scheme == "" {
				uri.Scheme = "local"
			}
		}
	}

	// FIXME: hack. support for cern-git.
	if uri.Host == "git.cern.ch" && uri.Scheme == "https" {
		uri.Scheme = "git+kerberos"
	}

	tmpdir, err := ioutil.TempDir("", "hwaf-pkg-co-")
	if err != nil {
		return nil, err
	}

	h := &Helper{
		Uri:     uri,
		TmpDir:  tmpdir,
		PkgUri:  pkguri,
		PkgName: pkgname,
		PkgId:   pkgid,
		PkgDir:  pkgdir,
	}

	// fmt.Printf(">>> [%v]\n", uri)
	// fmt.Printf("    Scheme: %q\n", uri.Scheme)
	// fmt.Printf("    Opaque: %q\n", uri.Opaque)
	// fmt.Printf("    Host:   %q\n", uri.Host)
	// fmt.Printf("    Path:   %q\n", uri.Path)
	// fmt.Printf("    Fragm:  %q\n", uri.Fragment)
	// fmt.Printf("    PkgUri: %q\n", pkguri)

	switch uri.Scheme {
	case "local":
		h.Type = "local"
		h.Repo = pkguri
		h.PkgName = pkgname
		if pkgname == "" {
			pkgname = filepath.Base(pkguri)
		}
		err = copytree(tmpdir, pkguri)
		if err != nil {
			return nil, err
		}

	case "svn", "svn+ssh":
		repo := pkguri
		if pkgid != "" && pkgid != "trunk" {
			// can't use filepath.Join as it may mess-up the uri.Scheme
			repo = strings.Join([]string{pkguri, "tags", pkgid}, "/")
		} else {
			repo = strings.Join([]string{pkguri, "trunk"}, "/")
		}
		h.Type = "svn"
		h.Repo = repo
		err = Svn.Create(tmpdir, repo)
		if err != nil {
			return nil, err
		}

		bout, err := Svn.runOutput(tmpdir, "info")
		if err != nil {
			return nil, err
		}

		pkgurl := ""
		rev := ""
		scanner := bufio.NewScanner(bytes.NewReader(bout))
		for scanner.Scan() {
			bline := scanner.Bytes()
			if bytes.HasPrefix(bline, []byte(`Repository Root: `)) {
				pkgurl = string(bytes.Replace(bline, []byte(`Repository Root: `), nil, -1))
			}
			if bytes.HasPrefix(bline, []byte(`Revision: `)) {
				rev = string(bytes.Replace(bline, []byte(`Revision: `), nil, -1))
			}
		}
		pkgurl = strings.Trim(pkgurl, " \n")
		//fmt.Printf("uri: %q\n", pkguri)
		//fmt.Printf("url: %q\n", pkgurl)
		n := strings.Replace(pkguri, pkgurl, "", -1)
		//fmt.Printf("n:   %q\n", n)
		if strings.HasPrefix(n, "/") {
			n = n[1:]
		}
		if n == "" {
			n = filepath.Base(uri.Path)
		}
		h.PkgName = n
		//fmt.Printf("n:   %q\n", n)

		// retrieve tag/version infos
		rev = strings.Trim(rev, " \n")
		if pkgid != "" {
			rev = pkgid
		} else {
			rev = filepath.Base(n) + "-" + rev
		}
		err = ioutil.WriteFile(filepath.Join(tmpdir, "version.hwaf"), []byte(n+"-"+rev+"\n"), 0666)
		if err != nil {
			return nil, err
		}

	case "git", "git+ssh", "git+kerberos":

		h.PkgName = strings.Join(strings.Split(uri.Path, "/")[3:], "/")
		repo := pkguri[:len(pkguri)-len(h.PkgName)]
		if strings.HasSuffix(repo, "/") {
			repo = repo[:len(repo)-1]
		}
		repo_name := func() string {
			switch pkgname {
			default:
				return pkgname
			case "":
				tmp := strings.Split(repo, "/")
				return tmp[len(tmp)-1]
			}
		}()
		h.RepoDir = filepath.Join(h.PkgDir, repo_name)

		if h.PkgId == "" {
			h.PkgId = "master"
		}

		h.Type = "git"
		h.Repo = repo

		// bout, err := Git.runOutput(h.RepoDir, "config --get {url}", "url", "remote.origin.url")
		// if err != nil {
		// 	return nil, err
		// }
		// pkgurl := strings.Trim(string(bout), " \n")
		// fmt.Printf("uri: %q\n", pkguri)
		// fmt.Printf("url: %q\n", pkgurl)

	default:
		return nil, fmt.Errorf("unknown URL scheme [%v]", uri.Scheme)
	}

	if pkgname != "" && h.Type != "git" {
		if strings.HasPrefix(pkgname, "./") || strings.HasPrefix(pkgname, "/") {
			abspath, err := filepath.Abs(pkgname)
			if err == nil {
				pkgname = abspath
			}
		}
		pkgname = filepath.Clean(pkgname)
		if filepath.IsAbs(pkgname) {
			abspath, err := filepath.Abs(pkgname)
			if err == nil {
				pkgname = abspath
				abs_pkgdir, _ := filepath.Abs(h.PkgDir)
				rel, err := filepath.Rel(abs_pkgdir, abspath)
				if err == nil {
					pkgname = rel
				}
			}
		} else {
			rel, err := filepath.Rel(h.PkgDir, pkgname)
			if err != nil {
				pkgname = rel
			}
		}

		h.PkgName = pkgname
	}

	//fmt.Printf(">>pkgname: %q\n", h.PkgName)
	return h, err
}

func (h *Helper) Checkout() error {
	var err error
	switch h.Type {
	default:
		top := h.PkgDir
		pkgdir := filepath.Join(top, h.PkgName)
		if filepath.IsAbs(h.PkgName) {
			pkgdir = h.PkgName
		}
		if !path_exists(pkgdir) {
			err = os.MkdirAll(pkgdir, 0755)
			if err != nil {
				return err
			}
		}
		err = copytree(pkgdir, h.TmpDir)
	case "git":
		err = h.git_checkout()
		if err != nil {
			fmt.Fprintf(os.Stderr, "**err-checkout** (%s): %v\n", h.PkgUri, err)
		}
	}
	return err
}

func (h *Helper) Delete() error {
	switch h.TmpDir {
	case "":
		return nil
	default:
		return os.RemoveAll(h.TmpDir)
	}
}

func (h *Helper) git_checkout() error {

	var err error
	repo_name := filepath.Base(h.RepoDir)

	err = os.MkdirAll(h.PkgDir, 0755)
	if err != nil {
		return err
	}

	do_sparse := h.PkgName != ""
	sparse_fname := filepath.Join(h.RepoDir, ".git", "info", "sparse-checkout")

	if !path_exists(h.RepoDir) {
		err = Git.run(h.PkgDir, "init {repo}", "repo", repo_name)
		if err != nil {
			return err
		}

		err = Git.run(h.RepoDir, "remote add origin {origin}", "origin", h.Repo)
		if err != nil {
			return err
		}

		if do_sparse {
			ff, err := os.Create(sparse_fname)
			if err != nil {
				return err
			}
			ff.Close()
		}
	}

	// consistency check:
	// make sure that no sparse-checkout file exists if we are configured to do no sparse-checkout
	if do_sparse {
		if !path_exists(sparse_fname) {
			return fmt.Errorf(
				"vcs.git: repository [%s] in inconsistent state. configured for sparse-checkout but [%s] file does NOT exist.",
				h.RepoDir,
				sparse_fname,
			)
		}
	} else {
		if path_exists(sparse_fname) {
			return fmt.Errorf(
				"vcs.git: repository [%s] in inconsistent state. not configured for sparse-checkout but [%s] file DOES exist.",
				h.RepoDir,
				sparse_fname,
			)
		}
	}

	err = Git.run(h.RepoDir, "remote update origin")
	if err != nil {
		return err
	}

	if do_sparse {
		err = Git.run(h.RepoDir, "config core.sparsecheckout true")
		if err != nil {
			return err
		}
	}

	if do_sparse {
		err = git_add_sparse_checkout(h)
		if err != nil {
			return err
		}
	}

	err = Git.run(h.RepoDir, "checkout {tag}", "tag", h.PkgId)
	if err != nil {
		return err
	}

	err = Git.run(h.RepoDir, "read-tree -mu {tag}", "tag", h.PkgId)
	if err != nil {
		return err
	}

	// retrieve tag/version infos
	bout, err := Git.runOutput(h.RepoDir, "rev-parse --short HEAD")
	if err != nil {
		return err
	}
	rev := h.PkgName + "-" + string(bout)
	err = ioutil.WriteFile(filepath.Join(h.RepoDir, "version.hwaf"), []byte(rev), 0666)
	if err != nil {
		return err
	}

	return err
}

func git_add_sparse_checkout(h *Helper) error {
	var err error
	sparse := filepath.Join(h.RepoDir, ".git", "info", "sparse-checkout")
	if !path_exists(sparse) {
		return fmt.Errorf(
			"vcs.git: repository [%s] not configured to allow sparse-checkout",
			h.RepoDir,
		)
	}

	content, err := ioutil.ReadFile(sparse)
	if err != nil {
		return err
	}

	paths := make(map[string]struct{})
	for _, line := range bytes.Split(content, []byte("\n")) {
		text := strings.Trim(string(line), " \r\n\t")
		if text == "" {
			continue
		}
		paths[text] = struct{}{}
	}

	pkgname := h.PkgName + "/"
	//fmt.Printf(">> adding [%s]...\n", pkgname)
	if _, ok := paths[pkgname]; ok {
		// already in sparse-checkout selection
		return nil
	}

	paths[pkgname] = struct{}{}

	pkgs := make([]string, 0, len(paths))
	for pkg, _ := range paths {
		pkgs = append(pkgs, pkg)
	}
	sort.Strings(pkgs)

	err = os.Rename(sparse, sparse+"-old")
	if err != nil {
		return nil
	}

	f, err := os.Create(sparse + "-new")
	if err != nil {
		return err
	}
	defer f.Close()
	for _, pkg := range pkgs {
		_, err = f.WriteString(pkg + "\n")
		if err != nil {
			return err
		}
	}
	err = f.Close()
	if err != nil {
		return err
	}
	err = os.Rename(sparse+"-new", sparse)
	return err
}

func copytree(dstdir, srcdir string) error {
	var err error

	if !path_exists(dstdir) {
		err = os.MkdirAll(dstdir, 0755)
		if err != nil {
			return err
		}
	}

	err = filepath.Walk(srcdir, func(path string, info os.FileInfo, err error) error {
		rel := ""
		rel, err = filepath.Rel(srcdir, path)
		out := filepath.Join(dstdir, rel)
		fmode := info.Mode()
		if fmode.IsDir() {
			err = os.MkdirAll(out, fmode.Perm())
			if err != nil {
				return err
			}
		} else if fmode.IsRegular() {
			dst, err := os.OpenFile(out, os.O_CREATE|os.O_RDWR, fmode.Perm())
			if err != nil {
				return nil
			}
			src, err := os.Open(path)
			if err != nil {
				return nil
			}
			_, err = io.Copy(dst, src)
			if err != nil {
				return nil
			}
		} else if (fmode & os.ModeSymlink) != 0 {
			rlink, err := os.Readlink(path)
			if err != nil {
				return err
			}
			err = os.Symlink(rlink, out)
			if err != nil {
				return err
			}
		} else {
			return fmt.Errorf("unhandled mode (%v) for path [%s]", fmode, path)
		}
		return nil
	})
	return err
}

// EOF
