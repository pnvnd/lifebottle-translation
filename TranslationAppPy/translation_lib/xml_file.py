import csv
import os
from .xml_section import XMLSection
from .models import EntryFound


class XMLFile:
    def __init__(self):
        self.name = None
        self.friendly_name = None
        self.file_type = None
        self.file_path = None
        self.sections = []
        self.speakers = None
        self.current_section = XMLSection("Default")
        self.is_legacy = False
        self.needs_save = False
        self.has_declaration = False

    def set_section(self, name):
        self.current_section = next(s for s in self.sections if s.name == name)

    def update_all_entry_text(self):
        speaker_dict = {}
        for spk in self.speakers:
            text = spk.english_text if spk.english_text else spk.japanese_text
            speaker_dict[spk.id] = text or ""

        for section in self.sections:
            for entry in section.entries:
                if entry.speaker_id is not None:
                    names = []
                    for sid in entry.speaker_id:
                        if sid in speaker_dict:
                            names.append(speaker_dict[sid])
                    entry.speaker_name = " / ".join(names)
                else:
                    entry.speaker_name = None

    def get_status_data(self):
        result = {"To Do": 0, "Edited": 0, "Proofread": 0, "Problematic": 0, "Done": 0}
        for section in self.sections:
            if section.name not in ("Other Strings", "All strings"):
                sd = section.get_status_data()
                for k in result:
                    result[k] += sd[k]
        if self.speakers:
            sd2 = self.speakers_get_status_data()
            for k in result:
                result[k] += sd2[k]
        return result

    def speakers_get_status_data(self):
        lst = self.speakers or []
        return {
            "To Do": sum(1 for e in lst if (e._status or "To Do") == "To Do"),
            "Edited": sum(1 for e in lst if e.status == "Editing"),
            "Proofread": sum(1 for e in lst if e.status == "Proofreading"),
            "Problematic": sum(1 for e in lst if e.status == "Problematic"),
            "Done": sum(1 for e in lst if e.status == "Done"),
        }

    def get_section_names(self):
        names = [s.name for s in self.sections if s.name != "All strings"]
        return ["All strings"] + names

    def save_to_disk(self):
        from xml.etree.ElementTree import Element, SubElement, tostring
        import xml.etree.ElementTree as ET

        root = Element(self.file_type)

        if self.friendly_name is not None:
            fn_el = SubElement(root, "FriendlyName")
            fn_el.text = self.friendly_name

        if self.speakers is not None:
            spk_el = SubElement(root, "Speakers")
            sec_el = SubElement(spk_el, "Section")
            sec_el.text = "Speaker"
            for entry in self.speakers:
                _append_entry_element(spk_el, entry, self.is_legacy)

        for section in self.sections:
            if section.name == "All strings":
                continue
            strings_el = SubElement(root, "Strings")
            sec_name_el = SubElement(strings_el, "Section")
            sec_name_el.text = section.name
            for entry in section.entries:
                _append_entry_element(strings_el, entry, self.is_legacy)

        xml_str = _indent_xml(root)
        xml_str = xml_str.replace(" />", "/>") + "\n"
        if self.has_declaration:
            xml_str = "<?xml version='1.0' encoding='UTF-8'?>\n" + xml_str

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

    def save_as_csv(self, path):
        has_speakers = self.speakers is not None
        en_names = {}
        jp_names = {}

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            headers = ["File", "Line Number", "Section", "Status"]
            if has_speakers:
                headers += ["Speaker JP"]
            headers += ["Text JP"]
            if has_speakers:
                headers += ["Speaker EN"]
            headers += ["Text EN", "Comment"]
            writer.writerow(headers)

            # Friendly name row
            fn_row = [self.name + ".xml", "", "Friendly Name", ""]
            if has_speakers:
                fn_row.append("")
            fn_row.append(self.friendly_name or "<null>")
            if has_speakers:
                fn_row.append("")
            fn_row += [self.friendly_name or "<null>", ""]
            writer.writerow(fn_row)

            if has_speakers:
                for entry in self.speakers:
                    en_name = entry.english_text or "<null>"
                    jp_name = entry.japanese_text or "<null>"
                    row = [self.name + ".xml", entry.id, "Speaker", entry.status,
                           "", jp_name, "", en_name, entry.notes or ""]
                    writer.writerow(row)
                    if entry.id is not None:
                        en_names[entry.id] = en_name
                        jp_names[entry.id] = jp_name

            for section in self.sections:
                if section.name == "All strings":
                    continue
                for entry in section.entries:
                    en_name_col = ""
                    jp_name_col = ""
                    if entry.speaker_id is not None:
                        en_parts = [en_names.get(sid, "") for sid in entry.speaker_id if en_names.get(sid)]
                        jp_parts = [jp_names.get(sid, "") for sid in entry.speaker_id if jp_names.get(sid)]
                        en_name_col = ",".join(str(s) for s in entry.speaker_id) + "[" + " / ".join(en_parts) + "]"
                        jp_name_col = ",".join(str(s) for s in entry.speaker_id) + "[" + " / ".join(jp_parts) + "]"

                    row = [self.name + ".xml", entry.id, section.name, entry.status]
                    if has_speakers:
                        row.append(jp_name_col)
                    row.append(entry.japanese_text or "<null>")
                    if has_speakers:
                        row.append(en_name_col)
                    row += [entry.english_text or "<null>", entry.notes or ""]
                    writer.writerow(row)

    def search_japanese(self, folder, file_id, text, match_whole_entry, match_case, match_whole_word, language):
        results = []
        for section in self.sections:
            if section.name != "All strings":
                results.extend(section.search_japanese(folder, file_id, section.name, text,
                                                        match_whole_entry, match_case, match_whole_word, language))
        if self.speakers is not None:
            results.extend(self._search_speakers(folder, file_id, text, match_whole_entry, match_case, match_whole_word, language))
        return results

    def _search_speakers(self, folder, file_id, text, match_whole_entry, match_case, match_whole_word, language):
        results = []
        for idx, entry in enumerate(self.speakers):
            if entry.is_found(text, match_whole_entry, match_case, match_whole_word, language):
                from .models import EntryFound
                ef = EntryFound()
                ef.folder = folder
                ef.file_id = file_id
                ef.section = "Speaker"
                ef.id = idx
                ef.entry = entry
                results.append(ef)
        return results


def _append_entry_element(parent, entry, is_legacy):
    from xml.etree.ElementTree import SubElement
    e_el = SubElement(parent, "Entry")

    def add(tag, val):
        if val is not None:
            el = SubElement(e_el, tag)
            el.text = str(val)

    add("PointerOffset", entry.pointer_offset)

    if entry.embed_offset:
        eo = SubElement(e_el, "EmbedOffset")
        hi_el = SubElement(eo, "hi")
        hi_el.text = entry.hi or ""
        lo_el = SubElement(eo, "lo")
        lo_el.text = entry.lo or ""

    add("MaxLength", entry.max_length)
    add("VoiceId", entry.voice_id)

    jp_el = SubElement(e_el, "JapaneseText")
    jp_el.text = entry.japanese_text

    en_el = SubElement(e_el, "EnglishText")
    en_el.text = entry.english_text

    notes_el = SubElement(e_el, "Notes")
    if entry.notes:
        notes_el.text = entry.notes

    if entry.speaker_id is not None:
        add("SpeakerId", ",".join(str(s) for s in entry.speaker_id))

    add("Id", entry.id)
    add("BubbleId", entry.bubble_id)
    add("SubId", entry.sub_id)

    status_el = SubElement(e_el, "Status")
    status_el.text = entry.status or "To Do"


def _indent_xml(elem, level=0):
    import xml.etree.ElementTree as ET
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            _indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent
    if not level:
        elem.tail = "\n"

    return ET.tostring(elem, encoding="unicode")
