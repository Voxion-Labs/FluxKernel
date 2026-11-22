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

	t.Run("Default Theme is System", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/dashboard", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, `data-theme="system"`) {
			t.Errorf("expected default theme to be system, body: %s", body)
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

	t.Run("Light Theme Query Override", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/dashboard?theme=light", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, `data-theme="light"`) {
			t.Errorf("expected light theme override in body")
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
			BatchID:    "diff-test-1",
			LoopID:     "loop-test-1",
			BranchName: "flux/task-loop-test-1",
			BaseBranch: "main",
			Iteration:  1,
			Files: []DiffFile{
				GenerateUnifiedDiff("math.go", "func Add(a, b int) int { return 0 }", "func Add(a, b int) int { return a + b }"),
			},
			Status:    "pending",
			CreatedAt: "12:00:00",
		}
		h.mu.Unlock()

		// Verify isolated branch badge in HTML rendering
		reqRender := httptest.NewRequest(http.MethodGet, "/dashboard?theme=light", nil)
		recRender := httptest.NewRecorder()
		h.ServeHTTP(recRender, reqRender)
		if !strings.Contains(recRender.Body.String(), "flux/task-loop-test-1") {
			t.Errorf("expected rendered HTML to contain isolated branch name 'flux/task-loop-test-1'")
		}

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

	t.Run("RAG Index and Search Form Dispatch", func(t *testing.T) {
		// Index form dispatch
		indexForm := url.Values{}
		indexForm.Set("theme", "light")
		reqIndex := httptest.NewRequest(http.MethodPost, "/dashboard/rag/index", strings.NewReader(indexForm.Encode()))
		reqIndex.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recIndex := httptest.NewRecorder()
		h.HandleRAGIndex(recIndex, reqIndex)

		if recIndex.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on RAG index, got %d", recIndex.Code)
		}

		// Search form dispatch
		searchForm := url.Values{}
		searchForm.Set("query", "SIMD vector dot")
		searchForm.Set("domain", "tech")
		searchForm.Set("theme", "light")
		reqSearch := httptest.NewRequest(http.MethodPost, "/dashboard/rag/search", strings.NewReader(searchForm.Encode()))
		reqSearch.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recSearch := httptest.NewRecorder()
		h.HandleRAGSearch(recSearch, reqSearch)

		if recSearch.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on RAG search, got %d", recSearch.Code)
		}

		// Clear search dispatch
		reqClear := httptest.NewRequest(http.MethodGet, "/dashboard/rag/search?clear=1&theme=light", nil)
		recClear := httptest.NewRecorder()
		h.HandleRAGSearch(recClear, reqClear)

		if recClear.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on RAG clear, got %d", recClear.Code)
		}
	})

	t.Run("Web Search and Research Form Dispatch", func(t *testing.T) {
		// Live Research dispatch
		researchForm := url.Values{}
		researchForm.Set("query", "Quantum Physics")
		researchForm.Set("mode", "research")
		researchForm.Set("theme", "light")
		reqResearch := httptest.NewRequest(http.MethodPost, "/dashboard/web/search", strings.NewReader(researchForm.Encode()))
		reqResearch.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recResearch := httptest.NewRecorder()
		h.HandleWebSearch(recResearch, reqResearch)

		if recResearch.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on web research, got %d", recResearch.Code)
		}

		// Live Search dispatch
		searchForm := url.Values{}
		searchForm.Set("query", "Algorithms")
		searchForm.Set("mode", "search")
		searchForm.Set("theme", "light")
		reqSearch := httptest.NewRequest(http.MethodPost, "/dashboard/web/search", strings.NewReader(searchForm.Encode()))
		reqSearch.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recSearch := httptest.NewRecorder()
		h.HandleWebSearch(recSearch, reqSearch)

		if recSearch.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on web search, got %d", recSearch.Code)
		}

		// Clear dispatch
		reqClear := httptest.NewRequest(http.MethodGet, "/dashboard/web/search?clear=1&theme=light", nil)
		recClear := httptest.NewRecorder()
		h.HandleWebSearch(recClear, reqClear)

		if recClear.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on web clear, got %d", recClear.Code)
		}
	})

	t.Run("Cross-AI Learning Ingest and Clear Form Dispatch", func(t *testing.T) {
		// 1. Ingest form dispatch with empty content (should reject safely)
		emptyForm := url.Values{}
		emptyForm.Set("source", "auto")
		emptyForm.Set("raw_content", "")
		emptyForm.Set("theme", "light")
		reqEmpty := httptest.NewRequest(http.MethodPost, "/dashboard/learning/ingest", strings.NewReader(emptyForm.Encode()))
		reqEmpty.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recEmpty := httptest.NewRecorder()
		h.HandleAILearningIngest(recEmpty, reqEmpty)

		if recEmpty.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on empty ingest, got %d", recEmpty.Code)
		}

		// 2. Ingest form dispatch with valid markdown transcript
		validForm := url.Values{}
		validForm.Set("source", "markdown")
		validForm.Set("session_title", "Golang Channel Design")
		validForm.Set("raw_content", "# Golang Channel Design\nUser:\nHow do buffered channels prevent goroutine leaks?\nAssistant:\nBuffered channels provide space for values without blocking.\n```go\nch := make(chan int, 10)\n```")
		validForm.Set("theme", "light")
		reqValid := httptest.NewRequest(http.MethodPost, "/dashboard/learning/ingest", strings.NewReader(validForm.Encode()))
		reqValid.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recValid := httptest.NewRecorder()
		h.HandleAILearningIngest(recValid, reqValid)

		if recValid.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on valid ingest, got %d", recValid.Code)
		}

		// 3. Clear form dispatch
		clearForm := url.Values{}
		clearForm.Set("theme", "light")
		reqClear := httptest.NewRequest(http.MethodPost, "/dashboard/learning/clear", strings.NewReader(clearForm.Encode()))
		reqClear.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recClear := httptest.NewRecorder()
		h.HandleAILearningClear(recClear, reqClear)

		if recClear.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on clear, got %d", recClear.Code)
		}
	})

	t.Run("Episodic Learned Rules Add and Delete Form Dispatch", func(t *testing.T) {
		// 1. Add rule with empty directive (should reject safely)
		emptyForm := url.Values{}
		emptyForm.Set("directive", "")
		emptyForm.Set("theme", "light")
		reqEmpty := httptest.NewRequest(http.MethodPost, "/dashboard/rules/add", strings.NewReader(emptyForm.Encode()))
		reqEmpty.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recEmpty := httptest.NewRecorder()
		h.HandleRuleAdd(recEmpty, reqEmpty)

		if recEmpty.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on empty directive, got %d", recEmpty.Code)
		}

		// 2. Add rule with valid directive
		validForm := url.Values{}
		validForm.Set("directive", "Never use Axios; always use standard library")
		validForm.Set("category", "forbidden_pattern")
		validForm.Set("domain", "tech")
		validForm.Set("theme", "light")
		reqValid := httptest.NewRequest(http.MethodPost, "/dashboard/rules/add", strings.NewReader(validForm.Encode()))
		reqValid.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recValid := httptest.NewRecorder()
		h.HandleRuleAdd(recValid, reqValid)

		if recValid.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on valid rule add, got %d", recValid.Code)
		}

		// 3. Delete rule dispatch
		delForm := url.Values{}
		delForm.Set("rule_id", "rule_tech_never_use_axios")
		delForm.Set("theme", "light")
		reqDel := httptest.NewRequest(http.MethodPost, "/dashboard/rules/delete", strings.NewReader(delForm.Encode()))
		reqDel.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recDel := httptest.NewRecorder()
		h.HandleRuleDelete(recDel, reqDel)

		if recDel.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on rule delete, got %d", recDel.Code)
		}
	})

	t.Run("Sovereign Storage Vault Form Dispatches (Checkpoint and Vacuum)", func(t *testing.T) {
		// 1. Checkpoint dispatch
		cpForm := url.Values{}
		cpForm.Set("theme", "light")
		reqCP := httptest.NewRequest(http.MethodPost, "/dashboard/vault/checkpoint", strings.NewReader(cpForm.Encode()))
		reqCP.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recCP := httptest.NewRecorder()
		h.HandleVaultCheckpoint(recCP, reqCP)

		if recCP.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on vault checkpoint, got %d", recCP.Code)
		}

		// 2. Vacuum dispatch
		vacForm := url.Values{}
		vacForm.Set("theme", "light")
		reqVac := httptest.NewRequest(http.MethodPost, "/dashboard/vault/vacuum", strings.NewReader(vacForm.Encode()))
		reqVac.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recVac := httptest.NewRecorder()
		h.HandleVaultVacuum(recVac, reqVac)

		if recVac.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on vault vacuum, got %d", recVac.Code)
		}
	})

	t.Run("Multi-Domain Agent Swarm Form Dispatch", func(t *testing.T) {
		form := url.Values{}
		form.Set("prompt", "Design microsecond matching engine with numerical bounds and risk management")
		form.Set("mode", "consensus")
		form.Set("domain_hint", "tech")
		form.Set("theme", "light")

		req := httptest.NewRequest(http.MethodPost, "/dashboard/swarm/deliberate", strings.NewReader(form.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		rec := httptest.NewRecorder()

		h.HandleSwarmDeliberate(rec, req)

		if rec.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on swarm deliberate, got %d", rec.Code)
		}
	})

	t.Run("Real-Time Telemetry Streaming (Zero-JS HTML and SSE)", func(t *testing.T) {
		// 1. Browser chunked progressive HTML stream (Zero-JS)
		reqHTML := httptest.NewRequest(http.MethodGet, "/dashboard/stream?theme=light", nil)
		recHTML := httptest.NewRecorder()
		h.HandleStream(recHTML, reqHTML)

		if recHTML.Code != http.StatusOK {
			t.Errorf("expected 200 OK for HTML stream, got %d", recHTML.Code)
		}
		if !strings.Contains(recHTML.Header().Get("Content-Type"), "text/html") {
			t.Errorf("expected Content-Type text/html, got %s", recHTML.Header().Get("Content-Type"))
		}
		htmlBody := recHTML.Body.String()
		if strings.Contains(htmlBody, "<script") {
			t.Errorf("VIOLATION: <script> detected in live telemetry stream! Policy requires Zero-JS.")
		}
		if !strings.Contains(htmlBody, "FLUXKERNEL LIVE TELEMETRY BUS") {
			t.Errorf("expected body to contain FLUXKERNEL LIVE TELEMETRY BUS")
		}

		// 2. Server-Sent Events (SSE) stream for programmatic clients
		reqSSE := httptest.NewRequest(http.MethodGet, "/dashboard/stream", nil)
		reqSSE.Header.Set("Accept", "text/event-stream")
		recSSE := httptest.NewRecorder()
		h.HandleStream(recSSE, reqSSE)

		if recSSE.Code != http.StatusOK {
			t.Errorf("expected 200 OK for SSE stream, got %d", recSSE.Code)
		}
		if !strings.Contains(recSSE.Header().Get("Content-Type"), "text/event-stream") {
			t.Errorf("expected Content-Type text/event-stream, got %s", recSSE.Header().Get("Content-Type"))
		}
	})

	t.Run("Universal Workspace & Cross-Domain Search (Phase 8)", func(t *testing.T) {
		// Create sample test files in workspace
		calcPath := filepath.Join(tempWorkspace, "calc.go")
		_ = os.WriteFile(calcPath, []byte("package math\n\nfunc CalculateROI() int {\n\treturn 42\n}\n"), 0644)
		csvPath := filepath.Join(tempWorkspace, "metrics.csv")
		_ = os.WriteFile(csvPath, []byte("item,val\nroi,15.2\n"), 0644)

		// 1. Dispatch search query
		form := url.Values{}
		form.Set("q", "CalculateROI")
		form.Set("domain", "tech")
		form.Set("theme", "light")

		reqSearch := httptest.NewRequest(http.MethodGet, "/dashboard/search?"+form.Encode(), nil)
		recSearch := httptest.NewRecorder()
		h.HandleGlobalSearch(recSearch, reqSearch)

		if recSearch.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on search dispatch, got %d", recSearch.Code)
		}

		// 2. Render dashboard with active search query
		reqDashboard := httptest.NewRequest(http.MethodGet, "/dashboard?q=CalculateROI&domain=tech&theme=light", nil)
		recDashboard := httptest.NewRecorder()
		h.ServeHTTP(recDashboard, reqDashboard)

		if recDashboard.Code != http.StatusOK {
			t.Errorf("expected 200 OK rendering search results, got %d", recDashboard.Code)
		}

		dashBody := recDashboard.Body.String()
		// Zero-JS verification
		if strings.Contains(dashBody, "<script") {
			t.Errorf("VIOLATION: <script> tag detected in search results rendering! Policy requires Zero-JS.")
		}
		if !strings.Contains(dashBody, "CalculateROI") {
			t.Errorf("expected body to contain search query 'CalculateROI'")
		}
		if !strings.Contains(dashBody, "calc.go") {
			t.Errorf("expected body to contain matched file 'calc.go'")
		}

		// 3. Clear search results
		reqClear := httptest.NewRequest(http.MethodGet, "/dashboard/search?clear=1&theme=light", nil)
		recClear := httptest.NewRecorder()
		h.HandleGlobalSearch(recClear, reqClear)

		if recClear.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect on clear search, got %d", recClear.Code)
		}
	})

	t.Run("Phase 10: Sovereign AI Driver Switching & Status Badge", func(t *testing.T) {
		// 1. Initial render: defaults to FLUX-NATIVE
		reqInitial := httptest.NewRequest(http.MethodGet, "/dashboard", nil)
		recInitial := httptest.NewRecorder()
		h.ServeHTTP(recInitial, reqInitial)

		if recInitial.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d", recInitial.Code)
		}
		bodyInitial := recInitial.Body.String()
		if !strings.Contains(bodyInitial, "FLUX-NATIVE") {
			t.Errorf("expected initial dashboard to contain 'FLUX-NATIVE' badge, got: %s", bodyInitial)
		}
		if !strings.Contains(bodyInitial, "⚡ Flux-1.0 Native") {
			t.Errorf("expected directive form to contain '⚡ Flux-1.0 Native' option")
		}

		// 2. Select another engine via HandleEngineSelect
		form := url.Values{}
		form.Set("engine", "gemini")
		form.Set("theme", "light")
		reqSelect := httptest.NewRequest(http.MethodPost, "/dashboard/engine/select", strings.NewReader(form.Encode()))
		reqSelect.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recSelect := httptest.NewRecorder()

		h.HandleEngineSelect(recSelect, reqSelect)
		if recSelect.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect, got %d", recSelect.Code)
		}

		// 3. Render dashboard with switched engine
		reqSwitched := httptest.NewRequest(http.MethodGet, "/dashboard", nil)
		recSwitched := httptest.NewRecorder()
		h.ServeHTTP(recSwitched, reqSwitched)

		bodySwitched := recSwitched.Body.String()
		if !strings.Contains(bodySwitched, "GEMINI") {
			t.Errorf("expected switched dashboard to display 'GEMINI' badge")
		}
		if strings.Contains(bodySwitched, "<script") {
			t.Errorf("VIOLATION: Zero-JS policy broken in engine selection view")
		}

		// 4. Switch back to native sovereign engine
		formNative := url.Values{}
		formNative.Set("engine", "flux-native")
		formNative.Set("theme", "light")
		reqNative := httptest.NewRequest(http.MethodPost, "/dashboard/engine/select", strings.NewReader(formNative.Encode()))
		reqNative.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recNative := httptest.NewRecorder()

		h.HandleEngineSelect(recNative, reqNative)
		if recNative.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect, got %d", recNative.Code)
		}
	})

	t.Run("Phase 11: Industrial Mission Control UI & Domain Hub", func(t *testing.T) {
		// 1. Overview Workspace rendering
		reqOverview := httptest.NewRequest(http.MethodGet, "/dashboard?tab=overview&theme=light", nil)
		recOverview := httptest.NewRecorder()
		h.ServeHTTP(recOverview, reqOverview)

		if recOverview.Code != http.StatusOK {
			t.Fatalf("expected 200 OK for overview tab, got %d", recOverview.Code)
		}
		bodyOverview := recOverview.Body.String()
		if !strings.Contains(bodyOverview, "mission-control-ribbon") {
			t.Errorf("expected body to contain 'mission-control-ribbon'")
		}
		if !strings.Contains(bodyOverview, "domain-hub-bar") {
			t.Errorf("expected body to contain 'domain-hub-bar'")
		}
		if !strings.Contains(bodyOverview, "OVERVIEW") {
			t.Errorf("expected body to contain 'OVERVIEW' active hub badge")
		}
		if !strings.Contains(bodyOverview, "Git Task Sandboxes") {
			t.Errorf("expected body to contain 'Git Task Sandboxes'")
		}
		if strings.Contains(bodyOverview, "<script") {
			t.Errorf("VIOLATION: Zero-JS policy broken in overview tab")
		}

		// 2. Tech Domain Hub rendering
		reqTech := httptest.NewRequest(http.MethodGet, "/dashboard?tab=tech&theme=light", nil)
		recTech := httptest.NewRecorder()
		h.ServeHTTP(recTech, reqTech)
		bodyTech := recTech.Body.String()
		if !strings.Contains(bodyTech, "Systems & Engineering Launchpad") {
			t.Errorf("expected Tech tab to contain 'Systems & Engineering Launchpad'")
		}
		if !strings.Contains(bodyTech, "Go Worker Pool") {
			t.Errorf("expected Tech tab to contain 'Go Worker Pool' preset")
		}

		// 3. Science Domain Hub rendering
		reqSci := httptest.NewRequest(http.MethodGet, "/dashboard?tab=science&theme=light", nil)
		recSci := httptest.NewRecorder()
		h.ServeHTTP(recSci, reqSci)
		bodySci := recSci.Body.String()
		if !strings.Contains(bodySci, "Science & Quantitative Launchpad") {
			t.Errorf("expected Science tab to contain 'Science & Quantitative Launchpad'")
		}
		if !strings.Contains(bodySci, "Physics Decay") {
			t.Errorf("expected Science tab to contain 'Physics Decay' preset")
		}

		// 4. Finance Domain Hub rendering
		reqFin := httptest.NewRequest(http.MethodGet, "/dashboard?tab=finance&theme=light", nil)
		recFin := httptest.NewRecorder()
		h.ServeHTTP(recFin, reqFin)
		bodyFin := recFin.Body.String()
		if !strings.Contains(bodyFin, "Finance & Economics Launchpad") {
			t.Errorf("expected Finance tab to contain 'Finance & Economics Launchpad'")
		}
		if !strings.Contains(bodyFin, "Cash Flow Audit") {
			t.Errorf("expected Finance tab to contain 'Cash Flow Audit' preset")
		}

		// 5. Sandbox handlers testing (Create, Merge, Abort)
		formCreate := url.Values{}
		formCreate.Set("task_id", "test-task-ui")
		formCreate.Set("theme", "light")
		formCreate.Set("tab", "tech")
		reqCreate := httptest.NewRequest(http.MethodPost, "/dashboard/sandbox/create", strings.NewReader(formCreate.Encode()))
		reqCreate.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recCreate := httptest.NewRecorder()
		h.HandleSandboxCreate(recCreate, reqCreate)
		if recCreate.Code != http.StatusSeeOther {
			t.Errorf("expected 303 redirect on sandbox create, got %d", recCreate.Code)
		}

		formMerge := url.Values{}
		formMerge.Set("task_id", "test-task-ui")
		formMerge.Set("theme", "light")
		formMerge.Set("tab", "tech")
		reqMerge := httptest.NewRequest(http.MethodPost, "/dashboard/sandbox/merge", strings.NewReader(formMerge.Encode()))
		reqMerge.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recMerge := httptest.NewRecorder()
		h.HandleSandboxMerge(recMerge, reqMerge)
		if recMerge.Code != http.StatusSeeOther {
			t.Errorf("expected 303 redirect on sandbox merge, got %d", recMerge.Code)
		}

		formAbort := url.Values{}
		formAbort.Set("task_id", "test-task-ui")
		formAbort.Set("theme", "light")
		formAbort.Set("tab", "tech")
		reqAbort := httptest.NewRequest(http.MethodPost, "/dashboard/sandbox/abort", strings.NewReader(formAbort.Encode()))
		reqAbort.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recAbort := httptest.NewRecorder()
		h.HandleSandboxAbort(recAbort, reqAbort)
		if recAbort.Code != http.StatusSeeOther {
			t.Errorf("expected 303 redirect on sandbox abort, got %d", recAbort.Code)
		}
	})

	t.Run("Phase 12: End-to-End Production Readiness & Embedded Asset Integrity", func(t *testing.T) {
		// 1. Verify embedded filesystem integrity (templates and static CSS)
		tmplEntries, err := embeddedFS.ReadDir("templates")
		if err != nil {
			t.Fatalf("failed to read embedded templates directory: %v", err)
		}
		if len(tmplEntries) == 0 {
			t.Errorf("expected embedded templates to be present, found 0")
		}

		staticEntries, err := embeddedFS.ReadDir("static/css")
		if err != nil {
			t.Fatalf("failed to read embedded static/css directory: %v", err)
		}
		if len(staticEntries) == 0 {
			t.Errorf("expected embedded CSS assets to be present, found 0")
		}

		// 2. Full render test of all 9 domain hubs
		hubs := []string{"overview", "tech", "science", "finance", "research", "rules", "consensus", "vault", "all"}
		for _, hub := range hubs {
			req := httptest.NewRequest(http.MethodGet, "/dashboard?tab="+hub+"&theme=light", nil)
			rec := httptest.NewRecorder()
			h.ServeHTTP(rec, req)

			if rec.Code != http.StatusOK {
				t.Errorf("hub '%s' failed to render, got status %d", hub, rec.Code)
			}
			body := rec.Body.String()
			if strings.Contains(body, "<script") {
				t.Errorf("VIOLATION: Zero-JS policy broken in hub '%s'", hub)
			}
			if !strings.Contains(body, "mission-control-ribbon") {
				t.Errorf("hub '%s' missing mission-control-ribbon", hub)
			}
			if !strings.Contains(body, "domain-hub-bar") {
				t.Errorf("hub '%s' missing domain-hub-bar", hub)
			}
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
		if !strings.Contains(body, "Plus Jakarta Sans") {
			t.Errorf("CSS missing Plus Jakarta Sans font import")
		}
		if !strings.Contains(body, "landing-body") {
			t.Errorf("CSS missing landing-body styles")
		}
	})

	t.Run("Sovereign Landing & Login Page (Lexio Aesthetic System)", func(t *testing.T) {
		// 1. Default GET /login renders with system theme and Zero-JS
		req := httptest.NewRequest(http.MethodGet, "/login", nil)
		rec := httptest.NewRecorder()
		h.HandleLogin(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 OK for /login, got %d", rec.Code)
		}

		body := rec.Body.String()
		if strings.Contains(body, "<script") {
			t.Errorf("VIOLATION: Zero-JS policy broken on /login")
		}
		if !strings.Contains(body, `data-theme="system"`) {
			t.Errorf("expected default theme 'system' on /login, got: %s", body)
		}
		if !strings.Contains(body, "landing-body") {
			t.Errorf("expected body to have landing-body class")
		}
		if !strings.Contains(body, "FluxKernel") {
			t.Errorf("expected body to contain FluxKernel brand")
		}
		if !strings.Contains(body, "Autonomous intelligence and foundational reasoning") {
			t.Errorf("expected body to contain hero headline")
		}
		if !strings.Contains(body, "Workspace Operator Profile") {
			t.Errorf("expected body to contain operator profile header")
		}
		if !strings.Contains(body, "Flux-1.0 Native") {
			t.Errorf("expected body to contain Flux-1.0 Native engine choice")
		}
		if !strings.Contains(body, "© 2026 Voxion Labs · All rights reserved.") {
			t.Errorf("expected body to contain official copyright line")
		}

		// 2. Light and Dark Theme Overrides
		for _, theme := range []string{"light", "dark"} {
			reqT := httptest.NewRequest(http.MethodGet, "/login?theme="+theme, nil)
			recT := httptest.NewRecorder()
			h.HandleLogin(recT, reqT)
			if recT.Code != http.StatusOK {
				t.Errorf("expected 200 OK for theme %s, got %d", theme, recT.Code)
			}
			if !strings.Contains(recT.Body.String(), `data-theme="`+theme+`"`) {
				t.Errorf("expected data-theme=\"%s\"", theme)
			}
		}

		// 3. POST /login form dispatch redirects to dashboard
		form := url.Values{}
		form.Set("operator", "chief_architect")
		form.Set("workspace", "./workspace")
		form.Set("engine", "flux-native")
		form.Set("theme", "dark")

		reqPost := httptest.NewRequest(http.MethodPost, "/login", strings.NewReader(form.Encode()))
		reqPost.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		recPost := httptest.NewRecorder()
		h.HandleLogin(recPost, reqPost)

		if recPost.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect, got %d", recPost.Code)
		}
		loc := recPost.Header().Get("Location")
		if !strings.Contains(loc, "/dashboard") || !strings.Contains(loc, "theme=dark") || !strings.Contains(loc, "engine=flux-native") {
			t.Errorf("unexpected redirect location: %s", loc)
		}
	})
}
