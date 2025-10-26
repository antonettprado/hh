# Configuration Guide

## How to Customize Your Analysis

### ⚡ Quick Start

**Want to change which channels or eras are combined?**

Just edit **`user_config.py`** - that's it!

```python
# user_config.py

SELECTIONS = {
    '3j_4j': ['SL_3j_resolved', 'SL_4j_resolved'],
    'my_custom_selection': ['channel1', 'channel2'],
}

ERAS_TO_COMBINE = {
    'eras_all': ['2022', '2022EE', '2023', '2023BPix'],
    'my_custom_era': ['2022', '2023'],
}
```

Save the file, run your analysis - done! ✅

---

## Configuration Architecture

### 📁 Files Involved

1. **`user_config.py`** ← **YOU EDIT THIS**
   - User-facing configuration
   - Simple dictionaries
   - Lots of comments and examples

2. **`analysis_config_central.py`** ← **DON'T EDIT**
   - Reads from user_config.py
   - Provides programmatic access
   - Used by all other modules

3. **All other modules** ← **DON'T EDIT**
   - Import from analysis_config_central
   - Automatically use your settings

### 🔄 How It Works

```
user_config.py
    │
    │ (read by)
    ▼
analysis_config_central.py
    │
    │ (imported by)
    ├──▶ workflow.py
    │       ├──▶ datacard_generator.py
    │       ├──▶ fit_orchestrator.py
    │       └──▶ results_organizer.py
    │
    └──▶ SummaryOnlyWorkflow
```

**Result:** Change one file (`user_config.py`), affects entire pipeline!

---

## What You Can Configure

### 1. **Channel Selections** (`SELECTIONS`)

Define which channels should be combined:

```python
SELECTIONS = {
    'selection_name': ['channel1', 'channel2', ...],
}
```

**What this does:**
- Creates combined datacards for these channels
- Creates fit results for the combination
- Creates a summary file named `selection_name.txt`

**Example - Split by jet multiplicity:**
```python
SELECTIONS = {
    '3j': ['SL_3j_resolved', 'SL_res_3j_1b', 'SL_res_3j_2b'],
    '4j': ['SL_4j_resolved', 'SL_res_4j_1b', 'SL_res_4j_2b'],
}
```

### 2. **Era Combinations** (`ERAS_TO_COMBINE`)

Define which eras should be combined:

```python
ERAS_TO_COMBINE = {
    'period_name': ['era1', 'era2', ...],
}
```

**What this does:**
- Creates combined datacards for these eras
- Creates fit results for the combination
- **Note:** Summary files only use `eras_all` by default

**Example - Separate by detector upgrade:**
```python
ERAS_TO_COMBINE = {
    'preEE': ['2022'],
    'postEE': ['2022EE', '2023', '2023BPix'],
    'eras_all': ['2022', '2022EE', '2023', '2023BPix'],
}
```

---

## Common Use Cases

### Use Case 1: Add a New Selection

**Goal:** Combine all high b-tag channels

```python
# In user_config.py

SELECTIONS = {
    # Keep existing selections
    '3j_4j': ['SL_3j_resolved', 'SL_4j_resolved'],
    '3j1b_3j2b_4j1b_4j2b': [
        'SL_res_3j_1b', 'SL_res_3j_2b',
        'SL_res_4j_1b', 'SL_res_4j_2b'
    ],
    
    # Add new selection
    'high_btag': ['SL_res_3j_2b', 'SL_res_4j_2b'],  # NEW!
}
```

**Result:** You'll get a new summary file `high_btag.txt`

### Use Case 2: Combine All Channels

**Goal:** Single selection with everything

```python
SELECTIONS = {
    'all_channels': [
        'SL_3j_resolved',
        'SL_4j_resolved',
        'SL_res_3j_1b',
        'SL_res_3j_2b',
        'SL_res_4j_1b',
        'SL_res_4j_2b'
    ],
}
```

**Result:** Single summary file `all_channels.txt` with all discriminants

### Use Case 3: Test with Fewer Channels

**Goal:** Quick test with just 2 channels

```python
SELECTIONS = {
    'test': ['SL_3j_resolved', 'SL_4j_resolved'],
}

ERAS_TO_COMBINE = {
    'eras_all': ['2022'],  # Only one era for speed
}
```

**Result:** Much faster test run

### Use Case 4: Different Era Groupings

**Goal:** Compare different data-taking periods

```python
ERAS_TO_COMBINE = {
    'early_2022': ['2022'],
    'late_2022': ['2022EE'],
    'all_2023': ['2023', '2023BPix'],
    'eras_all': ['2022', '2022EE', '2023', '2023BPix'],
}
```

**Result:** Separate datacards for each period

---

## Testing Your Configuration

### 1. Quick Syntax Check

```python
# Test your user_config.py
python -c "from user_config import SELECTIONS, ERAS_TO_COMBINE; print('✓ Config is valid')"
```

### 2. View What Will Be Generated

```python
from analysis_config_central import get_selections, get_eras_to_combine

print("Selections:")
for name, channels in get_selections().items():
    print(f"  {name}: {channels}")

print("\nEra combinations:")
for name, eras in get_eras_to_combine().items():
    print(f"  {name}: {eras}")
```

### 3. Test with Summary Only

After a full run, test new selections with summary only:

```bash
# Edit user_config.py with new selections
python run_analysis.py $WORKDIR --summary_only

# Check new summary files
ls fits_new/summary/
```

---

## Advanced: Programmatic Configuration

If you need to set configuration programmatically (e.g., from a script):

```python
from analysis_config_central import configure_analysis

# Set custom configuration
configure_analysis(
    selections={
        'my_selection': ['ch1', 'ch2']
    },
    eras_to_combine={
        'my_era': ['2022', '2023']
    }
)

# Then run workflow
from workflow import AnalysisWorkflow
workflow = AnalysisWorkflow(config)
workflow.run()
```

---

## Troubleshooting

### "No results found" in summary

**Problem:** Summary file shows "⚠ No results found"

**Solutions:**
1. Check selection name matches what's in user_config.py
2. Verify the channels actually exist in your data
3. Check that fits completed successfully
4. Run with `--summary_only` to regenerate

### Import errors

**Problem:** `ImportError: cannot import name 'SELECTIONS'`

**Solutions:**
1. Make sure user_config.py exists in the same directory
2. Check for syntax errors in user_config.py
3. Verify the dictionaries are named `SELECTIONS` and `ERAS_TO_COMBINE`

### Changes not taking effect

**Problem:** Modified user_config.py but nothing changed

**Solutions:**
1. Restart Python (if running interactively)
2. Delete any `.pyc` files: `find . -name "*.pyc" -delete`
3. Check you're editing the right user_config.py file

---

## Best Practices

✅ **DO:**
- Keep selection names descriptive and concise
- Use lowercase with underscores: `low_btag`, `eras_all`
- Include `eras_all` for complete era combination
- Comment your custom selections

❌ **DON'T:**
- Use spaces in selection names
- Use special characters (only letters, numbers, underscores)
- Delete `eras_all` (summary generation expects it)
- Edit analysis_config_central.py directly

---

## Summary

**To customize your analysis:**

1. ✏️ Edit `user_config.py`
2. 💾 Save the file
3. 🚀 Run your analysis
4. ✅ Done!

**No need to edit any other files - the entire pipeline uses your settings automatically!**

---

## Quick Reference

```python
# user_config.py - ONLY FILE YOU NEED TO EDIT

SELECTIONS = {
    'name': ['channel1', 'channel2', ...],
}

ERAS_TO_COMBINE = {
    'name': ['era1', 'era2', ...],
}
```

That's it! 🎉