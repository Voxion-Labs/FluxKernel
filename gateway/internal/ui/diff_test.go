package ui

import (
	"testing"
)

func TestUnifiedDiff(t *testing.T) {
	t.Run("New File Full Additions", func(t *testing.T) {
		diff := GenerateUnifiedDiff("hello.go", "", "package main\n\nfunc main() {}\n")
		if diff.Additions != 3 {
			t.Errorf("expected 3 additions, got %d", diff.Additions)
		}
		if diff.Deletions != 0 {
			t.Errorf("expected 0 deletions, got %d", diff.Deletions)
		}
		if len(diff.Lines) != 3 {
			t.Errorf("expected 3 diff lines, got %d", len(diff.Lines))
		}
	})

	t.Run("Modified File with Changes", func(t *testing.T) {
		oldCode := "line 1\nline 2\nline 3"
		newCode := "line 1\nline 2 modified\nline 3\nline 4"

		diff := GenerateUnifiedDiff("test.txt", oldCode, newCode)
		if diff.Additions != 2 {
			t.Errorf("expected 2 additions, got %d", diff.Additions)
		}
		if diff.Deletions != 1 {
			t.Errorf("expected 1 deletion, got %d", diff.Deletions)
		}
	})
}
