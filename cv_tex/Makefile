# Makefile for compiling CV
# Usage: make (or make cv.pdf)

MAIN = cv
TEX = $(MAIN).tex
PDF = $(MAIN).pdf

.PHONY: all clean view

all: $(PDF)

$(PDF): $(TEX) references.bib
	@echo "Compiling LaTeX (first pass)..."
	pdflatex -interaction=nonstopmode $(TEX) || true
	@echo "Running biber for bibliography..."
	-biber $(MAIN) || true
	@echo "Compiling LaTeX (second pass)..."
	pdflatex -interaction=nonstopmode $(TEX) || true
	@echo "Compiling LaTeX (third pass for references)..."
	pdflatex -interaction=nonstopmode $(TEX) || true
	@if [ -f $(PDF) ]; then \
		echo "✓ Done! PDF created: $(PDF)"; \
	else \
		echo "✗ Error: PDF was not created. Check cv.log for errors."; \
		exit 1; \
	fi

clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).bcf $(MAIN).log $(MAIN).out $(MAIN).run.xml $(MAIN).toc

cleanall: clean
	rm -f $(PDF)

view: $(PDF)
	open $(PDF)

# Watch mode - recompile on file changes (requires fswatch: brew install fswatch)
watch:
	@echo "Watching for changes. Press Ctrl+C to stop."
	fswatch -o $(TEX) references.bib | while read; do make; done

