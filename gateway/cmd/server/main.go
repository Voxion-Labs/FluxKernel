package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
	"github.com/Voxion-Labs/FluxKernel/gateway/internal/proxy"
)

func main() {
	cfg := config.Load()

	log.Printf("[FluxKernel Gateway] Initializing Go Gateway on :%s (Upstream: %s, Env: %s)",
		cfg.Port, cfg.EngineURL, cfg.Environment)

	handler, err := proxy.NewHandler(cfg)
	if err != nil {
		log.Fatalf("[FluxKernel Gateway Error] Failed to create proxy handler: %v", err)
	}

	mux := http.NewServeMux()
	handler.RegisterRoutes(mux)

	server := &http.Server{
		Addr:         fmt.Sprintf(":%s", cfg.Port),
		Handler:      proxy.WithCORS(mux, cfg.AllowedOrigins),
		ReadTimeout:  cfg.ReadTimeout,
		WriteTimeout: cfg.WriteTimeout,
	}

	// Server runner in background goroutine
	shutdownChan := make(chan os.Signal, 1)
	signal.Notify(shutdownChan, os.Interrupt, syscall.SIGTERM, syscall.SIGINT)

	go func() {
		log.Printf("[FluxKernel Gateway] Listening for HTTP traffic on port %s", cfg.Port)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("[FluxKernel Gateway Error] HTTP server listen failed: %v", err)
		}
	}()

	<-shutdownChan
	log.Println("[FluxKernel Gateway] Shutdown signal intercepted, gracefully stopping...")

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("[FluxKernel Gateway Error] Graceful shutdown failed: %v", err)
	}

	log.Println("[FluxKernel Gateway] Server successfully terminated.")
}
