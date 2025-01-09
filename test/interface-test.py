import tkinter as tk
from tkinter import ttk

# Function to create the Tkinter interface
def create_interface():
    # Initialize the main window
    root = tk.Tk()
    root.title("AI Debate Interface")
    
    # Create a notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, padx=10, pady=10)
    
    # Create the main debate configuration tab
    debate_frame = ttk.Frame(notebook)
    notebook.add(debate_frame, text="Debate Configuration")
    
    # Add labels and text entries for each required field in the debate tab
    
    # Personality for AI 1
    tk.Label(debate_frame, text="Personality AI 1:").grid(row=0, column=0, sticky=tk.W)
    personality1_entry = tk.Text(debate_frame, height=5, width=50)
    personality1_entry.grid(row=0, column=1, padx=5, pady=5)
    
    # Personality for AI 2
    tk.Label(debate_frame, text="Personality AI 2:").grid(row=1, column=0, sticky=tk.W)
    personality2_entry = tk.Text(debate_frame, height=5, width=50)
    personality2_entry.grid(row=1, column=1, padx=5, pady=5)
    
    # Opinion for AI 1
    tk.Label(debate_frame, text="Opinion AI 1:").grid(row=2, column=0, sticky=tk.W)
    opinion1_entry = tk.Entry(debate_frame, width=50)
    opinion1_entry.grid(row=2, column=1, padx=5, pady=5)
    
    # Opinion for AI 2
    tk.Label(debate_frame, text="Opinion AI 2:").grid(row=3, column=0, sticky=tk.W)
    opinion2_entry = tk.Entry(debate_frame, width=50)
    opinion2_entry.grid(row=3, column=1, padx=5, pady=5)
    
    
    # Debate topic
    tk.Label(debate_frame, text="Debate Topic:").grid(row=5, column=0, sticky=tk.W)
    topic_entry = tk.Entry(debate_frame, width=50)
    topic_entry.grid(row=5, column=1, padx=5, pady=5)
    
    # Create the advanced settings tab
    advanced_frame = ttk.Frame(notebook)
    notebook.add(advanced_frame, text="Advanced Settings")
    
    # Add labels and text entries for advanced settings
    
    # Conversation Length
    tk.Label(advanced_frame, text="CONVERSATION_LENGTH:").grid(row=0, column=0, sticky=tk.W)
    conversation_length_entry = tk.Entry(advanced_frame, width=50)
    conversation_length_entry.insert(0, "9")
    conversation_length_entry.grid(row=0, column=1, padx=5, pady=5)
    
    # Conversation Temperature
    tk.Label(advanced_frame, text="CONVERSATION_TEMPERATURE:").grid(row=1, column=0, sticky=tk.W)
    conversation_temperature_entry = tk.Entry(advanced_frame, width=50)
    conversation_temperature_entry.insert(0, "1")
    conversation_temperature_entry.grid(row=1, column=1, padx=5, pady=5)
    
    # Convince Time
    tk.Label(advanced_frame, text="CONVINCE_TIME:").grid(row=2, column=0, sticky=tk.W)
    convince_time_entry = tk.Entry(advanced_frame, width=50)
    convince_time_entry.insert(0, "2")
    convince_time_entry.grid(row=2, column=1, padx=5, pady=5)
    
    # Convince Time Definitive
    tk.Label(advanced_frame, text="CONVINCE_TIME_DEFINITIVE:").grid(row=3, column=0, sticky=tk.W)
    convince_time_definitive_entry = tk.Entry(advanced_frame, width=50)
    convince_time_definitive_entry.insert(0, "1")
    convince_time_definitive_entry.grid(row=3, column=1, padx=5, pady=5)
    
    # Frequency Penalty
    tk.Label(advanced_frame, text="FREQUENCY_PENALTY:").grid(row=4, column=0, sticky=tk.W)
    frequency_penalty_entry = tk.Entry(advanced_frame, width=50)
    frequency_penalty_entry.insert(0, "0.8")
    frequency_penalty_entry.grid(row=4, column=1, padx=5, pady=5)
    
    # Presence Penalty
    tk.Label(advanced_frame, text="PRESENCE_PENALTY:").grid(row=5, column=0, sticky=tk.W)
    presence_penalty_entry = tk.Entry(advanced_frame, width=50)
    presence_penalty_entry.insert(0, "0.5")
    presence_penalty_entry.grid(row=5, column=1, padx=5, pady=5)
    
    # Run the Tkinter main loop
    root.mainloop()

# Call the function to create the interface
create_interface()