# LLM-as-a-Judge Semantic Validation Analyzer

## Overview

The `semantic_llm_annot` analyzer uses multiple LLM voters to evaluate whether a SQL query semantically answers the given natural language question for a specific database schema. This provides human-like semantic validation beyond syntax and execution checks.

## Features

- **Multi-Voter Consensus**: Uses multiple LLM models to vote on correctness
- **Weighted Voting**: Each model can have a weight for more nuanced consensus
- **Multiple Providers**: Supports OpenAI, Anthropic, Gemini, and Ollama
- **Configurable Prompts**: Two built-in prompt variants + custom prompt support
- **Status Determination**: Automatic status based on voter consensus

## Architecture

### Components

1. **SemanticLLMAnnot** - Main analyzer implementing `AnnotatingAnalyzer` protocol
2. **PromptTemplateResolver** - Resolves prompt templates with dynamic parameters
3. **Provider System** - Abstraction layer for different LLM providers
4. **Metrics** - Structured metric events with voter results and features
5. **Smart DDL Generation** - Extracts only tables used in query with example data

### Voting System

Each configured LLM model acts as a voter and returns one of three verdicts:

- `CORRECT` - Query fully answers the question
- `PARTIALLY_CORRECT` - Query mostly correct but missing minor details
- `INCORRECT` - Query is logically wrong or doesn't answer the question

### Status Determination

The analyzer determines overall status based on aggregated votes:

- **ok**: All voters respond with `CORRECT`
- **warns**: At least one voter disagrees (but not majority `INCORRECT`)
- **errors**: Majority of voters respond with `INCORRECT`
- **failed**: Unable to evaluate (missing data, all LLMs failed, etc.)

## Configuration

### Basic Configuration

Add to your `configs/pipeline.example.yaml`:

```yaml
analyze:
  - name: semantic_llm_annot
    params:
      prompt_variant: default  # Options: variant_1, variant_2, default
      temperature: 0.0
      num_examples: 2  # Number of example values per column in DDL (default: 2)
      skip_on_empty_providers: true  # Skip if no providers configured
      providers:
        - name: openai
          api_key: "${OPENAI_API_KEY}"
          models:
            - name: gpt-4o
              weight: 1.0
```

### Smart DDL Generation

The analyzer uses intelligent DDL schema generation that:

1. **Extracts only referenced tables** from the SQL query (saves tokens)
2. **Includes example data** for each column (helps LLMs understand data types and patterns)
3. **Formats with inline comments** for readability

Example generated DDL:

```sql
CREATE TABLE People (
    person_id INTEGER NOT NULL /* ex: [111, 121] */,
    first_name VARCHAR(255) /* ex: ['Shannon', 'Virginie'] */,
    middle_name VARCHAR(255) /* ex: ['Elissa', 'Jasmin'] */,
    last_name VARCHAR(255) /* ex: ['Senger', 'Hartmann'] */,
    email_address VARCHAR(40) /* ex: ['javier.trantow@example.net', 'boyer.lonie@example.com'] */,
    PRIMARY KEY (person_id)
);

CREATE TABLE Students (
    student_id INTEGER NOT NULL /* ex: [111, 121] */,
    student_details VARCHAR(255) /* ex: ['Marry', 'Martin'] */,
    PRIMARY KEY (student_id),
    FOREIGN KEY (student_id) REFERENCES People (person_id)
);
```

This approach:
- **Reduces token usage** by only including relevant tables
- **Provides context** through example values
- **Improves accuracy** by showing actual data patterns

### Provider Configuration

#### OpenAI

```yaml
- name: openai
  api_key: "${OPENAI_API_KEY}"  # Or set OPENAI_API_KEY env var
  models:
    - name: gpt-4o
      weight: 1.0
    - name: gpt-4-turbo
      weight: 1.0
```

#### Anthropic

```yaml
- name: anthropic
  api_key: "${ANTHROPIC_API_KEY}"  # Or set ANTHROPIC_API_KEY env var
  models:
    - name: claude-3-5-sonnet-20241022
      weight: 1.0
```

#### Gemini

```yaml
- name: gemini
  api_key: "${GEMINI_API_KEY}"  # Or set GEMINI_API_KEY or GOOGLE_API_KEY env var
  models:
    - name: gemini-1.5-pro
      weight: 1.0
```

#### Ollama (Local)

```yaml
- name: ollama
  base_url: "http://localhost:11434"
  models:
    - name: llama3
      weight: 1.0
    - name: mistral
      weight: 1.0
```

### Prompt Variants

#### Variant 1 (Simple)
Basic semantic evaluation focusing on correctness.

#### Variant 2 (Comprehensive - Default)
Assumes SQL is parseable and executable, focuses only on semantic correctness with detailed decision rules:
- Filters, joins, and cardinality
- Aggregation and window functions
- NULL handling and DISTINCT
- Ordering and limits
- Date/time boundaries

#### Custom Prompt

```yaml
- name: semantic_llm_annot
  params:
    custom_prompt: |
      Your custom prompt here with placeholders:
      {{dialect}}, {{ddl_schema}}, {{natural_question}}, {{sql_to_revise}}
```

## Output Metrics

### Features (Aggregatable)

```python
{
  "total_voters": 3,
  "voters_correct": 2,
  "voters_partially_correct": 1,
  "voters_incorrect": 0,
  "voters_failed": 0,
  "weighted_score": 0.833,  # 0.0-1.0 scale
  "consensus_reached": False,
  "consensus_verdict": None
}
```

### Stats (Detailed)

```python
{
  "voter_results": [
    {
      "model": "gpt-4o",
      "provider": "openai",
      "verdict": "CORRECT",
      "explanation": "",
      "weight": 1.0,
      "error": None
    },
    # ... more voters
  ],
  "prompt_used": "...",
  "temperature": 0.0,
  "collect_ms": 1234.56
}
```

### Tags (Context)

```python
{
  "dialect": "sqlite",
  "prompt_variant": "default"
}
```

## Item Annotation

The analyzer adds metadata to each item:

```python
{
  "analysisSteps": [
    {
      "name": "semantic_llm_judge",
      "status": "ok",
      "consensus_verdict": "CORRECT",
      "weighted_score": 1.0
    }
  ]
}
```

## Usage Examples

### Example 1: Single Provider

```yaml
- name: semantic_llm_annot
  params:
    providers:
      - name: openai
        api_key: "${OPENAI_API_KEY}"
        models:
          - name: gpt-4o
            weight: 1.0
```

### Example 2: Multi-Provider Consensus

```yaml
- name: semantic_llm_annot
  params:
    providers:
      - name: openai
        api_key: "${OPENAI_API_KEY}"
        models:
          - name: gpt-4o
            weight: 1.0
      
      - name: anthropic
        api_key: "${ANTHROPIC_API_KEY}"
        models:
          - name: claude-3-5-sonnet-20241022
            weight: 1.0
      
      - name: gemini
        api_key: "${GEMINI_API_KEY}"
        models:
          - name: gemini-1.5-pro
            weight: 1.0
```

### Example 3: Weighted Voting

```yaml
- name: semantic_llm_annot
  params:
    providers:
      - name: openai
        api_key: "${OPENAI_API_KEY}"
        models:
          - name: gpt-4o
            weight: 2.0  # Higher weight for more advanced model
          - name: gpt-4-turbo
            weight: 1.0
```

## Dependencies

### Required Dependencies

- `openai` - For OpenAI provider
- `anthropic` - For Anthropic provider
- `google-generativeai` - For Gemini provider
- `requests` - For Ollama provider (usually pre-installed)

### Installation

```bash
# Install specific provider dependencies
pip install openai anthropic google-generativeai

# Or install all at once
pip install openai anthropic google-generativeai
```

## Error Handling

The analyzer handles various failure scenarios gracefully:

1. **Missing API Keys**: Providers without valid API keys are skipped
2. **LLM Failures**: Failed voters are counted separately in metrics
3. **Invalid JSON Responses**: Treated as failed votes
4. **Missing Data**: Items without SQL/question/dbId are marked as failed
5. **Schema Errors**: DDL schema extraction failures are reported

## Performance Considerations

- **Sequential Voting**: Voters are queried sequentially (not parallel)
- **Timeout**: Default timeout is 600s per provider (configurable in provider)
- **Rate Limits**: Consider provider rate limits when configuring multiple models
- **Cost**: Each item is evaluated by all configured models (can be expensive)

## Best Practices

1. **Start Small**: Test with 1-2 providers first
2. **Use Temperature 0.0**: For consistent deterministic results
3. **Weight Models**: Give higher weights to more reliable models
4. **Monitor Costs**: Track API usage and costs
5. **Consensus Threshold**: Use 3+ voters for reliable consensus
6. **Prompt Selection**: Use variant_2 (default) for comprehensive evaluation

## Troubleshooting

### No Providers Configured

If `skip_on_empty_providers: true`, the analyzer will skip without error. Set to `false` to fail explicitly.

### All Voters Failed

Check:
- API keys are set correctly
- Network connectivity to provider APIs
- Provider API status
- Rate limits not exceeded

### Unexpected Verdicts

- Review `voter_results` in stats for individual explanations
- Check if DDL schema is complete and accurate
- Verify prompt variant is appropriate for your use case

## Integration with Pipeline

The analyzer integrates seamlessly with the pipeline:

1. **Input**: Receives `DataItem` with `question`, `sql`, `dbId`
2. **Processing**: 
   - Gets DDL schema from `DbManager`
   - Resolves prompt template
   - Queries all configured LLM voters
   - Aggregates results
3. **Output**:
   - Emits `LLMJudgeMetricEvent` to sink
   - Annotates item with results
   - Yields item to next stage

## Future Enhancements

Potential improvements:

- Parallel voting for faster execution
- Caching of DDL schemas
- Support for more LLM providers (Azure OpenAI, AWS Bedrock, etc.)
- Custom verdict weights per provider
- Configurable consensus thresholds
- Retry logic for failed voters

