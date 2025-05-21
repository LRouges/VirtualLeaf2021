import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
import numpy as np

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

    def write(self, filename: str) -> None:
        """Write a full XML document in UTF‑8."""
        # ①  simply pass the *path* to ElementTree; it opens the file in 'wb'
        self.tree.write(filename, encoding="utf-8", xml_declaration=True)

        # --- alternative ---
        # with open(filename, "wb") as fh:          # binary mode!
        #     self.tree.write(fh, encoding="utf-8", xml_declaration=True)

# -----------------------------------------------------------------------------
leaf_in = Path("data/leaves/cambium.xml")
model = "libmodel_exp.so"
# Fixed expansion rate and different elastic modulus values
number_of_runs = 3
for r in number_of_runs:
    # Create unique output names
    datadir = f"/home/ardati/Data_VirtualLeaf/Cambium_r_{r}"
    output_suffix = f"_{r}"
    leaf_out = leaf_in.with_name(leaf_in.stem + output_suffix + ".xml")

    # Create and modify XML
    xml = MyXML(leaf_in)
    xml.set_simple_param("maxt", 1500)
    xml.set_simple_param("datadir", datadir)
    xml.set_simple_param("xml_storage_stride", 1) # Pour enregiustrer tous les pas de temps
    xml.set_simple_param("rseed", 1) #set seed to 1 for reproducibility


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

# After all simulations complete, analyze and plot the results
import matplotlib.pyplot as plt
import os
import re

# Collect area data for each elastic modulus value
areas = []

for r in number_of_runs:
    datadir = f"/home/ardati/Data_VirtualLeaf/model_exp_pressure_em{r}"
    print(f"getcwd : {os.getcwd()}")
    # Find the latest XML file based on numeric part
    xml_files = [f for f in os.listdir(datadir) if f.endswith('.xml')]
    if not xml_files:
        print(f"No XML files found in {datadir}")
        continue

    # Extract numbers from filenames like "leaf.000050.xml"
    pattern = re.compile(r'leaf\.(\d+)\.xml')
    latest_num = -1
    latest_file = None

    for file in xml_files:
        match = pattern.match(file)
        if match:
            num = int(match.group(1))
            if num > latest_num:
                latest_num = num
                latest_file = file

    if not latest_file:
        print(f"No matching XML files found in {datadir}")
        continue

    latest_xml = os.path.join(datadir, latest_file)
    print(f"Using {latest_file} for elastic_modulus {elastic_modulus}")

    # Parse the XML
    # Parse the XML
    tree = ET.parse(latest_xml)
    root = tree.getroot()
    cells = root.find("cells")
    if cells is not None:
        found = False
        for cell in cells.findall("cell"):
            if cell.get("index") == "0":
                found = True
                area = float(cell.get("area"))
                areas.append((elastic_modulus, area))
                print(f"Elastic modulus {elastic_modulus}: Cell area = {area}")
                break  # Stop after finding the target cell
        if not found:
            print(f"Cell with index 131 not found in {latest_xml}")

# Plot the results
if areas:
    modulus_values, area_values = zip(*sorted(areas))
    area_mean = sum(area_values) / len(area_values)
    plt.figure(figsize=(10, 6))
    plt.plot(modulus_values, area_values, 'o-')
    # plt.ylim(area_mean*0.9, area_mean*1.1)  # fixed, generous y‑window
    # plt.yticks(np.arange(area_mean, area_mean*1.1, 2))  # tidy ticks
    plt.xlabel('Elastic Modulus')
    plt.ylabel('Cell Area')
    plt.title(f'Cell Area vs Elastic Modulus (Expansion Rate = {expansion_rate})')
    plt.grid(True)
    plt.savefig('area_vs_elastic_modulus.png')
    plt.show()
else:
    print("No area data found to plot")