import os
import re

from tools.shared.fetch_logs import get_from_config

filename_output_units = 'output_list_units.txt'
filename_output_buildings = 'output_list_buildings.txt'

def extract_major_keys(folder_path, output_file):
    """
    Extracts major keys from all files in a folder and saves them to an output file.

    Args:
        folder_path (str): The path to the folder containing the files.
        output_file (str): The name of the file to save the extracted keys to.
    """
    major_keys = []
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            with open(os.path.join(folder_path, filename), 'r') as f:
                content = f.read()
                # Regex to find keys at the beginning of a line followed by '='
                keys = re.findall(r'^([a-zA-Z0-9_]+)\s*=', content, re.MULTILINE)
                major_keys.extend(keys)

    with open(output_file, 'w') as f:
        for key in major_keys:
            f.write(key + '\n')

if __name__ == '__main__':
	folder_units = get_from_config('Paths', 'unit_types')
	folder_buildings = get_from_config('Paths', 'building_types')

	extract_major_keys(folder_units, filename_output_units)
	print(f"Successfully extracted major keys to '{filename_output_units}'")
	extract_major_keys(folder_buildings, filename_output_buildings)
	print(f"Successfully extracted major keys to '{filename_output_buildings}'")

