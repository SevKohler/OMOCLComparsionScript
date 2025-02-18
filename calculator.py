import os
import yaml
import xml.etree.ElementTree as ET
import json

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def extract_archetype_from_yaml(yaml_data):
    try:
        return yaml_data['spec']['openEhrConfig']['archetype']
    except KeyError:
        return None

def extract_archetype_from_xml_published(file_path):
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
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define the OpenEHR namespace
    ns = {'openEHR': 'http://schemas.openehr.org/v1'}

    # Search for the archetype_id value using the namespace
    archetype_id = root.find('.//openEHR:archetype_id/openEHR:value', ns)
        
    if archetype_id is not None and "COMPOSITION" not in archetype_id.text and "DEMOGRAPHIC" not in archetype_id.text:
        return archetype_id.text
    return None

def compare_archetypes(OMOCL_data_dir, archetypes_dir):
    OMOCL_archetypes = set()
    archetypes_in_ckm_dir = set()
    archetypes_in_ckm_published = set()

    # Collect archetypes from OMOCL_data/
    for root, _, files in os.walk(OMOCL_data_dir):
        for file in files:
            if file.endswith('.yaml') or file.endswith('.yml'):
                yaml_file_path = os.path.join(root, file)
                yaml_data = load_yaml(yaml_file_path)
                archetype = extract_archetype_from_yaml(yaml_data)
                if archetype:
                    OMOCL_archetypes.add(archetype)

    # Collect archetypes from Archetypes/, excluding specific folders
    for root, dirs, files in os.walk(archetypes_dir):
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
                    archetypes_in_ckm_dir.add(archetype_id)
                if archetype_id_only_published:
                    archetypes_in_ckm_published.add(archetype_id_only_published)    
        
    in_ckm_not_in_OMOCL = list(archetypes_in_ckm_dir - OMOCL_archetypes)
    in_OMOCL_not_in_ckm = list(OMOCL_archetypes - archetypes_in_ckm_dir)
    published_not_in_OMOCL = list(archetypes_in_ckm_published - OMOCL_archetypes)

    # Save results to JSON
    result = {
        "published archetypes that are not mapped in OMOCL": published_not_in_OMOCL,
        "including draft archetypes that are not mapped in OMOCL": in_ckm_not_in_OMOCL,
        "not in CKM but in OMOCL (older versions of archetypes usually)": in_OMOCL_not_in_ckm
    }

    with open('archetype_comparison.json', 'w') as json_file:
        json.dump(result, json_file, indent=4)

    print("Comparison completed. Results saved to 'archetype_comparison.json'.")
    print(str(len(OMOCL_archetypes))+" archetypes are mapped in OMOCL")
    print(str(len(published_not_in_OMOCL))+" non mapped published archetypes found, "+str(len(in_ckm_not_in_OMOCL))+" non mapped draft archetypes found.")
    print("Be aware that not all of these archetypes are transformable in a useful way to OMOP")

if __name__ == "__main__":
    OMOCL_data_dir = 'medical_data/'
    ckm_dir = 'CKM/'
    compare_archetypes(OMOCL_data_dir, ckm_dir)