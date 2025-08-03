import os

def load_file(path):
    try:
        with open(path, 'rb') as f:
            return bytearray(f.read())
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

def save_file(path, data):
    try:
        with open(path, 'wb') as f:
            f.write(data)
            print(f"File saved to {path}")
    except Exception as e:
        print(f"Save failed: {e}")
    input("Press Enter to continue...")

def hex_page(data, offset, lines=16):
    os.system('cls' if os.name == 'nt' else 'clear')
    for i in range(offset, min(len(data), offset + lines * 16), 16):
        row = data[i:i+16]
        hex_str = ' '.join(f"{b:02X}" for b in row)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
        print(f"{i:06X}  {hex_str:<47}  {ascii_str}")
    print("\nCommands: n-next  p-prev  j-jump  s-search  e-edit  w-write  a-save-as  i-interleave options  q-quit")

def find_ascii(data, text, case_sensitive=True):
    results = []
    needle = text.encode()
    for i in range(len(data) - len(needle) + 1):
        chunk = data[i:i+len(needle)]
        if chunk == needle:
            results.append(i)
        elif not case_sensitive and chunk.lower() == needle.lower():
            results.append(i)
    return results

def find_hex(data, hex_str):
    try:
        pattern = bytes.fromhex(hex_str.replace(" ", ""))
        results = []
        for i in range(len(data) - len(pattern) + 1):
            if data[i:i+len(pattern)] == pattern:
                results.append(i)
        return results
    except:
        print("Invalid hex pattern.")
        input("Press Enter to continue...")
        return []

def edit_bytes(data, offset, hex_input):
    try:
        new_bytes = bytes.fromhex(hex_input.replace(" ", ""))
        data[offset:offset+len(new_bytes)] = new_bytes
        print("Hex edited successfully.")
    except Exception as e:
        print(f"Edit failed: {e}")
    input("Press Enter to continue...")

def edit_text_at_offset(data, offset, max_len):
    try:
        new_text = input(f"New text (max {max_len} chars): ")
        if len(new_text) > max_len:
            print("Too long. Edit cancelled.")
        else:
            new_bytes = new_text.encode().ljust(max_len, b'\x00')
            data[offset:offset+max_len] = new_bytes
            print("Text edited successfully.")
    except Exception as e:
        print(f"Edit failed: {e}")
    input("Press Enter to continue...")

def interleave(file1, file2, out_file, stride):
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2, open(out_file, 'wb') as out:
        while True:
            chunk1 = f1.read(stride)
            chunk2 = f2.read(stride)
            if not chunk1 and not chunk2:
                break
            out.write(chunk1)
            out.write(chunk2)

def uninterleave(input_file, out1, out2, stride):
    with open(input_file, 'rb') as f, open(out1, 'wb') as f1, open(out2, 'wb') as f2:
        while True:
            chunk1 = f.read(stride)
            chunk2 = f.read(stride)
            if not chunk1:
                break
            f1.write(chunk1)
            if chunk2:
                f2.write(chunk2)

def interleave_menu():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[96m=== Interleave & Uninterleave Tool by Sheikh Nightshader ===\033[0m")
    choice = input("Interleave (i) or Uninterleave (u)? ").strip().lower()
    try:
        stride = int(input("Byte difference (stride): ").strip())
    except:
        print("Invalid stride value.")
        input("Press Enter to continue...")
        return

    if choice == 'i':
        file1 = input("First file: ").strip()
        file2 = input("Second file: ").strip()
        out = input("Output file: ").strip()
        try:
            interleave(file1, file2, out, stride)
            print("\033[92mInterleaving complete.\033[0m")
        except Exception as e:
            print(f"\033[91mFailed: {e}\033[0m")
    elif choice == 'u':
        infile = input("Interleaved file: ").strip()
        out1 = input("Output file 1: ").strip()
        out2 = input("Output file 2: ").strip()
        try:
            uninterleave(infile, out1, out2, stride)
            print("\033[92mUninterleaving complete.\033[0m")
        except Exception as e:
            print(f"\033[91mFailed: {e}\033[0m")
    else:
        print("\033[91mInvalid choice.\033[0m")
    input("Press Enter to continue...")

def viewer(data, path):
    offset = 0
    results = []

    while True:
        hex_page(data, offset)
        cmd = input("Command: ").strip().lower()

        if cmd == 'n':
            offset = min(len(data) - 1, offset + 16 * 16)
        elif cmd == 'p':
            offset = max(0, offset - 16 * 16)
        elif cmd == 'j':
            try:
                offset = int(input("Jump to offset (hex): "), 16)
            except:
                print("Invalid offset.")
                input("Press Enter to continue...")

        elif cmd == 's':
            mode = input("Search [t]ext or [h]ex? ").strip().lower()
            results = []
            if mode == 't':
                text = input("Enter ASCII text to search: ")
                cs = input("Case-sensitive? (y/n): ").strip().lower() == 'y'
                results = find_ascii(data, text, cs)
            elif mode == 'h':
                hexstr = input("Enter hex pattern (e.g. DE AD BE EF): ")
                results = find_hex(data, hexstr)

            if results:
                print(f"{len(results)} match(es) found.")
                for idx, res in enumerate(results):
                    print(f"[{idx}] at 0x{res:06X}")
                try:
                    sel = 0 if len(results) == 1 else int(input("Jump to index #: "))
                    if 0 <= sel < len(results):
                        offset = results[sel]
                        input("Jumped. Press Enter to continue...")
                    else:
                        print("Invalid selection.")
                        input("Press Enter to continue...")
                except:
                    print("Invalid input.")
                    input("Press Enter to continue...")
            else:
                print("No matches found.")
                input("Press Enter to continue...")

        elif cmd == 'e':
            try:
                mode = input("Edit [t]ext or [h]ex? ").strip().lower()
                if mode == 't':
                    off = int(input("Text offset (hex): "), 16)
                    max_len = int(input("Max length of text to replace: "))
                    edit_text_at_offset(data, off, max_len)
                elif mode == 'h':
                    off = int(input("Hex offset (hex): "), 16)
                    hex_input = input("New hex bytes: ")
                    edit_bytes(data, off, hex_input)
                else:
                    print("Unknown edit type.")
                    input("Press Enter to continue...")
            except:
                print("Invalid input.")
                input("Press Enter to continue...")

        elif cmd == 'w':
            save_file(path, data)

        elif cmd == 'a':
            new_path = input("Enter new filename to save as: ").strip()
            if new_path:
                save_file(new_path, data)

        elif cmd == 'i':
            interleave_menu()

        elif cmd == 'q':
            break
        else:
            print("Unknown command.")
            input("Press Enter to continue...")

def main_menu():
    title = """
\033[95m
  H   H  EEEEE  X   X  EEEEE  DDDD
  H   H  E       X X   E      D   D
  HHHHH  EEEE     X    EEEE   D   D
  H   H  E       X X   E      D   D
  H   H  EEEEE  X   X  EEEEE  DDDD
                         
         \033[94mSheikh's HexEditor\033[0m
\033[0m
    """

    options = [
        "1. Open File for Hex Editing",
        "2. Interleave / Uninterleave",
        "3. Quit"
    ]

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(title)
        for opt in options:
            print(opt)
        choice = input("\nSelect an option: ").strip()

        if choice == '1':
            path = input("Enter file path: ").strip()
            if not os.path.isfile(path):
                print("File not found.")
                input("Press Enter to continue...")
            else:
                data = load_file(path)
                if data:
                    viewer(data, path)
        elif choice == '2':
            interleave_menu()
        elif choice == '3':
            break
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main_menu()
