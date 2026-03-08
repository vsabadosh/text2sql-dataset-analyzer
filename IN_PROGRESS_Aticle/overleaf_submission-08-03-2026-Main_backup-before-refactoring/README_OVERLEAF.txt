===============================================================================
  E-informatica Journal Paper - Overleaf Submission Package
===============================================================================

This package contains all files needed to compile the paper on Overleaf or
any online LaTeX editor.

===============================================================================
QUICK START FOR OVERLEAF
===============================================================================

1. Go to https://www.overleaf.com/ and create a free account

2. Click "New Project" → "Upload Project"

3. Upload the ZIP file containing this folder

4. IMPORTANT: Set the compiler to "LuaLaTeX"
   - Click on "Menu" (top left)
   - Find "Compiler" dropdown
   - Select "LuaLaTeX" (NOT pdfLaTeX!)
   - This is REQUIRED by the E-informatica template

5. Click "Recompile" button

6. Your PDF will be generated!

===============================================================================
FILES INCLUDED
===============================================================================

MAIN FILES:
  text2sql_quality_paper.tex    - Main paper file (641 lines)
  text2sql_quality_paper.bib    - Bibliography (30+ references)

TEMPLATE FILES (from E-informatica):
  einformatica.cls              - Document class (DO NOT MODIFY)
  IEEEtran_for_EI.bst          - Bibliography style (DO NOT MODIFY)
  EISEJ_logo.png               - Journal logo
  ISEJ_logo.png                - Journal logo

FIGURES (in figures/ directory):
  fig1_training_process.pdf     - Training pipeline diagram
  fig2_architecture.pdf         - Five-layer architecture
  fig3_dataflow.pdf            - Data flow diagram
  fig4_dbidentity.pdf          - Database identity normalization
  fig5_semantic_judge.pdf      - Semantic LLM judge architecture
  fig7_prompt.pdf              - LLM prompt structure
  fig8_protocols.pdf           - Protocol-based architecture

  NOTE: These are currently PLACEHOLDER files (empty).
        You need to replace them with actual figures!

===============================================================================
BEFORE YOU SUBMIT TO THE JOURNAL
===============================================================================

1. REPLACE PLACEHOLDER FIGURES with actual diagrams
   - See figures/README.md for specifications

2. UPDATE AUTHOR INFORMATION in text2sql_quality_paper.tex:
   - Your affiliation (line ~66)
   - Your email address (line ~67)
   - Your ORCiD number (line ~68) - Get from https://orcid.org/
   - Submission dates (lines ~56-59)

3. VERIFY ALL CONTENT:
   - Check all tables render correctly
   - Review all equations
   - Verify all citations appear
   - Check figure references

===============================================================================
COMPILATION SETTINGS
===============================================================================

Compiler: LuaLaTeX (REQUIRED - do not use pdfLaTeX!)
Main document: text2sql_quality_paper.tex
BibTeX: Yes (enabled by default in Overleaf)

===============================================================================
TROUBLESHOOTING
===============================================================================

Problem: PDF not generating
Solution: Make sure compiler is set to "LuaLaTeX"

Problem: Bibliography not appearing
Solution: Click "Recompile" twice (Overleaf should do this automatically)

Problem: Figure warnings
Solution: Normal - figures are placeholders and need to be replaced

Problem: Template errors
Solution: Do not modify einformatica.cls or IEEEtran_for_EI.bst

===============================================================================
PAPER STATISTICS
===============================================================================

Pages: ~25 pages (E-informatica format)
Sections: 7 main sections
Tables: 14 tables
Figures: 7 figures (placeholders)
References: 30+ citations
Format: E-informatica Software Engineering Journal

===============================================================================
NEXT STEPS
===============================================================================

1. Upload to Overleaf
2. Set compiler to LuaLaTeX
3. Compile and review PDF
4. Replace placeholder figures
5. Update author information
6. Final review
7. Submit to E-informatica journal!

===============================================================================
SUPPORT
===============================================================================

E-informatica Journal: https://e-informatyka.pl/
Editorial Office: e-informatica@pwr.edu.pl
Overleaf Help: https://www.overleaf.com/learn

===============================================================================
Good luck with your publication!
===============================================================================

