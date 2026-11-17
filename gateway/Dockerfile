# ==============================================================================
# Voxion Labs - FluxKernel High-Performance Go Gateway
# Distroless | Non-Root | Minimal Attack Surface
# ==============================================================================
FROM golang:1.23-bookworm AS builder

WORKDIR /app

COPY go.mod ./
RUN go mod download || true

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-s -w" \
    -o /out/fluxkernel-gateway \
    ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot

WORKDIR /
COPY --from=builder /out/fluxkernel-gateway /gateway

EXPOSE 8080

USER nonroot:nonroot

ENTRYPOINT ["/gateway"]
