import os
import yaml
import xml.etree.ElementTree as ET
import json


def load_yaml(file_path):
    """Load and parse a YAML file."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def extract_archetype_from_yaml(yaml_data):
    """Extract the archetype from YAML data."""
    try:
        return yaml_data['spec']['openEhrConfig']['archetype']
    except KeyError:
        return None


def extract_archetype_from_xml_published(file_path):
    """Extract the archetype ID from an XML file if it is published."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define the OpenEHR namespace
    ns = {'openEHR': 'http://schemas.openehr.org/v1'}

    # Search for the lifecycle_state value using the namespace
    lifecycle_state = root.find('.//openEHR:description/openEHR:lifecycle_state', ns)
    
    # Check if the lifecycle_state is "published"
    if lifecycle_state is not None and lifecycle_state.text == "published":
        # If lifecycle_state is published, find the archetype_id
        archetype_id = root.find('.//openEHR:archetype_id/openEHR:value', ns)
        if archetype_id is not None and "COMPOSITION" not in archetype_id.text and "DEMOGRAPHIC" not in archetype_id.text:
            return archetype_id.text  # Return the archetype_id
    return None  # Return None if lifecycle_state is not published or archetype_id is not found


def extract_archetype_from_xml(file_path):
    """Extract the archetype ID from an XML file."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define the OpenEHR namespace
    ns = {'openEHR': 'http://schemas.openehr.org/v1'}

    # Search for the archetype_id value using the namespace
    archetype_id = root.find('.//openEHR:archetype_id/openEHR:value', ns)
        
    if archetype_id is not None and "COMPOSITION" not in archetype_id.text and "DEMOGRAPHIC" not in archetype_id.text:
        return archetype_id.text
    return None


def collect_archetypes_from_yaml_files(directory):
    """Collect archetypes from YAML files in the given directory."""
    archetypes = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.yaml') or file.endswith('.yml'):
                yaml_file_path = os.path.join(root, file)
                yaml_data = load_yaml(yaml_file_path)
                archetype = extract_archetype_from_yaml(yaml_data)
                if archetype:
                    archetypes.add(archetype)
    return archetypes


def collect_archetypes_from_xml_files(directory):
    """Collect archetypes from XML files in the given directory, excluding specific folders."""
    archetypes = set()
    published_archetypes = set()

    for root, dirs, files in os.walk(directory):
        # Exclude 'demographics', 'folderA', and 'folderB' folders at any level
        folders_to_exclude = {'demographics'}
        for folder in folders_to_exclude:
            if folder in dirs:
                dirs.remove(folder)  # Skip the excluded folders
        for file in files:
            if file.endswith('.xml'):
                xml_file_path = os.path.join(root, file)
                archetype_id = extract_archetype_from_xml(xml_file_path)
                archetype_id_only_published = extract_archetype_from_xml_published(xml_file_path)
                if archetype_id:
                    archetypes.add(archetype_id)
                if archetype_id_only_published:
                    published_archetypes.add(archetype_id_only_published)
    return archetypes, published_archetypes


def calculate_coverage_published(published_archetypes, omocl_archetypes):
    """Calculate the percentage of published archetypes that are mapped in OMOCL."""
    unique_to_ckm = published_archetypes.difference(omocl_archetypes)
    if len(published_archetypes) > 0:  # Avoid division by zero
        percentage = (len(unique_to_ckm) / len(published_archetypes)) * 100
        percentage = 100 - percentage
    else:
        percentage = 0  # If list A is empty, return 0
    return percentage

def calculate_coverage_non_publihsed(archetypes, omocl_archetypes):
    """Calculate the percentage of published archetypes that are mapped in OMOCL."""
    unique_to_ckm = archetypes.difference(omocl_archetypes)
    if len(archetypes) > 0:  # Avoid division by zero
        percentage = (len(unique_to_ckm) / len(archetypes)) * 100
        percentage = 100 - percentage
    else:
        percentage = 0  # If list A is empty, return 0
    return percentage


def save_results_to_json(results, file_path):
    """Save the comparison results to a JSON file."""
    with open(file_path, 'w') as json_file:
        json.dump(results, json_file, indent=4)
    print("Comparison completed. Results saved to 'archetype_comparison.json'.")


def compare_archetypes(omocl_data_dir, archetypes_dir):
    """Compare archetypes between OMOCL data and CKM directories."""
    # Collect archetypes from OMOCL_data/
    omocl_archetypes = collect_archetypes_from_yaml_files(omocl_data_dir)

    # Collect archetypes from Archetypes/
    archetypes_in_ckm_dir, archetypes_in_ckm_published = collect_archetypes_from_xml_files(archetypes_dir)

    # Calculate differences
    in_ckm_not_in_omocl = list(archetypes_in_ckm_dir - omocl_archetypes)
    in_omocl_not_in_ckm = list(omocl_archetypes - archetypes_in_ckm_dir)
    published_not_in_omocl = list(archetypes_in_ckm_published - omocl_archetypes)

    # Calculate coverage percentage
    coverage_published = calculate_coverage_published(archetypes_in_ckm_published, omocl_archetypes)
    coverage_non_publihsed = calculate_coverage_published(archetypes_in_ckm_dir, omocl_archetypes)


    # Save results to JSON
    result = {
        "published archetypes that are not mapped in OMOCL": published_not_in_omocl,
        "including draft archetypes that are not mapped in OMOCL": in_ckm_not_in_omocl,
        "not in CKM but in OMOCL (older versions of archetypes usually)": in_omocl_not_in_ckm
    }
    save_results_to_json(result, 'archetype_comparison.json')

    # Print summary
    print(f"{len(omocl_archetypes)} archetypes are mapped in OMOCL")
    print(f"{len(published_not_in_omocl)} non-mapped published archetypes found, {len(in_ckm_not_in_omocl)} non-mapped non-published archetypes found.")
    print(f"The current coverage of publihsed archetypes is: {coverage_published:.2f}%")
    print(f"The current coverage of all archetypes is: {coverage_non_publihsed:.2f}%")
    print("Be aware that not all of these archetypes are transformable in a useful way to OMOP")


if __name__ == "__main__":
    omocl_data_dir = 'medical_data/'
    ckm_dir = 'CKM/'
    compare_archetypes(omocl_data_dir, ckm_dir)