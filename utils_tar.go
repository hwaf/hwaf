package main

import (
	"archive/tar"
	"compress/gzip"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

func _tar_gz(targ, workdir string) error {

	f, err := os.Create(targ)
	if err != nil {
		return err
	}
	zout := gzip.NewWriter(f)
	tw := tar.NewWriter(zout)

	err = filepath.Walk(workdir, func(path string, fi os.FileInfo, err error) error {
		//fmt.Printf("::> [%s]...\n", path)
		if !strings.HasPrefix(path, workdir) {
			err = fmt.Errorf("walked filename %q doesn't begin with workdir %q", path, workdir)
			return err

		}
		name := path

		// make name "relative"
		if strings.HasPrefix(name, "/") {
			name = name[1:]
		}
		target, _ := os.Readlink(path)
		if err != nil {
			return err
		}
		hdr, err := tar.FileInfoHeader(fi, target)
		if err != nil {
			return err
		}
		hdr.Name = name
		hdr.Uname = "root"
		hdr.Gname = "root"
		hdr.Uid = 0
		hdr.Gid = 0

		// Force permissions to 0755 for executables, 0644 for everything else.
		if fi.Mode().Perm()&0111 != 0 {
			hdr.Mode = hdr.Mode&^0777 | 0755
		} else {
			hdr.Mode = hdr.Mode&^0777 | 0644
		}

		err = tw.WriteHeader(hdr)
		if err != nil {
			return fmt.Errorf("Error writing file %q: %v", name, err)
		}
		// handle directories and symlinks
		if hdr.Size <= 0 {
			return nil
		}
		r, err := os.Open(path)
		if err != nil {
			return err
		}
		defer r.Close()
		_, err = io.Copy(tw, r)
		return err
	})
	if err != nil {
		return err
	}
	if err := tw.Close(); err != nil {
		return err
	}
	if err := zout.Close(); err != nil {
		return err
	}
	return f.Close()
}

// EOF
