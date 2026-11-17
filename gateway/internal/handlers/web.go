package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

// WebHandler routes web actions (fetch, download, api) to the Python engine.
type WebHandler struct {
	cfg        *config.Config
	httpClient *http.Client
}

// NewWebHandler creates a new WebHandler.
func NewWebHandler(cfg *config.Config, client *http.Client) *WebHandler {
	if client == nil {
		client = &http.Client{}
	}
	return &WebHandler{
		cfg:        cfg,
		httpClient: client,
	}
}

func (h *WebHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	parts := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
	action := parts[len(parts)-1]

	allowedActions := map[string]bool{
		"fetch":    true,
		"download": true,
		"api":      true,
	}

	if !allowedActions[action] {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": fmt.Sprintf("Unknown web action: %s", action),
		})
		return
	}

	targetURL := fmt.Sprintf("%s/api/v1/web/%s",
		strings.TrimRight(h.cfg.EngineURL, "/"), action)

	proxyReq, err := http.NewRequestWithContext(r.Context(), http.MethodPost, targetURL, r.Body)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to construct request: %v", err), http.StatusInternalServerError)
		return
	}

	if ct := r.Header.Get("Content-Type"); ct != "" {
		proxyReq.Header.Set("Content-Type", ct)
	} else {
		proxyReq.Header.Set("Content-Type", "application/json")
	}

	resp, err := h.httpClient.Do(proxyReq)
	if err != nil {
		http.Error(w, fmt.Sprintf("Engine unreachable: %v", err), http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	for k, vv := range resp.Header {
		for _, v := range vv {
			w.Header().Add(k, v)
		}
	}
	w.WriteHeader(resp.StatusCode)
	_, _ = io.Copy(w, resp.Body)
}
