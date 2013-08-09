package main

import (
	"fmt"
	"os"
	"path/filepath"
	//"strconv"
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

func handle_err(err error) {
	if err != nil {
		fmt.Fprintf(os.Stderr, "**error**: %v\n", err.Error())
		//panic(err.Error())

		if g_ctx != nil {
			g_ctx.Exit(1)
		}
		os.Exit(1)
	}
}

func is_git_repo(dirname string) bool {
	return path_exists(filepath.Join(dirname, ".git"))
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
