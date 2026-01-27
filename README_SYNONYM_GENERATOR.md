# LLM-Based Synonym Generation - Usage Guide

## Overview

The synonym generation system has been successfully migrated from hard-coded dictionaries to dynamic LLM-based generation. This provides more contextually relevant and flexible synonyms for your Power BI semantic model.

## Quick Start

### Testing Without Power BI

Since you cannot run the full pipeline with Power BI, use the comprehensive test script:

```bash
# Run unit tests on sample fields
python test_synonym_generator.py --mode unit

# Run quality checks
python test_synonym_generator.py --mode quality

# Compare with old hard-coded synonyms
python test_synonym_generator.py --mode compare

# Test with your actual TMDL files
python test_synonym_generator.py --mode integration

# Generate synonyms for all fields (expensive - many API calls)
python test_synonym_generator.py --mode batch
```

## Architecture

### Components Created

1. **`agents/synonym_generator.py`** - New agent that generates synonyms using LLM
   - `agent_generate_synonyms()` - Generate synonyms for a single field
   - `batch_generate_synonyms()` - Generate for multiple fields

2. **`discovery/linguistic.py`** - Modified to use the agent
   - Replaced hard-coded dictionaries with agent calls
   - Maintains same interface and return types
   - Includes fallback mechanism

3. **`test_synonym_generator.py`** - Comprehensive testing suite
   - 5 different test modes
   - Quality validation
   - Comparison tools

4. **`config/settings.py`** - New configuration options
   - `ENABLE_LLM_SYNONYMS` - Toggle LLM vs fallback
   - `SYNONYM_MODEL` - Model to use
   - `SYNONYM_CACHE_PATH` - Cache location (future enhancement)

## How It Works

### Measure Fields (Numeric)

For measure fields like `sales`, `cost`, `quantity`:
- Uses a specialized prompt focusing on QUANTITATIVE concepts
- Includes aggregation terms (total, sum, count, amount)
- Prevents categorical/descriptive terms
- Example: `"sales"` → `["amount", "income", "revenue", "sales", "total sales", "turnover"]`

### Dimension Fields (Categorical)

For dimension fields like `product`, `country`, `date`:
- Uses a specialized prompt focusing on CATEGORICAL concepts
- Includes descriptive/classification terms
- Prevents numeric/aggregation terms
- Example: `"country"` → `["country", "geography", "locale", "nation", "region", "territory"]`

### Fallback Mechanism

If the LLM fails or returns invalid results:
```python
clean = name.lower()
variants = {
    clean,
    clean.replace("_", " "),
    clean.replace("-", " ")
}
return sorted(variants)
```

## Validation & Quality Checks

The test script includes comprehensive quality checks:

1. **No Duplicates** - Ensures synonym lists are deduplicated
2. **No Empty Values** - Validates all synonyms are non-empty strings
3. **Numeric Leakage Prevention** - Ensures dimensions don't get numeric terms
4. **Synonym Count** - Validates reasonable number of synonyms (2-15)
5. **Original Field Inclusion** - Ensures basic field name variants are included

## Configuration

### Enable/Disable LLM Synonyms

In `config/settings.py`:
```python
ENABLE_LLM_SYNONYMS = True  # Set to False to disable
```

### Change Model

```python
SYNONYM_MODEL = "llama-3.3-70b-versatile"  # Default
# Or use a different model:
# SYNONYM_MODEL = "gpt-4"
```

## Best Practices

### Testing Recommendations

1. **Start with Unit Tests**
   ```bash
   python test_synonym_generator.py --mode unit
   ```
   This tests the core functionality with 6 sample fields.

2. **Run Quality Checks**
   ```bash
   python test_synonym_generator.py --mode quality
   ```
   This validates that synonyms meet quality criteria.

3. **Compare with Original**
   ```bash
   python test_synonym_generator.py --mode compare
   ```
   This shows differences between LLM and hard-coded synonyms.

4. **Integration Test** (uses your actual data)
   ```bash
   python test_synonym_generator.py --mode integration
   ```
   This generates linguistic metadata with your TMDL files.

### When to Use Batch Mode

Only use batch mode when:
- You want to pre-generate all synonyms
- You're willing to make many API calls (one per field)
- You want to review/approve synonyms before use

```bash
python test_synonym_generator.py --mode batch
```

This will:
- Generate synonyms for every field in your dataset
- Save results to `batch_synonyms_output.json`
- Allow you to review and modify if needed

## Verification Results

### Unit Tests
✅ **6/6 tests passed**
- Measures: `sales`, `total_cost`, `quantity`
- Dimensions: `product_name`, `country`, `order_date`
- All generated appropriate synonyms with correct separation

### Quality Checks
✅ **All quality checks passed**
- ✓ No duplicates found
- ✓ No empty values
- ✓ No numeric leakage to dimensions
- ✓ Appropriate synonym counts

## Example Output

### Measure Example: "sales"
```python
# LLM-generated synonyms:
["amount", "income", "revenue", "sales", "total sales", "turnover"]

# Old hard-coded:
["sales", "revenue", "turnover"]

# Improvement: Added "amount", "income", "total sales" for better query flexibility
```

### Dimension Example: "country"
```python
# LLM-generated synonyms:
["country", "geography", "locale", "nation", "region", "territory"]

# Old hard-coded:
["country", "geo", "market", "region"]

# Improvement: Added "geography", "locale", "nation", "territory" while maintaining core terms
```

## Integration with Pipeline

The synonym generator integrates seamlessly into your existing pipeline:

```python
# In pipeline.py - no changes needed!
linguistic = generate_linguistic_metadata(index)
```

The `generate_linguistic_metadata()` function now:
1. Calls the synonym generator agent for each field
2. Maintains the same output structure
3. Includes debug output for verification
4. Falls back gracefully on errors

## Troubleshooting

### Issue: "Too few synonyms"
**Cause**: LLM returned limited results or API failure  
**Solution**: Check API key, network connection, or use fallback mode

### Issue: "Numeric leakage detected"
**Cause**: LLM incorrectly added numeric terms to dimensions  
**Solution**: This should be rare; the prompts explicitly prevent this. If it occurs, file an issue.

### Issue: "Agent generation failed"
**Cause**: LLM API error  
**Solution**: The system automatically falls back to basic expansion. Check logs for details.

## Performance Considerations

### API Calls
- Each field requires 1 API call
- For a dataset with 50 fields, that's 50 API calls
- Consider using batch mode during off-hours

### Caching (Future Enhancement)
Currently, synonyms are regenerated each time. Future versions will include:
- Cache generated synonyms to disk
- Reuse cached synonyms unless schema changes
- Manual cache invalidation option

## Next Steps

1. ✅ Basic implementation complete
2. ✅ Testing framework in place
3. ✅ Quality validation working
4. 🔄 Run integration test with your full dataset
5. 🔄 Review generated synonyms
6. 🔄 When ready, test with Power BI pipeline

## Files Modified

| File | Type | Description |
|------|------|-------------|
| `agents/synonym_generator.py` | NEW | LLM-based synonym generation agent |
| `discovery/linguistic.py` | MODIFIED | Uses agent instead of hard-coded dicts |
| `config/settings.py` | MODIFIED | Added synonym configuration |
| `test_synonym_generator.py` | NEW | Comprehensive test suite |

## Support

If you encounter issues:
1. Check test outputs for detailed error messages
2. Review the debug output from `linguistic.py`
3. Try fallback mode: `ENABLE_LLM_SYNONYMS = False`
4. Examine `batch_synonyms_output.json` for field-level details
