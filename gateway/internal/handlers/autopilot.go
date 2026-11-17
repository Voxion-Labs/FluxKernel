package handlers

import (
	"fmt"
	"io"
	"net/http"
	"strings"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

// AutopilotHandler routes autopilot agentic loop actions and streams progress via SSE.
type AutopilotHandler struct {
	cfg        *config.Config
	httpClient *http.Client
}

// NewAutopilotHandler creates a new AutopilotHandler.
func NewAutopilotHandler(cfg *config.Config, client *http.Client) *AutopilotHandler {
	if client == nil {
		client = &http.Client{}
	}
	return &AutopilotHandler{
		cfg:        cfg,
		httpClient: client,
	}
}

func (h *AutopilotHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Strip prefix /api/autopilot/ or /api/autopilot
	subPath := strings.TrimPrefix(r.URL.Path, "/api/autopilot")
	subPath = strings.TrimPrefix(subPath, "/")

	targetURL := fmt.Sprintf("%s/api/v1/autopilot/%s",
		strings.TrimRight(h.cfg.EngineURL, "/"), subPath)

	isStream := strings.HasSuffix(subPath, "/stream") || subPath == "stream"

	proxyReq, err := http.NewRequestWithContext(r.Context(), r.Method, targetURL, r.Body)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to construct upstream request: %v", err), http.StatusInternalServerError)
		return
	}

	if ct := r.Header.Get("Content-Type"); ct != "" {
		proxyReq.Header.Set("Content-Type", ct)
	}
	if isStream {
		proxyReq.Header.Set("Accept", "text/event-stream")
	} else {
		proxyReq.Header.Set("Accept", "application/json")
	}

	resp, err := h.httpClient.Do(proxyReq)
	if err != nil {
		http.Error(w, fmt.Sprintf("Engine connection failed: %v", err), http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	if isStream {
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache, no-transform")
		w.Header().Set("Connection", "keep-alive")
		w.Header().Set("X-Accel-Buffering", "no")
		w.WriteHeader(resp.StatusCode)

		flusher, ok := w.(http.Flusher)
		buf := make([]byte, 4096)
		for {
			n, readErr := resp.Body.Read(buf)
			if n > 0 {
				w.Write(buf[:n])
				if ok {
					flusher.Flush()
				}
			}
			if readErr != nil {
				break
			}
		}
		return
	}

	for k, vv := range resp.Header {
		for _, v := range vv {
			w.Header().Add(k, v)
		}
	}
	w.WriteHeader(resp.StatusCode)
	_, _ = io.Copy(w, resp.Body)
}
