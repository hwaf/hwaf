package main

// FIXME: all of this should go away once we migrate to go-1.1

import (
	"archive/tar"
	"compress/gzip"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Mode constants from the tar spec. 
const (
	c_ISDIR  = 040000
	c_ISFIFO = 010000
	c_ISREG  = 0100000
	c_ISLNK  = 0120000
	c_ISBLK  = 060000
	c_ISCHR  = 020000
	c_ISSOCK = 0140000
)

// sysStat, if non-nil, populates h from system-dependent fields of fi. 
var sysStat func(fi os.FileInfo, h *tar.Header) error

// FileInfoHeader creates a partially-populated Header from fi.
// If fi describes a symlink, FileInfoHeader records link as the link target.
func _tar_FileInfoHeader(fi os.FileInfo, link string) (*tar.Header, error) {
	if fi == nil {
		return nil, errors.New("tar: FileInfo is nil")
	}
	h := &tar.Header{
		Name:    fi.Name(),
		ModTime: fi.ModTime(),
		Mode:    int64(fi.Mode().Perm()), // or'd with c_IS* constants later
	}
	switch {
	case fi.Mode()&os.ModeType == 0:
		h.Mode |= c_ISREG
		h.Typeflag = tar.TypeReg
		h.Size = fi.Size()
	case fi.IsDir():
		h.Typeflag = tar.TypeDir
		h.Mode |= c_ISDIR
	case fi.Mode()&os.ModeSymlink != 0:
		h.Typeflag = tar.TypeSymlink
		h.Mode |= c_ISLNK
		h.Linkname = link
	case fi.Mode()&os.ModeDevice != 0:
		if fi.Mode()&os.ModeCharDevice != 0 {
			h.Mode |= c_ISCHR
			h.Typeflag = tar.TypeChar
		} else {
			h.Mode |= c_ISBLK
			h.Typeflag = tar.TypeBlock
		}
	case fi.Mode()&os.ModeSocket != 0:
		h.Mode |= c_ISSOCK
	default:
		return nil, fmt.Errorf("archive/tar: unknown file mode %v", fi.Mode())
	}
	if sysStat != nil {
		return h, sysStat(fi, h)
	}
	return h, nil
}

func _tar_gz(targ, workdir string) error {
	// FIXME: use archive/tar instead (once go-1.1 is out)
	{
		matches, err := filepath.Glob(filepath.Join(workdir, "*"))
		if err != nil {
			return err
		}
		for i,m := range matches {
			matches[i] = m[len(workdir):]
		}
		args := []string{"-zcf", targ}
		args = append(args, matches...)
		cmd := exec.Command("tar", args...)
		return cmd.Run()
	}

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
		name := path[len(workdir):]

		// Chop of any leading / from filename, leftover from removing workdir.
		if strings.HasPrefix(name, "/") {
			name = name[1:]
		}
		target, _ := os.Readlink(path)
		hdr, err := _tar_FileInfoHeader(fi, target)
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
		if fi.IsDir() {
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
