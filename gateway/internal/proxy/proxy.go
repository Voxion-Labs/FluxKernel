package proxy

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
	"time"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
	"github.com/Voxion-Labs/FluxKernel/gateway/internal/handlers"
	"github.com/Voxion-Labs/FluxKernel/gateway/internal/ui"
)

// GatewayVersion is the current build version of the Go Gateway.
const GatewayVersion = "0.4.0-phase2"

// Handler orchestrates routing, UI serving, and reverse proxying to the Python core engine.
type Handler struct {
	cfg          *config.Config
	reverseProxy *httputil.ReverseProxy
	engineTarget *url.URL

	// Sovereign Embedded Web UI
	uiHandler *ui.UIHandler

	// Specialized Handlers replacing TS routes
	chatHandler      *handlers.ChatHandler
	autopilotHandler *handlers.AutopilotHandler
	tasksHandler     *handlers.TasksHandler
	webHandler       *handlers.WebHandler
	webhookHandler   *handlers.WebhookHandler
	workspaceHandler *handlers.WorkspaceHandler
}

// NewHandler initializes a new Gateway Handler with specialized route handlers and embedded UI.
func NewHandler(cfg *config.Config) (*Handler, error) {
	target, err := url.Parse(cfg.EngineURL)
	if err != nil {
		return nil, fmt.Errorf("invalid upstream engine URL '%s': %w", cfg.EngineURL, err)
	}

	rp := httputil.NewSingleHostReverseProxy(target)

	originalDirector := rp.Director
	rp.Director = func(req *http.Request) {
		originalDirector(req)
		req.Header.Set("X-Forwarded-Host", req.Host)
		req.Header.Set("X-Gateway-Origin", "fluxkernel-go-gateway")
	}

	rp.ModifyResponse = func(resp *http.Response) error {
		if strings.Contains(resp.Header.Get("Content-Type"), "text/event-stream") {
			resp.Header.Set("X-Accel-Buffering", "no")
			resp.Header.Set("Cache-Control", "no-cache, no-transform")
		}
		return nil
	}

	rp.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		log.Printf("[Gateway Proxy Error] %s %s -> %v", r.Method, r.URL.Path, err)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadGateway)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":   "Upstream Python engine unreachable",
			"message": err.Error(),
			"gateway": "fluxkernel-go-gateway",
		})
	}

	client := &http.Client{}

	uiH, err := ui.NewUIHandler(cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize embedded UI handler: %w", err)
	}

	return &Handler{
		cfg:              cfg,
		reverseProxy:     rp,
		engineTarget:     target,
		uiHandler:        uiH,
		chatHandler:      handlers.NewChatHandler(cfg, client),
		autopilotHandler: handlers.NewAutopilotHandler(cfg, client),
		tasksHandler:     handlers.NewTasksHandler(cfg, client),
		webHandler:       handlers.NewWebHandler(cfg, client),
		webhookHandler:   handlers.NewWebhookHandler(cfg),
		workspaceHandler: handlers.NewWorkspaceHandler(cfg),
	}, nil
}

// RegisterRoutes registers gateway endpoints, native services, UI dashboard, and upstream proxy handlers.
func (h *Handler) RegisterRoutes(mux *http.ServeMux) {
	// Telemetry & Health probes
	mux.HandleFunc("/healthz", h.handleHealthz)
	mux.HandleFunc("/readyz", h.handleReadyz)
	mux.HandleFunc("/version", h.handleVersion)

	// Sovereign Embedded Web UI & Pure SSR Actions (Zero JS)
	mux.Handle("/dashboard", h.uiHandler)
	mux.HandleFunc("/dashboard/dispatch", h.uiHandler.HandleDispatch)
	mux.HandleFunc("/dashboard/rollback", h.uiHandler.HandleRollback)
	mux.HandleFunc("/dashboard/loop/abort", h.uiHandler.HandleAbortLoop)
	mux.HandleFunc("/dashboard/file/write", h.uiHandler.HandleFileWrite)
	mux.HandleFunc("/dashboard/file/create", h.uiHandler.HandleFileCreate)
	mux.HandleFunc("/dashboard/file/delete", h.uiHandler.HandleFileDelete)
	mux.HandleFunc("/dashboard/diff/approve", h.uiHandler.HandleDiffApprove)
	mux.HandleFunc("/dashboard/diff/reject", h.uiHandler.HandleDiffReject)
	mux.HandleFunc("/dashboard/rag/index", h.uiHandler.HandleRAGIndex)
	mux.HandleFunc("/dashboard/rag/search", h.uiHandler.HandleRAGSearch)
	mux.HandleFunc("/dashboard/web/search", h.uiHandler.HandleWebSearch)
	mux.HandleFunc("/dashboard/learning/ingest", h.uiHandler.HandleAILearningIngest)
	mux.HandleFunc("/dashboard/learning/clear", h.uiHandler.HandleAILearningClear)
	mux.HandleFunc("/dashboard/rules/add", h.uiHandler.HandleRuleAdd)
	mux.HandleFunc("/dashboard/rules/delete", h.uiHandler.HandleRuleDelete)
	mux.HandleFunc("/dashboard/vault/checkpoint", h.uiHandler.HandleVaultCheckpoint)
	mux.HandleFunc("/dashboard/vault/vacuum", h.uiHandler.HandleVaultVacuum)
	mux.HandleFunc("/dashboard/swarm/deliberate", h.uiHandler.HandleSwarmDeliberate)
	mux.Handle("/static/", h.uiHandler.ServeStatic())

	// High-Performance Services (replacing TypeScript Next.js API routes)
	mux.Handle("/api/chat", h.chatHandler)
	mux.Handle("/api/chat/", h.chatHandler)

	mux.Handle("/api/autopilot", h.autopilotHandler)
	mux.Handle("/api/autopilot/", h.autopilotHandler)

	mux.Handle("/api/tasks", h.tasksHandler)
	mux.Handle("/api/tasks/", h.tasksHandler)

	mux.Handle("/api/web", h.webHandler)
	mux.Handle("/api/web/", h.webHandler)

	mux.Handle("/api/webhooks", h.webhookHandler)
	mux.Handle("/api/webhooks/", h.webhookHandler)

	mux.Handle("/api/workspace", h.workspaceHandler)
	mux.Handle("/api/workspace/", h.workspaceHandler)

	// General Upstream Proxy Fallback (e.g. /api/v1/...)
	mux.HandleFunc("/api/", h.handleUpstreamProxy)
	mux.HandleFunc("/", h.handleRoot)
}

func (h *Handler) handleHealthz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"component": "gateway",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	})
}

func (h *Handler) handleReadyz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"ready":           true,
		"upstream_engine": h.engineTarget.String(),
	})
}

func (h *Handler) handleVersion(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"name":        "fluxkernel-go-gateway",
		"version":     GatewayVersion,
		"environment": h.cfg.Environment,
	})
}

func (h *Handler) handleRoot(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		h.reverseProxy.ServeHTTP(w, r)
		return
	}

	// If browser request expecting HTML, render the sovereign dashboard
	if ui.IsBrowserRequest(r) {
		h.uiHandler.ServeHTTP(w, r)
		return
	}

	// Otherwise return JSON API discovery telemetry
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"status":      "online",
		"service":     "FluxKernel High-Performance Gateway (Go)",
		"version":     GatewayVersion,
		"dashboard":   "/dashboard",
		"upstream":    h.engineTarget.String(),
		"environment": h.cfg.Environment,
	})
}

func (h *Handler) handleUpstreamProxy(w http.ResponseWriter, r *http.Request) {
	h.reverseProxy.ServeHTTP(w, r)
}

// WithCORS wraps an http.Handler with standard CORS headers.
func WithCORS(next http.Handler, allowedOrigins string) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", allowedOrigins)
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, Accept")
		w.Header().Set("Access-Control-Allow-Credentials", "true")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		next.ServeHTTP(w, r)
	})
}
