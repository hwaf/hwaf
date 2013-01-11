package main

import (
	"fmt"
	// "os"
	// "os/exec"
	// "path/filepath"

	"github.com/gonuts/commander"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_git_svn_clone() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_git_svn_clone,
		UsageLine: "svn-clone [options] <URL> [<directory>]",
		Short:     "convert a SVN repository into a GIT one",
		Long: `
svn-clone converts a SVN repository into a GIT one.

ex:
 $ hwaf git svn-clone svn+ssh://svn.cern.ch/atlasoff/Control/AthenaCommon
 $ hwaf git svn-clone svn+ssh://svn.cern.ch/atlasoff/Control/AthenaCommon .
 $ hwaf git svn-clone svn+ssh://svn.cern.ch/atlasoff/Control/AthenaCommon athenacommon-git
`,
		Flag: *flag.NewFlagSet("hwaf-git-svn-clone", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_git_svn_clone(cmd *commander.Command, args []string) {
	var err error
	n := "hwaf-" + cmd.Name()

	svn_url := ""
	git_dir := ""
	switch len(args) {
	case 1:
		svn_url = args[0]
		git_dir = "."
	case 2:
		svn_url = args[0]
		git_dir = args[1]
	default:
		err = fmt.Errorf("%s: needs a URL to a SVN repository to clone", n)
		handle_err(err)
	}

	fmt.Printf("svn-url: %v\n", svn_url)
	fmt.Printf("out-dir: %v\n", git_dir)
	handle_err(err)
}

// EOF
