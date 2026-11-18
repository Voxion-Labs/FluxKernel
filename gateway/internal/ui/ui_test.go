package ui

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

func TestUIHandler(t *testing.T) {
	tempWorkspace := t.TempDir()
	cfg := &config.Config{
		Environment:  "test",
		EngineURL:    "http://localhost:8000",
		WorkspaceDir: tempWorkspace,
	}

	h, err := NewUIHandler(cfg)
	if err != nil {
		t.Fatalf("Failed to initialize UIHandler: %v", err)
	}

	t.Run("Default Theme is Light", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/dashboard", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, `data-theme="light"`) {
			t.Errorf("expected default theme to be light, body: %s", body)
		}

		// Ensure ZERO JavaScript policy compliance
		if strings.Contains(body, "<script") {
			t.Errorf("VIOLATION: <script> tag detected in rendered HTML! Policy requires pure HTML/CSS (Zero JS).")
		}

		if !strings.Contains(body, "FluxKernel") {
			t.Errorf("body missing 'FluxKernel'")
		}
		if !strings.Contains(body, "Emergency Rollback") {
			t.Errorf("body missing 'Emergency Rollback'")
		}
	})

	t.Run("Dark Theme Query Override", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/dashboard?theme=dark", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, `data-theme="dark"`) {
			t.Errorf("expected dark theme override in body")
		}
	})

	t.Run("System Theme Query Override", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/dashboard?theme=system", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, `data-theme="system"`) {
			t.Errorf("expected system theme override in body")
		}
	})

	t.Run("Directive Form Dispatch (Interactive)", func(t *testing.T) {
		form := url.Values{}
		form.Set("prompt", "Implement pure Go data structures")
		form.Set("mode", "interactive")
		form.Set("persona", "coder")
		form.Set("theme", "light")

		req := httptest.NewRequest(http.MethodPost, "/dashboard/dispatch", strings.NewReader(form.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		rec := httptest.NewRecorder()

		h.HandleDispatch(rec, req)

		if rec.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect, got %d", rec.Code)
		}

		location := rec.Header().Get("Location")
		if !strings.Contains(location, "/dashboard") {
			t.Errorf("expected redirect to /dashboard, got %s", location)
		}
	})

	t.Run("Directive Form Dispatch (Autonomous Auto-Pilot Loop)", func(t *testing.T) {
		form := url.Values{}
		form.Set("prompt", "Build a high-performance memory allocator in C++20")
		form.Set("mode", "autopilot")
		form.Set("persona", "architect")
		form.Set("theme", "light")

		req := httptest.NewRequest(http.MethodPost, "/dashboard/dispatch", strings.NewReader(form.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		rec := httptest.NewRecorder()

		h.HandleDispatch(rec, req)

		if rec.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect, got %d", rec.Code)
		}

		// Verify that decision matrix cards and pending diff batch are rendered on the dashboard
		reqDash := httptest.NewRequest(http.MethodGet, "/dashboard", nil)
		recDash := httptest.NewRecorder()
		h.ServeHTTP(recDash, reqDash)

		dashBody := recDash.Body.String()
		if !strings.Contains(dashBody, "decision-matrix-card") {
			t.Errorf("expected decision matrix card to be rendered on dashboard")
		}
		if !strings.Contains(dashBody, "timeline-item") {
			t.Errorf("expected timeline item to be rendered in decision stream")
		}
		if !strings.Contains(dashBody, "diff-gate-card") {
			t.Errorf("expected diff gate card to be rendered when diff batch is pending")
		}
	})

	t.Run("Abort Loop Form Dispatch", func(t *testing.T) {
		form := url.Values{}
		form.Set("theme", "light")

		req := httptest.NewRequest(http.MethodPost, "/dashboard/loop/abort", strings.NewReader(form.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		rec := httptest.NewRecorder()

		h.HandleAbortLoop(rec, req)

		if rec.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect, got %d", rec.Code)
		}

		reqDash := httptest.NewRequest(http.MethodGet, "/dashboard", nil)
		recDash := httptest.NewRecorder()
		h.ServeHTTP(recDash, reqDash)

		dashBody := recDash.Body.String()
		if !strings.Contains(dashBody, "ABORTED") {
			t.Errorf("expected ABORTED status in dashboard body")
		}
	})

	t.Run("File Create, Edit, and Delete Lifecycle (Sandbox Verified)", func(t *testing.T) {
		// 1. Create a file
		createForm := url.Values{}
		createForm.Set("filename", "sub/demo.go")
		createForm.Set("content", "package main\n\nfunc Hello() string { return \"FluxKernel\" }\n")
		createForm.Set("theme", "light")

		reqCreate := httptest.NewRequest(http.MethodPost, "/dashboard/file/create", strings.NewReader(createForm.Encode()))
		reqCreate.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recCreate := httptest.NewRecorder()

		h.HandleFileCreate(recCreate, reqCreate)
		if recCreate.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on file create, got %d", recCreate.Code)
		}

		// Verify file exists on disk
		createdFile := filepath.Join(tempWorkspace, "sub", "demo.go")
		content, err := os.ReadFile(createdFile)
		if err != nil || !strings.Contains(string(content), "Hello()") {
			t.Fatalf("failed to read created file on disk: %v", err)
		}

		// 2. Render dashboard with active file
		reqDash := httptest.NewRequest(http.MethodGet, "/dashboard?file=sub/demo.go", nil)
		recDash := httptest.NewRecorder()
		h.ServeHTTP(recDash, reqDash)
		dashBody := recDash.Body.String()
		if !strings.Contains(dashBody, "code-editor") {
			t.Errorf("expected code editor textarea when file is active")
		}
		if !strings.Contains(dashBody, "Save Changes") {
			t.Errorf("expected Save Changes button in file editor")
		}

		// 3. Edit and save file
		editForm := url.Values{}
		editForm.Set("file", "sub/demo.go")
		editForm.Set("content", "package main\n\nfunc Hello() string { return \"FluxKernel Enhanced\" }\n")
		editForm.Set("theme", "light")

		reqEdit := httptest.NewRequest(http.MethodPost, "/dashboard/file/write", strings.NewReader(editForm.Encode()))
		reqEdit.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recEdit := httptest.NewRecorder()

		h.HandleFileWrite(recEdit, reqEdit)
		if recEdit.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on file write, got %d", recEdit.Code)
		}

		updatedContent, _ := os.ReadFile(createdFile)
		if !strings.Contains(string(updatedContent), "Enhanced") {
			t.Errorf("file content was not updated: %s", string(updatedContent))
		}

		// 4. Block path traversal write
		badForm := url.Values{}
		badForm.Set("file", "../outside.txt")
		badForm.Set("content", "malicious payload")
		reqBad := httptest.NewRequest(http.MethodPost, "/dashboard/file/write", strings.NewReader(badForm.Encode()))
		reqBad.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recBad := httptest.NewRecorder()
		h.HandleFileWrite(recBad, reqBad)

		// 5. Block protected partition write
		secForm := url.Values{}
		secForm.Set("file", ".git/config")
		secForm.Set("content", "tamper")
		reqSec := httptest.NewRequest(http.MethodPost, "/dashboard/file/write", strings.NewReader(secForm.Encode()))
		reqSec.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recSec := httptest.NewRecorder()
		h.HandleFileWrite(recSec, reqSec)

		// 6. Delete file
		delForm := url.Values{}
		delForm.Set("file", "sub/demo.go")
		delForm.Set("theme", "light")

		reqDel := httptest.NewRequest(http.MethodPost, "/dashboard/file/delete", strings.NewReader(delForm.Encode()))
		reqDel.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recDel := httptest.NewRecorder()
		h.HandleFileDelete(recDel, reqDel)

		if _, err := os.Stat(createdFile); !os.IsNotExist(err) {
			t.Errorf("expected file to be deleted from disk")
		}
	})

	t.Run("Diff Batch Approve and Reject Gate", func(t *testing.T) {
		// Set up a pending diff batch
		h.mu.Lock()
		h.pendingDiffBatch = &DiffBatch{
			BatchID:   "diff-test-1",
			LoopID:    "loop-test-1",
			Iteration: 1,
			Files: []DiffFile{
				GenerateUnifiedDiff("math.go", "func Add(a, b int) int { return 0 }", "func Add(a, b int) int { return a + b }"),
			},
			Status:    "pending",
			CreatedAt: "12:00:00",
		}
		h.mu.Unlock()

		// 1. Approve diff batch
		apprForm := url.Values{}
		apprForm.Set("theme", "light")
		reqAppr := httptest.NewRequest(http.MethodPost, "/dashboard/diff/approve", strings.NewReader(apprForm.Encode()))
		reqAppr.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recAppr := httptest.NewRecorder()
		h.HandleDiffApprove(recAppr, reqAppr)

		if recAppr.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on diff approve, got %d", recAppr.Code)
		}

		h.mu.RLock()
		if h.pendingDiffBatch != nil {
			t.Errorf("expected pending diff batch to be cleared after approve")
		}
		h.mu.RUnlock()

		// 2. Reject diff batch
		h.mu.Lock()
		h.pendingDiffBatch = &DiffBatch{
			BatchID:   "diff-test-2",
			LoopID:    "loop-test-2",
			Iteration: 1,
			Files: []DiffFile{
				GenerateUnifiedDiff("evil.go", "", "malicious code"),
			},
			Status:    "pending",
			CreatedAt: "12:01:00",
		}
		h.mu.Unlock()

		rejForm := url.Values{}
		rejForm.Set("theme", "light")
		reqRej := httptest.NewRequest(http.MethodPost, "/dashboard/diff/reject", strings.NewReader(rejForm.Encode()))
		reqRej.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recRej := httptest.NewRecorder()
		h.HandleDiffReject(recRej, reqRej)

		if recRej.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on diff reject, got %d", recRej.Code)
		}

		h.mu.RLock()
		if h.pendingDiffBatch != nil {
			t.Errorf("expected pending diff batch to be cleared after reject")
		}
		h.mu.RUnlock()
	})

	t.Run("Emergency Rollback Form Dispatch", func(t *testing.T) {
		form := url.Values{}
		form.Set("snapshot_id", "snap_test_123")
		form.Set("theme", "light")

		req := httptest.NewRequest(http.MethodPost, "/dashboard/rollback", strings.NewReader(form.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		rec := httptest.NewRecorder()

		h.HandleRollback(rec, req)

		if rec.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect, got %d", rec.Code)
		}
	})

	t.Run("Static Asset Delivery (CSS Only, Zero JS)", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/static/css/dashboard.css", nil)
		rec := httptest.NewRecorder()

		h.ServeStatic().ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Errorf("expected 200 OK for dashboard.css, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, "FluxKernel Enterprise Minimalist UI Stylesheet") {
			t.Errorf("CSS missing enterprise theme signature")
		}
		if !strings.Contains(body, "diff-gate-card") {
			t.Errorf("CSS missing diff-gate-card styles")
		}
		if !strings.Contains(body, "code-editor") {
			t.Errorf("CSS missing code-editor styles")
		}
	})
}
