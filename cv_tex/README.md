# CV LaTeX Source

This directory contains the LaTeX source files for your CV.

## Files

- `cv.tex` - Main LaTeX document
- `references.bib` - Bibliography file (BibTeX format)

## Compiling the CV

You have several options to compile the CV:

### Option 1: Using Make (Recommended)

```bash
cd cv_tex
make
```

```bash
cd cv_tex
make          # Compile the CV
make view     # Compile and open the PDF
make clean    # Remove build artifacts
```

This will compile the CV and create `cv.pdf`. You can also:

- `make clean` - Remove build artifacts (`.aux`, `.log`, etc.)
- `make cleanall` - Remove build artifacts and the PDF
- `make view` - Compile and open the PDF

### Option 2: Using the compile script

```bash
cd cv_tex
./compile.sh
```

### Option 3: Using VS Code/Cursor with LaTeX Workshop

1. Install the [LaTeX Workshop extension](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop)
2. Open `cv.tex` in Cursor
3. Press `Cmd+Option+B` (or use the LaTeX Workshop commands) to build
4. Press `Cmd+Option+V` to view the PDF

The workspace is already configured with the correct build recipe (pdflatex → biber → pdflatex → pdflatex).

### Option 4: Manual compilation

```bash
cd cv_tex
pdflatex cv.tex
biber cv
pdflatex cv.tex
pdflatex cv.tex
```

## Notes

- The CV uses `biblatex` with `biber` for bibliography management
- The compilation process requires 3 passes of `pdflatex` and 1 pass of `biber` to resolve all references and citations
- Build artifacts (`.aux`, `.log`, etc.) are ignored by git (see `.gitignore`)

