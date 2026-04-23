import streamlit as st
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the TranslationAppPy directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'TranslationAppPy'))

from translation_lib.translation_project import TranslationProject
from translation_lib.models import XMLEntry, EntryFound
from config import Config, GameConfig
from packing_lib.packing_project import PackingProject

# Constants
VERSION = "1.0.0"
PROJECTS = [
    ("NDX", "Narikiri Dungeon X", "2_translated"),
    ("TOR", "Tales of Rebirth", "2_translated"),
    ("TOH", "Tales of Hearts (DS)", "2_translated"),
    ("RM2", "Tales of the World: Radiant Mythology 2", "2_translated"),
]

COLOR_BY_STATUS = {
    "To Do": "#FFFFFF",
    "Editing": "#A2FFFF",
    "Proofreading": "#FF00FF",
    "Problematic": "#FFFFA2",
    "Done": "#A2FFA2",
}

def main():
    st.set_page_config(page_title=f"Translation App v{VERSION}", layout="wide")
    
    # Initialize session state
    if 'project' not in st.session_state:
        st.session_state.project = None
    if 'current_folder' not in st.session_state:
        st.session_state.current_folder = None
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'current_section' not in st.session_state:
        st.session_state.current_section = None
    if 'entries' not in st.session_state:
        st.session_state.entries = []
    if 'selected_entry' not in st.session_state:
        st.session_state.selected_entry = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        menu = st.selectbox("Menu", ["Project", "File", "Packing", "Tools"])
        
        if menu == "Project":
            project_menu()
        elif menu == "File":
            file_menu()
        elif menu == "Packing":
            packing_menu()
        elif menu == "Tools":
            tools_menu()
    
    # Main content
    if st.session_state.project:
        display_main_ui()
    else:
        st.write("Please open a project from the Project menu.")

def project_menu():
    st.header("Project")
    
    # Open Folder
    if st.button("Open Folder"):
        uploaded_files = st.file_uploader("Upload XML files", type=["xml"], accept_multiple_files=True)
        if uploaded_files:
            # Create temporary directory and save files
            temp_dir = tempfile.mkdtemp()
            for file in uploaded_files:
                with open(os.path.join(temp_dir, file.name), "wb") as f:
                    f.write(file.getbuffer())
            
            # Assume all files are in one folder for simplicity
            folders_included = ["."]
            st.session_state.project = TranslationProject(temp_dir, folders_included)
            st.session_state.project.load_xmls()
            st.success("Project loaded!")
            st.rerun()
    
    # Predefined projects
    st.subheader("Predefined Projects")
    for short, full, folder in PROJECTS:
        with st.expander(f"{short} - {full}"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Open Last Folder ({short})"):
                    st.info("Last folder functionality not implemented in Streamlit version")
            with col2:
                if st.button(f"Open New Folder ({short})"):
                    st.info("New folder functionality - use Open Folder above")

def file_menu():
    st.header("File")
    if not st.session_state.project:
        st.warning("No project loaded")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Save Current File"):
            save_current_file()
    with col2:
        if st.button("Reload Current File"):
            reload_current_file()
    with col3:
        if st.button("Save All"):
            save_all()
    with col4:
        if st.button("Reload All"):
            reload_all()
    
    if st.button("Export file to csv"):
        export_csv()
    
    if st.button("Import from csv"):
        st.info("Not implemented yet")
    
    col5, col6 = st.columns(2)
    with col5:
        if st.button("Set file as Done"):
            set_file_as_done()
    with col6:
        if st.button("Set section as Done"):
            set_section_as_done()

def packing_menu():
    st.header("Packing")
    if st.button("Setup"):
        st.info("Setup dialog not implemented in Streamlit version")
    
    st.subheader("NDX")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Extract Iso (NDX)"):
            ndx_extract()
    with col2:
        if st.button("Make Iso (NDX)"):
            ndx_make()
    
    st.subheader("TOR")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Extract Iso (TOR)"):
            tor_extract()
    with col2:
        if st.button("Make Iso (TOR)"):
            tor_make()

def tools_menu():
    st.header("Tools")
    if st.button("Hex to Japanese"):
        open_hex_dialog()
    
    if st.button("Search files for Japanese"):
        search_japanese()

def display_main_ui():
    # Three columns layout
    left_col, middle_col, right_col = st.columns([1, 1.5, 1.5])
    
    with left_col:
        display_left_column()
    
    with middle_col:
        display_middle_column()
    
    with right_col:
        display_right_column()

def display_left_column():
    st.subheader("File Selection")
    
    # File Kind and File Name
    if st.session_state.project:
        folder_names = st.session_state.project.get_folder_names()
        if folder_names:
            file_kind = st.selectbox("File Kind", folder_names, key="file_kind")
            st.session_state.current_folder = st.session_state.project.get_folder_by_name(file_kind)
            
            if st.session_state.current_folder:
                file_names = [f.name for f in st.session_state.current_folder.xml_files]
                if file_names:
                    file_name = st.selectbox("File Name", file_names, key="file_name")
                    st.session_state.current_file = next((f for f in st.session_state.current_folder.xml_files if f.name == file_name), None)
                    
                    if st.session_state.current_file:
                        section_names = [s.name for s in st.session_state.current_file.sections]
                        if section_names:
                            section_name = st.selectbox("Section Filter", ["All"] + section_names, key="section")
                            st.session_state.current_section = section_name if section_name != "All" else None
                            
                            # Load entries
                            load_entries()
                            
                            # Display Language
                            display_lang = st.selectbox("Display Language", ["English (if available)", "Japanese"], key="display_lang")
                            
                            # Status filters
                            st.write("Status Filters")
                            status_filters = {}
                            for status in ["To Do", "Editing", "Proofreading", "Problematic", "Done"]:
                                status_filters[status] = st.checkbox(status, value=True, key=f"filter_{status}")
                            
                            # Tabs for Text and Speaker
                            tab1, tab2 = st.tabs(["Text", "Speaker"])
                            
                            with tab1:
                                display_text_entries(display_lang, status_filters)
                            
                            with tab2:
                                display_speaker_entries(display_lang, status_filters)

def display_text_entries(display_lang, status_filters):
    st.subheader("Text Entries")
    
    filtered_entries = [e for e in st.session_state.entries if status_filters.get(e.status, True)]
    
    if filtered_entries:
        entry_options = []
        for i, entry in enumerate(filtered_entries):
            text = entry.english_text if entry.english_text and display_lang == "English (if available)" else entry.japanese_text or ""
            speaker = f" [{entry.speaker_name}]" if entry.speaker_name else ""
            status = f" ({entry.status})" if entry.status else ""
            option = f"{i+1}. {text[:50]}...{speaker}{status}"
            entry_options.append(option)
        
        selected_option = st.selectbox("Select Entry", entry_options, key="entry_select")
        if selected_option:
            index = int(selected_option.split('.')[0]) - 1
            st.session_state.selected_entry = filtered_entries[index]
    else:
        st.write("No entries found")

def display_speaker_entries(display_lang, status_filters):
    st.subheader("Speaker Entries")
    
    if st.session_state.current_file and st.session_state.current_file.speakers:
        filtered_speakers = [s for s in st.session_state.current_file.speakers if status_filters.get(s.status, True)]
        
        if filtered_speakers:
            speaker_options = []
            for i, speaker in enumerate(filtered_speakers):
                text = speaker.english_text if speaker.english_text and display_lang == "English (if available)" else speaker.japanese_text or ""
                status = f" ({speaker.status})" if speaker.status else ""
                option = f"{i+1}. {text}{status}"
                speaker_options.append(option)
            
            selected_option = st.selectbox("Select Speaker", speaker_options, key="speaker_select")
            if selected_option:
                index = int(selected_option.split('.')[0]) - 1
                st.session_state.selected_entry = filtered_speakers[index]
        else:
            st.write("No speakers found")
    else:
        st.write("No speakers in this file")

def load_entries():
    if st.session_state.current_file:
        entries = []
        for section in st.session_state.current_file.sections:
            if st.session_state.current_section is None or section.name == st.session_state.current_section:
                entries.extend(section.entries)
        st.session_state.entries = entries

def display_middle_column():
    st.subheader("Entry Details")
    
    if st.session_state.selected_entry:
        entry = st.session_state.selected_entry
        
        # File and Section names
        col1, col2 = st.columns(2)
        with col1:
            friendly_name = st.text_input("File Friendly Name", value=st.session_state.current_file.friendly_name or "", key="friendly_name")
            if friendly_name != (st.session_state.current_file.friendly_name or ""):
                st.session_state.current_file.friendly_name = friendly_name
                st.session_state.current_file.needs_save = True
        with col2:
            section_name = st.text_input("Section Name", value=st.session_state.current_section or "", key="section_name")
            # Section name change might be more complex, for now just display
        
        # Notes
        notes = st.text_area("Notes", value=entry.notes or "", height=100, key="notes")
        
        # Status
        status = st.selectbox("Status", ["To Do", "Editing", "Proofreading", "Problematic", "Done"], 
                             index=["To Do", "Editing", "Proofreading", "Problematic", "Done"].index(entry.status or "To Do"), key="status")
        
        # Empty checkbox
        is_empty = st.checkbox("Empty", value=not entry.english_text, key="is_empty")
        
        # Japanese text
        st.write("Japanese")
        st.text_area("Japanese Text", value=entry.japanese_text or "", height=150, disabled=True, key="japanese_text")
        
        # English text
        st.write("English")
        english_text = st.text_area("English Text", value=entry.english_text or "", height=150, key="english_text")
        
        # Simple Preview
        st.write("Simple Preview")
        preview_text = english_text or entry.japanese_text or ""
        st.text_area("Preview", value=preview_text, height=100, disabled=True, key="preview")
        
        # Update entry if changed
        if english_text != (entry.english_text or ""):
            entry.english_text = english_text
            if st.session_state.current_file:
                st.session_state.current_file.needs_save = True
        if notes != (entry.notes or ""):
            entry.notes = notes
            if st.session_state.current_file:
                st.session_state.current_file.needs_save = True
        if status != (entry.status or "To Do"):
            entry.status = status
            if st.session_state.current_file:
                st.session_state.current_file.needs_save = True
    else:
        st.write("No entry selected")

def display_right_column():
    st.subheader("Search & Other Translations")
    
    tab1, tab2 = st.tabs(["Search", "Other Translations"])
    
    with tab1:
        st.write("Search")
        
        file_kind_search = st.selectbox("File Kind", ["All", "Story", "Skits", "Menu"], key="search_file_kind")
        language_search = st.selectbox("Language", ["Japanese", "English"], key="search_lang")
        search_text = st.text_input("Search Text", key="search_text")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            match_entry = st.checkbox("Match Entry", key="match_entry")
        with col2:
            match_case = st.checkbox("Match Case", key="match_case")
        with col3:
            match_whole = st.checkbox("Match Whole", key="match_whole")
        
        if st.button("Search"):
            perform_search(search_text, language_search, match_entry, match_case, match_whole)
        
        if st.session_state.search_results:
            st.write(f"Found {len(st.session_state.search_results)} entries")
            for result in st.session_state.search_results[:10]:  # Show first 10
                st.write(f"{result.folder} - {result.section} - {result.id}: {result.entry.japanese_text[:50]}...")
    
    with tab2:
        st.write("Other Translations")
        if st.session_state.selected_entry:
            # This would show other translations for the same Japanese text
            st.write("Other translations functionality not fully implemented")
        else:
            st.write("Select an entry to see other translations")

# Placeholder functions for menu actions
def save_current_file():
    if st.session_state.current_file:
        try:
            st.session_state.current_file.save_to_disk()
            st.success("Current file saved!")
        except Exception as e:
            st.error(f"Error saving file: {e}")
    else:
        st.warning("No file selected")

def reload_current_file():
    if st.session_state.current_file:
        try:
            # Reload logic - for simplicity, just mark as not needing save
            st.session_state.current_file.needs_save = False
            st.success("Current file reloaded!")
        except Exception as e:
            st.error(f"Error reloading file: {e}")
    else:
        st.warning("No file selected")

def save_all():
    if st.session_state.project:
        try:
            for folder in st.session_state.project.xml_folders:
                folder.save_changed()
            st.success("All files saved!")
        except Exception as e:
            st.error(f"Error saving all files: {e}")
    else:
        st.warning("No project loaded")

def reload_all():
    if st.session_state.project:
        try:
            st.session_state.project.load_xmls()
            st.success("All files reloaded!")
        except Exception as e:
            st.error(f"Error reloading all files: {e}")
    else:
        st.warning("No project loaded")

def export_csv():
    if st.session_state.current_file:
        try:
            csv_path = st.session_state.current_file.file_path.replace('.xml', '.csv')
            st.session_state.current_file.save_as_csv(csv_path)
            st.success(f"CSV exported to {csv_path}")
        except Exception as e:
            st.error(f"Error exporting CSV: {e}")
    else:
        st.warning("No file selected")

def set_file_as_done():
    if st.session_state.current_file:
        try:
            for section in st.session_state.current_file.sections:
                for entry in section.entries:
                    entry.status = "Done"
            st.success("File set as done!")
        except Exception as e:
            st.error(f"Error setting file as done: {e}")
    else:
        st.warning("No file selected")

def set_section_as_done():
    if st.session_state.current_section and st.session_state.current_file:
        try:
            section = next((s for s in st.session_state.current_file.sections if s.name == st.session_state.current_section), None)
            if section:
                for entry in section.entries:
                    entry.status = "Done"
                st.success("Section set as done!")
            else:
                st.warning("Section not found")
        except Exception as e:
            st.error(f"Error setting section as done: {e}")
    else:
        st.warning("No section selected")

def ndx_extract():
    st.info("NDX Extract functionality requires external tools and is not implemented in Streamlit version")

def ndx_make():
    st.info("NDX Make functionality requires external tools and is not implemented in Streamlit version")

def tor_extract():
    st.info("TOR Extract functionality requires external tools and is not implemented in Streamlit version")

def tor_make():
    st.info("TOR Make functionality requires external tools and is not implemented in Streamlit version")

def open_hex_dialog():
    st.info("Hex to Japanese dialog not implemented in Streamlit version")

def search_japanese():
    st.info("Search Japanese functionality not fully implemented")

def perform_search(search_text, language, match_entry, match_case, match_whole):
    if not st.session_state.project or not search_text:
        return
    
    results = []
    for folder in st.session_state.project.xml_folders:
        for file_id, xml_file in enumerate(folder.xml_files):
            for section in xml_file.sections:
                for entry_id, entry in enumerate(section.entries):
                    if entry.is_found(search_text, match_entry, match_case, match_whole, language):
                        ef = EntryFound()
                        ef.folder = folder.name
                        ef.file_id = file_id
                        ef.section = section.name
                        ef.id = entry_id
                        ef.entry = entry
                        results.append(ef)
    
    st.session_state.search_results = results

if __name__ == "__main__":
    main()
