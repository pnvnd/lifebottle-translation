import os
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET

from .models import XMLEntry, TranslationEntry
from .xml_section import XMLSection
from .xml_file import XMLFile


class XMLFolder:
    def __init__(self, name, path):
        self.name = name
        self.folder_path = path
        self.xml_files = []
        self.translations = {}
        self.current_file = XMLFile()

    def load_xmls(self, file_loaded_callback=None):
        try:
            file_list = sorted(os.listdir(self.folder_path))
        except OSError:
            return

        for fname in file_list:
            if fname.lower().endswith(".xml"):
                full_path = os.path.join(self.folder_path, fname)
                self.xml_files.append(self.load_xml(full_path))
                if file_loaded_callback:
                    file_loaded_callback()

        if self.xml_files:
            self.current_file = self.xml_files[0]

    def load_xml(self, xml_path):
        xml_file = XMLFile()
        xml_file.name = os.path.splitext(os.path.basename(xml_path))[0]
        xml_file.file_path = xml_path

        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            return xml_file

        root = tree.getroot()
        xml_file.file_type = root.tag

        with open(xml_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
        xml_file.has_declaration = first_line.startswith("<?xml")

        fn_el = root.find("FriendlyName")
        xml_file.friendly_name = fn_el.text if fn_el is not None else None

        everything_section = XMLSection("All strings")
        xml_file.sections.append(everything_section)

        for strings_el in root.findall("Strings"):
            sec_name_el = strings_el.find("Section")
            sec_name = sec_name_el.text if sec_name_el is not None else "Unknown"
            section = XMLSection(sec_name)
            xml_file.sections.append(section)

            for entry_el in strings_el.findall("Entry"):
                entry = _extract_xml_entry(entry_el)
                section.entries.append(entry)
                everything_section.entries.append(entry)

                if entry.japanese_text:
                    self._add_translation(entry.japanese_text, entry.english_text)

        speakers_el = root.find("Speakers")
        if speakers_el is not None:
            xml_file.speakers = []
            for entry_el in speakers_el.findall("Entry"):
                entry = _extract_xml_entry(entry_el)
                xml_file.speakers.append(entry)
                if entry.japanese_text:
                    self._add_translation(entry.japanese_text, entry.english_text)
            xml_file.update_all_entry_text()

        xml_file.current_section = xml_file.sections[0] if xml_file.sections else XMLSection("Default")
        return xml_file

    def save_changed(self):
        count = 0
        for xml_file in self.xml_files:
            if xml_file.needs_save:
                xml_file.save_to_disk()
                xml_file.needs_save = False
                count += 1
        return count

    def invalidate_translations(self):
        self.translations = {}
        for xml_file in self.xml_files:
            for section in xml_file.sections:
                if section.name == "All strings":
                    continue
                for entry in section.entries:
                    if entry.japanese_text:
                        self._add_translation(entry.japanese_text, entry.english_text)
            if xml_file.speakers:
                for entry in xml_file.speakers:
                    if entry.japanese_text:
                        self._add_translation(entry.japanese_text, entry.english_text)

    def _add_translation(self, japanese, english):
        if japanese not in self.translations:
            self.translations[japanese] = TranslationEntry(english_translation=english or "", count=1)
        else:
            existing = self.translations[japanese]
            if not existing.english_translation and english:
                existing.english_translation = english
            existing.count += 1

    def file_list(self):
        return [f.name for f in self.xml_files]

    def set_current_file(self, index):
        self.current_file = self.xml_files[index]
        self.current_file.current_section = self.current_file.sections[0]

    def search_japanese(self, text, match_whole_entry, match_case, match_whole_word, language):
        results = []
        for i, xml_file in enumerate(self.xml_files):
            results.extend(xml_file.search_japanese(self.name, i, text, match_whole_entry, match_case, match_whole_word, language))
        return results


def _extract_xml_entry(element):
    entry = XMLEntry()
    entry.id = _extract_nullable_int(element.find("Id"))
    entry.pointer_offset = _extract_nullable_str(element.find("PointerOffset"))
    entry.voice_id = _extract_nullable_str(element.find("VoiceId"))
    entry.english_text = _extract_nullable_str(element.find("EnglishText"))
    entry.japanese_text = _extract_nullable_str(element.find("JapaneseText"))
    entry.notes = _extract_nullable_str(element.find("Notes"))
    status_val = _extract_nullable_str(element.find("Status"))
    entry._status = status_val
    entry.speaker_id = _extract_nullable_int_array(element.find("SpeakerId"))
    entry.bubble_id = _extract_nullable_int(element.find("BubbleId"))
    entry.sub_id = _extract_optional_int(element.find("SubId"))
    entry.struct_id = _extract_nullable_int(element.find("StructId"))
    entry.unknown_pointer = _extract_nullable_int(element.find("UnknownPointer"))
    entry.max_length = _extract_nullable_int(element.find("MaxLength"))

    eo_el = element.find("EmbedOffset")
    if eo_el is not None:
        entry.embed_offset = True
        entry.hi = _extract_nullable_str(eo_el.find("hi"))
        entry.lo = _extract_nullable_str(eo_el.find("lo"))
    else:
        entry.embed_offset = False

    return entry


def _extract_nullable_int(element):
    if element is None or not (element.text or "").strip():
        return None
    try:
        return int(element.text.strip())
    except ValueError:
        return None


def _extract_optional_int(element):
    if element is None:
        return None
    try:
        return int(element.text.strip())
    except (ValueError, AttributeError):
        return None


def _extract_nullable_int_array(element):
    if element is None or not (element.text or "").strip():
        return None
    try:
        return [int(x) for x in element.text.strip().split(",")]
    except ValueError:
        return None


def _extract_nullable_str(element):
    if element is None:
        return None
    text = element.text
    if text is None:
        return None
    return text if text else None
