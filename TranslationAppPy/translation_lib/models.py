import re


class TranslationEntry:
    def __init__(self, english_translation="", count=1):
        self.english_translation = english_translation
        self.count = count


class XMLEntry:
    def __init__(self):
        self.pointer_offset = None
        self.voice_id = None
        self.japanese_text = None
        self.english_text = None
        self.notes = None
        self.id = None
        self.struct_id = None
        self.speaker_id = None   # list of ints or None
        self.bubble_id = None
        self.sub_id = None
        self.unknown_pointer = None
        self.max_length = None
        self.embed_offset = False
        self.hi = None
        self.lo = None
        self._status = None
        self.speaker_name = None  # not serialised

    @property
    def status(self):
        if self._status == "Edited":
            return "Editing"
        if self._status == "Proofread":
            return "Proofreading"
        return self._status

    @status.setter
    def status(self, value):
        if value == "Editing":
            self._status = "Edited"
        elif value == "Proofreading":
            self._status = "Proofread"
        else:
            self._status = value

    def is_found(self, text, match_whole_entry, match_case, match_whole_word, language):
        text_compare = self.japanese_text if language == "Japanese" else self.english_text
        if text_compare is None:
            return False
        if match_whole_entry:
            return text_compare == text
        if match_case:
            return text in text_compare
        if match_whole_word:
            return bool(re.search(rf"\b{re.escape(text)}\b", text_compare, re.IGNORECASE))
        return bool(re.search(re.escape(text), text_compare, re.IGNORECASE))


class EntryFound:
    def __init__(self):
        self.folder = None
        self.file_id = None
        self.section = None
        self.id = None
        self.entry = None
        self.category = None
