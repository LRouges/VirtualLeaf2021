import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
import numpy as np
import time

class MyXML:
    """Utility to clone a LeafML file and tweak simple <par name="…"> entries."""

    def __init__(self, templatefile: str):
        self.tree = ET.parse(templatefile)
        self.root = self.tree.getroot()
        self.parameters = self.root.find("parameter")

    def set_simple_param(self, name: str, value) -> None:
        """Change the ‘val’ attribute of <par name='…'>."""
        par = self.parameters.find(f"./par[@name='{name}']")
        if par is None:
            raise KeyError(f"Parameter '{name}' not found in XML")
        par.set("val", str(value))
    def set_setting(self, name: str, value) -> None:
        """Change the 'val' attribute of <setting name='...'>."""
        settings = self.root.find("settings")
        if settings is None:
            raise KeyError("Settings section not found in XML")

        setting = settings.find(f"./setting[@name='{name}']")
        if setting is None:
            raise KeyError(f"Setting '{name}' not found in XML")

        # Convert boolean values to lowercase strings (true/false)
        setting.set("val", str(value).lower() if isinstance(value, bool) else str(value))

    def write(self, filename: str) -> None:
        """Write a full XML document in UTF‑8."""
        # ①  simply pass the *path* to ElementTree; it opens the file in 'wb'
        self.tree.write(filename, encoding="utf-8", xml_declaration=True)


# -----------------------------------------------------------------------------
simulation_start_time = time.time()
leaf_in = Path("data/leaves/cambium.xml")
model = "libcambium.so"
# Fixed expansion rate and different elastic modulus values
number_of_runs = np.arange(0,1)
for r in number_of_runs:
    # Create unique output names
    output_suffix = f"Test_if_stiffness_is_beign_passed_{r}"
    datadir = f"/home/ardati/Data_VirtualLeaf/Cambium_{output_suffix}"
    leaf_out = leaf_in.with_name(leaf_in.stem + output_suffix + ".xml")

    # Create and modify XML
    xml = MyXML(leaf_in)
    xml.set_simple_param("maxt", 5000)
    xml.set_simple_param("datadir", datadir)
    xml.set_simple_param("rseed", 1) #set seed to 1 for reproducibility
    xml.set_simple_param("mc_stepsize", 0.2)
    xml.set_simple_param("mc_cell_stepsize", 0.1)
    xml.set_simple_param("compatibility_level", 1)
    xml.set_setting("show_nodes", False)
    xml.set_setting("show_node_numbers", False)
    xml.set_setting("show_cell_numbers", False)
    xml.set_setting("show_cell_centers", False)

    # Write XML file
    xml.write(leaf_out)

    # Run simulation
    print(f"Running simulation with number {r} and output {leaf_out}")
    subprocess.run([
        "./bin/VirtualLeaf",
        "-b",
        "-l", str(leaf_out),
        "-m", model
    ], check=True)

    # here i want to ran this bash script in the same directory to animate the pngs
    # Animate the PNGs generated in the simulation
    animate_script = f"""#!/bin/bash
    # Get directory name for the output file name
    dir_name=$(basename "$(pwd)")

    # 1. Make numbered links
    i=0
    for f in $(ls leaf.[0-9][0-9][0-9][0-9][0-9][0-9].png | sort); do
        printf -v link "link_%06d.png" "$i"
        ln -s "$f" "$link"
        ((i++))
    done

    # 2. Encode
    ffmpeg -framerate 25 -i link_%06d.png \\
           -c:v libx264 -crf 18 -preset slow \\
           -pix_fmt yuv420p -movflags +faststart \\
           "$dir_name.mp4"

    # 3. Clean up
    rm link_*.png
    """
    # Create the script file in the data directory
    import os

    script_path = os.path.join(datadir, "animate.sh")

    # Write the script
    with open(script_path, 'w') as f:
        f.write(animate_script)

    # Make executable
    os.chmod(script_path, 0o755)

    # Run the animation script in the data directory
    print(f"Animating PNGs in {datadir}")
    subprocess.run(
        [script_path],
        cwd=datadir,  # Run in the data directory
        check=True
    )

print(f"This Simulation took {round((time.time() - simulation_start_time) / 60, 2)} minutes.")
