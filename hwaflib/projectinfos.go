package hwaflib

import (
	"fmt"
	"path/filepath"

	gocfg "github.com/gonuts/config"
)

type ProjectInfo struct {
	cfg *gocfg.Config
}

func NewProjectInfo(name string) (*ProjectInfo, error) {
	var err error
	fname := filepath.Clean(name)
	if !path_exists(fname) {
		err = fmt.Errorf("could not find project info [%s]", fname)
		return nil, err
	}
	cfg, err := gocfg.ReadDefault(fname)
	if err != nil {
		return nil, err
	}
	//fmt.Printf("cfg [%s]\nsections: %s\n", fname, cfg.Sections())
	return &ProjectInfo{cfg}, nil
}

func (pi *ProjectInfo) Get(key string) (string, error) {
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

// EOF
