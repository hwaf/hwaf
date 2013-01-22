package platform

import (
	"os/exec"
	"strings"
)

func uname(opts ...string) (string, error) {

	cmd := exec.Command("uname", opts...)
	bout, err := cmd.Output()
	if err != nil {
		return "", err
	}
	out := strings.Trim(string(bout), " \r\n")
	return out, err
}

func infos() (Platform, error) {
	var err error
	var plat Platform

	table := map[string]string{
		"System":    "-s",
		"Node":      "-n",
		"Release":   "-r",
		"Version":   "-v",
		"Machine":   "-m",
		"Processor": "-p",
	}

	for n, arg := range table {
		var v string
		v, err = uname(arg)
		if err != nil {
			return plat, err
		}
		table[n] = v
	}

	plat.System = table["System"]
	plat.Node = table["Node"]
	plat.Release = table["Release"]
	plat.Version = table["Version"]
	plat.Machine = table["Machine"]
	plat.Processor = table["Processor"]

	return plat, nil
}

// EOF
