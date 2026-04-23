from .models import EntryFound, XMLEntry


class XMLSection:
    def __init__(self, name):
        self.name = name
        self.entries = []

    def get_status_data(self):
        return {
            "To Do": sum(1 for e in self.entries if (e._status or "To Do") == "To Do"),
            "Edited": sum(1 for e in self.entries if e.status == "Editing"),
            "Proofread": sum(1 for e in self.entries if e.status == "Proofreading"),
            "Problematic": sum(1 for e in self.entries if e.status == "Problematic"),
            "Done": sum(1 for e in self.entries if e.status == "Done"),
        }

    def search_japanese(self, folder, file_id, section_name, text, match_whole_entry, match_case, match_whole_word, language):
        results = []
        for idx, entry in enumerate(self.entries):
            if entry.is_found(text, match_whole_entry, match_case, match_whole_word, language):
                ef = EntryFound()
                ef.folder = folder
                ef.file_id = file_id
                ef.section = section_name
                ef.id = idx  # list index, used as fallback
                ef.entry = entry  # actual reference so navigation can match by identity
                results.append(ef)
        return results
