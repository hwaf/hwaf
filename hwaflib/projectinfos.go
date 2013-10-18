package hwaflib

import (
	"fmt"
	"path/filepath"
	"sort"

	gocfg "github.com/gonuts/config"
)

type ProjectInfos struct {
	cfg *gocfg.Config
}

func NewProjectInfos(name string) (*ProjectInfos, error) {
	var err error
	fname := filepath.Clean(name)
	if !path_exists(fname) {
		err = fmt.Errorf("could not find project infos [%s]", fname)
		return nil, err
	}
	cfg, err := gocfg.ReadDefault(fname)
	if err != nil {
		return nil, err
	}
	//fmt.Printf("cfg [%s]\nsections: %s\n", fname, cfg.Sections())
	return &ProjectInfos{cfg}, nil
}

func (pi *ProjectInfos) Get(key string) (string, error) {
	s, err := pi.cfg.String("DEFAULT", key)

	// we can't use strconv.Unquote as these are python strings...
	if len(s) > 1 {
		slen := len(s) - 1
		s0 := string(s[0])
		s1 := string(s[slen])
		if (s0 == "'" && s1 == "'") || (s0 == `"` && s1 == `"`) {
			s = s[1:slen]
		}
	}
	return s, err
}

func (pi *ProjectInfos) Keys() []string {

	opts, err := pi.cfg.Options("DEFAULT")
	if err != nil {
		return nil
	}
	sort.Strings(opts)

	keys := make([]string, 0, len(opts))
	for _, key := range opts {
		if key == "HWAF_ENV_SPY" {
			continue
		}
		keys = append(keys, key)
	}
	return keys
}

// EOF
