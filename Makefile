# AdLab Laboratory Management System - Makefile
# Refactored from run script to provide better dependency management and standard make conventions

SHELL := /bin/bash
.DEFAULT_GOAL := help
DC ?= exec
TTY := $(shell [ -t 1 ] && echo "" || echo "-T")

# Docker helper functions will be sourced in individual targets

# -----------------------------------------------------------------------------
# .PHONY declarations for all targets
# -----------------------------------------------------------------------------

.PHONY: help cmd shell psql redis-cli manage secret test test-cleanup lint lint-dockerfile lint-shell format format-shell quality db-dump db-restore db-list-backups deps-install uv uv-outdated yarn yarn-install yarn-outdated yarn-build-js yarn-build-css yarn-optimize-images docs-serve docs-build docs-update-paths docs-update-paths-preview clean ci-install-deps ci-test server-connect deploy deploy-prod safety-check safety-report

# -----------------------------------------------------------------------------
# Help target (default)
# -----------------------------------------------------------------------------

help: ## Display available targets
	@echo "AdLab Laboratory Management System - Available Targets:"
	@echo ""
	@echo "Docker & Container Management:"
	@echo "  cmd                    Run any command in the web container"
	@echo "  shell                  Start a shell session in the web container"
	@echo "  psql                   Connect to PostgreSQL"
	@echo "  redis-cli              Connect to Redis"
	@echo ""
	@echo "Django Management:"
	@echo "  manage                 Run Django manage.py commands (use: make manage ARGS=\"migrate\")"
	@echo "  secret                 Generate a Django secret key"
	@echo ""
	@echo "Testing:"
	@echo "  test                   Run the full Django test suite"
	@echo "  test-specific          Run specific tests (use: make test-specific ARGS=\"protocols.tests.ProtocolViewsTest\")"
	@echo "  test-cleanup           Clean up test database connections"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint                   Lint Python code"
	@echo "  lint-dockerfile        Lint Dockerfile"
	@echo "  lint-shell             Lint shell scripts"
	@echo "  format                 Format Python code"
	@echo "  format-shell           Format shell scripts"
	@echo "  quality                Run all code quality checks"
	@echo "  safety-check           Check dependencies for security vulnerabilities"
	@echo "  safety-report          Generate security report and save to file"
	@echo ""
	@echo "Database Operations:"
	@echo "  db-dump                Generate a database dump"
	@echo "  db-restore             Restore database from dump (use: make db-restore DUMP_FILE=path)"
	@echo "  db-list-backups        List available database backups"
	@echo ""
	@echo "Dependencies:"
	@echo "  deps-install           Install all dependencies"
	@echo "  uv                     Run uv commands (use: make uv ARGS=\"add package\")"
	@echo "  uv-outdated            List outdated Python packages"
	@echo "  yarn                   Run yarn commands (use: make yarn ARGS=\"add package\")"
	@echo "  yarn-install           Install JS dependencies"
	@echo "  yarn-outdated          List outdated JS packages"
	@echo "  yarn-build-js          Build JavaScript assets"
	@echo "  yarn-build-css         Build CSS assets"
	@echo "  yarn-optimize-images   Optimize images"
	@echo ""
	@echo "Documentation:"
	@echo "  docs-serve             Preview documentation with live reload"
	@echo "  docs-build             Build documentation site"
	@echo "  docs-update-paths-preview  Preview image path updates (dry run)"
	@echo "  docs-update-paths      Update all image placeholder paths"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean                  Remove cache and generated files"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci-install-deps        Install CI dependencies"
	@echo "  ci-test                Run full CI pipeline"
	@echo ""
	@echo "Server:"
	@echo "  server-connect         Connect to production server via SSH"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy                 Run development deployment script"
	@echo "  deploy-prod            Run production deployment script"
	@echo ""
	@echo "Examples:"
	@echo "  make test              # Run tests"
	@echo "  make manage ARGS=\"migrate\"  # Run Django migrations"
	@echo "  make shell             # Start shell in container"
	@echo "  make db-dump           # Create database backup"
	@echo "  make docs-serve        # Preview documentation"
	@echo "  make docs-build        # Build documentation site"

# -----------------------------------------------------------------------------
# Docker & Container Management
# -----------------------------------------------------------------------------

cmd: ## Run any command in the web container
	@source scripts/docker-helper.sh && _dc web $(ARGS)

shell: ## Start a shell session in the web container
	@source scripts/docker-helper.sh && _dc web bash $(ARGS)

psql: ## Connect to PostgreSQL
	@source scripts/docker-helper.sh && . .env && _dc postgres psql -U $$POSTGRES_USER $(ARGS)

redis-cli: ## Connect to Redis
	@source scripts/docker-helper.sh && _dc redis redis-cli $(ARGS)

# -----------------------------------------------------------------------------
# Django Management
# -----------------------------------------------------------------------------

manage: ## Run Django manage.py commands
	@./scripts/manage-wrapper.sh $(ARGS)

secret: ## Generate a Django secret key
	@source scripts/docker-helper.sh && _dc web python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------

test: ## Run the full Django test suite
	@./scripts/test-wrapper.sh

test-specific: ## Run specific tests (use: make test-specific ARGS="protocols.tests.ProtocolViewsTest")
	@source scripts/docker-helper.sh && _dc web python3 manage.py collectstatic --no-input
	@source scripts/docker-helper.sh && _dc -e DJANGO_TESTING=true -e RUNNING_TESTS=true web python3 manage.py test $(ARGS)

test-cleanup: ## Clean up test database connections
	@./scripts/test-cleanup.sh

# -----------------------------------------------------------------------------
# Code Quality
# -----------------------------------------------------------------------------

lint: ## Lint Python code
	@source scripts/docker-helper.sh && _dc web ruff check $(ARGS)

lint-dockerfile: ## Lint Dockerfile
	@docker container run --rm -i \
		-v "$(PWD)/.hadolint.yaml:/.config/hadolint.yaml" \
		hadolint/hadolint hadolint $(ARGS) - <Dockerfile

lint-shell: ## Lint shell scripts
	@local cmd=(shellcheck); \
	if ! command -v shellcheck >/dev/null 2>&1; then \
		local cmd=(docker container run --rm -i -v "$(PWD):/mnt" koalaman/shellcheck:stable); \
	fi; \
	find . -type f \
		! -path "./.git/*" \
		! -path "./.ruff_cache/*" \
		! -path "./.pytest_cache/*" \
		! -path "./assets/*" \
		! -path "./public/*" \
		! -path "./public_collected/*" \
		! -name "*.md" \
		-exec grep --quiet '^#!.*sh' {} \; -exec "$${cmd[@]}" {} +

format: ## Format Python code
	@source scripts/docker-helper.sh && _dc web ruff check --fix
	@source scripts/docker-helper.sh && _dc web ruff format $(ARGS)

format-shell: ## Format shell scripts
	@local cmd=(shfmt); \
	if ! command -v shfmt >/dev/null 2>&1; then \
		local cmd=(docker container run --rm -i -v "$(PWD):/mnt" -u "$$(id -u):$$(id -g)" -w /mnt mvdan/shfmt:v3); \
	fi; \
	local maybe_write=("--write"); \
	for arg in $(ARGS); do \
		if [ "$$arg" == "-d" ] || [ "$$arg" == "--diff" ]; then \
			unset "maybe_write[0]"; \
		fi; \
	done; \
	"$${cmd[@]}" "$${maybe_write[@]}" $(ARGS) .

quality: ## Run all code quality checks
	@$(MAKE) lint-dockerfile
	@$(MAKE) lint-shell
	@$(MAKE) lint
	@$(MAKE) format-shell
	@$(MAKE) format
	@$(MAKE) safety-check

# -----------------------------------------------------------------------------
# Database Operations
# -----------------------------------------------------------------------------

db-dump: ## Generate a database dump
	@./scripts/db-dump.sh

db-restore: ## Restore database from dump
	@if [ -z "$(DUMP_FILE)" ]; then \
		echo "❌ Please provide DUMP_FILE variable"; \
		echo "Usage: make db-restore DUMP_FILE=path/to/dump.sql"; \
		exit 1; \
	fi
	@./scripts/db-restore.sh $(DUMP_FILE)

db-list-backups: ## List available database backups
	@./scripts/db-list-backups.sh

# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------

deps-install: ## Install all dependencies
	@if [ -z "$(NO_BUILD)" ]; then \
		docker compose down && docker compose build; \
	fi
	@source scripts/docker-helper.sh && _dc_run js yarn install
	@source scripts/docker-helper.sh && _dc_run web bash -c "cd .. && bin/uv-install"

uv: ## Run uv commands
	@source scripts/docker-helper.sh && _dc web uv $(ARGS)

uv-outdated: ## List outdated Python packages
	@source scripts/docker-helper.sh && _dc_run web uv tree --outdated --depth 1 $(ARGS)

yarn: ## Run yarn commands
	@source scripts/docker-helper.sh && _dc js yarn $(ARGS)

yarn-install: ## Install JS dependencies
	@source scripts/docker-helper.sh && _dc_run js yarn install

yarn-outdated: ## List outdated JS packages
	@source scripts/docker-helper.sh && _dc_run js yarn outdated

yarn-build-js: ## Build JavaScript assets
	@mkdir -p ../public/js
	@source scripts/docker-helper.sh && _dc js node esbuild.config.mjs

yarn-build-css: ## Build CSS assets
	@mkdir -p ../public/css
	@source scripts/docker-helper.sh && \
	if [ "$(NODE_ENV)" == "production" ]; then \
		_dc js DEBUG=0 tailwindcss -i css/app.css -o ../public/css/app.css --minify; \
	else \
		_dc js DEBUG=0 tailwindcss -i css/app.css -o ../public/css/app.css --watch; \
	fi

yarn-optimize-images: ## Optimize images
	@source scripts/docker-helper.sh && _dc js node optimize-images.js

# -----------------------------------------------------------------------------
# Documentation
# -----------------------------------------------------------------------------

docs-serve: ## Preview documentation with live reload
	@echo "📚 Starting MkDocs development server..."
	@echo "📝 Documentation will be available at http://127.0.0.1:8000"
	@echo ""
	@source scripts/docker-helper.sh && _dc web bash -c "cd /app && mkdocs serve -a 0.0.0.0:8000"

docs-build: ## Build documentation site
	@echo "🔨 Building documentation site..."
	@echo ""
	@source scripts/docker-helper.sh && _dc web bash -c "cd /app && mkdocs build -d public_collected/docs --clean && cp -r public_collected/docs /public_collected/"
	@echo ""
	@echo "✅ Documentation built successfully!"
	@echo "📦 Output: public_collected/docs/ (host) and /public_collected/docs/ (container)"
	@echo "📝 Access at http://localhost:8000/static/docs/"

docs-update-paths-preview: ## Preview image path updates (dry run)
	@echo "🔍 Previewing image path updates..."
	@echo ""
	@source scripts/docker-helper.sh && _dc web bash -c "cd /app && python3 scripts/update-image-paths.py" <<< "1"

docs-update-paths: ## Update all image placeholder paths
	@echo "✏️  Updating image placeholder paths..."
	@echo ""
	@source scripts/docker-helper.sh && _dc web bash -c "cd /app && echo '2' | python3 scripts/update-image-paths.py && echo 'yes' | python3 scripts/update-image-paths.py"

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------

clean: ## Remove cache and generated files
	@rm -rf public/*.* public/admin public/js public/css public/images public/fonts \
		public_collected/*.* public_collected/admin public_collected/js \
		public_collected/css public_collected/images public_collected/fonts \
		.ruff_cache/ .pytest_cache/ .coverage celerybeat-schedule
	@touch public/.keep public_collected/.keep

# -----------------------------------------------------------------------------
# CI/CD
# -----------------------------------------------------------------------------

ci-install-deps: ## Install CI dependencies
	@sudo apt-get install -y curl
	@sudo curl \
		-L https://raw.githubusercontent.com/nickjj/wait-until/v0.2.0/wait-until \
		-o /usr/local/bin/wait-until && sudo chmod +x /usr/local/bin/wait-until

ci-test: ## Run full CI pipeline
	@./scripts/ci-test.sh $(ARGS)

# -----------------------------------------------------------------------------
# Server
# -----------------------------------------------------------------------------

server-connect: ## Connect to production server via SSH
	@if [ -f .env ]; then \
		. .env; \
	fi; \
	local server_ip="$${SERVER_IP:-}"; \
	local server_user="$${SERVER_USER:-root}"; \
	if [ -z "$$server_ip" ]; then \
		echo "❌ SERVER_IP is not set in .env file"; \
		echo ""; \
		echo "Please add the following to your .env file:"; \
		echo "  SERVER_IP=your-server-ip-here"; \
		echo ""; \
		echo "Example:"; \
		echo "  SERVER_IP=147.93.7.60"; \
		echo ""; \
		echo "You can also set SERVER_USER if different from root:"; \
		echo "  SERVER_USER=your-username"; \
		exit 1; \
	fi; \
	echo "🔗 Connecting to server: $$server_user@$$server_ip"; \
	echo ""; \
	ssh "$$server_user@$$server_ip"

# -----------------------------------------------------------------------------
# Deployment
# -----------------------------------------------------------------------------

deploy: ## Run development deployment script
	@echo "🚀 Running development deployment..."
	@chmod +x bin/deploy
	@./bin/deploy

deploy-prod: ## Run production deployment script
	@echo "🚀 Running production deployment..."
	@chmod +x bin/deploy-production.sh
	@./bin/deploy-production.sh

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------

safety-check: ## Check dependencies for security vulnerabilities
	@echo "🔒 Checking dependencies for security vulnerabilities..."
	@source scripts/docker-helper.sh && _dc web safety check

safety-report: ## Generate security report and save to file
	@echo "📊 Generating security report..."
	@source scripts/docker-helper.sh && _dc web safety check --save-json safety-report.json
	@echo "✅ Security report saved to safety-report.json in container"
	@echo "💡 To copy the report to host: make cmd ARGS=\"cp safety-report.json /app/safety-report.json\""

# -----------------------------------------------------------------------------
# Special targets for argument handling
# -----------------------------------------------------------------------------

%:
	@:
