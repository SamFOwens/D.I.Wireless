import pyvisa
import tkinter as tk

# 1. Setup Connection
rm = pyvisa.ResourceManager('@py')
gen = rm.open_resource('USB0::2391::1031::MY44006981::0::INSTR')

# 2. Initial Config
gen.write('*RST')           
gen.write('OUTP:LOAD 25')  
gen.write('VOLT 1.5')       
gen.write('FUNC SIN')       
gen.write('OUTP ON')        

# 3. Define Note Map 
notes = {
    # White Keys
    'a': (246.94*4, 'B5'),
    's': (261.63*4, 'C6'),
    'd': (293.66*4, 'D6'),
    'f': (329.63*4, 'E6'),
    'g': (349.23*4, 'F6'),
    'h': (392.00*4, 'G6'),
    'j': (440.00*4, 'A6'),
    'k': (493.88*4, 'B6'),
    'l': (523.25*4, 'C7'),
    ';': (587.33*4, 'D7'), 
    "'": (659.25*4, 'E7'),
    
    # Black Keys
    'e': (277.18*4, 'C#6'),
    'r': (311.13*4, 'D#6'),
    'y': (369.99*4, 'F#6'),
    'u': (415.30*4, 'G#6'),
    'i': (466.16*4, 'A#6'),
    'p': (554.37*4, 'C#7'), 
    '[': (622.25*4, 'D#7')
}

# The visual order of keys
white_keys = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"]
black_keys = {'e': 1, 'r': 2, 'y': 4, 'u': 5, 'i': 6, 'p': 8, '[': 9}

# 4. App Window Setup
root = tk.Tk()
root.title("Agilent 33220A Synth")
root.geometry("600x300") 
root.configure(bg="#2b2b2b") 

status_label = tk.Label(root, text="Click here first to play", font=("Helvetica", 16), fg="white", bg="#2b2b2b")
status_label.pack(pady=15)

canvas = tk.Canvas(root, width=550, height=200, bg="#2b2b2b", highlightthickness=0)
canvas.pack()

key_rects = {}
active_keys = {} 

# 5. The Press and Release Logic
def key_down(event):
    char = event.char.lower()
    if char in notes and not active_keys.get(char, False):
        active_keys[char] = True
        freq, note_name = notes[char]
        
        gen.write(f'FREQ {freq}')
        status_label.config(text=f"Playing: {note_name} | Freq: {freq} Hz")
        
        color = "#00ffff" if char in white_keys else "#0055ff"
        canvas.itemconfig(key_rects[char], fill=color)

def key_up(event):
    char = event.char.lower()
    if char in notes:
        active_keys[char] = False
        
        original_color = "white" if char in white_keys else "black"
        canvas.itemconfig(key_rects[char], fill=original_color)
        gen.write(f'FREQ 50')

# 6. Drawing the Piano Graphics
for i, char in enumerate(white_keys):
    x1 = i * 50
    x2 = x1 + 50
    rect = canvas.create_rectangle(x1, 0, x2, 200, fill="white", outline="black")
    key_rects[char] = rect

for char, pos in black_keys.items():
    x1 = (pos * 50) + 35 
    x2 = x1 + 30
    rect = canvas.create_rectangle(x1, 0, x2, 120, fill="black", outline="black")
    key_rects[char] = rect

# 7. Bind the computer keyboard to the app
root.bind('<KeyPress>', key_down)
root.bind('<KeyRelease>', key_up)

# 8. Safe Shutdown
def on_closing():
    print("Shutting down output...")
    gen.write('OUTP OFF')
    gen.close()
    root.destroy() 

root.protocol("WM_DELETE_WINDOW", on_closing)

# Run App
root.mainloop()