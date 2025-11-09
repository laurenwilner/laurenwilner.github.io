#!/bin/bash
# Simple compilation script for CV
# Usage: ./compile.sh

set -e  # Exit on error

cd "$(dirname "$0")"

MAIN="cv"

echo "Compiling CV..."
echo "Step 1/4: First pdflatex pass..."
pdflatex -interaction=nonstopmode "$MAIN.tex" || true

echo "Step 2/4: Running biber for bibliography..."
if [ -f "$MAIN.bcf" ]; then
    biber "$MAIN" || true
else
    echo "No .bcf file found, skipping biber"
fi

echo "Step 3/4: Second pdflatex pass..."
pdflatex -interaction=nonstopmode "$MAIN.tex" || true

echo "Step 4/4: Third pdflatex pass (for references)..."
pdflatex -interaction=nonstopmode "$MAIN.tex" || true

if [ -f "$MAIN.pdf" ]; then
    echo "✓ Success! PDF created: $MAIN.pdf"
    # Optionally open the PDF
    # open "$MAIN.pdf"
else
    echo "✗ Error: PDF was not created. Check the log file for errors."
    exit 1
fi

