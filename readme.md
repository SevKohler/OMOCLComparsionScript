# OMOCL comparsion script

Note
------
OMOCL is the result of a research project. To support our research, please cite one of our papers instead of referencing our github in scientific articles. You can find an overview of papers about OMOCL here. If you are not sure which paper to cite, we recommend this one:

Severin Kohler, Diego Boscá, Florian Kärcher, Birger Haarbrandt, Manuel Prinz, Michael Marschollek, Roland Eils, Eos and OMOCL: Towards a seamless integration of openEHR records into the OMOP Common Data Model, Journal of Biomedical Informatics, Volume 144, 2023 [(Link)](https://doi.org/10.1016/j.jbi.2023.104437)

Thanks!

Setup
-----
To run the script:
1. Download the OMOCL mappings and replace the medical_data folder with the one from OMOCL. 
2. Bulk download all archetypes from the CKM and paste the unzipped folder into CKM/. This could be also from your local CKM. 
3. Run the python script. 
4. Detailed output is in the archetype_comparsion.json.
Count is provided in the print. 

The comparsion does not include COMPOSITION and DEMOGRAPHIC archetypes.

If you want to use this to check how much of your openEHR platform can be mapped to OMOP you can also provide the archetypes in XML format instead as subfolders into CKM/archetypes/. 
