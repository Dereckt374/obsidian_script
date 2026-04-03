from utils_obsidian import *

OBS_PRO = r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\obsidian_pro"
OBS_LOS = r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\LOS\obsidian_los"

move_md_by_yaml_header(
    root_dir=OBS_PRO,
    yaml_key="tags",
    yaml_value="companies",
    dest_dir=os.path.join(OBS_PRO, "companies")
)

move_md_by_yaml_header(
    root_dir=OBS_LOS,
    yaml_key="type",
    yaml_value="Document",
    dest_dir=os.path.join(OBS_LOS, "Documents")
)

move_md_by_yaml_header(
    root_dir=OBS_LOS,
    yaml_key="type",
    yaml_value="Spec",
    dest_dir=os.path.join(OBS_LOS, "Specs")
)

process_vault(OBS_PRO)