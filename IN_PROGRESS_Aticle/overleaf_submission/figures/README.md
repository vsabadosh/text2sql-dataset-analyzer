# Figures for Text-to-SQL Quality Assessment Paper

This directory should contain the following figures referenced in the paper:

## Required Figures

### 1. **fig1_training_process.pdf**
- **Description**: Complete training pipeline for LLMs in Text-to-SQL systems
- **Content**: Diagram showing three key components:
  1. Training dataset (with triplets: {natural language question, database schema, target SQL query})
  2. Supervised fine-tuning step
  3. Evaluation on held-out test set
- **Suggested tool**: Draw.io, PowerPoint, or similar diagramming tool
- **Format**: PDF (vector graphics preferred)

### 2. **fig2_architecture.pdf**
- **Description**: Five-layer architecture of the text2sql-pipeline system
- **Content**: Layered diagram showing:
  - Input Layer (SpiderLoader, JSONLLoader, CSVLoader, DuckDBLoader)
  - Normalization Layer (Alias Mapper, Field Enricher, Database Identity Normalizer)
  - Analysis Layer (5 analyzers: Schema, Syntax, Execution, Antipattern, Semantic LLM)
  - Output Layer (Annotated Dataset, Metrics Database)
  - Report Generation Layer (Markdown reports)
- **Suggested tool**: Draw.io, Lucidchart, or similar
- **Format**: PDF (vector graphics)

### 3. **fig3_dataflow.pdf**
- **Description**: Data flow through the pipeline from input to output
- **Content**: Flowchart showing:
  - Record loading → Normalization → Analysis (parallel analyzers) → Output streams
  - Show streaming/iterator pattern
  - Indicate parallel processing of analyzers
- **Suggested tool**: Draw.io, Visio, or similar
- **Format**: PDF (vector graphics)

### 4. **fig4_dbidentity.pdf**
- **Description**: DbIdentity normalization process
- **Content**: Decision tree diagram with three branches:
  1. Has dbId → Health check → Pass/Fail → Proceed/Recreate
  2. No dbId but has DDL → Hash DDL → Check exists → Create if needed
  3. No dbId, no DDL → ValueError
- **Suggested tool**: Draw.io, Lucidchart
- **Format**: PDF (vector graphics)

### 5. **fig5_semantic_judge.pdf**
- **Description**: Architecture of the Semantic LLM Judge with multi-model consensus voting
- **Content**: System diagram showing:
  - Input: Question + SQL + Schema
  - Smart DDL Generation stage
  - Prompt Template Resolution
  - Parallel LLM queries (OpenAI, Anthropic, Google, Ollama)
  - Consensus voting mechanism
  - Output: Consensus verdict
- **Suggested tool**: Draw.io, PowerPoint
- **Format**: PDF (vector graphics)

### 6. **fig7_prompt.pdf**
- **Description**: LLM prompt structure
- **Content**: Template showing:
  - Input parameters: {{question}}, {{sql}}, {{ddl_schema}}, {{dialect}}
  - Evaluation criteria
  - Output format: JSON with "verdict" and "explanation"
  - Four verdict categories: CORRECT, PARTIALLY_CORRECT, INCORRECT, UNANSWERABLE
- **Suggested tool**: Text editor with code formatting, then export to PDF
- **Format**: PDF

### 7. **fig8_protocols.pdf**
- **Description**: Protocol-based architecture with automatic dependency injection
- **Content**: UML-style diagram showing:
  - Protocol interfaces: AnnotatingAnalyzer, MetricsSink, Normalizer, DbAdapter
  - Concrete implementations
  - Dependency injection container
  - Relationships between components
- **Suggested tool**: PlantUML, Draw.io, or UML tool
- **Format**: PDF (vector graphics)

## Creating Placeholder Figures

For initial compilation testing, you can create simple placeholder PDFs with the figure names as text.

## Tips for Creating Figures

1. **Use vector graphics** (PDF, SVG converted to PDF) rather than raster images for better quality
2. **Keep fonts readable** - minimum 8-10pt in the final PDF
3. **Use consistent styling** across all figures
4. **Keep color scheme professional** - consider colorblind-friendly palettes
5. **Add clear labels** to all components and arrows
6. **Export at high resolution** if using raster elements

## Recommended Tools

- **Draw.io (diagrams.net)**: Free, web-based, excellent for flowcharts and architecture diagrams
- **Microsoft PowerPoint/Keynote**: Good for process diagrams and simple illustrations
- **PlantUML**: Excellent for UML diagrams and protocol relationships
- **Inkscape**: Free vector graphics editor
- **Adobe Illustrator**: Professional vector graphics (paid)

## Extracting Figures from Your Word Document

If your original Word document contains these figures as images:
1. Open the document in Word
2. Right-click on each figure → "Save as Picture"
3. Save as PNG or JPEG
4. Convert to PDF using:
   - Online tools (e.g., png2pdf.com)
   - ImageMagick: `convert figure.png figure.pdf`
   - Python PIL: See conversion script below

## Python Script to Convert Images to PDF

```python
from PIL import Image

def convert_image_to_pdf(image_path, output_path):
    """Convert an image file to PDF."""
    image = Image.open(image_path)
    # Convert to RGB if needed (for PNG with transparency)
    if image.mode in ('RGBA', 'LA', 'P'):
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
        image = rgb_image
    image.save(output_path, 'PDF', resolution=100.0)
    print(f"Converted {image_path} to {output_path}")

# Example usage:
# convert_image_to_pdf('figure1.png', 'figures/fig1_training_process.pdf')
```

