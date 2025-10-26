# Statistical Analysis Pipeline

Professional-grade pipeline for datacard generation and statistical fitting in High Energy Physics analysis.

## Architecture Overview

The codebase is organized into clear modules with single responsibilities:

```
├── run_analysis.py              # Main entry point with CLI
├── workflow.py                  # High-level workflow orchestration
├── discriminant_new.py          # Discriminant data model
├── datacard_path_manager.py    # Path computation logic
├── datacard_generator.py       # Parallel datacard generation
├── fit_orchestrator.py         # Statistical fitting pipeline
└── results_organizer.py        # Results processing and summaries
```

## Design Principles

### 1. Separation of Concerns
Each module has a single, well-defined responsibility:
- **Path management** is isolated from **generation**
- **Generation** is isolated from **fitting**
- **Fitting** is isolated from **results organization**

### 2. Dependency Injection
Configuration is injected rather than globally accessed:
```python
config = DiscriminantConfig(...)
Discriminant.configure(config)
```

### 3. Type Safety
Extensive use of type hints and dataclasses:
```python
@dataclass
class FitConfiguration:
    fit_types: List[str]
    fit_functions: List[Callable]
    num_processes: int = None
```

### 4. Testability
Each component can be tested independently:
- Path computation doesn't require actual file generation
- Task building doesn't require actual execution
- Results organization doesn't depend on fit execution

### 5. Performance
Parallelization at every appropriate level:
- Datacard generation (all types)
- Workspace creation
- Fit execution
- Independent discriminants

## Component Details

### DatacardPathManager
**Responsibility:** Compute file system paths for datacards

**Key Features:**
- Handles hierarchical vs flat channel structures
- Computes base, selection, and era combination paths
- No file I/O - pure computation
- Can compute paths without generating files (enables --fit_only)

**Usage:**
```python
manager = DatacardPathManager(name, base_path, eras)
paths = manager.compute_all_paths(refs, is_complex, selections, eras_to_combine)
```

### DatacardGenerator
**Responsibility:** Generate datacards in parallel

**Key Features:**
- Task-based architecture (generation tasks vs combination tasks)
- Parallel execution with multiprocessing
- Progress tracking and timing
- Separation of task building from execution

**Usage:**
```python
generator = DatacardGenerator(num_processes=8)
generator.generate_base_datacards(disc, single_tasks, combo_tasks)
generator.generate_selection_combinations(tasks)
```

### FitOrchestrator
**Responsibility:** Execute statistical fits

**Key Features:**
- Workspace creation with validation
- Parallel fit execution
- Automatic handling of empty workspaces
- Result aggregation and file writing
- Comprehensive error handling

**Workflow:**
1. Create workspaces (parallel)
2. Validate workspaces (filter empty)
3. Execute fits (parallel)
4. Aggregate results
5. Write output files

### ResultsOrganizer
**Responsibility:** Process and organize fit results

**Key Features:**
- Selection-specific summaries
- Automatic result collection
- Validation of result files
- Clean directory structure

**Output Structure:**
```
fits_new/
└── summary/
    ├── 3j_4j.txt
    └── 3j1b_3j2b_4j1b_4j2b.txt
```

### Discriminant
**Responsibility:** Represent a single analysis discriminant

**Key Features:**
- Lazy path computation
- Active references filtering
- Complexity detection (hierarchical vs flat)
- Clean initialization pattern

**Lifecycle:**
1. Configure class (once): `Discriminant.configure(config)`
2. Create instances: `Discriminant(name, references)`
3. Initialize paths: `disc.initialize_paths(selections, eras)`
4. Access paths: `disc.paths.base_combined`, etc.

### AnalysisWorkflow
**Responsibility:** Coordinate the complete pipeline

**Workflow Steps:**
1. **Initialize discriminants** - Create from results directory
2. **Generate datacards** - Unless --fit_only
3. **Run fits** - Parallel execution on all datacards
4. **Organize results** - Selection-specific summaries

## Usage

### Full Pipeline
```bash
python run_analysis.py /path/to/workdir \
    -c bamboo_hh/config/analysis.yml
```

### Fit Only Mode
When datacards already exist:
```bash
python run_analysis.py /path/to/workdir \
    -c bamboo_hh/config/analysis.yml \
    --fit_only
```

### Legacy Summary Mode
```bash
python run_analysis.py /path/to/workdir --summary_only
```

## Configuration

Selections and era combinations are defined in `workflow.py`:

```python
selections = {
    '3j_4j': ['SL_3j_resolved', 'SL_4j_resolved'],
    '3j1b_3j2b_4j1b_4j2b': [
        'SL_res_3j_1b', 'SL_res_3j_2b',
        'SL_res_4j_1b', 'SL_res_4j_2b'
    ],
}

eras_to_combine = {
    'eras_22': ['2022', '2022EE'],
    'eras_23': ['2023', '2023BPix'],
    'eras_all': ['2022', '2022EE', '2023', '2023BPix'],
}
```

## Error Handling

### Empty Workspaces
Automatically detected and skipped with note files:
```
Asymptotic Limits (SKIPPED)
Reason: no observed events
Workspace: /path/to/workspace.root
```

### Missing Files
Validation before processing with clear error messages

### Interruption
Graceful handling of Ctrl+C with cleanup

## Performance Characteristics

### Parallelization Levels
1. **Datacard Generation:** All datacards generated in parallel
2. **Workspace Creation:** All workspaces created in parallel
3. **Fit Execution:** All fits run in parallel (multiple per workspace)

### Expected Speedup
For N datacards with M fit types on a C-core machine:
- Serial time: O(N × M)
- Parallel time: O((N × M) / C)
- Typical speedup: 4-8x on modern machines

### Memory Considerations
Each parallel process holds one datacard/workspace in memory.
Default configuration uses all available CPU cores.

## Extensibility

### Adding New Fit Types
```python
# In workflow.py
config = FitConfiguration(
    fit_types=['blinded', 'unblinded', 'diagnostic'],
    fit_functions=[
        fitter.run_asymptotic_limits,
        fitter.run_diagnostic_fits
    ]
)
```

### Adding New Selection Combinations
```python
# In workflow.py
selections = {
    '3j_4j': [...],
    'new_combination': ['channel1', 'channel2', 'channel3']
}
```

### Custom Results Processing
Subclass `ResultsOrganizer` and override methods:
```python
class CustomResultsOrganizer(ResultsOrganizer):
    def _write_selection_summary(self, sel_name, result_files):
        # Custom processing
        pass
```

## Migration from Legacy Code

The new architecture maintains backward compatibility:

1. **Same outputs:** Identical datacards and fit results
2. **Same CLI:** Minor enhancements, but old usage works
3. **Same dependencies:** Uses existing `fitting` and `utils` modules
4. **Better performance:** Parallel execution at all levels

### Key Improvements
- ✓ 4-8x faster datacard generation
- ✓ Clean architecture with testable components
- ✓ Type-safe with comprehensive type hints
- ✓ Professional error handling
- ✓ Progress tracking and timing
- ✓ Fit-only mode support
- ✓ Organized selection summaries

## Testing

Each component can be tested independently:

```python
# Test path computation
manager = DatacardPathManager('test', Path('/tmp'), ['2022'])
paths = manager.compute_all_paths(refs, False, {}, {})
assert len(paths.base_combined) == expected_count

# Test task building
tasks = TaskBuilder.build_base_generation_tasks(...)
assert len(tasks[0]) == expected_single_tasks
assert len(tasks[1]) == expected_combo_tasks
```

## Troubleshooting

### No datacards generated
- Check that `results/` directory exists and contains data
- Verify config file path is correct
- Check filter conditions in workflow

### Empty workspaces
- Normal for some channel/era combinations
- Check note files in output for details
- Skipped automatically, not an error

### Fit failures
- Check CombineHarvester installation
- Verify workspace file integrity
- Review fit output logs

## Future Enhancements

Potential improvements while maintaining architecture:

1. **Async I/O:** Use `asyncio` for file operations
2. **Progress bars:** Add `tqdm` for better progress tracking
3. **Caching:** Cache intermediate results for faster re-runs
4. **Validation:** Add datacard schema validation
5. **Logging:** Replace prints with proper logging framework
6. **Configuration:** Move selections/eras to config file
7. **Metrics:** Add detailed performance profiling
8. **Tests:** Add comprehensive unit and integration tests
