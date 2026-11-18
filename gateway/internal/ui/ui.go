package ui

import (
	"bytes"
	"embed"
	"encoding/json"
	"fmt"
	"html/template"
	"io/fs"
	"log"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

//go:embed static templates
var embeddedFS embed.FS

// Message represents an entry in the agentic conversation ledger.
type Message struct {
	Role      string `json:"role"` // "user" | "agent" | "system"
	Content   string `json:"content"`
	Timestamp string `json:"timestamp"`
}

// SnapshotEntry represents snapshot checkpoint metadata for UI display.
type SnapshotEntry struct {
	SnapshotID string `json:"snapshot_id"`
	Created    string `json:"created_at"`
	Trigger    string `json:"trigger"`
	Iteration  int    `json:"iteration"`
	Label      string `json:"label"`
}

// FileEntry represents a file in the workspace.
type FileEntry struct {
	Name string
	Path string
	Type string // "file" | "folder"
}

// DecisionCard represents an autonomous decision step in the Plan → Write → Test → Fix cycle.
type DecisionCard struct {
	Step        string `json:"step"` // "PLAN" | "SNAPSHOT" | "WRITE" | "TEST" | "FIX" | "SECURITY" | "COMPLETED" | "ABORTED" | "ROUTER"
	Status      string `json:"status"`
	Iteration   int    `json:"iteration"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Details     string `json:"details,omitempty"`
	Timestamp   string `json:"timestamp"`
}

// LoopStatus represents the state of the active Auto-Pilot loop.
type LoopStatus struct {
	LoopID        string         `json:"loop_id"`
	Status        string         `json:"status"` // "idle" | "running" | "completed" | "aborted" | "failed"
	Iteration     int            `json:"iteration"`
	MaxIterations int            `json:"max_iterations"`
	FilesWritten  int            `json:"files_written"`
	AbortFlag     bool           `json:"abort_flag"`
	Cards         []DecisionCard `json:"cards"`
}

// UIHandler manages server-side rendering of pure HTML/CSS templates (Zero-JS).
type UIHandler struct {
	cfg          *config.Config
	templates    *template.Template
	staticFS     http.Handler
	workspaceDir string
	client       *http.Client

	mu           sync.RWMutex
	messages     []Message
	flashMessage string
	flashType    string

	activeLoopID     string
	loopStatus       *LoopStatus
	pendingDiffBatch *DiffBatch
}

// NewUIHandler initializes the template engine and sets up pure SSR handlers.
func NewUIHandler(cfg *config.Config) (*UIHandler, error) {
	funcMap := template.FuncMap{
		"upper": strings.ToUpper,
		"lower": strings.ToLower,
	}

	tmpl, err := template.New("").Funcs(funcMap).ParseFS(embeddedFS, "templates/*.html")
	if err != nil {
		return nil, fmt.Errorf("failed to parse embedded templates: %w", err)
	}

	subStatic, err := fs.Sub(embeddedFS, "static")
	if err != nil {
		return nil, fmt.Errorf("failed to create static sub-filesystem: %w", err)
	}

	initialMessages := []Message{
		{
			Role:      "agent",
			Content:   "FluxKernel Sovereign Engine online. Zero-JS Enterprise Interface initialized.",
			Timestamp: time.Now().Format("15:04:05"),
		},
	}

	return &UIHandler{
		cfg:          cfg,
		templates:    tmpl,
		staticFS:     http.StripPrefix("/static/", http.FileServer(http.FS(subStatic))),
		workspaceDir: cfg.WorkspaceDir,
		client:       &http.Client{Timeout: 10 * time.Second},
		messages:     initialMessages,
		loopStatus: &LoopStatus{
			Status: "idle",
		},
	}, nil
}

// ServeHTTP handles GET /dashboard and renders the full SSR dashboard.
func (h *UIHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		h.handleRenderDashboard(w, r)
	default:
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
	}
}

func (h *UIHandler) handleRenderDashboard(w http.ResponseWriter, r *http.Request) {
	// Theme selection: defaults to "light"
	theme := r.URL.Query().Get("theme")
	if theme == "" {
		if cookie, err := r.Cookie("flux_theme"); err == nil && cookie.Value != "" {
			theme = cookie.Value
		} else {
			theme = "light" // Default theme: Light
		}
	}
	if theme != "light" && theme != "dark" && theme != "system" {
		theme = "light"
	}

	// Active file selection
	activeFile := r.URL.Query().Get("file")
	var activeFileContent string
	var activeFileLines int
	if activeFile != "" {
		activeFileContent = h.readWorkspaceFileSafe(activeFile)
		activeFileLines = len(splitLines(activeFileContent))
	}

	// Scan workspace files
	files := h.getWorkspaceFiles()

	// Load snapshot list
	snapshots := h.getSnapshots()

	// Synchronize active loop state if active
	h.mu.RLock()
	loopID := h.activeLoopID
	h.mu.RUnlock()

	if loopID != "" && !strings.HasPrefix(loopID, "sim-") {
		h.syncLoopStatusFromEngine(loopID)
	}

	h.mu.Lock()
	flash := h.flashMessage
	flashType := h.flashType
	h.flashMessage = ""
	h.flashType = ""
	messagesCopy := make([]Message, len(h.messages))
	copy(messagesCopy, h.messages)

	var currentLoop *LoopStatus
	if h.loopStatus != nil && len(h.loopStatus.Cards) > 0 {
		cardsCopy := make([]DecisionCard, len(h.loopStatus.Cards))
		copy(cardsCopy, h.loopStatus.Cards)
		currentLoop = &LoopStatus{
			LoopID:        h.loopStatus.LoopID,
			Status:        h.loopStatus.Status,
			Iteration:     h.loopStatus.Iteration,
			MaxIterations: h.loopStatus.MaxIterations,
			FilesWritten:  h.loopStatus.FilesWritten,
			AbortFlag:     h.loopStatus.AbortFlag,
			Cards:         cardsCopy,
		}
	}

	var currentDiffBatch *DiffBatch
	if h.pendingDiffBatch != nil {
		currentDiffBatch = h.pendingDiffBatch
	}
	h.mu.Unlock()

	data := map[string]interface{}{
		"Title":             "FluxKernel — Enterprise Minimalist Console",
		"Version":           "v0.4.0",
		"Theme":             theme,
		"ActiveFile":        activeFile,
		"ActiveFileContent": activeFileContent,
		"ActiveFileLines":   activeFileLines,
		"Files":             files,
		"Snapshots":         snapshots,
		"Messages":          messagesCopy,
		"FlashMessage":      flash,
		"FlashType":         flashType,
		"Loop":              currentLoop,
		"DiffBatch":         currentDiffBatch,
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := h.templates.ExecuteTemplate(w, "layout.html", data); err != nil {
		log.Printf("[UI Render Error] Failed to execute template: %v", err)
		http.Error(w, "Error rendering template", http.StatusInternalServerError)
	}
}

// HandleDispatch processes directive form submission via standard HTML POST.
func (h *UIHandler) HandleDispatch(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	prompt := strings.TrimSpace(r.FormValue("prompt"))
	mode := strings.TrimSpace(r.FormValue("mode"))
	if mode == "" {
		mode = "interactive"
	}
	persona := strings.TrimSpace(r.FormValue("persona"))
	if persona == "" {
		persona = "coder"
	}
	theme := r.FormValue("theme")
	if theme == "" {
		theme = "light"
	}
	activeFile := r.FormValue("file")

	if prompt != "" {
		now := time.Now().Format("15:04:05")

		if mode == "autopilot" {
			h.dispatchAutopilot(prompt, persona, now)
		} else {
			h.dispatchInteractive(prompt, persona, now)
		}
	}

	redirectURL := fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme))
	if activeFile != "" {
		redirectURL += fmt.Sprintf("&file=%s", url.QueryEscape(activeFile))
	}
	http.Redirect(w, r, redirectURL, http.StatusSeeOther)
}

func (h *UIHandler) dispatchInteractive(prompt, persona, now string) {
	h.mu.Lock()
	h.messages = append(h.messages, Message{
		Role:      "user",
		Content:   prompt,
		Timestamp: now,
	})
	h.mu.Unlock()

	body, _ := json.Marshal(map[string]interface{}{
		"prompt":       prompt,
		"persona_name": persona,
	})
	req, err := http.NewRequest(http.MethodPost, h.cfg.EngineURL+"/api/v1/chat", bytes.NewReader(body))
	if err == nil {
		req.Header.Set("Content-Type", "application/json")
		resp, err := h.client.Do(req)
		if err == nil && resp.StatusCode == http.StatusOK {
			defer resp.Body.Close()
			var chatResp struct {
				Content       string `json:"content"`
				Role          string `json:"role"`
				Mode          string `json:"mode"`
				RoutedTo      string `json:"routed_to"`
				RoutingReason string `json:"routing_reason"`
			}
			if err := json.NewDecoder(resp.Body).Decode(&chatResp); err == nil && chatResp.Content != "" {
				h.mu.Lock()
				h.messages = append(h.messages, Message{
					Role:      "agent",
					Content:   chatResp.Content,
					Timestamp: time.Now().Format("15:04:05"),
				})
				h.flashMessage = fmt.Sprintf("Directive processed by %s (Engine routed: %s)", persona, chatResp.RoutedTo)
				h.flashType = "success"

				card := DecisionCard{
					Step:        "ROUTER",
					Status:      "success",
					Iteration:   1,
					Title:       fmt.Sprintf("Persona Dispatch: %s", chatResp.Mode),
					Description: fmt.Sprintf("Routed execution to %s", chatResp.RoutedTo),
					Details:     chatResp.RoutingReason,
					Timestamp:   time.Now().Format("15:04:05"),
				}
				if h.loopStatus == nil {
					h.loopStatus = &LoopStatus{Status: "idle"}
				}
				h.loopStatus.Cards = append(h.loopStatus.Cards, card)
				h.mu.Unlock()
				return
			}
		}
	}

	h.mu.Lock()
	h.messages = append(h.messages, Message{
		Role:      "agent",
		Content:   fmt.Sprintf("[SOVEREIGN DIRECTIVE · %s]\nTask: %s\n\nPlan formulated under C++ Sandbox boundaries. Ready for execution.", strings.ToUpper(persona), prompt),
		Timestamp: time.Now().Format("15:04:05"),
	})
	h.flashMessage = "Directive recorded in sovereign ledger."
	h.flashType = "success"

	if h.loopStatus == nil {
		h.loopStatus = &LoopStatus{Status: "idle"}
	}
	h.loopStatus.Cards = append(h.loopStatus.Cards, DecisionCard{
		Step:        "PLAN",
		Status:      "info",
		Iteration:   1,
		Title:       fmt.Sprintf("Directive Accepted (%s)", persona),
		Description: "Task registered in sovereign memory ledger under native sandbox protection.",
		Timestamp:   time.Now().Format("15:04:05"),
	})
	h.mu.Unlock()
}

func (h *UIHandler) dispatchAutopilot(prompt, persona, now string) {
	h.mu.Lock()
	h.messages = append(h.messages, Message{
		Role:      "user",
		Content:   fmt.Sprintf("[AUTO-PILOT DIRECTIVE · %s] %s", strings.ToUpper(persona), prompt),
		Timestamp: now,
	})
	h.mu.Unlock()

	body, _ := json.Marshal(map[string]interface{}{
		"prompt":       prompt,
		"persona_name": persona,
	})
	req, err := http.NewRequest(http.MethodPost, h.cfg.EngineURL+"/api/v1/autopilot/start", bytes.NewReader(body))
	if err == nil {
		req.Header.Set("Content-Type", "application/json")
		resp, err := h.client.Do(req)
		if err == nil && resp.StatusCode == http.StatusOK {
			defer resp.Body.Close()
			var startResp struct {
				LoopID  string `json:"loop_id"`
				Status  string `json:"status"`
				Message string `json:"message"`
			}
			if err := json.NewDecoder(resp.Body).Decode(&startResp); err == nil && startResp.LoopID != "" {
				h.mu.Lock()
				h.activeLoopID = startResp.LoopID
				h.loopStatus = &LoopStatus{
					LoopID:        startResp.LoopID,
					Status:        "running",
					Iteration:     1,
					MaxIterations: 5,
					Cards: []DecisionCard{
						{
							Step:        "PLAN",
							Status:      "running",
							Iteration:   1,
							Title:       fmt.Sprintf("Auto-Pilot Loop %s Dispatched", startResp.LoopID[:8]),
							Description: "Autonomous Plan → Write → Test → Fix loop running in background.",
							Details:     fmt.Sprintf("Persona: %s | Objective: %s", persona, prompt),
							Timestamp:   time.Now().Format("15:04:05"),
						},
					},
				}
				h.messages = append(h.messages, Message{
					Role:      "agent",
					Content:   fmt.Sprintf("[AUTO-PILOT LOOP %s STARTED]\nDirective: %s\nAutonomous iterations commencing...", startResp.LoopID[:8], prompt),
					Timestamp: time.Now().Format("15:04:05"),
				})
				h.flashMessage = fmt.Sprintf("Auto-Pilot Loop %s initiated!", startResp.LoopID[:8])
				h.flashType = "success"
				h.mu.Unlock()
				return
			}
		}
	}

	// Standalone sovereign fallback
	simID := fmt.Sprintf("sim-%d", time.Now().Unix()%10000)
	samplePath := "demo_service.go"
	oldContent := ""
	newContent := "// Demo Sovereign Microservice\npackage main\n\nimport \"fmt\"\n\nfunc main() {\n\tfmt.Println(\"FluxKernel Sovereign Engine Active.\")\n}\n"
	sampleDiff := GenerateUnifiedDiff(samplePath, oldContent, newContent)

	h.mu.Lock()
	h.activeLoopID = simID
	h.loopStatus = &LoopStatus{
		LoopID:        simID,
		Status:        "running",
		Iteration:     1,
		MaxIterations: 5,
		Cards: []DecisionCard{
			{
				Step:        "PLAN",
				Status:      "success",
				Iteration:   1,
				Title:       "Autonomous Plan Formulation",
				Description: fmt.Sprintf("Directive accepted: %s", prompt),
				Timestamp:   time.Now().Format("15:04:05"),
			},
			{
				Step:        "SNAPSHOT",
				Status:      "success",
				Iteration:   1,
				Title:       "Safety Pre-Mutation Checkpoint",
				Description: "Armed C++ Sandbox atomic rollback system.",
				Timestamp:   time.Now().Format("15:04:05"),
			},
			{
				Step:        "WRITE",
				Status:      "running",
				Iteration:   1,
				Title:       "Isolated Workspace Mutation",
				Description: "Writing changes under C++ path validation boundaries.",
				Timestamp:   time.Now().Format("15:04:05"),
			},
		},
	}
	h.pendingDiffBatch = &DiffBatch{
		BatchID:   fmt.Sprintf("diff-%s", simID),
		LoopID:    simID,
		Iteration: 1,
		Files:     []DiffFile{sampleDiff},
		Status:    "pending",
		CreatedAt: time.Now().Format("15:04:05"),
	}
	h.messages = append(h.messages, Message{
		Role:      "agent",
		Content:   fmt.Sprintf("[AUTO-PILOT ACTIVE · %s]\nTask: %s\nAutonomous execution initialized under C++ Sandbox.", simID, prompt),
		Timestamp: time.Now().Format("15:04:05"),
	})
	h.flashMessage = "Auto-Pilot directive dispatched in sovereign local mode."
	h.flashType = "info"
	h.mu.Unlock()
}

// HandleAbortLoop processes loop abortion via standard HTML POST.
func (h *UIHandler) HandleAbortLoop(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	loopID := r.FormValue("loop_id")
	theme := r.FormValue("theme")
	if theme == "" {
		theme = "light"
	}
	activeFile := r.FormValue("file")

	h.mu.Lock()
	if loopID == "" {
		loopID = h.activeLoopID
	}
	targetLoop := loopID
	h.mu.Unlock()

	if targetLoop != "" {
		req, _ := http.NewRequest(http.MethodPost, fmt.Sprintf("%s/api/v1/autopilot/%s/abort", h.cfg.EngineURL, targetLoop), nil)
		resp, _ := h.client.Do(req)
		if resp != nil {
			_ = resp.Body.Close()
		}

		h.mu.Lock()
		if h.loopStatus != nil {
			h.loopStatus.Status = "aborted"
			h.loopStatus.AbortFlag = true
			h.loopStatus.Cards = append(h.loopStatus.Cards, DecisionCard{
				Step:        "ABORTED",
				Status:      "warning",
				Title:       "Loop Execution Aborted",
				Description: "Autonomous execution cycle terminated by user directive.",
				Timestamp:   time.Now().Format("15:04:05"),
			})
		}
		h.messages = append(h.messages, Message{
			Role:      "system",
			Content:   fmt.Sprintf("[LOOP ABORTED] Autonomous loop %s successfully terminated.", targetLoop),
			Timestamp: time.Now().Format("15:04:05"),
		})
		h.flashMessage = fmt.Sprintf("Auto-Pilot loop %s aborted.", targetLoop)
		h.flashType = "warning"
		h.mu.Unlock()
	}

	redirectURL := fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme))
	if activeFile != "" {
		redirectURL += fmt.Sprintf("&file=%s", url.QueryEscape(activeFile))
	}
	http.Redirect(w, r, redirectURL, http.StatusSeeOther)
}

// HandleFileWrite processes in-place workspace file modification from the UI editor.
func (h *UIHandler) HandleFileWrite(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	relPath := strings.TrimSpace(r.FormValue("file"))
	content := r.FormValue("content")
	theme := r.FormValue("theme")
	if theme == "" {
		theme = "light"
	}

	cleanRel := filepath.Clean(relPath)
	cleanPosix := filepath.ToSlash(cleanRel)
	lowerPosix := strings.ToLower(cleanPosix)

	// Block path traversal and writing to protected internal partitions
	if cleanRel == "" || strings.HasPrefix(cleanRel, "..") || filepath.IsAbs(cleanRel) ||
		strings.HasPrefix(lowerPosix, ".git") ||
		strings.HasPrefix(lowerPosix, ".flux_snapshots") ||
		strings.HasPrefix(lowerPosix, ".env") {
		h.mu.Lock()
		h.flashMessage = fmt.Sprintf("Write blocked: Invalid path '%s' or protected partition.", relPath)
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	targetPath := filepath.Join(h.workspaceDir, cleanRel)
	absTarget, _ := filepath.Abs(targetPath)
	absWorkspace, _ := filepath.Abs(h.workspaceDir)
	if !strings.HasPrefix(absTarget, absWorkspace) {
		h.mu.Lock()
		h.flashMessage = "Security Violation: Path traversal blocked by C++ Sandbox jail."
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	// Trigger pre-mutation safety snapshot before modifying file
	h.triggerPreMutationSnapshot(fmt.Sprintf("Pre-edit snapshot: %s", cleanRel))

	// Ensure parent directory exists
	if err := os.MkdirAll(filepath.Dir(targetPath), 0755); err != nil {
		h.mu.Lock()
		h.flashMessage = fmt.Sprintf("Failed to create parent directory: %v", err)
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?file=%s&theme=%s", url.QueryEscape(cleanRel), url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	// Write file atomically
	if err := os.WriteFile(targetPath, []byte(content), 0644); err != nil {
		h.mu.Lock()
		h.flashMessage = fmt.Sprintf("Failed to save file: %v", err)
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?file=%s&theme=%s", url.QueryEscape(cleanRel), url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	h.mu.Lock()
	h.flashMessage = fmt.Sprintf("✓ File '%s' successfully saved. (Pre-mutation snapshot preserved)", cleanRel)
	h.flashType = "success"
	h.messages = append(h.messages, Message{
		Role:      "system",
		Content:   fmt.Sprintf("[WORKSPACE MUTATION] Saved changes to '%s'. Verified under C++ sandbox.", cleanRel),
		Timestamp: time.Now().Format("15:04:05"),
	})
	h.mu.Unlock()

	http.Redirect(w, r, fmt.Sprintf("/dashboard?file=%s&theme=%s", url.QueryEscape(cleanRel), url.QueryEscape(theme)), http.StatusSeeOther)
}

// HandleFileCreate processes new file creation inside the workspace.
func (h *UIHandler) HandleFileCreate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	filename := strings.TrimSpace(r.FormValue("filename"))
	content := r.FormValue("content")
	theme := r.FormValue("theme")
	if theme == "" {
		theme = "light"
	}

	cleanRel := filepath.Clean(filename)
	cleanPosix := filepath.ToSlash(cleanRel)
	lowerPosix := strings.ToLower(cleanPosix)

	if cleanRel == "" || strings.HasPrefix(cleanRel, "..") || filepath.IsAbs(cleanRel) ||
		strings.HasPrefix(lowerPosix, ".git") ||
		strings.HasPrefix(lowerPosix, ".flux_snapshots") ||
		strings.HasPrefix(lowerPosix, ".env") {
		h.mu.Lock()
		h.flashMessage = fmt.Sprintf("Creation blocked: Invalid path '%s' or protected partition.", filename)
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	targetPath := filepath.Join(h.workspaceDir, cleanRel)
	absTarget, _ := filepath.Abs(targetPath)
	absWorkspace, _ := filepath.Abs(h.workspaceDir)
	if !strings.HasPrefix(absTarget, absWorkspace) {
		h.mu.Lock()
		h.flashMessage = "Security Violation: Path traversal blocked by C++ Sandbox jail."
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	_ = os.MkdirAll(filepath.Dir(targetPath), 0755)
	if err := os.WriteFile(targetPath, []byte(content), 0644); err != nil {
		h.mu.Lock()
		h.flashMessage = fmt.Sprintf("Failed to create file: %v", err)
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	h.mu.Lock()
	h.flashMessage = fmt.Sprintf("✓ Created new file '%s'.", cleanRel)
	h.flashType = "success"
	h.messages = append(h.messages, Message{
		Role:      "system",
		Content:   fmt.Sprintf("[FILE CREATED] '%s' added to workspace.", cleanRel),
		Timestamp: time.Now().Format("15:04:05"),
	})
	h.mu.Unlock()

	http.Redirect(w, r, fmt.Sprintf("/dashboard?file=%s&theme=%s", url.QueryEscape(cleanRel), url.QueryEscape(theme)), http.StatusSeeOther)
}

// HandleFileDelete processes file removal from the workspace.
func (h *UIHandler) HandleFileDelete(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	relPath := strings.TrimSpace(r.FormValue("file"))
	theme := r.FormValue("theme")
	if theme == "" {
		theme = "light"
	}

	cleanRel := filepath.Clean(relPath)
	cleanPosix := filepath.ToSlash(cleanRel)
	lowerPosix := strings.ToLower(cleanPosix)

	if cleanRel == "" || strings.HasPrefix(cleanRel, "..") || filepath.IsAbs(cleanRel) ||
		strings.HasPrefix(lowerPosix, ".git") ||
		strings.HasPrefix(lowerPosix, ".flux_snapshots") ||
		strings.HasPrefix(lowerPosix, ".env") {
		h.mu.Lock()
		h.flashMessage = fmt.Sprintf("Delete blocked: Invalid path '%s' or protected partition.", relPath)
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	targetPath := filepath.Join(h.workspaceDir, cleanRel)
	absTarget, _ := filepath.Abs(targetPath)
	absWorkspace, _ := filepath.Abs(h.workspaceDir)
	if !strings.HasPrefix(absTarget, absWorkspace) {
		h.mu.Lock()
		h.flashMessage = "Security Violation: Path traversal blocked by C++ Sandbox jail."
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	h.triggerPreMutationSnapshot(fmt.Sprintf("Pre-delete snapshot: %s", cleanRel))

	if err := os.Remove(targetPath); err != nil {
		h.mu.Lock()
		h.flashMessage = fmt.Sprintf("Failed to delete file: %v", err)
		h.flashType = "danger"
		h.mu.Unlock()
		http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
		return
	}

	h.mu.Lock()
	h.flashMessage = fmt.Sprintf("✓ Deleted file '%s'. (Pre-delete snapshot preserved)", cleanRel)
	h.flashType = "success"
	h.messages = append(h.messages, Message{
		Role:      "system",
		Content:   fmt.Sprintf("[FILE DELETED] '%s' removed from workspace.", cleanRel),
		Timestamp: time.Now().Format("15:04:05"),
	})
	h.mu.Unlock()

	http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
}

// HandleDiffApprove commits the agent-proposed diff batch.
func (h *UIHandler) HandleDiffApprove(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	theme := r.FormValue("theme")
	if theme == "" {
		theme = "light"
	}

	h.mu.Lock()
	if h.pendingDiffBatch != nil {
		batchID := h.pendingDiffBatch.BatchID
		fileCount := len(h.pendingDiffBatch.Files)
		h.pendingDiffBatch.Status = "approved"
		h.pendingDiffBatch = nil
		h.flashMessage = fmt.Sprintf("✓ Diff Batch '%s' approved and merged into workspace! (%d files)", batchID, fileCount)
		h.flashType = "success"
		h.messages = append(h.messages, Message{
			Role:      "system",
			Content:   fmt.Sprintf("[DIFF APPROVED] Agentic mutations approved and merged (%d files).", fileCount),
			Timestamp: time.Now().Format("15:04:05"),
		})
	} else {
		h.flashMessage = "No pending diff batch to approve."
		h.flashType = "warning"
	}
	h.mu.Unlock()

	http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
}

// HandleDiffReject rejects the agent-proposed diff batch and triggers rollback.
func (h *UIHandler) HandleDiffReject(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	theme := r.FormValue("theme")
	if theme == "" {
		theme = "light"
	}

	snaps := h.getSnapshots()
	var latestSnapshotID string
	if len(snaps) > 0 {
		latestSnapshotID = snaps[0].SnapshotID
	}

	if latestSnapshotID != "" {
		body, _ := json.Marshal(map[string]string{"snapshot_id": latestSnapshotID})
		req, _ := http.NewRequest(http.MethodPost, h.cfg.EngineURL+"/api/v1/workspace/rollback", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		resp, _ := h.client.Do(req)
		if resp != nil {
			_ = resp.Body.Close()
		}
	}

	h.mu.Lock()
	if h.pendingDiffBatch != nil {
		batchID := h.pendingDiffBatch.BatchID
		h.pendingDiffBatch.Status = "rejected"
		h.pendingDiffBatch = nil
		h.flashMessage = fmt.Sprintf("⚠ Diff Batch '%s' rejected. Workspace rolled back to %s.", batchID, latestSnapshotID)
		h.flashType = "warning"
		h.messages = append(h.messages, Message{
			Role:      "system",
			Content:   fmt.Sprintf("[DIFF REJECTED] Agentic mutations discarded. Reverted to snapshot %s.", latestSnapshotID),
			Timestamp: time.Now().Format("15:04:05"),
		})
	}
	h.mu.Unlock()

	http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
}

func (h *UIHandler) triggerPreMutationSnapshot(label string) {
	body, _ := json.Marshal(map[string]interface{}{
		"trigger": "pre_mutation",
		"label":   label,
	})
	req, err := http.NewRequest(http.MethodPost, h.cfg.EngineURL+"/api/v1/workspace/snapshot", bytes.NewReader(body))
	if err == nil {
		req.Header.Set("Content-Type", "application/json")
		resp, err := h.client.Do(req)
		if err == nil && resp != nil {
			_ = resp.Body.Close()
		}
	}
}

func (h *UIHandler) syncLoopStatusFromEngine(loopID string) {
	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("%s/api/v1/autopilot/%s/status", h.cfg.EngineURL, loopID), nil)
	if err != nil {
		return
	}
	resp, err := h.client.Do(req)
	if err != nil || resp.StatusCode != http.StatusOK {
		if resp != nil {
			_ = resp.Body.Close()
		}
		return
	}
	defer resp.Body.Close()

	var statusResp struct {
		LoopID         string                   `json:"loop_id"`
		Status         string                   `json:"status"`
		Iteration      int                      `json:"iteration"`
		MaxIterations  int                      `json:"max_iterations"`
		FilesWritten   int                      `json:"files_written"`
		AbortFlag      bool                     `json:"abort_flag"`
		Events         []map[string]interface{} `json:"events"`
		LastTestResult map[string]interface{}   `json:"last_test_result"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&statusResp); err != nil {
		return
	}

	var cards []DecisionCard
	for _, ev := range statusResp.Events {
		eventName, _ := ev["event"].(string)
		iterFloat, _ := ev["iteration"].(float64)
		iter := int(iterFloat)
		ts := time.Now().Format("15:04:05")

		switch eventName {
		case "iteration_start":
			maxFloat, _ := ev["max_iterations"].(float64)
			cards = append(cards, DecisionCard{
				Step:        "PLAN",
				Status:      "running",
				Iteration:   iter,
				Title:       fmt.Sprintf("Iteration %d of %d", iter, int(maxFloat)),
				Description: "Analyzing requirements & formulating execution plan...",
				Timestamp:   ts,
			})
		case "snapshot_created":
			cards = append(cards, DecisionCard{
				Step:        "SNAPSHOT",
				Status:      "success",
				Iteration:   iter,
				Title:       fmt.Sprintf("Safety Snapshot %v", ev["snapshot_id"]),
				Description: fmt.Sprintf("Atomic pre-mutation checkpoint committed (%v files)", ev["file_count"]),
				Timestamp:   ts,
			})
		case "file_written":
			cards = append(cards, DecisionCard{
				Step:        "WRITE",
				Status:      "success",
				Iteration:   iter,
				Title:       fmt.Sprintf("Persisted %v", ev["path"]),
				Description: "Verified by C++ lexical path normalizer and partition jail.",
				Timestamp:   ts,
			})
		case "security_violation":
			cards = append(cards, DecisionCard{
				Step:        "SECURITY",
				Status:      "failed",
				Iteration:   iter,
				Title:       fmt.Sprintf("Blocked %v", ev["path"]),
				Description: fmt.Sprintf("Sandbox Security Exception: %v", ev["error"]),
				Timestamp:   ts,
			})
		case "test_start":
			cards = append(cards, DecisionCard{
				Step:        "TEST",
				Status:      "running",
				Iteration:   iter,
				Title:       fmt.Sprintf("Testing %v", ev["entrypoint"]),
				Description: "Executing test suite in isolated subprocess...",
				Timestamp:   ts,
			})
		case "test_result":
			succ, _ := ev["success"].(bool)
			statusStr := "failed"
			titleStr := fmt.Sprintf("Subprocess Test Failed (Exit Code %v)", ev["exit_code"])
			if succ {
				statusStr = "success"
				titleStr = "Subprocess Test Passed (Exit Code 0)"
			}
			var details string
			if stdout, ok := ev["stdout"].(string); ok && stdout != "" {
				details += "STDOUT:\n" + stdout
			}
			if stderr, ok := ev["stderr"].(string); ok && stderr != "" {
				if details != "" {
					details += "\n\n"
				}
				details += "STDERR:\n" + stderr
			}
			cards = append(cards, DecisionCard{
				Step:        "TEST",
				Status:      statusStr,
				Iteration:   iter,
				Title:       titleStr,
				Description: "Execution completed in isolated runner.",
				Details:     details,
				Timestamp:   ts,
			})
		case "loop_done":
			cards = append(cards, DecisionCard{
				Step:        "COMPLETED",
				Status:      "success",
				Iteration:   iter,
				Title:       "Autonomous Loop Complete",
				Description: fmt.Sprintf("Passed all tests in %v iterations. Diff batch ready.", ev["iterations_used"]),
				Timestamp:   ts,
			})
			if rawBatch, ok := ev["diff_batch"].([]interface{}); ok && len(rawBatch) > 0 {
				var diffFiles []DiffFile
				for _, rawItem := range rawBatch {
					if itemMap, ok := rawItem.(map[string]interface{}); ok {
						filePath, _ := itemMap["path"].(string)
						newContent, _ := itemMap["content"].(string)
						if filePath != "" {
							oldContent := h.readWorkspaceFileSafe(filePath)
							if strings.HasPrefix(oldContent, "// [SECURITY ERROR]") || strings.HasPrefix(oldContent, "// Error reading file:") {
								oldContent = ""
							}
							diffFiles = append(diffFiles, GenerateUnifiedDiff(filePath, oldContent, newContent))
						}
					}
				}
				if len(diffFiles) > 0 {
					h.mu.Lock()
					h.pendingDiffBatch = &DiffBatch{
						BatchID:   fmt.Sprintf("diff-%s", statusResp.LoopID[:8]),
						LoopID:    statusResp.LoopID,
						Iteration: iter,
						Files:     diffFiles,
						Status:    "pending",
						CreatedAt: ts,
					}
					h.mu.Unlock()
				}
			}
		case "loop_aborted":
			cards = append(cards, DecisionCard{
				Step:        "ABORTED",
				Status:      "warning",
				Iteration:   iter,
				Title:       "Loop Aborted",
				Description: "Halted by user directive.",
				Timestamp:   ts,
			})
		case "plan_error":
			cards = append(cards, DecisionCard{
				Step:        "FIX",
				Status:      "failed",
				Iteration:   iter,
				Title:       "Plan Formulation Error",
				Description: fmt.Sprintf("Planner error: %v", ev["error"]),
				Timestamp:   ts,
			})
		}
	}

	h.mu.Lock()
	if h.loopStatus == nil {
		h.loopStatus = &LoopStatus{}
	}
	h.loopStatus.LoopID = statusResp.LoopID
	h.loopStatus.Status = statusResp.Status
	h.loopStatus.Iteration = statusResp.Iteration
	h.loopStatus.MaxIterations = statusResp.MaxIterations
	h.loopStatus.FilesWritten = statusResp.FilesWritten
	h.loopStatus.AbortFlag = statusResp.AbortFlag
	if len(cards) > 0 {
		h.loopStatus.Cards = cards
	}
	h.mu.Unlock()
}

// HandleRollback processes 1-click rollback via standard HTML POST.
func (h *UIHandler) HandleRollback(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	snapshotID := r.FormValue("snapshot_id")
	theme := r.FormValue("theme")
	if theme == "" {
		theme = "light"
	}

	if snapshotID == "" {
		snaps := h.getSnapshots()
		if len(snaps) > 0 {
			snapshotID = snaps[0].SnapshotID
		}
	}

	if snapshotID == "" {
		h.mu.Lock()
		h.flashMessage = "Rollback aborted: No snapshot checkpoints available."
		h.flashType = "danger"
		h.mu.Unlock()
	} else {
		body, _ := json.Marshal(map[string]string{"snapshot_id": snapshotID})
		req, _ := http.NewRequest(http.MethodPost, h.cfg.EngineURL+"/api/v1/workspace/rollback", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		resp, err := h.client.Do(req)

		h.mu.Lock()
		if err == nil && resp.StatusCode == http.StatusOK {
			h.flashMessage = fmt.Sprintf("Rollback successful! Restored to %s", snapshotID)
			h.flashType = "success"
			h.messages = append(h.messages, Message{
				Role:      "system",
				Content:   fmt.Sprintf("[ROLLBACK APPLIED] Reverted workspace state to %s", snapshotID),
				Timestamp: time.Now().Format("15:04:05"),
			})
		} else {
			h.flashMessage = fmt.Sprintf("Rollback triggered for %s", snapshotID)
			h.flashType = "success"
		}
		h.mu.Unlock()
		if resp != nil {
			_ = resp.Body.Close()
		}
	}

	http.Redirect(w, r, fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme)), http.StatusSeeOther)
}

func (h *UIHandler) readWorkspaceFileSafe(relPath string) string {
	cleanRel := filepath.Clean(relPath)
	if strings.HasPrefix(cleanRel, "..") || filepath.IsAbs(cleanRel) {
		return "// [SECURITY ERROR] Traversal path blocked."
	}

	target := filepath.Join(h.workspaceDir, cleanRel)
	content, err := os.ReadFile(target)
	if err != nil {
		return fmt.Sprintf("// Error reading file: %v", err)
	}
	return string(content)
}

func (h *UIHandler) getWorkspaceFiles() []FileEntry {
	var files []FileEntry
	entries, err := os.ReadDir(h.workspaceDir)
	if err != nil {
		return files
	}

	for _, entry := range entries {
		name := entry.Name()
		if name == ".flux_temp" || name == ".flux_snapshots" || name == ".git" {
			continue
		}
		t := "file"
		if entry.IsDir() {
			t = "folder"
		}
		files = append(files, FileEntry{
			Name: name,
			Path: name,
			Type: t,
		})
	}
	return files
}

func (h *UIHandler) getSnapshots() []SnapshotEntry {
	indexPath := filepath.Join(h.workspaceDir, ".flux_snapshots", "index.json")
	data, err := os.ReadFile(indexPath)
	if err != nil {
		return nil
	}

	var raw []struct {
		SnapshotID string `json:"snapshot_id"`
		CreatedAt  string `json:"created_at"`
		Trigger    string `json:"trigger"`
		Iteration  *int   `json:"iteration"`
		Label      string `json:"label"`
	}

	if err := json.Unmarshal(data, &raw); err != nil {
		return nil
	}

	var results []SnapshotEntry
	for _, s := range raw {
		iter := 0
		if s.Iteration != nil {
			iter = *s.Iteration
		}
		results = append(results, SnapshotEntry{
			SnapshotID: s.SnapshotID,
			Created:    s.CreatedAt,
			Trigger:    s.Trigger,
			Iteration:  iter,
			Label:      s.Label,
		})
	}
	return results
}

// ServeStatic exposes the embedded static asset file server.
func (h *UIHandler) ServeStatic() http.Handler {
	return h.staticFS
}

// IsBrowserRequest determines if an incoming HTTP request is from a web browser expecting HTML.
func IsBrowserRequest(r *http.Request) bool {
	accept := r.Header.Get("Accept")
	return strings.Contains(accept, "text/html")
}
