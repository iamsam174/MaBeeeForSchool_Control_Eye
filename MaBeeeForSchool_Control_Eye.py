import tkinter as tk
from tkinter import ttk, messagebox
import threading
import cv2
from PIL import Image, ImageTk
import winsound
import sys
import asyncio
import traceback
import configparser
import os
from bleak import BleakClient, BleakScanner

# MaBeee for School (Scratch) dedicated app
class App:
      def __init__(self, root):
                self.root = root
                self.root.title("MaBeeeForSchool Control Eye App")

        self.root.state('zoomed')
        self.root.configure(bg="#f0f0f0")

        self.config_file = "config_school.ini"
        self.config = configparser.ConfigParser()
        self.load_config()

        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("1", lambda e: self.mode.set(1))
        self.root.bind("2", lambda e: self.mode.set(2))
        self.root.bind("3", lambda e: self.mode.set(3))
        self.root.bind("<Left>", self.decrease_timer)
        self.root.bind("<Right>", self.increase_timer)

        self.target_mac = None
        self.target_device = None
        self.client = None
        self.active_char_uuid = None
        self.scratch_uuids = []
        self.is_connecting = False
        self.is_running = False
        self.is_sending = False
        self.target_on = False
        self.current_on = None
        self.remaining = 0
        self.motor_task = None
        self._is_dragging = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.cap = None
        self.loop = None
        self.tk_img = None

        self.lbl_s = None
        self.cb_dev = None
        self.cb_cam = None
        self.sc_t = None
        self.cb_size = None
        self.cv = None
        self.id_i = None
        self.id_t = None

        self.sound = tk.BooleanVar(value=self.config.getboolean('Settings', 'sound', fallback=True))
        self.mode = tk.IntVar(value=self.config.getint('Settings', 'mode', fallback=1))
        self.found_devs = []
        self.size_var = tk.StringVar(value=self.config.get('Settings', 'size', fallback="Large"))
        self.sizes = {"ExtraLarge": (1000, 563), "Large": (800, 450), "Medium": (600, 338), "Small": (400, 225)}

        try:
                      self.setup_ui()
                      self.root.after(100, self.update_camera)
                      self.root.after(200, self.start_thread)
except Exception as e:
            messagebox.showerror("UI Startup Error", traceback.format_exc())
            sys.exit()

    def load_config(self):
              if os.path.exists(self.config_file):
                            self.config.read(self.config_file, encoding='utf-8')
else:
            self.config['Settings'] = {'sound': 'True', 'mode': '1', 'size': 'Medium', 'timer': '5', 'camera': 'No Camera'}
              self.save_config()

    def save_config(self):
              try:
                            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                                              self.config.write(configfile)
                                      except: pass

          def on_setting_change(self, *args):
                    if not self.config.has_section('Settings'): self.config.add_section('Settings')
                              self.config.set('Settings', 'sound', str(self.sound.get()))
        self.config.set('Settings', 'mode', str(self.mode.get()))
        self.config.set('Settings', 'size', self.size_var.get())
        if hasattr(self, 'sc_t'): self.config.set('Settings', 'timer', str(self.sc_t.get()))
                  if hasattr(self, 'cb_cam'): self.config.set('Settings', 'camera', self.cb_cam.get())
                            self.save_config()

    def decrease_timer(self, event=None):
              current = self.sc_t.get()
        if current > 1: self.sc_t.set(current - 1); self.on_setting_change()
              def increase_timer(self, event=None):
                        current = self.sc_t.get()
                        if current < 180: self.sc_t.set(current + 1); self.on_setting_change()
                              def toggle_fullscreen(self, event=None):
                                        is_full = self.root.attributes("-fullscreen")
                                        self.root.attributes("-fullscreen", not is_full)
                                        return "break"

    def setup_ui(self):
              f_b = ("Yu Gothic", 12, "bold")
        self.header = tk.Frame(self.root, bg="#f0f0f0")
        self.header.pack(side="top", fill="x", padx=40, pady=5)
        adm = tk.LabelFrame(self.header, text=" [MaBeee for School] Settings ", font=f_b, bg="white", fg="#D32F2F", padx=15, pady=10)
        adm.pack(fill="x", pady=2)
        r1 = tk.Frame(adm, bg="white")
        r1.pack(fill="x", pady=2)
        tk.Button(r1, text="Scan MaBeee", command=self.scan, font=f_b, bg="#4CAF50", fg="white", padx=10).pack(side="left", padx=5)
        self.lbl_s = tk.Label(r1, text="Waiting...", font=f_b, bg="white")
        self.lbl_s.pack(side="left", padx=15)
        tk.Label(r1, text="Pairing:", font=f_b, bg="white").pack(side="left")
        self.cb_dev = ttk.Combobox(r1, state="readonly", width=27, font=("Consolas", 10))
        self.cb_dev.pack(side="left", padx=5)
        tk.Button(r1, text="Connect", command=self.conn, font=f_b, bg="#2196F3", fg="white", padx=10).pack(side="left", padx=5)
        tk.Label(r1, text=" | Camera:", font=f_b, bg="white").pack(side="left", padx=(15,0))
        self.cb_cam = ttk.Combobox(r1, state="readonly", width=10, font=f_b)
        self.cb_cam['values'] = ("Camera 1", "Camera 2", "No Camera")
        saved_cam = self.config.get('Settings', 'camera', fallback="No Camera")
        if saved_cam in self.cb_cam['values']: self.cb_cam.set(saved_cam)
else: self.cb_cam.current(2)
        self.cb_cam.pack(side="left", padx=5)
        self.cb_cam.bind("<<ComboboxSelected>>", self.cam_chg)
        tk.Label(r1, text=" | Timer (1-180s):", font=f_b, bg="white").pack(side="left", padx=(15,0))
        self.sc_t = tk.Scale(r1, from_=1, to=180, orient="horizontal", length=300, bg="white", highlightthickness=0, font=f_b, command=lambda e: self.on_setting_change())
        self.sc_t.set(self.config.getint('Settings', 'timer', fallback=5))
        self.sc_t.pack(side="left", padx=10)
        r2 = tk.Frame(adm, bg="white")
        r2.pack(fill="x", pady=(10, 0))
        tk.Checkbutton(r2, text="Enable operation sound", variable=self.sound, font=f_b, bg="white", command=self.on_setting_change).pack(side="left", padx=10)
        tk.Label(r2, text=" | Operation Mode:", font=f_b, bg="white").pack(side="left", padx=(10,0))
        tk.Radiobutton(r2, text="1:Click/Dwell", variable=self.mode, value=1, font=f_b, bg="white", command=self.on_setting_change).pack(side="left", padx=5)
        tk.Radiobutton(r2, text="2:Mouse Over", variable=self.mode, value=2, font=f_b, bg="white", command=self.on_setting_change).pack(side="left", padx=5)
        tk.Radiobutton(r2, text="3:Inside Button", variable=self.mode, value=3, font=f_b, bg="white", command=self.on_setting_change).pack(side="left", padx=5)
        tk.Label(r2, text=" | Size:", font=f_b, bg="white").pack(side="left", padx=(15,0))
        self.cb_size = ttk.Combobox(r2, textvariable=self.size_var, state="readonly", width=5, font=f_b)
        self.cb_size['values'] = ("ExtraLarge", "Large", "Medium", "Small")
        self.cb_size.pack(side="left", padx=5)
        self.cb_size.bind("<<ComboboxSelected>>", self.resize_canvas)
        self.canvas_container = tk.Frame(self.root, bg="#f0f0f0")
        self.canvas_container.place(relx=0.5, rely=0.6, anchor="center")
        w, h = self.sizes[self.size_var.get()]
        self.cv = tk.Canvas(self.canvas_container, width=w, height=h, bg="#add8e6", highlightthickness=10, highlightbackground="#87ceeb")
        self.cv.pack()
        self.id_i = self.cv.create_image(w//2, h//2, anchor="center")
        self.id_t = self.cv.create_text(w//2, h//2, text="MaBeee ON", font=("Yu Gothic", 48, "bold"), fill="#333333", anchor="center")
        self.cv.bind("<Button-1>", self.on_start_drag)
        self.cv.bind("<B1-Motion>", self.on_drag)
        self.cv.bind("<ButtonRelease-1>", self.on_stop_drag)
        self.cv.bind("<Enter>", lambda e: self.ent())
        self.cv.bind("<Leave>", lambda e: self.lev())
        self.lbl_esc = tk.Label(self.root, text="[F11]:FullScreen / [1][2][3]:Mode / [Left][Right]:Timer", font=f_b, bg="#f0f0f0", fg="#555")
        self.lbl_esc.pack(side="bottom", pady=10)

    def on_start_drag(self, event):
              self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._is_dragging = False
    def on_drag(self, event):
              if abs(event.x - self._drag_start_x) > 5 or abs(event.y - self._drag_start_y) > 5:
                            self._is_dragging = True
                            x = self.canvas_container.winfo_x() + (event.x - self._drag_start_x)
                            y = self.canvas_container.winfo_y() + (event.y - self._drag_start_y)
                            self.canvas_container.place(x=x, y=y, anchor="nw", relx=0, rely=0)
                    def on_stop_drag(self, event):
                              if not getattr(self, '_is_dragging', False): self.act()
                                        self._is_dragging = False
    def resize_canvas(self, event=None):
              self.on_setting_change()
        w, h = self.sizes[self.size_var.get()]
        self.cv.config(width=w, height=h)
        self.cv.coords(self.id_i, w//2, h//2)
        s = self.cb_cam.get()
        if s == "No Camera":
                      self.cv.coords(self.id_t, w//2, h//2)
            self.cv.itemconfig(self.id_t, font=("Yu Gothic", 48, "bold"))
else:
            self.cv.coords(self.id_t, w//2, 40)
            self.cv.itemconfig(self.id_t, font=("Yu Gothic", 28, "bold"))
    def cam_chg(self, e=None):
              self.on_setting_change()
        w, h = self.sizes[self.size_var.get()]
        s = self.cb_cam.get()
        if self.cap: self.cap.release()
                  if s == "No Camera":
                                self.cap = None
                                self.cv.itemconfig(self.id_i, image="")
                                self.cv.coords(self.id_t, w//2, h//2)
                                self.cv.itemconfig(self.id_t, font=("Yu Gothic", 48, "bold"))
else:
            self.cv.coords(self.id_t, w//2, 40)
            self.cv.itemconfig(self.id_t, font=("Yu Gothic", 28, "bold"))
            idx = 0 if s == "Camera 1" else 1
            self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    def update_camera(self):
              try:
                            if self.cap and self.cap.isOpened():
                                              ret, frame = self.cap.read()
                                              if ret:
                                                                    w, h = self.sizes[self.size_var.get()]
                                                                    frame = cv2.resize(cv2.flip(frame, 1), (w, h))
                                                                    self.tk_img = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                                                                    self.cv.itemconfig(self.id_i, image=self.tk_img)
              except Exception: pass
        self.root.after(15, self.update_camera)
    def start_thread(self):
              def run():
                            self.loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(self.loop)
                            self.loop.create_task(self.keep())
                            self.loop.run_forever()
                        threading.Thread(target=run, daemon=True).start()
    async def keep(self):
              while True:
                            await asyncio.sleep(2)
                            if self.target_mac and (self.client is None or not self.client.is_connected):
                                              await self.do_connect(silent=True)
                                  async def do_connect(self, silent=False):
                                            if self.is_connecting: return
                                                      self.is_connecting = True
        try:
                      if not silent: self.up_s("Connecting...", "orange")
                                    if self.client:
                                                      try: await self.client.disconnect()
                                                                        except: pass
                                                                                      dev = getattr(self, "target_device", self.target_mac)
            self.client = BleakClient(dev, timeout=15.0)
            await self.client.connect()
            await asyncio.sleep(2.0)
            self.up_s("Connecting...", "blue")

            f_uuid = None
            self.scratch_uuids = []
            self.current_on = None 

            for attempt in range(3):
                              if attempt > 0: 
                                                    self.up_s(f"Connecting... ({attempt+1})", "blue")
                    await asyncio.sleep(1.0)
                try:
                                      services = self.client.services
                    for service in services:
                                              for char in service.characteristics:
                                                                            uuid = char.uuid.lower()
                                                                            props = char.properties
                                                                            if "write" in props or "write-without-response" in props:
                                                                                                              if "3d42" in uuid:
                                                                                                                                                    if uuid not in self.scratch_uuids: self.scratch_uuids.append(uuid)
                                                                                                                                                                                          if "3d421001" in uuid: f_uuid = uuid
                                                                                                                                                                                                            except Exception: pass
                                                                                                                                if f_uuid or self.scratch_uuids: break
                                                                                                                                              
                                                                                          if f_uuid or self.scratch_uuids:
                                                                                                            self.active_char_uuid = f_uuid if f_uuid else self.scratch_uuids[0]
                                                                                                            
                async def on_notify(char_uuid, data):
                                      pass 

                for service in self.client.services:
                                      for char in service.characteristics:
                                                                if "notify" in char.properties:
                                                                                              try: await self.client.start_notify(char.uuid, on_notify)
                                                                                                                            except: pass
                                                                                                                                              
                                                                                  CONF_UUID = "3d421000-7480-4c5b-bedd-465a59ddbbef"
                try: await self.client.write_gatt_char(CONF_UUID, bytes([0x00, 0x58, 0x02, 0x00, 0x00]))
                                  except: pass

                self.up_s("Connected", "green")
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
else: self.up_s("Unknown characteristic", "red")
except Exception: self.up_s("Connection Failed", "red")
finally: self.is_connecting = False

    def up_s(self, t, c):
              if self.root: self.root.after(0, lambda: self.lbl_s.config(text=t, fg=c))
                    def scan(self):
                              if not self.loop: return
                                        self.up_s("Scanning...", "blue")
        async def do():
                      try:
                                        ds = await BleakScanner.discover(timeout=5.0)
                                        nms, found = [], []
                                        info = []
                                        for d in ds:
                                                              name = (d.name or "").lower()
                                                              if "scratch" in name or "mabee" in name or "mb" in name or d.name:
                                                                                        rssi = getattr(d, "rssi", -100)
                                                                                        disp = d.name if d.name and d.name.strip() else f"No Name({d.address})"
                                                                                        info.append((rssi, d, disp))
                                                                                info.sort(key=lambda x: x[0], reverse=True)
                                                          for r, dev, dname in info:
                                                                                found.append(dev)
                                                                                addr = dev.address
                                                                                if r != -100: nms.append(f"{dname} (RSSI: {r}dBm) [{addr}]")
                                                            else: nms.append(f"{dname} [{addr}]")
                                                                              self.root.after(0, lambda: self.update_dev_list(nms, found))
                self.up_s("Scan complete", "black")
                if self.sound.get(): winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                              except: pass
        asyncio.run_coroutine_threadsafe(do(), self.loop)
    def update_dev_list(self, nms, found):
              self.cb_dev.config(values=nms); self.found_devs = found
    def conn(self):
              i = self.cb_dev.current()
        if i >= 0 and self.loop:
                      self.target_device = self.found_devs[i]
            self.target_mac = self.target_device.address
            asyncio.run_coroutine_threadsafe(self.do_connect(), self.loop)
    def send(self, on):
        if self.is_connecting or not self.client or not self.client.is_connected: return

        async def heartbeat_loop():
                      MOTOR2_UUID = "3d423006-7480-4c5b-bedd-465a59ddbbef"
            p_on = bytes([0x01, 0x64, 0x00, 0x00, 0x00])
            try:
                              while self.target_on and self.client and self.client.is_connected:
                                                    await self.client.write_gatt_char(MOTOR2_UUID, p_on)
                                                    await asyncio.sleep(0.05)
except Exception: pass

        async def do_send():
                      MOTOR2_UUID = "3d423006-7480-4c5b-bedd-465a59ddbbef"
            if on:
                              if self.target_on: return
                                                self.target_on = True
                self.motor_task = asyncio.get_event_loop().create_task(heartbeat_loop())
else:
                self.target_on = False
                await asyncio.sleep(0.07)
                try: await self.client.write_gatt_char(MOTOR2_UUID, bytes([0x01, 0x00, 0x00, 0x00, 0x00]))
                                  except: pass

        asyncio.run_coroutine_threadsafe(do_send(), self.loop)
    def act(self):
              if self.mode.get() == 1: self.run_t()
                    def ent(self):
                              if self.mode.get() == 2: self.run_t()
                              elif self.mode.get() == 3:
            self.send(True)
            if self.sound.get(): winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                          self.cv.itemconfig(self.id_t, text="Running", fill="#FFFFFF")
            self.cv.config(highlightbackground="#F44336", bg="#F44336")
    def lev(self):
              if self.mode.get() == 3:
                            self.send(False)
            if self.sound.get(): winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                          self.cv.itemconfig(self.id_t, text="MaBeee ON", fill="#333333")
            self.cv.config(highlightbackground="#add8e6", bg="#add8e6")
    def run_t(self):
              if self.is_running: return
                        self.is_running = True
        self.send(True)
        if self.sound.get(): winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                  self.remaining = self.sc_t.get()
        self.cv.config(highlightbackground="#F44336", bg="#F44336")
        self.cv.itemconfig(self.id_t, fill="#FFFFFF"); self.update_timer()
    def update_timer(self):
              if self.remaining > 0:
                            self.cv.itemconfig(self.id_t, text=f"Running {self.remaining}s")
            self.remaining -= 1; self.root.after(1000, self.update_timer)
else: self.fin_t()
    def fin_t(self):
              self.send(False)
        self.cv.itemconfig(self.id_t, text="MaBeee ON", fill="#333333")
        self.cv.config(highlightbackground="#add8e6", bg="#add8e6")
        self.is_running = False
if __name__ == "__main__":
      r = tk.Tk(); App(r); r.mainloop()
