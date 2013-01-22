// Package platform provides informations about the current platform:
//   - kernel name, 
//   - node name, 
//   - kernel release, 
//   - kernel version, 
//   - machine and
//   - processor
package platform

import (
	"fmt"
)

type Platform struct {
	System    string // Operating system name
	Node      string // Network node hostname
	Release   string // Operating system release
	Version   string // Operating system version
	Machine   string // Machine hardware name
	Processor string // Processor type
}

func (p Platform) String() string {
	return fmt.Sprintf(
		"Platform{System=%q Node=%q Release=%q Version=%q Machine=%q Processor=%q}",
		p.System,
		p.Node,
		p.Release,
		p.Version,
		p.Machine,
		p.Processor)
}

// Infos return the platform informations
func Infos() (Platform, error) {
	return infos()
}

// EOF
