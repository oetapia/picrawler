# Makefile for PiCrawler Development
# Provides convenient shortcuts for common development tasks

.PHONY: help encoding-check encoding-fix encoding-check-all test clean

# Default target
help:
	@echo "PiCrawler Development Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make encoding-check       - Check Python files for Unicode encoding issues"
	@echo "  make encoding-fix         - Fix encoding issues in Python files"
	@echo "  make encoding-check-all   - Check ALL Python files (including examples)"
	@echo "  make test                 - Run diagnostic tests"
	@echo "  make clean                - Remove backup files and Python cache"
	@echo ""
	@echo "Examples:"
	@echo "  make encoding-fix         - Fix all production code"
	@echo "  make encoding-check       - Preview changes without modifying"
	@echo "  make clean                - Clean up backup files"

# Check encoding in production files (dry-run)
encoding-check:
	@echo "🔍 Checking encoding in production files..."
	@echo ""
	@python3 tools/fix_encoding.py components/ --dry-run
	@echo ""
	@python3 tools/fix_encoding.py manual_control/ --dry-run
	@echo ""
	@python3 tools/fix_encoding.py self_aware/ --dry-run
	@echo ""
	@echo "✅ Encoding check complete!"
	@echo "   To fix issues, run: make encoding-fix"

# Fix encoding in production files
encoding-fix:
	@echo "🔧 Fixing encoding in production files..."
	@echo ""
	@python3 tools/fix_encoding.py components/
	@echo ""
	@python3 tools/fix_encoding.py manual_control/
	@echo ""
	@python3 tools/fix_encoding.py self_aware/
	@echo ""
	@echo "✅ Encoding fixes applied!"
	@echo "   Backup files created with .backup extension"
	@echo "   Review changes and commit when ready"

# Check encoding in ALL Python files (including examples)
encoding-check-all:
	@echo "🔍 Checking encoding in ALL Python files..."
	@echo ""
	@python3 tools/fix_encoding.py . --dry-run
	@echo ""
	@echo "✅ Full encoding check complete!"

# Run diagnostic tests
test:
	@echo "🧪 Running diagnostic tests..."
	@python3 components/diagnostic.py --list
	@echo ""
	@echo "To run a specific test:"
	@echo "  python3 components/diagnostic.py --test <test-id>"

# Clean backup files and Python cache
clean:
	@echo "🧹 Cleaning backup files and cache..."
	@find . -name "*.backup" -type f -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete
	@echo "✅ Clean complete!"
