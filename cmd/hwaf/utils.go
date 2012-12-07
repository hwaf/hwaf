package main

import (
	"fmt"
	"os"
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
		fmt.Printf("**error**: %v\n", err.Error())
		os.Exit(1)
	}
}
