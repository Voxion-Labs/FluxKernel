package config

import (
	"os"
	"strconv"
	"time"
)

// Config represents runtime configuration for the FluxKernel Go Gateway.
type Config struct {
	Port           string
	EngineURL      string
	Environment    string
	ReadTimeout    time.Duration
	WriteTimeout   time.Duration
	AllowedOrigins string
}

// Load loads configuration from environment variables with fallback defaults.
func Load() *Config {
	port := os.Getenv("PORT")
	if port == "" {
		port = os.Getenv("GATEWAY_PORT")
	}
	if port == "" {
		port = "8080"
	}

	engineURL := os.Getenv("ENGINE_URL")
	if engineURL == "" {
		engineURL = "http://localhost:8000"
	}

	env := os.Getenv("ENVIRONMENT")
	if env == "" {
		env = "development"
	}

	origins := os.Getenv("ALLOWED_ORIGINS")
	if origins == "" {
		origins = "*"
	}

	readTimeoutSec, _ := strconv.Atoi(os.Getenv("READ_TIMEOUT_SECONDS"))
	if readTimeoutSec <= 0 {
		readTimeoutSec = 30
	}

	writeTimeoutSec, _ := strconv.Atoi(os.Getenv("WRITE_TIMEOUT_SECONDS"))
	if writeTimeoutSec <= 0 {
		writeTimeoutSec = 60
	}

	return &Config{
		Port:           port,
		EngineURL:      engineURL,
		Environment:    env,
		ReadTimeout:    time.Duration(readTimeoutSec) * time.Second,
		WriteTimeout:   time.Duration(writeTimeoutSec) * time.Second,
		AllowedOrigins: origins,
	}
}
