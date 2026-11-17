package ui

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

func TestUIHandler(t *testing.T) {
	cfg := &config.Config{
		Environment: "test",
		EngineURL:   "http://localhost:8000",
	}

	h, err := NewUIHandler(cfg)
	if err != nil {
		t.Fatalf("Failed to initialize UIHandler: %v", err)
	}

	t.Run("Render Dashboard HTML", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/dashboard", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Errorf("expected 200 OK, got %d", rec.Code)
		}

		contentType := rec.Header().Get("Content-Type")
		if !strings.Contains(contentType, "text/html") {
			t.Errorf("expected text/html content-type, got %s", contentType)
		}

		body := rec.Body.String()
		if !strings.Contains(body, "FluxKernel") {
			t.Errorf("body missing 'FluxKernel'")
		}
		if !strings.Contains(body, "Emergency Rollback") {
			t.Errorf("body missing 'Emergency Rollback'")
		}
		if !strings.Contains(body, "HARDENED C++ SANDBOX ACTIVE") {
			t.Errorf("body missing hardened sandbox status")
		}
	})

	t.Run("Browser Request Detection", func(t *testing.T) {
		browserReq := httptest.NewRequest(http.MethodGet, "/", nil)
		browserReq.Header.Set("Accept", "text/html,application/xhtml+xml")
		if !IsBrowserRequest(browserReq) {
			t.Errorf("expected IsBrowserRequest to be true for text/html")
		}

		apiReq := httptest.NewRequest(http.MethodGet, "/", nil)
		apiReq.Header.Set("Accept", "application/json")
		if IsBrowserRequest(apiReq) {
			t.Errorf("expected IsBrowserRequest to be false for application/json")
		}
	})

	t.Run("Static Asset Delivery", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/static/css/dashboard.css", nil)
		rec := httptest.NewRecorder()

		h.ServeStatic().ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Errorf("expected 200 OK for /static/css/dashboard.css, got %d", rec.Code)
		}

		if !strings.Contains(rec.Body.String(), "FluxKernel Sovereign Dashboard Theme") {
			t.Errorf("CSS content missing theme signature")
		}
	})
}
