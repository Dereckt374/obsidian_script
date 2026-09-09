from gestion_yaml_notes.utils_obsidian import *
import os

OBS_PRO = r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\obsidian_pro"
OBS_LOS = r"C:\Users\virgil.mesle\Sirius Space Services\Technique - 0000000-Systeme_de_lancement\0300000 - Loi spatiale\0320000 - Loi française\0321000 - LOS\obsidian_los"
PATH_ARCHIVE_OBS_LOS = r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\98 - Archive\ARCHIVE - LOS OBSIDIAN"

def main():
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

if __name__ == "__main__":
    main()