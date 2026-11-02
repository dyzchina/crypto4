.PHONY: all pull panel estimate figs compile anon audit clean

all: pull panel estimate figs compile audit
	@echo "=== v11.0 rebuild complete ==="

# Pulls live endpoints and is therefore skipped by `make all` unless run explicitly.
pull:
	bash scripts/pull_all.sh

anon: compile
	bash scripts/build.sh --anon

panel:
	python scripts/aggregate_panel.py

estimate:
	python scripts/inject_numbers.py
	python scripts/estimator_gradient.py
	python scripts/robustness_gradient.py
	python scripts/emit_robustness_table.py

figs:
	python scripts/fig1_wall_chamber.py
	python scripts/fig2_gradient.py

compile:
	bash scripts/build.sh

audit:
	python audit/audit_wordcount.py
	python audit/audit_ref_check.py
	python audit/audit_sample_period.py
	python audit/audit_captions.py
	python audit/audit_figure_files.py
	python audit/audit_ref_labels.py
	python scripts/audit_macros.py
	python scripts/audit_stale_claims.py

clean:
	rm -f manuscript/*.aux manuscript/*.bbl manuscript/*.blg manuscript/*.log manuscript/*.out
