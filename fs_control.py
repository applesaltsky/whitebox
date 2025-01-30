from pathlib import Path
import os

class FSController:
    def delete_unused_image(db_controller,path_image):
        list_used_image = db_controller.get_image_all()
        list_stored_image = os.listdir(path_image)
        for image in list_stored_image:
            if image not in list_used_image:
                os.remove(Path(path_image,image))