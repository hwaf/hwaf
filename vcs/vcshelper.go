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
	PkgName string
	PkgId   string
	PkgDir  string

	Repo string
	Type string
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
			uri.Scheme = "local"
		}
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

	fmt.Printf(">>> [%v]\n", uri)
	fmt.Printf("    Scheme: %q\n", uri.Scheme)
	fmt.Printf("    Opaque: %q\n", uri.Opaque)
	fmt.Printf("    Host:   %q\n", uri.Host)
	fmt.Printf("    Path:   %q\n", uri.Path)
	fmt.Printf("    Fragm:  %q\n", uri.Fragment)
	fmt.Printf("    PkgUri: %q\n", pkguri)

	switch uri.Scheme {
	case "local":
		h.Type = "local"
		h.Repo = pkguri
		h.PkgName = pkgname
		if pkgname == "" {
			return nil, fmt.Errorf("local packages need an explicit pkgname")
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
		scanner := bufio.NewScanner(bytes.NewReader(bout))
		for scanner.Scan() {
			bline := scanner.Bytes()
			if bytes.HasPrefix(bline, []byte(`Repository Root: `)) {
				pkgurl = string(bytes.Replace(bline, []byte(`Repository Root: `), nil, -1))
				break
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

	case "git", "git+ssh":
		err = Git.Create(tmpdir, pkguri)
		if err != nil {
			return nil, err
		}

		if pkgid != "" {
			err = Git.run(tmpdir, "checkout {tag}", "tag", pkgid)
			if err != nil {
				return nil, err
			}
		}

		h.Type = "git"
		h.Repo = pkguri

		bout, err := Git.runOutput(tmpdir, "config --get {url}", "url", "remote.origin.url")
		if err != nil {
			return nil, err
		}
		pkgurl := strings.Trim(string(bout), " \n")

		//fmt.Printf("uri: %q\n", pkguri)
		//fmt.Printf("url: %q\n", pkgurl)
		n := strings.Replace(pkguri, pkgurl, "", -1)
		//fmt.Printf("n:   %q\n", n)
		if n == "" {
			n = filepath.Base(uri.Path)
		}
		h.PkgName = n
		//fmt.Printf("n:   %q\n", n)

	default:
		return nil, fmt.Errorf("unknown URL scheme [%v]", uri.Scheme)
	}

	if pkgname != "" {
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
	return err
}

func (h *Helper) Delete() error {
	return os.RemoveAll(h.TmpDir)
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
