package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
	"github.com/Voxion-Labs/FluxKernel/gateway/internal/proxy"
)

func TestGatewayHealthEndpoints(t *testing.T) {
	cfg := &config.Config{
		Port:           "8080",
		EngineURL:      "http://127.0.0.1:8000",
		Environment:    "test",
		AllowedOrigins: "*",
	}

	handler, err := proxy.NewHandler(cfg)
	if err != nil {
		t.Fatalf("failed to create proxy handler: %v", err)
	}

	mux := http.NewServeMux()
	handler.RegisterRoutes(mux)
	wrapped := proxy.WithCORS(mux, cfg.AllowedOrigins)

	t.Run("Healthz Endpoint", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
		rec := httptest.NewRecorder()

		wrapped.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Errorf("expected 200 OK, got %d", rec.Code)
		}

		var payload map[string]interface{}
		if err := json.Unmarshal(rec.Body.Bytes(), &payload); err != nil {
			t.Fatalf("failed to parse response JSON: %v", err)
		}

		if payload["status"] != "healthy" {
			t.Errorf("expected status 'healthy', got %v", payload["status"])
		}
	})

	t.Run("Version Endpoint", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/version", nil)
		rec := httptest.NewRecorder()

		wrapped.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Errorf("expected 200 OK, got %d", rec.Code)
		}

		var payload map[string]string
		if err := json.Unmarshal(rec.Body.Bytes(), &payload); err != nil {
			t.Fatalf("failed to parse response JSON: %v", err)
		}

		if payload["version"] != proxy.GatewayVersion {
			t.Errorf("expected version '%s', got %v", proxy.GatewayVersion, payload["version"])
		}
	})

	t.Run("CORS Preflight", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodOptions, "/api/v1/chat", nil)
		rec := httptest.NewRecorder()

		wrapped.ServeHTTP(rec, req)

		if rec.Code != http.StatusNoContent {
			t.Errorf("expected 204 No Content for OPTIONS, got %d", rec.Code)
		}

		if rec.Header().Get("Access-Control-Allow-Origin") != "*" {
			t.Errorf("expected '*' CORS origin, got %s", rec.Header().Get("Access-Control-Allow-Origin"))
		}
	})
}
