#!/usr/bin/env python3
"""Tombola natalizia: finestra di controllo (PC) + finestra di proiezione.
Solo libreria standard; Pillow (pip install pillow) serve solo per l'immagine di sfondo."""
import glob, json, math, os, random, tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None

CFG = "tombola_config.json"
DEFAULT = {
    "mode": "manual",  # "manual": clicchi i numeri sul PC | "auto": estrae il programma (tasto Estrai / barra spaziatrice)
    "numbers": 100,
    "show_prize": True,  # mostra sul proiettore per cosa si gioca
    "animation_ms": 5000,  # per quanto tempo il numero estratto resta in grande prima della tabella
    "snow": False,  # neve che cade sul proiettore
    "projector_geometry": "1280x720+0+0",  # LxA+X+Y: X = larghezza del monitor principale
    "projector_fullscreen": False,  # F11 sulla finestra di proiezione per alternare
}
PRIZES = ["Ambo", "Terna", "Quaterna", "Cinquina", "Tombola"]
BG, CELL, RED, GOLD, WHITE, DIM = "#0d3b2e", "#17604a", "#c8102e", "#ffd24a", "#ffffff", "#7fb59f"
LIGHTS = [RED, GOLD, WHITE, "#3fa6e0"]
FRAME = 33  # ms per fotogramma
FONT = "Comic Sans MS"

def load_cfg():
    user = json.load(open(CFG)) if os.path.exists(CFG) else {}
    cfg = {k: user.get(k, v) for k, v in DEFAULT.items()}
    if cfg != user:
        json.dump(cfg, open(CFG, "w"), indent=2)
    return cfg


class Tombola:
    def __init__(s, root):
        s.root, s.cfg = root, load_cfg()
        s.drawn, s.prize, s.busy, s.t, s.num, s.bg, s.frame = [], 0, False, 0, 0, False, 0
        s.bg_key = s.bg_tk = None
        s.flakes = [[random.random(), random.random(), random.uniform(1.5, 4), random.uniform(.002, .006),
                     random.uniform(0, 6.28)] for _ in range(70)]
        os.makedirs("runs", exist_ok=True)
        s.path = s.new_path()

        # --- proiezione ---
        s.proj = tk.Toplevel(root)
        s.proj.title("Tombola - Proiezione")
        s.proj.geometry(s.cfg["projector_geometry"])
        s.proj.protocol("WM_DELETE_WINDOW", root.destroy)
        s.proj.bind("<F11>", lambda e: s.proj.attributes("-fullscreen", not s.proj.attributes("-fullscreen")))
        s.cv = tk.Canvas(s.proj, bg=BG, highlightthickness=0)
        s.cv.pack(fill="both", expand=True)
        if s.cfg["projector_fullscreen"]:
            s.proj.update()
            s.proj.attributes("-fullscreen", True)

        # --- controllo ---
        root.title("Tombola - Controllo")
        top = tk.Frame(root)
        top.pack(pady=6)
        s.pv = tk.IntVar(value=0)
        for i, p in enumerate(PRIZES):
            tk.Radiobutton(top, text=p, variable=s.pv, value=i, indicatoron=False, padx=10, pady=4,
                           command=s.set_prize).pack(side="left", padx=2)
        grid = tk.Frame(root)
        grid.pack(padx=8, pady=4)
        s.cells = {}
        for n in range(1, (s.cfg["numbers"]+1)):
            l = tk.Label(grid, text=n, width=4, height=2, relief="raised", font=("Helvetica", 14, "bold"))
            l.grid(row=(n - 1) // 10, column=(n - 1) % 10, padx=1, pady=1)
            l.bind("<Button-1>", lambda e, n=n: s.click(n))
            s.cells[n] = l
        s.info = tk.Label(root, font=("Helvetica", 12))
        s.info.pack()
        s.silent = tk.BooleanVar()
        for row in ((("Estrai (spazio)", s.extract),) if s.cfg["mode"] == "auto" else ()), \
                   (("Annulla ultimo", s.undo), ("Sfondo on/off", s.toggle_bg)), \
                   (("Carica...", s.load_dialog), ("Nuova partita", s.new)):
            bar = tk.Frame(root)
            bar.pack(pady=3)
            for txt, cmd in row:
                tk.Button(bar, text=txt, command=cmd).pack(side="left", padx=4)
            if row and row[0][0] == "Annulla ultimo":
                tk.Checkbutton(bar, text="Aggiunta silenziosa (senza animazione)", variable=s.silent).pack(side="left")
        if s.cfg["mode"] == "auto":
            root.bind("<space>", lambda e: s.extract())

        s.refresh()
        s.loop()
        runs = sorted(glob.glob(os.path.join("runs", "tombola_*.json")))
        if runs:
            root.update()
            if messagebox.askyesno("Ripristino", f"Riprendere l'ultima partita?\n{os.path.basename(runs[-1])}"):
                s.load(runs[-1])

    # --- persistenza ---
    def new_path(s):
        return os.path.join("runs", datetime.now().strftime("tombola_%Y-%m-%d_%H-%M-%S.json"))

    def save(s):
        tmp = s.path + ".tmp"
        json.dump({"prize": s.prize, "drawn": s.drawn}, open(tmp, "w"))
        os.replace(tmp, s.path)  # scrittura atomica: niente file corrotti in caso di crash

    def load(s, path):
        try:
            d = json.load(open(path))
            drawn = [int(n) for n in d["drawn"]]
            assert len(set(drawn)) == len(drawn) and all(1 <= n <= s.cfg["numbers"] for n in drawn)
            prize = int(d.get("prize", 0))
        except Exception as e:
            return messagebox.showerror("Errore", f"File non valido: {e}")
        s.path, s.drawn, s.prize = path, drawn, min(prize, len(PRIZES) - 1)
        s.pv.set(s.prize)
        s.refresh()

    def load_dialog(s):
        p = None if s.busy else filedialog.askopenfilename(initialdir="runs", filetypes=[("Partita", "*.json")])
        if p:
            s.load(p)

    # --- logica ---
    def click(s, n):
        if s.busy or n in s.drawn:
            return
        if s.silent.get():
            s.add(n)
        elif s.cfg["mode"] == "manual":
            s.extract(n)

    def add(s, n):
        s.drawn.append(n)
        s.save()
        s.refresh()

    def extract(s, n=None):
        if s.busy or len(s.drawn) >= s.cfg["numbers"]:
            return
        s.add(n or random.choice([x for x in range(1, (s.cfg["numbers"]+1)) if x not in s.drawn]))
        s.num, s.busy, s.t, s.bg = s.drawn[-1], True, 0, False

    def undo(s):
        if not s.busy and s.drawn:
            s.drawn.pop()
            s.save()
            s.refresh()

    def new(s):
        if not s.busy and messagebox.askyesno("Nuova partita", "Azzerare i numeri estratti?"):
            s.path, s.drawn, s.prize = s.new_path(), [], 0
            s.pv.set(0)
            s.refresh()

    def set_prize(s):
        s.prize = s.pv.get()
        if s.drawn:
            s.save()

    def bg_file(s):
        return next((f for f in ("background.png", "background.jpg", "background.jpeg") if os.path.exists(f)), None)

    def toggle_bg(s):
        if s.busy:
            return
        if not s.bg and (Image is None or not s.bg_file()):
            return messagebox.showerror("Sfondo", "Serve Pillow (pip install pillow) e un file background.png/jpg "
                                                  "nella cartella da cui lanci il programma.")
        s.bg, s.bg_key = not s.bg, None

    # --- grafica ---
    def refresh(s):
        last = s.drawn[-1] if s.drawn else None
        for n, l in s.cells.items():
            l.config(bg=GOLD if n == last else RED if n in s.drawn else "#e8e8e8",
                     fg="black" if n == last else "white" if n in s.drawn else "black")
        s.info.config(text=f"Estratti: {len(s.drawn)}/{s.cfg["numbers"]}  Ultimo: {last or '-'}")

    def loop(s):
        s.frame += 1
        for f in s.flakes:
            f[1] = (f[1] + f[3]) % 1
        if s.busy:
            s.t += FRAME
            s.busy = s.t < s.cfg["animation_ms"]
        s.draw()
        s.root.after(FRAME, s.loop)

    def bauble(s, x, y, R, fill, width=None):
        cv = s.cv
        cv.create_rectangle(x - R * .2, y - R * 1.2, x + R * .2, y - R * .9, fill=GOLD, outline="")
        cv.create_oval(x - R, y - R, x + R, y + R, fill=fill, outline=GOLD, width=width or max(2, int(R * .05)))
        cv.create_oval(x - R * .6, y - R * .7, x - R * .25, y - R * .4, fill="#e85a70", outline="")

    def pill(s, x1, y1, x2, y2, **kw):
        r = (y2 - y1) / 2
        s.cv.create_polygon(x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r,
                            x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r,
                            x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1, smooth=True, **kw)

    def draw(s):
        cv = s.cv
        W, H = cv.winfo_width(), cv.winfo_height()
        cv.delete("all")
        if s.bg and not s.busy:
            if s.bg_key != (W, H):
                im = Image.open(s.bg_file()).convert("RGB")
                k = max(W / im.width, H / im.height)
                im = im.resize((math.ceil(im.width * k), math.ceil(im.height * k)))
                l, t = (im.width - W) // 2, (im.height - H) // 2
                s.bg_tk, s.bg_key = ImageTk.PhotoImage(im.crop((l, t, l + W, t + H))), (W, H)
            return cv.create_image(0, 0, anchor="nw", image=s.bg_tk)

        # ghirlanda
        gh = H * .05
        pts = [(i * W / 24, gh * (.15 + 2.8 * (i % 6 / 6) * (1 - i % 6 / 6))) for i in range(25)]
        cv.create_line(pts, fill="#3fa66f", width=3, smooth=True)
        for i, (x, y) in enumerate(pts):
            r = gh * .17
            cv.create_oval(x - r, y + gh * .1, x + r, y + gh * .1 + 2 * r, fill=LIGHTS[i % 4], outline="")

        # premio in palio
        y0 = gh
        if s.cfg["show_prize"]:
            bar, w = H * .11, W / len(PRIZES)
            for i, p in enumerate(PRIZES):
                on = i == s.prize
                s.pill(i * w + w * .05, y0 + 6, (i + 1) * w - w * .05, y0 + bar - 6,
                       fill=GOLD if on else "#7d0f22", outline=WHITE if on else "#c9a23a", width=3 if on else 1)
                cv.create_text((i + .5) * w, y0 + bar / 2, text=p.upper(), fill=BG if on else "#ffe9a8",
                               font=(FONT, -int(min(bar * .4, w / 6.5)), "bold"))
            y0 += bar
        bh, cx, cy = H - y0, W / 2, y0 + (H - y0) / 2
        m = min(W, bh)

        if s.busy:  # numero subito visibile in una grande pallina (zoom rapido), con luci che girano
            R = m * .3 * (1 - (1 - min(1, s.t / 500)) ** 3)
            s.bauble(cx, cy + R * .1, R, RED, width=max(3, int(R * .06)))
            cv.create_text(cx, cy + R * .1, text=s.num, fill=WHITE, font=(FONT, -max(8, int(R)), "bold"))
            for k in range(12):
                b = s.t * .003 + k * math.pi / 6
                x, y, r = cx + R * 1.45 * math.cos(b), cy + R * 1.45 * math.sin(b), R * .09
                cv.create_oval(x - r, y - r, x + r, y + r, fill=LIGHTS[k % 4], outline="")
        else:  # tabella
            cw, ch, last = W / 10, bh / math.ceil(s.cfg["numbers"]/10), s.drawn[-1] if s.drawn else None
            for n in range(1, (s.cfg["numbers"]+1)):
                r_, c_ = divmod(n - 1, 10)
                x, y, r, on = (c_ + .5) * cw, y0 + (r_ + .5) * ch, min(cw, ch) * .46, n in s.drawn
                if n == last:
                    r *= 1.03 + .04 * math.sin(s.frame * .2)
                cv.create_oval(x - r, y - r, x + r, y + r, width=3 if n == last else 2,
                               fill=GOLD if n == last else RED if on else CELL,
                               outline=WHITE if n == last else GOLD if on else "")
                cv.create_text(x, y, text=n, font=(FONT, -int(r * .9), "bold"),
                               fill=BG if n == last else WHITE if on else DIM)

        # neve
        for fx, fy, r, _, ph in s.flakes if s.cfg["snow"] else ():
            x, y = (fx + .01 * math.sin(s.frame * .03 + ph)) * W, fy * H
            cv.create_oval(x - r, y - r, x + r, y + r, fill=WHITE, outline="")


if __name__ == "__main__":
    root = tk.Tk()
    Tombola(root)
    root.mainloop()