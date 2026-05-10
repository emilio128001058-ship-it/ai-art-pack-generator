.PHONY: help run dry-run test test-cov install clean logs

help:
	@echo "AI Art Pack Generator"
	@echo "────────────────────────────────────────"
	@echo "make run           Full pipeline (random theme/style)"
	@echo "make dry-run       Pipeline without API calls"
	@echo "make test          Run test suite"
	@echo "make test-cov      Run tests with coverage report"
	@echo "make install       Install Python dependencies"
	@echo "make clean         Clean output directory"
	@echo "make logs          Show last 5 run logs"
	@echo ""
	@echo "Custom run:"
	@echo "  python scripts/run_automation.py --theme cosmic_nebula --style watercolor --count 50"

install:
	pip install -r requirements.txt pytest pytest-cov

run:
	python scripts/run_automation.py

dry-run:
	python scripts/run_automation.py --dry-run

test:
	python -m pytest tests/ -v --tb=short

test-cov:
	python -m pytest tests/ -v --cov=scripts --cov=utils --cov-report=term-missing

clean:
	python scripts/cleanup.py --clean-logs

logs:
	@ls -lt logs/run_*.json 2>/dev/null | head -5 | awk '{print $$NF}' | xargs -I{} sh -c 'echo "=== {} ===" && python -m json.tool {} | grep -E "(run_id|theme|style|image_count|success|duration)" | head -10'
