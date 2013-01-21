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
		os.Exit(1)
	}
}

func is_git_repo(dirname string) bool {
	return path_exists(filepath.Join(dirname, ".git"))
}

// EOF
