package handlers

import (
	"fmt"
	"io"
	"net/http"
	"strings"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

// TasksHandler handles Celery task status checking and real-time SSE event streaming.
type TasksHandler struct {
	cfg        *config.Config
	httpClient *http.Client
}

// NewTasksHandler creates a new TasksHandler.
func NewTasksHandler(cfg *config.Config, client *http.Client) *TasksHandler {
	if client == nil {
		client = &http.Client{}
	}
	return &TasksHandler{
		cfg:        cfg,
		httpClient: client,
	}
}

func (h *TasksHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	subPath := strings.TrimPrefix(r.URL.Path, "/api/tasks")
	subPath = strings.TrimPrefix(subPath, "/")

	targetURL := fmt.Sprintf("%s/api/v1/tasks/%s",
		strings.TrimRight(h.cfg.EngineURL, "/"), subPath)

	isStream := strings.HasSuffix(subPath, "/stream")

	proxyReq, err := http.NewRequestWithContext(r.Context(), r.Method, targetURL, r.Body)
	if err != nil {
		http.Error(w, fmt.Sprintf("Request build error: %v", err), http.StatusInternalServerError)
		return
	}

	if isStream {
		proxyReq.Header.Set("Accept", "text/event-stream")
	} else {
		proxyReq.Header.Set("Accept", "application/json")
	}

	resp, err := h.httpClient.Do(proxyReq)
	if err != nil {
		http.Error(w, fmt.Sprintf("Engine unreachable: %v", err), http.StatusBadGateway)
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
