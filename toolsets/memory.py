import os
from datetime import datetime
from .toolkit import tool, toolset

# The directory where all notes will be persistently stored
NOTES_DIR = r"C:\Users\Redux Gamer\AI-Notes"

@toolset
class MemoryToolset:
    @tool
    def get_notes(self) -> str:
        """Retrieve all currently saved notes."""
        if not os.path.exists(NOTES_DIR):
            return "No notes found. Directory does not exist yet."
        
        try:
            notes = []
            for filename in os.listdir(NOTES_DIR):
                if filename.endswith(".txt"):
                    filepath = os.path.join(NOTES_DIR, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    notes.append(f"--- {filename} ---\n{content}\n")
            
            if not notes:
                return "No notes found."
            
            return "\n".join(notes)
        except Exception as e:
            return f"Error retrieving notes: {e}"

    @tool
    def create_note(self, content: str) -> str:
        """Create a new saved note with the given content. Only make notes when you think you'll need this info for later or can't get it later without asking."""
        try:
            # Ensure the folder exists
            os.makedirs(NOTES_DIR, exist_ok=True)
            
            # Use timestamp to make guaranteed unique filenames
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"note_{timestamp}.txt"
            filepath = os.path.join(NOTES_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return f"Note successfully securely stored at: {filepath}"
        except Exception as e:
            return f"Error creating note: {e}"