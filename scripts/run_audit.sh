#!/bin/bash
# Quick run script for ViText2SQL audit
# Usage: ./scripts/run_audit.sh [num_samples]

set -e

# Activate venv
source venv/bin/activate

# Default 700 samples
SAMPLES=${1:-700}

echo "=========================================="
echo "Running ViText2SQL Translation Audit"
echo "Samples: $SAMPLES (~10% of dataset)"
echo "=========================================="

# Run audit
python scripts/audit_vitext2sql_noise.py \
  --samples $SAMPLES \
  --output results/audit_results.jsonl \
  --stats results/audit_statistics.json \
  --seed 42

echo ""
echo "=========================================="
echo "✅ Audit Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review results: cat results/audit_results.jsonl | jq ."
echo "2. Sample for validation:"
echo "   python scripts/manual_validation_sampler.py \\"
echo "     --input results/audit_results.jsonl \\"
echo "     --num 100"
echo ""
echo "3. Check statistics: cat results/audit_statistics.json"
echo "4. LaTeX table: results/audit_statistics_table.tex"
echo ""
