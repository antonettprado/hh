from pathlib import Path
from typing import List, Optional
from core import AnalysisConfig, Reference
from utils import functions, histogram as hist_utils

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
            self._processes = functions.find_mc_processes(self.resultsdir)
        return self._processes
    
    @property 
    def eras(self):
        if self._eras is None:
            self._eras = functions.get_eras(self.resultsdir)
        return self._eras
    
    def get_references(self, channels: Optional[List[str]] = None) -> List[Reference]:
        """Get filtered and sorted references."""
        refs = Reference.get_refs_from(self.resultsdir)
        refs.sort(key=lambda r: (r.channel_base, r.observable_base))
        if channels:
            refs = [ref for ref in refs if ref.channel_base in channels]
        return refs