.PHONY: setup register run dev test status logout clean help

CONFIG_DIR := $(HOME)/.config/n26-mcp
REPO_DIR   := $(shell pwd)

setup: ## Install deps and verify credentials are accessible
	uv sync
	@echo "Checking credentials..."
	@if [ -f .env ]; then \
		export $$(grep -v '^#' .env | xargs) 2>/dev/null; \
		if [ -n "$$N26_USERNAME" ] && [ -n "$$N26_PASSWORD" ]; then \
			echo "  .env: N26_USERNAME and N26_PASSWORD found"; \
		else \
			echo "  .env: missing N26_USERNAME or N26_PASSWORD — check .env (see .env.example)"; \
		fi; \
	elif command -v op >/dev/null 2>&1; then \
		op read "op://Local Environment/ENV/N26_USERNAME" >/dev/null 2>&1 \
			&& echo "  1Password: N26_USERNAME OK" \
			|| echo "  1Password: N26_USERNAME NOT FOUND"; \
		op read "op://Local Environment/ENV/N26_PASSWORD" >/dev/null 2>&1 \
			&& echo "  1Password: N26_PASSWORD OK" \
			|| echo "  1Password: N26_PASSWORD NOT FOUND"; \
	else \
		echo "  No .env file found and op CLI not available."; \
		echo "  Copy .env.example to .env and fill in your credentials."; \
	fi

register: ## Register n26-mcp with Claude Code (auto-detects op vs plain .env)
	@if command -v op >/dev/null 2>&1 && [ ! -f .env -o "$$(grep -c '^N26_' .env 2>/dev/null | head -1)" = "0" ] || \
	    grep -q '^N26_USERNAME=op://' .env 2>/dev/null; then \
		echo "Registering with 1Password (op run)..."; \
		claude mcp add n26 --scope user -- op run --env-file $(HOME)/.config/op/local-env.env -- uv --directory $(REPO_DIR) run n26-mcp; \
	else \
		echo "Registering with plain .env (dotenv auto-load)..."; \
		claude mcp add n26 --scope user -- uv --directory $(REPO_DIR) run n26-mcp; \
	fi
	@echo "Done. Restart Claude Code to pick up the new server."

run: ## Run MCP server over stdio
	uv run n26-mcp

dev: ## Run MCP server with interactive inspector UI
	uv run mcp dev src/n26_mcp/server.py

test: ## Run test suite
	uv run pytest

status: ## Show auth status
	@if [ -f "$(CONFIG_DIR)/session.json" ]; then \
		echo "Authenticated — session at $(CONFIG_DIR)/session.json"; \
	else \
		echo "Not authenticated — call login() via Claude Code"; \
	fi

logout: ## Delete cached session (forces re-auth)
	@rm -f "$(CONFIG_DIR)/session.json"
	@echo "Session removed"

clean: ## Remove build artifacts and cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ *.egg-info/

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | awk 'BEGIN {FS = ":.*##"}; {printf "  %-12s %s\n", $$1, $$2}'
