import pyvisa
import time
import curses
import threading

# --- HARDWARE CONFIGURATION ---
MAX_VOLTAGE = 1.7            # Locked at 1.7Vpp
IMPEDANCE = "25"             # 25-ohm load
INAUDIBLE_FREQ = 1.0         # 1 Hz represents "silence"
OCTAVE_SHIFT = 1             # Transpose everything up 2 octaves
WAVEFORM = "SQUare"          # Square waves sound more like an ice cream truck
# ------------------------------

def midi_to_freq(note):
    """Converts a MIDI note number to Hz, applying an octave shift."""
    if note == 0: return INAUDIBLE_FREQ
    shifted_note = note + (OCTAVE_SHIFT * 12)
    return 440.0 * (2.0 ** ((shifted_note - 69) / 12.0))

# --- FULL SONG TRANSCRIPTIONS ---
# Format: (MIDI_Note, Note_Duration_Secs, Rest_After_Secs)
# 0 = Musical Rest

songs = {
    "Daisy Bell (Bicycle Built for Two)": [
        (79, 0.6, 0.1), (76, 0.6, 0.1), (72, 0.6, 0.1), (67, 0.6, 0.1), # Daisy, Daisy
        (69, 0.3, 0.05), (72, 0.3, 0.05), (69, 0.3, 0.05), (67, 0.4, 0.1), (64, 0.3, 0.05), (60, 0.8, 0.2), # Give me your answer do
        (62, 0.6, 0.1), (65, 0.6, 0.1), (69, 0.6, 0.1), (67, 0.6, 0.1), # I'm half crazy
        (64, 0.3, 0.05), (65, 0.3, 0.05), (67, 0.3, 0.05), (69, 0.4, 0.1), (62, 0.4, 0.1), (67, 0.8, 0.2), # All for the love of you
        (76, 0.4, 0.05), (74, 0.2, 0.05), (72, 0.3, 0.05), (69, 0.3, 0.05), (72, 0.4, 0.1), (69, 0.3, 0.05), (67, 0.3, 0.05), # It won't be a stylish marriage
        (60, 0.3, 0.05), (62, 0.3, 0.05), (64, 0.3, 0.05), (67, 0.3, 0.05), (69, 0.3, 0.05), (72, 0.3, 0.05), (69, 0.6, 0.1), # I can't afford a carriage
        (67, 0.4, 0.1), (72, 0.4, 0.1), (69, 0.4, 0.1), (67, 0.3, 0.05), (64, 0.3, 0.05), (60, 0.4, 0.1), # But you'll look sweet, upon the seat
        (62, 0.3, 0.05), (64, 0.3, 0.05), (67, 0.3, 0.05), (71, 0.3, 0.05), (72, 0.8, 0.4) # Of a bicycle built for two!
    ],
    "Mister Softee Theme (Full)": [
        (76, 0.2, 0.05), (72, 0.2, 0.05), (76, 0.2, 0.05), (72, 0.2, 0.05), (76, 0.2, 0.05), (72, 0.2, 0.05), (76, 0.4, 0.05),
        (79, 0.2, 0.05), (77, 0.2, 0.05), (74, 0.2, 0.05), (77, 0.2, 0.05), (74, 0.2, 0.05), (77, 0.2, 0.05), (74, 0.2, 0.05), (77, 0.4, 0.05),
        (77, 0.2, 0.05), (74, 0.2, 0.05), (77, 0.2, 0.05), (74, 0.2, 0.05), (77, 0.2, 0.05), (74, 0.2, 0.05), (77, 0.4, 0.05),
        (76, 0.2, 0.05), (72, 0.2, 0.05), (76, 0.2, 0.05), (72, 0.2, 0.05), (76, 0.2, 0.05), (72, 0.2, 0.05), (76, 0.4, 0.2)
    ],
    "Turkey in the Straw (Full A & B Part)": [
        (67, 0.2, 0.05), (67, 0.2, 0.05), (71, 0.2, 0.05), (67, 0.2, 0.05), (69, 0.2, 0.05), (67, 0.2, 0.05), (64, 0.2, 0.05), (62, 0.4, 0.05),
        (67, 0.2, 0.05), (67, 0.2, 0.05), (71, 0.2, 0.05), (67, 0.2, 0.05), (69, 0.2, 0.05), (71, 0.2, 0.05), (74, 0.6, 0.1),
        (74, 0.2, 0.05), (76, 0.2, 0.05), (74, 0.2, 0.05), (71, 0.2, 0.05), (69, 0.2, 0.05), (67, 0.2, 0.05), (64, 0.2, 0.05), (62, 0.4, 0.05),
        (67, 0.2, 0.05), (64, 0.2, 0.05), (62, 0.2, 0.05), (64, 0.2, 0.05), (67, 0.4, 0.05), (67, 0.6, 0.2)
    ],
    "Pop Goes the Weasel (Complete)": [
        (60, 0.3, 0.05), (60, 0.3, 0.05), (62, 0.3, 0.05), (62, 0.3, 0.05), (64, 0.2, 0.05), (67, 0.2, 0.05), (64, 0.2, 0.05), (60, 0.4, 0.1),
        (60, 0.3, 0.05), (60, 0.3, 0.05), (62, 0.3, 0.05), (62, 0.3, 0.05), (64, 0.6, 0.2),
        (60, 0.3, 0.05), (60, 0.3, 0.05), (62, 0.3, 0.05), (62, 0.3, 0.05), (64, 0.2, 0.05), (67, 0.2, 0.05), (64, 0.2, 0.05), (60, 0.4, 0.1),
        (69, 0.6, 0.1), (65, 0.4, 0.1), (64, 0.2, 0.05), (62, 0.2, 0.05), (60, 0.6, 0.4)
    ],
    "Yankee Doodle (Verse & Chorus)": [
        (60, 0.2, 0.05), (60, 0.2, 0.05), (62, 0.2, 0.05), (64, 0.2, 0.05), (60, 0.2, 0.05), (64, 0.2, 0.05), (62, 0.4, 0.1),
        (60, 0.2, 0.05), (60, 0.2, 0.05), (62, 0.2, 0.05), (64, 0.2, 0.05), (60, 0.2, 0.05), (59, 0.4, 0.1),
        (60, 0.2, 0.05), (60, 0.2, 0.05), (62, 0.2, 0.05), (64, 0.2, 0.05), (65, 0.2, 0.05), (64, 0.2, 0.05), (62, 0.2, 0.05), (60, 0.2, 0.05),
        (59, 0.2, 0.05), (55, 0.2, 0.05), (57, 0.2, 0.05), (59, 0.2, 0.05), (60, 0.4, 0.05), (60, 0.6, 0.2),
        (65, 0.3, 0.05), (64, 0.1, 0.05), (65, 0.2, 0.05), (67, 0.2, 0.05), (65, 0.4, 0.05), (64, 0.4, 0.05),
        (62, 0.3, 0.05), (64, 0.1, 0.05), (62, 0.2, 0.05), (60, 0.2, 0.05), (62, 0.4, 0.05), (64, 0.2, 0.05), (60, 0.2, 0.05)
    ],
    "London Bridge (Extended)": [
        (67, 0.3, 0.05), (69, 0.2, 0.05), (67, 0.2, 0.05), (65, 0.2, 0.05), (64, 0.2, 0.05), (65, 0.2, 0.05), (67, 0.4, 0.1),
        (62, 0.2, 0.05), (64, 0.2, 0.05), (65, 0.4, 0.1), (64, 0.2, 0.05), (65, 0.2, 0.05), (67, 0.4, 0.1),
        (67, 0.3, 0.05), (69, 0.2, 0.05), (67, 0.2, 0.05), (65, 0.2, 0.05), (64, 0.2, 0.05), (65, 0.2, 0.05), (67, 0.4, 0.1),
        (62, 0.4, 0.05), (67, 0.4, 0.05), (64, 0.2, 0.05), (60, 0.6, 0.2)
    ],
    "Oh! Susanna (Verse & Chorus)": [
        (60, 0.2, 0.05), (62, 0.2, 0.05), (64, 0.3, 0.05), (67, 0.3, 0.05), (67, 0.3, 0.05), (69, 0.2, 0.05), (67, 0.2, 0.05), (64, 0.2, 0.05), 
        (60, 0.3, 0.05), (62, 0.3, 0.05), (64, 0.2, 0.05), (64, 0.2, 0.05), (62, 0.2, 0.05), (60, 0.2, 0.05), (62, 0.6, 0.1),
        (60, 0.2, 0.05), (62, 0.2, 0.05), (64, 0.3, 0.05), (67, 0.3, 0.05), (67, 0.3, 0.05), (69, 0.2, 0.05), (67, 0.2, 0.05), (64, 0.2, 0.05), 
        (60, 0.3, 0.05), (62, 0.3, 0.05), (64, 0.2, 0.05), (64, 0.2, 0.05), (62, 0.2, 0.05), (62, 0.2, 0.05), (60, 0.8, 0.2),
        (65, 0.4, 0.05), (65, 0.4, 0.05), (69, 0.6, 0.05), (69, 0.4, 0.05), (67, 0.4, 0.05), (67, 0.2, 0.05), (64, 0.2, 0.05), (60, 0.6, 0.2)
    ],
    "Camptown Races (Full)": [
        (67, 0.3, 0.05), (67, 0.3, 0.05), (64, 0.2, 0.05), (67, 0.2, 0.05), (69, 0.4, 0.05), (67, 0.4, 0.05), (64, 0.6, 0.1),
        (62, 0.4, 0.05), (62, 0.4, 0.05), (64, 0.2, 0.05), (62, 0.2, 0.05), (60, 0.4, 0.1),
        (67, 0.3, 0.05), (67, 0.3, 0.05), (64, 0.2, 0.05), (67, 0.2, 0.05), (69, 0.4, 0.05), (67, 0.4, 0.05), (64, 0.6, 0.1),
        (62, 0.4, 0.05), (64, 0.2, 0.05), (62, 0.2, 0.05), (60, 0.6, 0.2)
    ],
    "The Entertainer (Full A-Section)": [
        (74, 0.15, 0.05), (75, 0.15, 0.05), (76, 0.15, 0.05), (84, 0.3, 0.1), (76, 0.15, 0.05), (84, 0.3, 0.1), (76, 0.15, 0.05), (84, 0.5, 0.1),
        (84, 0.15, 0.05), (83, 0.15, 0.05), (81, 0.15, 0.05), (79, 0.15, 0.05), (81, 0.15, 0.05), (79, 0.15, 0.05), (76, 0.15, 0.05), (77, 0.15, 0.05), (79, 0.6, 0.2),
        (74, 0.15, 0.05), (75, 0.15, 0.05), (76, 0.15, 0.05), (84, 0.3, 0.1), (76, 0.15, 0.05), (84, 0.3, 0.1), (76, 0.15, 0.05), (84, 0.5, 0.1),
        (79, 0.15, 0.05), (81, 0.15, 0.05), (83, 0.15, 0.05), (84, 0.15, 0.05), (86, 0.15, 0.05), (84, 0.15, 0.05), (81, 0.15, 0.05), (83, 0.15, 0.05), (84, 0.8, 0.2)
    ]
}

# --- THREADING & PLAYBACK LOGIC ---
stop_event = threading.Event()
current_thread = None

def smart_sleep(duration, stop_ev):
    end = time.time() + duration
    while time.time() < end:
        if stop_ev.is_set(): return False
        time.sleep(0.01)
    return True

def play_tune(agilent, song_name, stop_ev):
    melody = songs[song_name]
    while not stop_ev.is_set():
        for note, duration, rest in melody:
            if stop_ev.is_set(): break
            
            freq = midi_to_freq(note)
            agilent.write(f"FREQuency {freq:.3f}")
            if not smart_sleep(duration, stop_ev): break
            
            if rest > 0:
                agilent.write(f"FREQuency {INAUDIBLE_FREQ}")
                if not smart_sleep(rest, stop_ev): break
        
        if not stop_ev.is_set():
            agilent.write(f"FREQuency {INAUDIBLE_FREQ}")
            smart_sleep(1.5, stop_ev) # 1.5 second pause between loops

# --- CURSES TUI ---
def draw_menu(stdscr, agilent):
    global current_thread, stop_event
    curses.curs_set(0)
    stdscr.nodelay(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    
    menu_items = list(songs.keys())
    current_row = 0
    playing_song = None

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        
        title = " 🍦 MR. AGILENT'S 8-BIT ICE CREAM TRUCK 🍦 "
        stdscr.addstr(1, w//2 - len(title)//2, title, curses.A_BOLD | curses.color_pair(1))
        
        status = f" Status: [{'PLAYING' if playing_song else 'STOPPED'}] {playing_song if playing_song else ''}"
        stdscr.addstr(3, 2, status, curses.A_BOLD)
        stdscr.addstr(4, 2, "-" * (w - 4))

        for idx, row in enumerate(menu_items):
            x = w//2 - len(row)//2
            y = h//2 - len(menu_items)//2 + idx
            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, f" > {row} < ")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, f"   {row}   ")
                
        footer = "[UP/DOWN]: Select   [ENTER]: Play   [S]: Stop   [Q]: Quit"
        stdscr.addstr(h-2, w//2 - len(footer)//2, footer)
        
        stdscr.refresh()
        
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items)-1:
            current_row += 1
        elif key in [10, 13]: 
            if current_thread and current_thread.is_alive():
                stop_event.set()
                current_thread.join()
            stop_event.clear()
            playing_song = menu_items[current_row]
            current_thread = threading.Thread(target=play_tune, args=(agilent, playing_song, stop_event))
            current_thread.start()
        elif key in [ord('s'), ord('S')]:
            if current_thread and current_thread.is_alive():
                stop_event.set()
                current_thread.join()
            playing_song = None
            agilent.write(f"FREQuency {INAUDIBLE_FREQ}")
        elif key in [ord('q'), ord('Q')]:
            if current_thread and current_thread.is_alive():
                stop_event.set()
                current_thread.join()
            break
            
        time.sleep(0.05)

# --- MAIN EXECUTION ---
def main():
    rm = pyvisa.ResourceManager('@py')
    try:
        resources = rm.list_resources()
        usb_instruments = [res for res in resources if 'USB' in res]
        if not usb_instruments:
            print("No Agilent found. Check USB connection.")
            return
            
        agilent = rm.open_resource(usb_instruments[0])
        
        # Hardware Setup
        agilent.write("*RST")
        time.sleep(0.5)
        agilent.write(f"FUNCtion {WAVEFORM}") 
        agilent.write(f"OUTPut:LOAD {IMPEDANCE}")
        agilent.write(f"VOLTage {MAX_VOLTAGE}") 
        agilent.write(f"FREQuency {INAUDIBLE_FREQ}")
        agilent.write("OUTPut ON")
        
        curses.wrapper(draw_menu, agilent)
        
    except Exception as e:
        print(f"Hardware Error: {e}")
    finally:
        try:
            agilent.write("VOLTage 0.01")
            agilent.write("OUTPut OFF")
            agilent.close()
        except:
            pass

if __name__ == "__main__":
    main()
