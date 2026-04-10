#!/usr/bin/env python3
"""
AC'S Chip 8 Emulator
Tkinter GUI styled like mGBA — black background, blue button labels
"""

import tkinter as tk
from tkinter import filedialog
import random
import os

class Chip8:
    def __init__(self):
        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [[0]*64 for _ in range(32)]
        self.keys = [0]*16
        self.draw_flag = False
        self.load_fontset()

    def load_fontset(self):
        fontset = [
            0xF0,0x90,0x90,0x90,0xF0,  # 0
            0x20,0x60,0x20,0x20,0x70,  # 1
            0xF0,0x10,0xF0,0x80,0xF0,  # 2
            0xF0,0x10,0xF0,0x10,0xF0,  # 3
            0x90,0x90,0xF0,0x10,0x10,  # 4
            0xF0,0x80,0xF0,0x10,0xF0,  # 5
            0xF0,0x80,0xF0,0x90,0xF0,  # 6
            0xF0,0x10,0x20,0x40,0x40,  # 7
            0xF0,0x90,0xF0,0x90,0xF0,  # 8
            0xF0,0x90,0xF0,0x10,0xF0,  # 9
            0xF0,0x90,0xF0,0x90,0x90,  # A
            0xE0,0x90,0xE0,0x90,0xE0,  # B
            0xF0,0x80,0x80,0x80,0xF0,  # C
            0xE0,0x90,0x90,0x90,0xE0,  # D
            0xF0,0x80,0xF0,0x80,0xF0,  # E
            0xF0,0x80,0xF0,0x80,0x80   # F
        ]
        for i, b in enumerate(fontset):
            self.memory[0x50 + i] = b

    def load_rom(self, path):
        with open(path, 'rb') as f:
            rom = f.read()
        for i, b in enumerate(rom):
            self.memory[0x200 + i] = b
        self.reset()

    def reset(self):
        self.V = [0]*16
        self.I = 0
        self.pc = 0x200
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [[0]*64 for _ in range(32)]
        self.draw_flag = True

    def cycle(self):
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc+1]
        self.pc += 2

        nnn = opcode & 0x0FFF
        n = opcode & 0x000F
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        kk = opcode & 0x00FF

        if opcode == 0x00E0:  # CLS
            self.display = [[0]*64 for _ in range(32)]
            self.draw_flag = True
        elif opcode == 0x00EE:  # RET
            self.pc = self.stack.pop()
        elif (opcode & 0xF000) == 0x1000:  # JP addr
            self.pc = nnn
        elif (opcode & 0xF000) == 0x2000:  # CALL addr
            self.stack.append(self.pc)
            self.pc = nnn
        elif (opcode & 0xF000) == 0x3000:  # SE Vx, byte
            if self.V[x] == kk: self.pc += 2
        elif (opcode & 0xF000) == 0x4000:  # SNE Vx, byte
            if self.V[x] != kk: self.pc += 2
        elif (opcode & 0xF00F) == 0x5000:  # SE Vx, Vy
            if self.V[x] == self.V[y]: self.pc += 2
        elif (opcode & 0xF000) == 0x6000:  # LD Vx, byte
            self.V[x] = kk
        elif (opcode & 0xF000) == 0x7000:  # ADD Vx, byte
            self.V[x] = (self.V[x] + kk) & 0xFF
        elif (opcode & 0xF00F) == 0x8000:
            self.V[x] = self.V[y]
        elif (opcode & 0xF00F) == 0x8001:
            self.V[x] |= self.V[y]
        elif (opcode & 0xF00F) == 0x8002:
            self.V[x] &= self.V[y]
        elif (opcode & 0xF00F) == 0x8003:
            self.V[x] ^= self.V[y]
        elif (opcode & 0xF00F) == 0x8004:
            s = self.V[x] + self.V[y]
            self.V[0xF] = 1 if s > 255 else 0
            self.V[x] = s & 0xFF
        elif (opcode & 0xF00F) == 0x8005:
            self.V[0xF] = 1 if self.V[x] > self.V[y] else 0
            self.V[x] = (self.V[x] - self.V[y]) & 0xFF
        elif (opcode & 0xF00F) == 0x8006:
            self.V[0xF] = self.V[x] & 0x1
            self.V[x] >>= 1
        elif (opcode & 0xF00F) == 0x8007:
            self.V[0xF] = 1 if self.V[y] > self.V[x] else 0
            self.V[x] = (self.V[y] - self.V[x]) & 0xFF
        elif (opcode & 0xF00F) == 0x800E:
            self.V[0xF] = (self.V[x] >> 7) & 0x1
            self.V[x] = (self.V[x] << 1) & 0xFF
        elif (opcode & 0xF00F) == 0x9000:
            if self.V[x] != self.V[y]: self.pc += 2
        elif (opcode & 0xF000) == 0xA000:
            self.I = nnn
        elif (opcode & 0xF000) == 0xB000:
            self.pc = nnn + self.V[0]
        elif (opcode & 0xF000) == 0xC000:
            self.V[x] = random.randint(0,255) & kk
        elif (opcode & 0xF000) == 0xD000:
            self.V[0xF] = 0
            for row in range(n):
                sprite = self.memory[self.I + row]
                for col in range(8):
                    if sprite & (0x80 >> col):
                        px = (self.V[x] + col) % 64
                        py = (self.V[y] + row) % 32
                        if self.display[py][px] == 1:
                            self.V[0xF] = 1
                        self.display[py][px] ^= 1
            self.draw_flag = True
        elif (opcode & 0xF0FF) == 0xE09E:
            if self.keys[self.V[x]]: self.pc += 2
        elif (opcode & 0xF0FF) == 0xE0A1:
            if not self.keys[self.V[x]]: self.pc += 2
        elif (opcode & 0xF0FF) == 0xF007:
            self.V[x] = self.delay_timer
        elif (opcode & 0xF0FF) == 0xF00A:
            pressed = -1
            for i,k in enumerate(self.keys):
                if k: pressed = i; break
            if pressed == -1:
                self.pc -= 2
            else:
                self.V[x] = pressed
        elif (opcode & 0xF0FF) == 0xF015:
            self.delay_timer = self.V[x]
        elif (opcode & 0xF0FF) == 0xF018:
            self.sound_timer = self.V[x]
        elif (opcode & 0xF0FF) == 0xF01E:
            self.I = (self.I + self.V[x]) & 0xFFF
        elif (opcode & 0xF0FF) == 0xF029:
            self.I = 0x50 + (self.V[x] * 5)
        elif (opcode & 0xF0FF) == 0xF033:
            self.memory[self.I] = self.V[x] // 100
            self.memory[self.I+1] = (self.V[x] // 10) % 10
            self.memory[self.I+2] = self.V[x] % 10
        elif (opcode & 0xF0FF) == 0xF055:
            for i in range(x+1):
                self.memory[self.I + i] = self.V[i]
        elif (opcode & 0xF0FF) == 0xF065:
            for i in range(x+1):
                self.V[i] = self.memory[self.I + i]

class ACSChip8:
    def __init__(self, root):
        self.root = root
        root.title("AC'S Chip 8 Emulator")
        root.configure(bg='black')
        root.resizable(False, False)

        self.chip8 = Chip8()
        self.running = False
        self.scale = 10

        # mGBA style header
        header = tk.Label(root, text="AC'S CHIP-8", bg='black', fg='#0080ff',
                          font=('Consolas', 16, 'bold'))
        header.pack(pady=(10,5))

        self.canvas = tk.Canvas(root, width=64*self.scale, height=32*self.scale,
                                bg='black', highlightthickness=1, highlightbackground='#0080ff')
        self.canvas.pack(padx=12, pady=8)

        # create pixels
        self.pixels = []
        for y in range(32):
            row = []
            for x in range(64):
                rect = self.canvas.create_rectangle(
                    x*self.scale, y*self.scale,
                    (x+1)*self.scale, (y+1)*self.scale,
                    fill='black', outline='')
                row.append(rect)
            self.pixels.append(row)

        # control buttons — black bg, blue label
        btn_style = {'bg':'black','fg':'#0080ff','activebackground':'#111111',
                     'activeforeground':'#00aaff','bd':1,'relief':'solid',
                     'font':('Consolas',10,'bold'),'width':12,'highlightbackground':'#0080ff'}

        controls = tk.Frame(root, bg='black')
        controls.pack(pady=5)

        tk.Button(controls, text='LOAD ROM', command=self.load_rom, **btn_style).grid(row=0,column=0,padx=4)
        tk.Button(controls, text='START', command=self.start, **btn_style).grid(row=0,column=1,padx=4)
        tk.Button(controls, text='PAUSE', command=self.pause, **btn_style).grid(row=0,column=2,padx=4)
        tk.Button(controls, text='RESET', command=self.reset, **btn_style).grid(row=0,column=3,padx=4)

        # keypad
        keypad = tk.Frame(root, bg='black')
        keypad.pack(pady=10)
        tk.Label(keypad, text='KEYPAD', bg='black', fg='#0080ff', font=('Consolas',10)).grid(row=0,column=0,columnspan=4,pady=(0,5))

        layout = [['1','2','3','C'],
                  ['4','5','6','D'],
                  ['7','8','9','E'],
                  ['A','0','B','F']]
        key_style = {'bg':'black','fg':'#0080ff','activebackground':'#003366',
                     'activeforeground':'white','width':4,'height':2,
                     'font':('Consolas',12,'bold'),'relief':'solid','bd':1}

        self.key_map = {}
        for r, row in enumerate(layout):
            for c, k in enumerate(row):
                idx = int(k,16)
                btn = tk.Button(keypad, text=k, **key_style)
                btn.grid(row=r+1, column=c, padx=3, pady=3)
                btn.bind('<ButtonPress-1>', lambda e,i=idx: self.key_down(i))
                btn.bind('<ButtonRelease-1>', lambda e,i=idx: self.key_up(i))
                self.key_map[idx] = btn

        # keyboard mapping
        self.keyboard = {
            '1':0x1,'2':0x2,'3':0x3,'4':0xC,
            'q':0x4,'w':0x5,'e':0x6,'r':0xD,
            'a':0x7,'s':0x8,'d':0x9,'f':0xE,
            'z':0xA,'x':0x0,'c':0xB,'v':0xF
        }
        root.bind('<KeyPress>', self.on_key_press)
        root.bind('<KeyRelease>', self.on_key_release)

        self.status = tk.Label(root, text='Ready — Load a .ch8 ROM', bg='black', fg='#0080ff', font=('Consolas',9))
        self.status.pack(pady=(0,10))

        self.update_loop()

    def load_rom(self):
        path = filedialog.askopenfilename(filetypes=[('Chip-8 ROMs','*.ch8 *.c8 *.rom'),('All files','*.*')])
        if path:
            self.chip8.load_rom(path)
            self.status.config(text=f'Loaded: {os.path.basename(path)}')
            self.draw()

    def start(self):
        self.running = True
        self.status.config(text='Running')

    def pause(self):
        self.running = False
        self.status.config(text='Paused')

    def reset(self):
        self.chip8.reset()
        self.draw()
        self.status.config(text='Reset')

    def key_down(self, idx):
        self.chip8.keys[idx] = 1
        if idx in self.key_map:
            self.key_map[idx].config(bg='#003366')

    def key_up(self, idx):
        self.chip8.keys[idx] = 0
        if idx in self.key_map:
            self.key_map[idx].config(bg='black')

    def on_key_press(self, e):
        k = e.keysym.lower()
        if k in self.keyboard:
            self.key_down(self.keyboard[k])

    def on_key_release(self, e):
        k = e.keysym.lower()
        if k in self.keyboard:
            self.key_up(self.keyboard[k])

    def draw(self):
        for y in range(32):
            for x in range(64):
                color = '#00e5ff' if self.chip8.display[y][x] else 'black'
                self.canvas.itemconfig(self.pixels[y][x], fill=color)
        self.chip8.draw_flag = False

    def update_loop(self):
        if self.running:
            # ~500 Hz: 8 cycles per frame at 60fps
            for _ in range(10):
                self.chip8.cycle()
            if self.chip8.delay_timer > 0:
                self.chip8.delay_timer -= 1
            if self.chip8.sound_timer > 0:
                self.chip8.sound_timer -= 1
            if self.chip8.draw_flag:
                self.draw()
        self.root.after(16, self.update_loop)

if __name__ == '__main__':
    root = tk.Tk()
    app = ACSChip8(root)
    root.mainloop()
