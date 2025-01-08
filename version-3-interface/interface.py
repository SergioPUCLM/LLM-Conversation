import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import json

class DebateConfigInterface:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Debate Server Configuration")
        self.config = {}
        self.available_models = [
            "gemma2-9b-it",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-guard-3-8b",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768"
        ]

        self.create_interface()

    def create_interface(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, padx=10, pady=10)

        # Debate configuration tab
        debate_frame = ttk.Frame(notebook)
        notebook.add(debate_frame, text="Debate Configuration")

        # Add Load JSON button at the top
        load_button = tk.Button(debate_frame, text="Load from JSON", command=self.load_from_json)
        load_button.grid(row=0, column=0, columnspan=2, pady=5)

        # AI Configuration
        # Model Selection
        tk.Label(debate_frame, text="Model 1:", padx=5).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.model1_combo = ttk.Combobox(debate_frame, values=self.available_models, state="readonly", width=30)
        self.model1_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=10)
        self.model1_combo.set("llama3-70b-8192")

        tk.Label(debate_frame, text="Model 2:", padx=5).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.model2_combo = ttk.Combobox(debate_frame, values=self.available_models, state="readonly", width=30)
        self.model2_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=10)
        self.model2_combo.set("llama3-70b-8192")

        # Debate Topic
        tk.Label(debate_frame, text="Debate Topic:").grid(row=3, column=0, sticky=tk.W)
        self.topic_entry = tk.Entry(debate_frame, width=50)
        self.topic_entry.insert(0, "¿La tortilla de patatas está mejor con o sin ketchup?")
        self.topic_entry.grid(row=3, column=1, padx=5, pady=5)

        # Opinions for AI x2
        tk.Label(debate_frame, text="AI 1 Opinion:").grid(row=4, column=0, sticky=tk.W)
        self.opinion1_entry = tk.Entry(debate_frame, width=50)
        self.opinion1_entry.insert(0, "Te gusta mucho el ketchup en la tortilla de patatas")
        self.opinion1_entry.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(debate_frame, text="AI 2 Opinion:").grid(row=5, column=0, sticky=tk.W)
        self.opinion2_entry = tk.Entry(debate_frame, width=50)
        self.opinion2_entry.insert(0, "No te gusta el ketchup en la tortilla de patatas")
        self.opinion2_entry.grid(row=5, column=1, padx=5, pady=5)

        # Personality for AI x2
        tk.Label(debate_frame, text="Personality AI 1:").grid(row=6, column=0, sticky=tk.W)
        self.personality1_entry = tk.Text(debate_frame, height=5, width=50)
        self.personality1_entry.grid(row=6, column=1, padx=5, pady=5)
        
        tk.Label(debate_frame, text="Personality AI 2:").grid(row=7, column=0, sticky=tk.W)
        self.personality2_entry = tk.Text(debate_frame, height=5, width=50)
        self.personality2_entry.grid(row=7, column=1, padx=5, pady=5)

        # Advanced settings tab
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced Settings")

        # Advanced parameters
        params = [
            ("Conversation Length", "CONVERSATION_LENGTH", "9"),
            ("Temperature", "CONVERSATION_TEMPERATURE", "1"),
            ("Convince Time", "CONVINCE_TIME", "2"),
            ("Convince Time Definitive", "CONVINCE_TIME_DEFINITIVE", "1"),
            ("Frequency Penalty", "FREQUENCY_PENALTY", "0.8"),
            ("Presence Penalty", "PRESENCE_PENALTY", "0.5")
        ]

        self.advanced_entries = {}
        for i, (label, key, default) in enumerate(params):
            tk.Label(advanced_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W)
            entry = tk.Entry(advanced_frame, width=50)
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.advanced_entries[key] = entry

        # Start button
        start_button = tk.Button(self.root, text="Start Debate", command=self.start_debate)
        start_button.grid(row=1, column=0, pady=10)

    def load_from_json(self):
        file_path = filedialog.askopenfilename(
            title="Select JSON Configuration File",
            filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                config_data = json.load(file)

            # Update GUI elements with loaded data
            if "model1" in config_data:
                self.model1_combo.set(config_data["model1"])
            if "model2" in config_data:
                self.model2_combo.set(config_data["model2"])
            if "topic" in config_data:
                self.topic_entry.delete(0, tk.END)
                self.topic_entry.insert(0, config_data["topic"])
            if "model1_opinion" in config_data:
                self.opinion1_entry.delete(0, tk.END)
                self.opinion1_entry.insert(0, config_data["model1_opinion"])
            if "model2_opinion" in config_data:
                self.opinion2_entry.delete(0, tk.END)
                self.opinion2_entry.insert(0, config_data["model2_opinion"])
            if "model1_personality" in config_data:
                self.personality1_entry.delete("1.0", tk.END)
                self.personality1_entry.insert("1.0", config_data["model1_personality"])
            if "model2_personality" in config_data:
                self.personality2_entry.delete("1.0", tk.END)
                self.personality2_entry.insert("1.0", config_data["model2_personality"])

            # Update advanced settings
            for key, entry in self.advanced_entries.items():
                if key in config_data:
                    entry.delete(0, tk.END)
                    entry.insert(0, str(config_data[key]))
                    
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error loading JSON file: {str(e)}")

    def start_debate(self):
        # Save configuration
        self.config = {
            "model1_personality": self.personality1_entry.get("1.0", "end-1c"),
            "model1_opinion": self.opinion1_entry.get(),
            "model2_personality": self.personality2_entry.get("1.0","end-1c"),
            "model2_opinion": self.opinion2_entry.get(),
            "topic": self.topic_entry.get(),
            "model1": self.model1_combo.get(),
            "model2": self.model2_combo.get()
        }
        
        # Add advanced settings
        for key, entry in self.advanced_entries.items():
            value = entry.get()
            if value.replace('.', '', 1).isdigit():
                self.config[key] = float(value)
            else:
                print(f"Invalid value for {key}")
                return

        self.root.destroy()  # Close the configuration window

    def get_config(self):
        self.root.mainloop()
        return self.config

class SpeakingWindow:
    def __init__(self, model_name):
        self.window = tk.Tk()
        self.window.title(f"AI Speaking - {model_name}")
        self.window.geometry("800x600")
        
        # Configure grid weights
        self.window.grid_columnconfigure(0, weight=3)  # Avatar column
        self.window.grid_columnconfigure(1, weight=2)  # Text column
        
        # Left frame (Avatar)
        left_frame = ttk.Frame(self.window)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Load avatar image
        avatar_path = f"model-avatars/{model_name}.webp"
        if not os.path.exists(avatar_path):
            avatar_path = "model-avatars/default.jpg"
            
        img = Image.open(avatar_path)
        img = img.resize((300, 300))  # Fixed size
        photo = ImageTk.PhotoImage(img)
        
        avatar_label = ttk.Label(left_frame, image=photo)
        avatar_label.image = photo  # Keep reference
        avatar_label.pack(expand=True)
        
        # Right frame (Text boxes)
        right_frame = ttk.Frame(self.window)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Speaking box
        ttk.Label(right_frame, text="Speaking:").pack(anchor="w")
        self.speaking_text = tk.Text(right_frame, height=10, width=40)
        self.speaking_text.pack(fill="x", pady=(0, 10))
        
        # Listening box
        ttk.Label(right_frame, text="Listening:").pack(anchor="w")
        self.listening_text = tk.Text(right_frame, height=10, width=40)
        self.listening_text.pack(fill="x")
        
    def update_speaking(self, text):
        self.speaking_text.delete(1.0, tk.END)
        self.speaking_text.insert(tk.END, text)
        
    def update_listening(self, text):
        self.listening_text.delete(1.0, tk.END)
        self.listening_text.insert(tk.END, text)