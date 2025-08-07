def part1():
    import os
    import shutil
    import re
    from pathlib import Path

    # --- INPUT: list of original datacards ---
    datacards = [
        "/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_Rep/0806_NNInf_even/fits/multi_HH_ttbar_tW_both/datacard_multi_HH_ttbar_tW_both.txt",
        "/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_Rep/0806_NNInf_even/fits/multi_HH_ttbar_tW_lrs/datacard_multi_HH_ttbar_tW_lrs.txt",
        "/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_Rep/0806_NNInf_even/fits/multi_HH_ttbar_tW_vars/datacard_multi_HH_ttbar_tW_vars.txt",
    ]

    # --- OUTPUT ROOT BASE DIR ---
    hhinf_outpath = Path("/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_Rep/0806_NNInf_even/hhinf")
    hhinf_outpath.mkdir(parents=True, exist_ok=True)

    import uproot

    def copy_and_rename_root(input_root_path: Path, output_root_path: Path):
        with uproot.open(input_root_path) as infile:
            keys = infile.keys()
            with uproot.recreate(output_root_path) as outfile:
                for key in keys:
                    obj = infile[key]
                    name = obj.name
                    if name == "HH_bbWW":
                        name = "ggHH_kl_1_kt_1"
                    outfile[name] = obj

    # --- FUNCTION to modify one datacard ---
    def modify_datacard(datacard_path: Path):
        model_name = datacard_path.stem.replace("datacard_", "")
        model_dir = hhinf_outpath / model_name
        model_dir.mkdir(parents=True, exist_ok=True)

        with open(datacard_path, "r") as f:
            content = f.read()

        # Replace HH_bbWW with ggHH_kl_1_kt_1
        content = re.sub(r'\bHH_bbWW\b', 'ggHH_kl_1_kt_1', content)

        # Copy referenced .root files to model_dir and update paths
        root_files = set(re.findall(r'(/\S+\.root)', content))
        for original_path in root_files:
            original_file = Path(original_path)
            if original_file.exists():
                local_copy = model_dir / original_file.name
                copy_and_rename_root(original_file, local_copy)
                content = content.replace(str(original_file), str(local_copy))
            else:
                print(f"⚠️  WARNING: Missing file {original_file}")

        # Save modified datacard
        output_dc = model_dir / datacard_path.name
        shutil.copy2(datacard_path, output_dc)
        with open(output_dc, "w") as f:
            f.write(content)

        return output_dc

    # --- PROCESS ALL ---
    modified_paths = []
    for dc_path in datacards:
        dc_path = Path(dc_path)
        out_path = modify_datacard(dc_path)
        modified_paths.append(out_path)

    # --- PRINT SUMMARY ---
    print("\n✅ All modified datacards:")
    for path in modified_paths:
        print(f"\t{path}")

from dhi.tasks.limits import PlotUpperLimitsAtPoint
import luigi
from pathlib import Path
import shutil

def plot():
    hhinf_outpath = Path("/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_Rep/0806_NNInf_even/hhinf")

    multi_datacards = ":".join([
        str(hhinf_outpath / "multi_HH_ttbar_tW_both" / "datacard_multi_HH_ttbar_tW_both.txt"),
        str(hhinf_outpath / "multi_HH_ttbar_tW_lrs" / "datacard_multi_HH_ttbar_tW_lrs.txt"),
        str(hhinf_outpath / "multi_HH_ttbar_tW_vars" / "datacard_multi_HH_ttbar_tW_vars.txt"),
    ])

    # --- Instantiate task with version tag that makes output easy to find ---
    version_tag = "SM_UpperLimits"
    task = PlotUpperLimitsAtPoint(
        version=version_tag,
        multi_datacards=multi_datacards,
        # hh_model="noklDependentUnc"
        # You can also add: pois="r", mass="125", unblinded=True, etc.
    )

    # --- Run the task ---
    luigi.build([task], local_scheduler=True, workers=1)

    # --- Copy output plot (e.g. output.pdf or output_combined.pdf) ---
    plot_output_path = task.output().path  # Law target
    plot_dest = hhinf_outpath / f"limits_{version_tag}.pdf"
    shutil.copy2(plot_output_path, plot_dest)
    print(f"\n✅ Plot copied to: {plot_dest}")

if __name__ == "__main__":
    # part1()
    plot()
