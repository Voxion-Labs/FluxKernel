package ui

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

func TestUIHandler(t *testing.T) {
	cfg := &config.Config{
		Environment:  "test",
		EngineURL:    "http://localhost:8000",
		WorkspaceDir: t.TempDir(),
	}

	h, err := NewUIHandler(cfg)
	if err != nil {
		t.Fatalf("Failed to initialize UIHandler: %v", err)
	}

	t.Run("Default Theme is Light", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/dashboard", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, `data-theme="light"`) {
			t.Errorf("expected default theme to be light, body: %s", body)
		}

		// Ensure ZERO JavaScript policy compliance
		if strings.Contains(body, "<script") {
			t.Errorf("VIOLATION: <script> tag detected in rendered HTML! Policy requires pure HTML/CSS (Zero JS).")
		}

		if !strings.Contains(body, "FluxKernel") {
			t.Errorf("body missing 'FluxKernel'")
		}
		if !strings.Contains(body, "Emergency Rollback") {
			t.Errorf("body missing 'Emergency Rollback'")
		}
	})

	t.Run("Dark Theme Query Override", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/dashboard?theme=dark", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, `data-theme="dark"`) {
			t.Errorf("expected dark theme override in body")
		}
	})

	t.Run("System Theme Query Override", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/dashboard?theme=system", nil)
		rec := httptest.NewRecorder()

		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, `data-theme="system"`) {
			t.Errorf("expected system theme override in body")
		}
	})

	t.Run("Directive Form Dispatch", func(t *testing.T) {
		form := url.Values{}
		form.Set("prompt", "Implement pure Go data structures")
		form.Set("persona", "coder")
		form.Set("theme", "light")

		req := httptest.NewRequest(http.MethodPost, "/dashboard/dispatch", strings.NewReader(form.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		rec := httptest.NewRecorder()

		h.HandleDispatch(rec, req)

		if rec.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect, got %d", rec.Code)
		}

		location := rec.Header().Get("Location")
		if !strings.Contains(location, "/dashboard") {
			t.Errorf("expected redirect to /dashboard, got %s", location)
		}
	})

	t.Run("Emergency Rollback Form Dispatch", func(t *testing.T) {
		form := url.Values{}
		form.Set("snapshot_id", "snap_test_123")
		form.Set("theme", "light")

		req := httptest.NewRequest(http.MethodPost, "/dashboard/rollback", strings.NewReader(form.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		rec := httptest.NewRecorder()

		h.HandleRollback(rec, req)

		if rec.Code != http.StatusSeeOther {
			t.Errorf("expected 303 See Other redirect, got %d", rec.Code)
		}
	})

	t.Run("Static Asset Delivery (CSS Only, Zero JS)", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/static/css/dashboard.css", nil)
		rec := httptest.NewRecorder()

		h.ServeStatic().ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Errorf("expected 200 OK for dashboard.css, got %d", rec.Code)
		}

		body := rec.Body.String()
		if !strings.Contains(body, "FluxKernel Enterprise Minimalist UI Stylesheet") {
			t.Errorf("CSS missing enterprise theme signature")
		}
	})
}
