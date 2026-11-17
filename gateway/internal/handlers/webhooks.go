package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

// WebhookPayload represents an event payload emitted by the autonomous engine.
type WebhookPayload struct {
	Event     string                 `json:"event"`
	SessionID *int                   `json:"session_id,omitempty"`
	Data      map[string]interface{} `json:"data,omitempty"`
	Timestamp string                 `json:"timestamp,omitempty"`
}

// WebhookHandler manages incoming webhooks and provides an audit ledger.
type WebhookHandler struct {
	cfg      *config.Config
	mu       sync.RWMutex
	eventLog []WebhookPayload
	maxLimit int
}

// NewWebhookHandler creates a new WebhookHandler with a thread-safe ring buffer.
func NewWebhookHandler(cfg *config.Config) *WebhookHandler {
	return &WebhookHandler{
		cfg:      cfg,
		eventLog: make([]WebhookPayload, 0, 100),
		maxLimit: 100,
	}
}

func (h *WebhookHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodPost:
		h.handlePost(w, r)
	case http.MethodGet:
		h.handleGet(w, r)
	default:
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
	}
}

func (h *WebhookHandler) handlePost(w http.ResponseWriter, r *http.Request) {
	var payload WebhookPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "Invalid JSON payload."})
		return
	}

	if payload.Event == "" {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusUnprocessableEntity)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "Missing required field: event."})
		return
	}

	if payload.Timestamp == "" {
		payload.Timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	// Append to thread-safe event ledger
	h.mu.Lock()
	if len(h.eventLog) >= h.maxLimit {
		// Evict oldest entry
		h.eventLog = h.eventLog[1:]
	}
	h.eventLog = append(h.eventLog, payload)
	h.mu.Unlock()

	// Specialized event dispatch logging
	switch payload.Event {
	case "IMAGE_GENERATED":
		log.Printf("[Webhook] Image generated for session %v: %v", payload.SessionID, payload.Data)
	case "CODE_EXECUTION_COMPLETE":
		log.Printf("[Webhook] Code execution complete: %v", payload.Data)
	case "FILE_WRITTEN":
		log.Printf("[Webhook] File written: %v", payload.Data)
	case "AGENT_TASK_COMPLETE":
		log.Printf("[Webhook] Agent task complete: %v", payload.Data)
	default:
		log.Printf("[Webhook] Received event: %s", payload.Event)
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"received": true,
		"event":    payload.Event,
	})
}

func (h *WebhookHandler) handleGet(w http.ResponseWriter, r *http.Request) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	// Return up to last 50 events
	start := 0
	if len(h.eventLog) > 50 {
		start = len(h.eventLog) - 50
	}
	recent := h.eventLog[start:]

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"count":  len(h.eventLog),
		"events": recent,
	})
}
