package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

func TestWebhookHandler(t *testing.T) {
	cfg := &config.Config{}
	h := NewWebhookHandler(cfg)

	t.Run("POST Webhook Event", func(t *testing.T) {
		body := bytes.NewBufferString(`{"event": "IMAGE_GENERATED", "session_id": 42, "data": {"url": "test.png"}}`)
		req := httptest.NewRequest(http.MethodPost, "/api/webhooks", body)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", rec.Code)
		}

		var res map[string]interface{}
		if err := json.Unmarshal(rec.Body.Bytes(), &res); err != nil {
			t.Fatal(err)
		}

		if res["event"] != "IMAGE_GENERATED" || res["received"] != true {
			t.Errorf("unexpected webhook response: %v", res)
		}
	})

	t.Run("GET Webhook Audit", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/api/webhooks", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", rec.Code)
		}

		var res struct {
			Count  int              `json:"count"`
			Events []WebhookPayload `json:"events"`
		}
		if err := json.Unmarshal(rec.Body.Bytes(), &res); err != nil {
			t.Fatal(err)
		}

		if res.Count < 1 {
			t.Errorf("expected count >= 1, got %d", res.Count)
		}
	})
}

func TestWorkspaceHandler(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "flux_workspace_test_*")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(tempDir)

	cfg := &config.Config{
		WorkspaceDir: tempDir,
	}
	h := NewWorkspaceHandler(cfg)

	t.Run("Safe File Write", func(t *testing.T) {
		payload := `{"path": "subfolder/hello.txt", "content": "Hello Flux Engine"}`
		req := httptest.NewRequest(http.MethodPost, "/api/workspace", bytes.NewBufferString(payload))
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d (body: %s)", rec.Code, rec.Body.String())
		}

		writtenPath := filepath.Join(tempDir, "subfolder", "hello.txt")
		content, err := os.ReadFile(writtenPath)
		if err != nil {
			t.Fatalf("file not found on disk: %v", err)
		}
		if string(content) != "Hello Flux Engine" {
			t.Errorf("content mismatch: %s", string(content))
		}
	})

	t.Run("Block Path Traversal", func(t *testing.T) {
		payload := `{"path": "../escape.txt", "content": "Malicious payload"}`
		req := httptest.NewRequest(http.MethodPost, "/api/workspace", bytes.NewBufferString(payload))
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusForbidden {
			t.Errorf("expected 403 Forbidden for traversal, got %d", rec.Code)
		}
	})

	t.Run("Get Workspace Tree", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/api/workspace", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", rec.Code)
		}

		var res struct {
			Tree []FileNode `json:"tree"`
		}
		if err := json.Unmarshal(rec.Body.Bytes(), &res); err != nil {
			t.Fatal(err)
		}

		if len(res.Tree) == 0 {
			t.Errorf("expected at least 1 node in tree, got 0")
		}
	})
}

func TestWebHandlerValidation(t *testing.T) {
	cfg := &config.Config{EngineURL: "http://127.0.0.1:8000"}
	h := NewWebHandler(cfg, nil)

	t.Run("Reject Unknown Action", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodPost, "/api/web/unknown_action", bytes.NewBufferString("{}"))
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400 Bad Request, got %d", rec.Code)
		}
	})
}
