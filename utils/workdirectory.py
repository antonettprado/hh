from pathlib import Path
from typing import Optional
from core.analysis_config import AnalysisConfig
from core.reference import Reference
from utils.functions import get_eras, find_mc_processes, get_refs_from

class WorkDirectory:
    """Manages analysis workspace and data access."""
    
    def __init__(self, path: Path):
        if isinstance(path, str): path = Path(path)
        else:   assert isinstance(path, Path), ValueError("path must be a str or Path")
        self.path = path
        self.resultsdir = self.path / 'results'
        self._processes: list[str] = None
        self._eras: list[str] = None
        self._refs: list[Reference] = None
    
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
    
    @property
    def refs(self) -> list[Reference]:
        if self._refs is None:
            self._refs = get_refs_from(self.resultsdir)
            self._refs.sort(key=lambda r: (r.channel_base, r.observable_base))
        return self._refs

    def get_refs_for(self, channels: list[str]) -> list[Reference]:
        """Get filtered and sorted references."""
        refs = self.refs
        refs = [ref for ref in refs if ref.channel_base in channels]
        return refs