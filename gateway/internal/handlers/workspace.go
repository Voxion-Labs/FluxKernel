package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/Voxion-Labs/FluxKernel/gateway/internal/config"
)

// FileNode mirrors the frontend WorkspaceTree file structure.
type FileNode struct {
	Name     string     `json:"name"`
	Path     string     `json:"path"`
	Type     string     `json:"type"` // "file" | "folder"
	ID       string     `json:"id"`
	Children []FileNode `json:"children,omitempty"`
}

// WritePayload represents a file write instruction.
type WritePayload struct {
	Path    string `json:"path"`
	Content string `json:"content"`
}

// WorkspaceHandler manages native filesystem operations inside the workspace directory.
type WorkspaceHandler struct {
	cfg          *config.Config
	workspaceDir string
}

// NewWorkspaceHandler creates a new WorkspaceHandler.
func NewWorkspaceHandler(cfg *config.Config) *WorkspaceHandler {
	_ = os.MkdirAll(cfg.WorkspaceDir, 0755)
	return &WorkspaceHandler{
		cfg:          cfg,
		workspaceDir: cfg.WorkspaceDir,
	}
}

func (h *WorkspaceHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		h.handleGetTree(w, r)
	case http.MethodPost:
		h.handleWriteFile(w, r)
	default:
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
	}
}

func (h *WorkspaceHandler) handleGetTree(w http.ResponseWriter, r *http.Request) {
	tree, err := h.scanDirectory(h.workspaceDir, "")
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": fmt.Sprintf("Failed to scan workspace: %v", err),
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"tree": tree,
	})
}

func (h *WorkspaceHandler) scanDirectory(basePath, relPath string) ([]FileNode, error) {
	targetDir := filepath.Join(basePath, relPath)
	entries, err := os.ReadDir(targetDir)
	if err != nil {
		if os.IsNotExist(err) {
			return []FileNode{}, nil
		}
		return nil, err
	}

	var nodes []FileNode
	for _, entry := range entries {
		name := entry.Name()
		if name == ".flux_temp" || name == ".flux_snapshots" || name == ".git" || name == "node_modules" {
			continue
		}

		itemRelPath := filepath.Join(relPath, name)
		// Normalize to forward slashes for cross-platform compatibility
		posixPath := filepath.ToSlash(itemRelPath)

		node := FileNode{
			Name: name,
			Path: posixPath,
			ID:   posixPath,
		}

		if entry.IsDir() {
			node.Type = "folder"
			children, err := h.scanDirectory(basePath, itemRelPath)
			if err == nil {
				node.Children = children
			} else {
				node.Children = []FileNode{}
			}
		} else {
			node.Type = "file"
		}

		nodes = append(nodes, node)
	}

	// Sort folders first, then alphabetically
	sort.Slice(nodes, func(i, j int) bool {
		if nodes[i].Type != nodes[j].Type {
			return nodes[i].Type == "folder"
		}
		return strings.ToLower(nodes[i].Name) < strings.ToLower(nodes[j].Name)
	})

	if nodes == nil {
		nodes = []FileNode{}
	}

	return nodes, nil
}

func (h *WorkspaceHandler) handleWriteFile(w http.ResponseWriter, r *http.Request) {
	var payload WritePayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "Invalid JSON payload."})
		return
	}

	cleanRel := filepath.Clean(payload.Path)
	cleanPosix := filepath.ToSlash(cleanRel)
	lowerPosix := strings.ToLower(cleanPosix)

	// Block path traversal and writing to protected internal partitions
	if strings.HasPrefix(cleanRel, "..") || filepath.IsAbs(cleanRel) ||
		strings.HasPrefix(lowerPosix, ".git") ||
		strings.HasPrefix(lowerPosix, ".flux_snapshots") ||
		strings.HasPrefix(lowerPosix, ".env") {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusForbidden)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": "Path traversal or protected partition write blocked",
		})
		return
	}

	targetPath := filepath.Join(h.workspaceDir, cleanRel)
	// Double check absolute path starts with workspaceDir
	absTarget, _ := filepath.Abs(targetPath)
	absWorkspace, _ := filepath.Abs(h.workspaceDir)
	if !strings.HasPrefix(absTarget, absWorkspace) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusForbidden)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": "Path traversal blocked",
		})
		return
	}

	// Create parent directory if needed
	if err := os.MkdirAll(filepath.Dir(targetPath), 0755); err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": fmt.Sprintf("Failed to create parent directory: %v", err),
		})
		return
	}

	// Write file atomically
	if err := os.WriteFile(targetPath, []byte(payload.Content), 0644); err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": fmt.Sprintf("Failed to write file: %v", err),
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"path":    filepath.ToSlash(cleanRel),
	})
}
