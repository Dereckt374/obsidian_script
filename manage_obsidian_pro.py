from utils_obsidian import *

OBS_REPO = r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\obsidian_pro"
print(os.path.join(OBS_REPO, "companies"))


move_md_by_yaml_header(
    root_dir=OBS_REPO,
    yaml_key="tags",
    yaml_value="companies",
    dest_dir=os.path.join(OBS_REPO, "companies")
)

