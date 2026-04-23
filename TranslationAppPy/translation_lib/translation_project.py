import os
from .xml_folder import XMLFolder


class TranslationProject:
    def __init__(self, base_path, folders_included):
        self.project_path = base_path
        self.xml_folders = []
        self.current_folder = None

        for folder in folders_included:
            full_path = os.path.join(base_path, folder)
            if os.path.isdir(full_path):
                files = os.listdir(full_path)
                if any(f.lower().endswith(".xml") for f in files):
                    self.xml_folders.append(XMLFolder(folder, full_path))

    def load_xmls(self, progress_callback=None):
        if not self.xml_folders:
            self.current_folder = None
            return

        total_files = 0
        for folder in self.xml_folders:
            if os.path.isdir(folder.folder_path):
                total_files += sum(1 for f in os.listdir(folder.folder_path) if f.lower().endswith(".xml"))

        current_file = [0]

        def on_file_loaded():
            current_file[0] += 1
            if progress_callback:
                progress_callback(current_file[0], total_files)

        for xml_folder in self.xml_folders:
            xml_folder.load_xmls(on_file_loaded)

        self.current_folder = self.xml_folders[0] if self.xml_folders else None

    def get_folder_by_name(self, name):
        return next(f for f in self.xml_folders if f.name == name)

    def get_folder_names(self):
        return [f.name for f in self.xml_folders]

    def set_current_folder(self, name):
        self.current_folder = next(f for f in self.xml_folders if f.name == name)

    def get_folder_id(self, name):
        for i, f in enumerate(self.xml_folders):
            if f.name == name:
                return i
        return -1
