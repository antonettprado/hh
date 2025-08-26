import uproot
from dataclasses import dataclass, field
from pathlib import Path
from references.constants import *

@dataclass(frozen=True, eq=True)
class Reference:
    name: str

    channel: str = field(init=False)
    observable: str = field(init=False)
    channel_base: str = field(init=False)
    channel_sub: str = field(init=False)
    observable_base: str = field(init=False)
    observable_sub: str = field(init=False)

    def __post_init__(self):
        channel, observable = self.name.split(CHANNEL_DISCRIMINANT_DELIM, 1)
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "observable", observable)

        ch_parts = channel.split(WITHIN_GROUP_DELIM)
        obs_parts = observable.split(WITHIN_GROUP_DELIM)

        object.__setattr__(self, "channel_base", ch_parts[0])
        object.__setattr__(self, "channel_sub", ch_parts[1] if len(ch_parts) > 1 else "")
        object.__setattr__(self, "observable_base", obs_parts[0])
        object.__setattr__(self, "observable_sub", obs_parts[1] if len(obs_parts) > 1 else "")

    # ------------------------------------------------------------------
    # Alternate constructors
    # ------------------------------------------------------------------
    @classmethod
    def from_parts(cls, channel_parts: list[str], obs_parts: list[str]) -> "Reference":
        assert all(isinstance(arg, list) for arg in [channel_parts, obs_parts])
        channel = WITHIN_GROUP_DELIM.join(channel_parts)
        disc = WITHIN_GROUP_DELIM.join(obs_parts)
        return cls(CHANNEL_DISCRIMINANT_DELIM.join([channel, disc]))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def is_simple(self) -> bool:
        return self.observable_sub is None

    # ------------------------------------------------------------------
    # ROOT file integration
    # ------------------------------------------------------------------
    @staticmethod
    def get_refs_from_file(file: Path, hist_dim: str = "All") -> list["Reference"]:
        valid_dims = {"TH1", "TH2", "TH3"}
        if hist_dim != "All" and hist_dim not in valid_dims:
            raise ValueError(f"Invalid dim '{hist_dim}'. Choose from 'TH1', 'TH2', 'TH3', or 'All'.")

        with uproot.open(file) as upfile:
            keys = [
                key for key, obj in upfile.items(cycle=False)
                if (obj.classname.startswith(hist_dim if hist_dim != "All" else tuple(valid_dims))
                    and not key.startswith("yields_")
                    and key != "generated_sum_corrected")
            ]
        return [Reference(k) for k in keys]
