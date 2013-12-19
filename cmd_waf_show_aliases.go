package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/gonuts/commander"
	gocfg "github.com/gonuts/config"
	"github.com/gonuts/flag"
)

func hwaf_make_cmd_waf_show_aliases() *commander.Command {
	cmd := &commander.Command{
		Run:       hwaf_run_cmd_waf_show_aliases,
		UsageLine: "aliases [options]",
		Short:     "show list of registered aliases for the local project",
		Long: `
show list of registered aliases for the local project.

ex:
 $ hwaf show aliases
 ['target-slc6', 'opt']

 $ hwaf show aliases athena
 athena=athena.py

`,
		Flag: *flag.NewFlagSet("hwaf-waf-show-aliases", flag.ExitOnError),
	}
	return cmd
}

func hwaf_run_cmd_waf_show_aliases(cmd *commander.Command, args []string) error {
	var err error

	pinfo, err := g_ctx.ProjectInfos()
	if err != nil {
		return err
	}

	val, err := pinfo.Get("HWAF_RUNTIME_ALIASES")
	if err != nil {
		if _, ok := err.(gocfg.OptionError); ok {
			// no alias defined
			return fmt.Errorf("no runtime alias defined")
		}
		if err != nil {
			return err
		}
	}

	tmp := make([][2]string, 0)
	val = strings.Replace(val, `['`, `["`, -1)
	val = strings.Replace(val, `', '`, `", "`, -1)
	val = strings.Replace(val, `']`, `"]`, -1)

	buf := bytes.NewReader([]byte(val))
	err = json.NewDecoder(buf).Decode(&tmp)
	if err != nil {
		return err
	}

	aliases := make(map[string]string, len(tmp))
	for _, alias := range tmp {
		dst, src := alias[0], alias[1]
		aliases[dst] = src
		//fmt.Printf("%s=%q\n", dst, src)
	}

	if len(args) <= 0 {
		for dst, src := range aliases {
			fmt.Printf("%s=%q\n", dst, src)
		}
	} else {
		all_good := true
		for _, dst := range args {
			src, ok := aliases[dst]
			if !ok {
				g_ctx.Errorf("no such alias %q\n", dst)
				all_good = false
				continue
			}
			fmt.Printf("%s=%q\n", dst, src)
		}
		if !all_good {
			// TODO(sbinet) define and use an ErrorStack
			err = fmt.Errorf("problem while running show alias")
		}
	}

	return err
}

// EOF
