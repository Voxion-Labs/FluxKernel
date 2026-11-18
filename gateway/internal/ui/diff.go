package ui

import (
	"strings"
)

// DiffLineType denotes whether a diff line is an addition, deletion, or unchanged.
type DiffLineType string

const (
	DiffLineSame DiffLineType = "same"
	DiffLineAdd  DiffLineType = "add"
	DiffLineDel  DiffLineType = "del"
)

// DiffLine represents a single line in a unified diff view.
type DiffLine struct {
	Type   DiffLineType `json:"type"`
	Text   string       `json:"text"`
	OldNum int          `json:"old_num,omitempty"`
	NewNum int          `json:"new_num,omitempty"`
}

// DiffFile represents diff details for a single workspace file.
type DiffFile struct {
	Path       string     `json:"path"`
	OldContent string     `json:"old_content"`
	NewContent string     `json:"new_content"`
	Lines      []DiffLine `json:"lines"`
	Additions  int        `json:"additions"`
	Deletions  int        `json:"deletions"`
}

// DiffBatch represents a collection of file diffs produced by an agentic loop.
type DiffBatch struct {
	BatchID   string     `json:"batch_id"`
	LoopID    string     `json:"loop_id"`
	Iteration int        `json:"iteration"`
	Files     []DiffFile `json:"files"`
	Status    string     `json:"status"` // "pending" | "approved" | "rejected"
	CreatedAt string     `json:"created_at"`
}

// GenerateUnifiedDiff computes an optimal line-by-line LCS unified diff.
func GenerateUnifiedDiff(path, oldContent, newContent string) DiffFile {
	oldLines := splitLines(oldContent)
	newLines := splitLines(newContent)

	var diffLines []DiffLine
	adds := 0
	dels := 0

	// New file: all lines are additions
	if len(oldLines) == 0 || (len(oldLines) == 1 && oldLines[0] == "") {
		for i, line := range newLines {
			adds++
			diffLines = append(diffLines, DiffLine{
				Type:   DiffLineAdd,
				Text:   line,
				NewNum: i + 1,
			})
		}
		return DiffFile{
			Path:       path,
			OldContent: oldContent,
			NewContent: newContent,
			Lines:      diffLines,
			Additions:  adds,
			Deletions:  dels,
		}
	}

	// LCS matrix computation
	n := len(oldLines)
	m := len(newLines)
	dp := make([][]int, n+1)
	for i := range dp {
		dp[i] = make([]int, m+1)
	}

	for i := 1; i <= n; i++ {
		for j := 1; j <= m; j++ {
			if oldLines[i-1] == newLines[j-1] {
				dp[i][j] = dp[i-1][j-1] + 1
			} else if dp[i-1][j] >= dp[i][j-1] {
				dp[i][j] = dp[i-1][j]
			} else {
				dp[i][j] = dp[i][j-1]
			}
		}
	}

	// Backtrack to construct diff
	var revLines []DiffLine
	i, j := n, m
	for i > 0 || j > 0 {
		if i > 0 && j > 0 && oldLines[i-1] == newLines[j-1] {
			revLines = append(revLines, DiffLine{
				Type:   DiffLineSame,
				Text:   oldLines[i-1],
				OldNum: i,
				NewNum: j,
			})
			i--
			j--
		} else if j > 0 && (i == 0 || dp[i][j-1] >= dp[i-1][j]) {
			revLines = append(revLines, DiffLine{
				Type:   DiffLineAdd,
				Text:   newLines[j-1],
				NewNum: j,
			})
			adds++
			j--
		} else if i > 0 && (j == 0 || dp[i][j-1] < dp[i-1][j]) {
			revLines = append(revLines, DiffLine{
				Type:   DiffLineDel,
				Text:   oldLines[i-1],
				OldNum: i,
			})
			dels++
			i--
		}
	}

	// Reverse to restore original sequence
	for k := len(revLines) - 1; k >= 0; k-- {
		diffLines = append(diffLines, revLines[k])
	}

	return DiffFile{
		Path:       path,
		OldContent: oldContent,
		NewContent: newContent,
		Lines:      diffLines,
		Additions:  adds,
		Deletions:  dels,
	}
}

func splitLines(s string) []string {
	if s == "" {
		return nil
	}
	s = strings.ReplaceAll(s, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	s = strings.TrimSuffix(s, "\n")
	if s == "" {
		return nil
	}
	return strings.Split(s, "\n")
}
