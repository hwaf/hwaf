package main

import (
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"runtime"

	"github.com/sbinet/go-commander"
	"github.com/sbinet/go-flag"
)

func hwaf_make_cmd_self_update() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_self_update,
		UsageLine: "self-update [options]",
		Short:     "update hwaf itself",
		Long: `
self-update updates hwaf internal files and the hwaf binary itself.

ex:
 $ hwaf self-update
`,
		Flag: *flag.NewFlagSet("hwaf-self-update", flag.ExitOnError),
	}
	cmd.Flag.Bool("q", false, "only print error and warning messages, all other output will be suppressed")

	return cmd
}

func hwaf_run_cmd_self_update(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	switch len(args) {
	case 0:
		// ok
	default:
		err = fmt.Errorf("%s: does NOT take any argument", n)
		handle_err(err)
	}

	quiet := cmd.Flag.Lookup("q").Value.Get().(bool)

	if !quiet {
		fmt.Printf("%s: self-update...\n", n)
	}

	old, err := exec.LookPath(os.Args[0])
	handle_err(err)

	url := fmt.Sprintf(
		"https://github.com/downloads/mana-fwk/hwaf/hwaf-%s-%s",
		runtime.GOOS, runtime.GOARCH,
	)
	tmp, err := ioutil.TempFile("", "hwaf-")
	handle_err(err)
	defer tmp.Close()

	// make it executable
	err = tmp.Chmod(0777)
	handle_err(err)

	// download new file
	resp, err := http.Get(url)
	handle_err(err)
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		err = fmt.Errorf("could not d/l [%s] (reason: %q)\n", url, resp.Status)
		handle_err(err)
	}

	nbytes, err := io.Copy(tmp, resp.Body)
	handle_err(err)

	if nbytes <= 0 {
		err = fmt.Errorf("could not copy hwaf from [%s]", url)
		handle_err(err)
	}

	err = tmp.Sync()
	handle_err(err)

	// self-init
	hwaf := exec.Command(tmp.Name(), "self-init", fmt.Sprintf("-q=%v", quiet))
	hwaf.Stderr = os.Stderr
	hwaf.Stdout = os.Stdout
	err = hwaf.Run()
	handle_err(err)

	// replace current binary
	err = os.Rename(tmp.Name(), old)
	handle_err(err)

	if !quiet {
		fmt.Printf("%s: [%s] updated\n", n, old)
		fmt.Printf("%s: self-update... [ok]\n", n)
	}
}

// EOF
