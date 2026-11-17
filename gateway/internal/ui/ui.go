package ui

import (
	"embed"
	"fmt"
	"html/template"
	"io/fs"
	"log"
	"net/http"
	"strings"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

//go:embed static templates
var embeddedFS embed.FS

// UIHandler manages rendering of embedded HTML templates and static assets.
type UIHandler struct {
	cfg       *config.Config
	templates *template.Template
	staticFS  http.Handler
}

// NewUIHandler initializes the template engine and static asset server.
func NewUIHandler(cfg *config.Config) (*UIHandler, error) {
	tmpl, err := template.ParseFS(embeddedFS, "templates/*.html")
	if err != nil {
		return nil, fmt.Errorf("failed to parse embedded templates: %w", err)
	}

	subStatic, err := fs.Sub(embeddedFS, "static")
	if err != nil {
		return nil, fmt.Errorf("failed to create static sub-filesystem: %w", err)
	}

	return &UIHandler{
		cfg:       cfg,
		templates: tmpl,
		staticFS:  http.StripPrefix("/static/", http.FileServer(http.FS(subStatic))),
	}, nil
}

// ServeHTTP renders the main sovereign dashboard.
func (h *UIHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	data := map[string]interface{}{
		"Title":       "FluxKernel — Voxion Labs Autonomous Engine",
		"Version":     "v0.4.0-phase2",
		"Environment": h.cfg.Environment,
		"EngineURL":   h.cfg.EngineURL,
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := h.templates.ExecuteTemplate(w, "layout.html", data); err != nil {
		log.Printf("[UI Template Error] Failed to render dashboard: %v", err)
		http.Error(w, "Internal Server Error rendering UI", http.StatusInternalServerError)
	}
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
