.PHONY: setup run dev test status logout clean

CONFIG_DIR := $(HOME)/.config/n26-mcp

setup: ## Install deps and verify 1Password secrets are configured
	uv sync
	@op read "op://Local Environment/ENV/N26_USERNAME" >/dev/null 2>&1 \
		&& echo "1Password: N26_USERNAME OK" \
		|| echo "1Password: N26_USERNAME NOT FOUND — add it to vault 'Local Environment', item 'ENV'"
	@op read "op://Local Environment/ENV/N26_PASSWORD" >/dev/null 2>&1 \
		&& echo "1Password: N26_PASSWORD OK" \
		|| echo "1Password: N26_PASSWORD NOT FOUND — add it to vault 'Local Environment', item 'ENV'"

run: ## Run MCP server over stdio (for use with MCP clients)
	uv run n26-mcp

dev: ## Run MCP server with interactive inspector UI
	uv run mcp dev src/n26_mcp/server.py

test: ## Run test suite
	uv run pytest

status: ## Show auth status (session file present or not)
	@if [ -f "$(CONFIG_DIR)/session.json" ]; then \
		echo "Authenticated — session at $(CONFIG_DIR)/session.json"; \
	else \
		echo "Not authenticated — call login() via Claude"; \
	fi

logout: ## Delete cached session (forces re-auth)
	@rm -f "$(CONFIG_DIR)/session.json"
	@echo "Session removed"

clean: ## Remove build artifacts and cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ *.egg-info/

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | awk 'BEGIN {FS = ":.*##"}; {printf "  %-10s %s\n", $$1, $$2}'
