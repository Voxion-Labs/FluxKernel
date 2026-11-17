package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

// ChatHandler handles client chat requests, proxying to the Python core engine
// and formatting responses as Server-Sent Events (SSE).
type ChatHandler struct {
	cfg        *config.Config
	httpClient *http.Client
}

// NewChatHandler creates a new ChatHandler.
func NewChatHandler(cfg *config.Config, client *http.Client) *ChatHandler {
	if client == nil {
		client = &http.Client{}
	}
	return &ChatHandler{
		cfg:        cfg,
		httpClient: client,
	}
}

// ServeHTTP processes chat POST requests and streams SSE events to the client.
func (h *ChatHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}

	// Set SSE response headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache, no-transform")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")

	sendSSE := func(payload interface{}) {
		data, err := json.Marshal(payload)
		if err == nil {
			fmt.Fprintf(w, "data: %s\n\n", data)
			flusher.Flush()
		}
	}

	sendError := func(msg string) {
		sendSSE(map[string]interface{}{
			"type":    "error",
			"message": msg,
		})
	}

	targetURL := fmt.Sprintf("%s/api/v1/chat/", strings.TrimRight(h.cfg.EngineURL, "/"))
	proxyReq, err := http.NewRequestWithContext(r.Context(), http.MethodPost, targetURL, r.Body)
	if err != nil {
		sendError(fmt.Sprintf("Failed to construct upstream request: %v", err))
		return
	}

	// Forward original content headers
	if ct := r.Header.Get("Content-Type"); ct != "" {
		proxyReq.Header.Set("Content-Type", ct)
	}
	if auth := r.Header.Get("Authorization"); auth != "" {
		proxyReq.Header.Set("Authorization", auth)
	}

	resp, err := h.httpClient.Do(proxyReq)
	if err != nil {
		sendError(fmt.Sprintf("Upstream engine connection error: %v", err))
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		bodyBytes, _ := io.ReadAll(resp.Body)
		sendError(fmt.Sprintf("Engine returned error (%d): %s", resp.StatusCode, string(bodyBytes)))
		return
	}

	// Check if upstream is already an event stream
	if strings.Contains(resp.Header.Get("Content-Type"), "text/event-stream") {
		buf := make([]byte, 4096)
		for {
			n, readErr := resp.Body.Read(buf)
			if n > 0 {
				w.Write(buf[:n])
				flusher.Flush()
			}
			if readErr != nil {
				break
			}
		}
		return
	}

	// Otherwise parse JSON response from engine and format as standard frontend SSE event
	var chatResult struct {
		SessionID int                    `json:"session_id"`
		MessageID int                    `json:"message_id"`
		Role      string                 `json:"role"`
		Content   string                 `json:"content"`
		Mode      string                 `json:"mode"`
		Meta      map[string]interface{} `json:"meta"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&chatResult); err != nil {
		log.Printf("[ChatHandler] Failed to decode engine JSON: %v", err)
		sendError("Invalid response received from cognitive engine")
		return
	}

	// Emit formatted message event
	sendSSE(map[string]interface{}{
		"type":       "message",
		"session_id": chatResult.SessionID,
		"message_id": chatResult.MessageID,
		"role":       chatResult.Role,
		"content":    chatResult.Content,
		"mode":       chatResult.Mode,
	})

	// Emit done completion event
	sendSSE(map[string]interface{}{
		"type": "done",
	})
}
