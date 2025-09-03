from pathlib import Path
from typing import Optional
from core import AnalysisConfig, Reference
from utils.functions import get_eras, find_mc_processes, get_refs_from

class WorkDirectory:
    """Manages analysis workspace and data access."""
    
    def __init__(self, path: Path):
        if isinstance(path, str): path = Path(path)
        else:   assert isinstance(path, Path), ValueError("path must be a str or Path")
        self.path = path
        self.resultsdir = self.path / 'results'
        self._processes = None
        self._eras = None
    
    @property
    def processes(self):
        if self._processes is None:
            self._processes = find_mc_processes(self.resultsdir)
        return self._processes
    
    @property 
    def eras(self):
        if self._eras is None:
            self._eras = get_eras(self.resultsdir)
        return self._eras
    
    def get_references(self, channels: Optional[list[str]] = None) -> list[Reference]:
        """Get filtered and sorted references."""
        refs: list[Reference] = get_refs_from(self.resultsdir)
        refs.sort(key=lambda r: (r.channel_base, r.observable_base))
        if channels:
            refs = [ref for ref in refs if ref.channel_base in channels]
        return refs