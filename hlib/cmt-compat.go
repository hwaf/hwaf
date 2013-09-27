package hlib

//
// ----------- cmt statements models ----------
//

// PathStmt declares a new path entry with name Name and value Value
type PathStmt struct {
	Value Value
}

func (stmt *PathStmt) is_stmt() {
}

type PathAppendStmt struct {
	Value Value
}

func (stmt *PathAppendStmt) is_stmt() {
}

type PathPrependStmt struct {
	Value Value
}

func (stmt *PathPrependStmt) is_stmt() {
}

type PathRemoveStmt struct {
	Value Value
}

func (stmt *PathRemoveStmt) is_stmt() {
}

type MacroStmt struct {
	Value Value
}

func (stmt *MacroStmt) is_stmt() {
}

type MacroAppendStmt struct {
	Value Value
}

func (stmt *MacroAppendStmt) is_stmt() {
}

type MacroPrependStmt struct {
	Value Value
}

func (stmt *MacroPrependStmt) is_stmt() {
}

type MacroRemoveStmt struct {
	Value Value
}

func (stmt *MacroRemoveStmt) is_stmt() {
}

// TagStmt defines a new CMT tag with name Name and content Content
type TagStmt struct {
	Name    string
	Content []string
}

func (stmt *TagStmt) is_stmt() {
}

type ApplyTagStmt struct {
	Value Value
}

func (stmt *ApplyTagStmt) is_stmt() {
}

// TagExcludeStmt defines a new CMT tag with name Name and content Content
type TagExcludeStmt struct {
	Name    string
	Content []string
}

func (stmt *TagExcludeStmt) is_stmt() {
}

type IncludeDirsStmt struct {
	Value []string
}

func (stmt *IncludeDirsStmt) is_stmt() {
}

type IncludePathStmt struct {
	Value []string
}

func (stmt *IncludePathStmt) is_stmt() {
}

type SetStmt struct {
	Value Value
}

func (stmt *SetStmt) is_stmt() {
}

type SetAppendStmt struct {
	Value Value
}

func (stmt *SetAppendStmt) is_stmt() {
}

type SetPrependStmt struct {
	Value Value
}

func (stmt *SetPrependStmt) is_stmt() {
}

type SetRemoveStmt struct {
	Value Value
}

func (stmt *SetRemoveStmt) is_stmt() {
}

type AliasStmt struct {
	Value Value
}

func (stmt *AliasStmt) is_stmt() {
}

type ActionStmt struct {
	Value Value
}

func (stmt *ActionStmt) is_stmt() {
}

type PatternStmt struct {
	Name string
	Def  string
}

func (stmt *PatternStmt) is_stmt() {
}

type ApplyPatternStmt struct {
	Name string
	Args []string
}

func (stmt *ApplyPatternStmt) is_stmt() {
}

type DocumentStmt struct {
	Name string
	Args []string
}

func (stmt *DocumentStmt) is_stmt() {
}

type IgnorePatternStmt struct {
	Value Value
}

func (stmt *IgnorePatternStmt) is_stmt() {
}

type MakeFragmentStmt struct {
	Name string
}

func (stmt *MakeFragmentStmt) is_stmt() {
}

// test interfaces
var _ Stmt = (*PathStmt)(nil)
var _ Stmt = (*PathAppendStmt)(nil)
var _ Stmt = (*PathPrependStmt)(nil)
var _ Stmt = (*PathRemoveStmt)(nil)
var _ Stmt = (*MacroStmt)(nil)
var _ Stmt = (*MacroAppendStmt)(nil)
var _ Stmt = (*MacroPrependStmt)(nil)
var _ Stmt = (*MacroRemoveStmt)(nil)
var _ Stmt = (*TagStmt)(nil)
var _ Stmt = (*ApplyTagStmt)(nil)
var _ Stmt = (*TagExcludeStmt)(nil)
var _ Stmt = (*IncludeDirsStmt)(nil)
var _ Stmt = (*IncludePathStmt)(nil)
var _ Stmt = (*SetStmt)(nil)
var _ Stmt = (*SetAppendStmt)(nil)
var _ Stmt = (*SetPrependStmt)(nil)
var _ Stmt = (*SetRemoveStmt)(nil)
var _ Stmt = (*AliasStmt)(nil)
var _ Stmt = (*PatternStmt)(nil)
var _ Stmt = (*ApplyPatternStmt)(nil)
var _ Stmt = (*IgnorePatternStmt)(nil)
var _ Stmt = (*DocumentStmt)(nil)
var _ Stmt = (*ActionStmt)(nil)
var _ Stmt = (*MakeFragmentStmt)(nil)

// EOF
