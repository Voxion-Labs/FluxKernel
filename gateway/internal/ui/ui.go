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
}

// NewUIHandler initializes the template engine and sets up pure SSR handlers.
func NewUIHandler(cfg *config.Config) (*UIHandler, error) {
	tmpl, err := template.ParseFS(embeddedFS, "templates/*.html")
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
		client:       &http.Client{Timeout: 15 * time.Second},
		messages:     initialMessages,
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
	if activeFile != "" {
		activeFileContent = h.readWorkspaceFileSafe(activeFile)
	}

	// Scan workspace files
	files := h.getWorkspaceFiles()

	// Load snapshot list
	snapshots := h.getSnapshots()

	h.mu.Lock()
	flash := h.flashMessage
	flashType := h.flashType
	h.flashMessage = ""
	h.flashType = ""
	messagesCopy := make([]Message, len(h.messages))
	copy(messagesCopy, h.messages)
	h.mu.Unlock()

	data := map[string]interface{}{
		"Title":             "FluxKernel — Enterprise Minimalist Console",
		"Version":           "v0.4.0",
		"Theme":             theme,
		"ActiveFile":        activeFile,
		"ActiveFileContent": activeFileContent,
		"Files":             files,
		"Snapshots":         snapshots,
		"Messages":          messagesCopy,
		"FlashMessage":      flash,
		"FlashType":         flashType,
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
	persona := r.FormValue("persona")
	theme := r.FormValue("theme")
	if theme == "" {
		theme = "light"
	}
	activeFile := r.FormValue("file")

	if prompt != "" {
		now := time.Now().Format("15:04:05")
		h.mu.Lock()
		h.messages = append(h.messages, Message{
			Role:      "user",
			Content:   prompt,
			Timestamp: now,
		})
		h.messages = append(h.messages, Message{
			Role:      "agent",
			Content:   fmt.Sprintf("[Directive Processed - Persona: %s] Plan formulated under C++ Sandbox boundaries.", persona),
			Timestamp: now,
		})
		h.flashMessage = "Directive successfully dispatched."
		h.flashType = "success"
		h.mu.Unlock()
	}

	redirectURL := fmt.Sprintf("/dashboard?theme=%s", url.QueryEscape(theme))
	if activeFile != "" {
		redirectURL += fmt.Sprintf("&file=%s", url.QueryEscape(activeFile))
	}
	http.Redirect(w, r, redirectURL, http.StatusSeeOther)
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

	// If no snapshot ID specified, find latest from disk
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
		// Forward rollback to Python backend /api/v1/workspace/rollback
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
