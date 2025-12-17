#!/usr/bin/env python3
#version 2.3
import os,sys,struct

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
    print("\nCommands: n-next  p-prev  j-jump  s-search  e-edit  w-write  a-save-as  v-palette viewer  i-interleave options  q-quit")

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

def rgb555_to_rgb888(v):
    r = (v >> 10) & 0x1F
    g = (v >> 5) & 0x1F
    b = v & 0x1F
    r = (r * 255) // 31
    g = (g * 255) // 31
    b = (b * 255) // 31
    return r,g,b

def rgb5551_to_rgb888(v):
    r = (v >> 11) & 0x1F
    g = (v >> 6) & 0x1F
    b = (v >> 1) & 0x1F
    r = (r * 255) // 31
    g = (g * 255) // 31
    b = (b * 255) // 31
    return r,g,b

def rgb444_to_rgb888(v):
    # Big-endian: word = [BBBB GGGG RRRR]
    r = v & 0xF          
    g = (v >> 4) & 0xF   
    b = (v >> 8) & 0xF   
    # scale 0-15 → 0-255
    r = (r * 255) // 15
    g = (g * 255) // 15
    b = (b * 255) // 15
    return r, g, b

def bg_block(r,g,b,w=6):
    return f"\x1b[48;2;{r};{g};{b}m" + " " * w + "\x1b[0m"

def print_palette_grid(data, pal_off, count, cols=16, fmt='rgb555', endian='le'):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\033[95m=== Palette Viewer — Sheikh Nightshader ===\033[0m")
    print(f"Offset: 0x{pal_off:X}  Entries: {count}  Format: {fmt}  Endian: {endian}\n")

    rows = (count + cols - 1) // cols

    for row in range(rows):
        row_start_idx = row * cols
        row_offset = pal_off + row_start_idx * 2
        line_colors = []
        line_hexes = []

        for col in range(cols):
            idx = row_start_idx + col
            addr = pal_off + idx * 2
            if idx >= count or addr + 1 >= len(data):
                line_colors.append(" " * 6)
                line_hexes.append(" " * 6)
                continue

            if endian == 'le':
                v = data[addr] | (data[addr + 1] << 8)
            else:
                v = (data[addr] << 8) | data[addr + 1]

            if fmt == 'rgb555':
                r, g, b = rgb555_to_rgb888(v)
            elif fmt == 'rgb5551':
                r, g, b = rgb5551_to_rgb888(v)
            elif fmt == 'rgb444':
                r, g, b = rgb444_to_rgb888(v)

            line_colors.append(bg_block(r, g, b, 2))
            line_hexes.append(f"{v:04X}".ljust(6))

        print(f"{row_offset:06X}  " + " ".join(line_colors) + "  " + " ".join(line_hexes))

    print("\nCommands: e-edit  o-offset  c-count  f-toggle-format  n-toggle-endian  s-save  r-reload  p-paste  q-back")

def edit_palette_entry_by_offset(data, offset, fmt, endian):
    try:
        hx = input("Enter hex values (groups of 4 digits): ").strip().replace(" ", "").replace(",", "")
        if len(hx) == 0 or len(hx) % 4 != 0:
            print("Invalid hex length.")
            input("Enter to continue...")
            return
        for i in range(0, len(hx), 4):
            v = int(hx[i:i+4], 16)
            o = offset + (i//4)*2
            if o+1 >= len(data):
                break
            if endian == 'le':
                data[o] = v & 0xFF
                data[o+1] = (v >> 8) & 0xFF
            else:
                data[o] = (v >> 8) & 0xFF
                data[o+1] = v & 0xFF
        print("Written.")
    except:
        print("Bad hex.")
    input("Enter to continue...")

def paste_palette_hex(data, offset, hex_data, endian):
    try:
        cleaned = hex_data.replace(" ", "").replace("\n", "").replace("\r", "").replace(",", "")
        if len(cleaned) % 4 != 0:
            print("Invalid length. Need multiples of 4 hex digits per 16-bit color.")
            input("Enter to continue...")
            return
        for i in range(0, len(cleaned), 4):
            j = i // 4
            v = int(cleaned[i:i+4], 16) & 0xFFFF
            o = offset + j*2
            if o+1 >= len(data):
                break
            if endian == 'le':
                data[o] = v & 0xFF
                data[o+1] = (v >> 8) & 0xFF
            else:
                data[o] = (v >> 8) & 0xFF
                data[o+1] = v & 0xFF
        print("Pasted.")
    except Exception as e:
        print(f"Pasting failed: {e}")
    input("Enter to continue...")

def palette_viewer(data, path, start_offset=0):
    pal_off = start_offset
    if pal_off < 0:
        pal_off = 0
    pal_off = pal_off - (pal_off % 2)
    count = 256
    cols = 16
    fmt = 'rgb555'
    endian = 'le'
    while True:
        print_palette_grid(data, pal_off, count, cols, fmt, endian)
        cmd = input("pal> ").strip().lower()
        if cmd == 'q':
            break
        elif cmd == 'e':
            try:
                off = int(input("Hex offset: "),16)
                edit_palette_entry_by_offset(data, off, fmt, endian)
            except:
                pass
        elif cmd == 'o':
            try:
                pal_off = int(input("hex offset: "),0)
                pal_off = pal_off - (pal_off % 2)
            except:
                pass
        elif cmd == 'c':
            try:
                count = int(input("count: "))
            except:
                pass
        elif cmd == 'f':
            if fmt == 'rgb555':
                fmt = 'rgb5551'
            elif fmt == 'rgb5551':
                fmt = 'rgb444'
            else:
                fmt = 'rgb555'
        elif cmd == 'n':
            endian = 'be' if endian == 'le' else 'le'
        elif cmd == 's':
            save_file(path, data)
        elif cmd == 'r':
            fresh = load_file(path)
            if fresh:
                data[:] = fresh
        elif cmd == 'p':
            try:
                off = int(input("Hex offset: "),16)
                hx_lines = []
                print("Paste hex colors (4 hex digits per color). End with a blank line.")
                while True:
                    line = input()
                    if line.strip() == "":
                        break
                    hx_lines.append(line)
                hx = "\n".join(hx_lines)
                paste_palette_hex(data, off, hx, endian)
            except:
                pass
        else:
            pass

def viewer(data, path):
    offset = 0
    results = []
    while True:
        hex_page(data, offset)
        cmd = input("Command: ").strip().lower()
        if cmd == 'n':
            offset = min(len(data)-1, offset + 256)
        elif cmd == 'p':
            offset = max(0, offset - 256)
        elif cmd == 'j':
            try:
                offset = int(input("offset hex: "),16)
            except:
                pass
        elif cmd == 's':
            mode = input("Search [t]ext or [h]ex? ").strip().lower()
            results = []
            if mode == 't':
                text = input("ASCII: ")
                cs = input("Case-sensitive? (y/n): ").strip().lower()=='y'
                results = find_ascii(data, text, cs)
            elif mode == 'h':
                hexstr = input("Hex: ")
                results = find_hex(data, hexstr)
            if results:
                for i,r in enumerate(results):
                    print(f"[{i}] at 0x{r:06X}")
                try:
                    sel = int(input("jump #: "))
                    offset = results[sel]
                except:
                    pass
            input("Press Enter...")
        elif cmd == 'e':
            mode = input("Edit [t]ext or [h]ex? ").strip().lower()
            try:
                if mode == 't':
                    off = int(input("offset hex: "),16)
                    max_len = int(input("max len: "))
                    edit_text_at_offset(data, off, max_len)
                else:
                    off = int(input("offset hex: "),16)
                    hx = input("hex bytes: ")
                    edit_bytes(data, off, hx)
            except:
                pass
        elif cmd == 'w':
            save_file(path, data)
        elif cmd == 'a':
            p = input("new filename: ").strip()
            save_file(p, data)
        elif cmd == 'i':
            interleave_menu()
        elif cmd == 'v':
            palette_viewer(data, path, offset)
        elif cmd == 'q':
            break

def main_menu():
    title = """
\033[95m
  H   H  EEEEE  X   X  EEEEE  DDDD
  H   H  E       X X   E      D   D
  HHHHH  EEEE     X    EEEE   D   D
  H   H  E       X X   E      D   D
  H   H  EEEEE  X   X  EEEEE  DDDD
                         
      \033[94mSheikh's HexEditor v2.3\033[0m
\033[0m
    """
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(title)
        print("1. Open File")
        print("2. Interleave / Uninterleave")
        print("3. Quit")
        c = input("> ").strip()
        if c == '1':
            path = input("File: ").strip()
            if os.path.isfile(path):
                data = load_file(path)
                viewer(data, path)
        elif c == '2':
            interleave_menu()
        elif c == '3':
            break

if __name__ == "__main__":
    main_menu()
