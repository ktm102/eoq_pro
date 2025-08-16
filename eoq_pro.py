# -*- coding: utf-8 -*-
"""
EOQ Pro - Versione Semplice (senza ABC)
---------------------------------------
- EOQ, costi, ROP, Scorta di Sicurezza
- Import/Export CSV, Salva/Apri progetto JSON
- Report HTML (sempre) + PDF (se 'reportlab' presente)
- Grafico costi vs Q (se 'matplotlib' presente)
- Branding base (nome, colore, logo PNG/SVG)
"""
import csv, json, math, os
from datetime import datetime
from typing import Tuple, Dict
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import matplotlib.pyplot as plt  # type: ignore
    HAS_MPL = True
except Exception:
    HAS_MPL = False

try:
    from reportlab.lib.pagesizes import A4  # type: ignore
    from reportlab.pdfgen import canvas as pdfcanvas  # type: ignore
    from reportlab.lib.units import cm  # type: ignore
    HAS_PDF = True
except Exception:
    HAS_PDF = False

Z_BY_CSL = {0.80: 0.8416, 0.90: 1.2816, 0.95: 1.6449, 0.975: 1.9600, 0.99: 2.3263, 0.995: 2.5758}

def parse_number(value: str, allow_zero: bool = False) -> float:
    s = (value or "").strip().replace(",", ".")
    if s == "": raise ValueError("vuoto")
    x = float(s)
    if allow_zero:
        if x < 0: raise ValueError("<0")
    else:
        if x <= 0: raise ValueError("<=0")
    return x

def eoq_only(D: float, S: float, H: float) -> Tuple[float, float, float, float]:
    Q = math.sqrt((2.0 * D * S) / H)
    cost_order = (D / Q) * S
    cost_hold = (Q / 2.0) * H
    return Q, cost_order, cost_hold, cost_order + cost_hold

def rop_and_safety(D: float, L_days: float, sigma_d: float = 0.0, csl: float = 0.95) -> Tuple[float, float]:
    mu_d = D / 365.0
    z = Z_BY_CSL.get(round(csl, 3), Z_BY_CSL[0.95])
    ss = (z * sigma_d * math.sqrt(max(L_days, 0.0))) if sigma_d > 0 and L_days > 0 else 0.0
    rop = mu_d * max(L_days, 0.0) + ss
    return rop, ss

class EOQProSimple(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EOQ Pro - Semplice")
        self.geometry("1100x650"); self.minsize(980, 600)
        self.brand: Dict[str, str] = {"name": "EOQ Pro", "color": "#0F6FFF", "logo_path": ""}
        self.entries = []
        self._style(); self._ui()

    def _style(self):
        style = ttk.Style(self)
        try:
            if "clam" in style.theme_names(): style.theme_use("clam")
        except Exception: pass
        style.configure("Header.TLabel", font=("Arial", 14, "bold"))
        style.configure("Bold.TLabel", font=("Arial", 10, "bold"))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        style.configure("TButton", padding=6)

    def _ui(self):
        # Menù
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Nuovo", command=self._new)
        filemenu.add_command(label="Apri progetto…", command=self._open)
        filemenu.add_command(label="Salva progetto", command=self._save)
        filemenu.add_separator()
        filemenu.add_command(label="Importa CSV…", command=self._import_csv)
        filemenu.add_command(label="Esporta CSV…", command=self._export_csv)
        filemenu.add_separator()
        filemenu.add_command(label="Report HTML…", command=self._export_html)
        if HAS_PDF: filemenu.add_command(label="Report PDF…", command=self._export_pdf)
        menubar.add_cascade(label="File", menu=filemenu)

        toolsmenu = tk.Menu(menubar, tearoff=0)
        toolsmenu.add_command(label="Grafico costi vs Q", command=self._plot_cost_curve)
        menubar.add_cascade(label="Strumenti", menu=toolsmenu)

        brandmenu = tk.Menu(menubar, tearoff=0)
        brandmenu.add_command(label="Imposta brand…", command=self._set_brand)
        menubar.add_cascade(label="Brand", menu=brandmenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Guida rapida", command=self._help)
        helpmenu.add_command(label="Info", command=self._about)
        menubar.add_cascade(label="Aiuto", menu=helpmenu)
        self.config(menu=menubar)

        ttk.Label(self, text="Inserisci i dati (una riga per anno/periodo)", style="Header.TLabel").pack(anchor="w", padx=12, pady=(10, 6))

        # Editor
        frame = ttk.Frame(self); frame.pack(fill="x", padx=12, pady=(0,8))
        labels = ["Anno","Domanda annua (D)","Costo setup (S)","Costo mantenimento (H)","Lead time L (giorni)","σ domanda giornaliera","Livello servizio (es. 0.95)"]
        for c, text in enumerate(labels):
            ttk.Label(frame, text=text, style="Bold.TLabel").grid(row=0, column=c, sticky="w", padx=6, pady=4)
        self.entries_frame = frame; self._rows = 0
        for _ in range(3): self._add_row()

        btns = ttk.Frame(self); btns.pack(fill="x", padx=12, pady=6)
        ttk.Button(btns, text="Aggiungi riga", command=self._add_row).pack(side="left", padx=4)
        ttk.Button(btns, text="Pulisci tutto", command=self._clear).pack(side="left", padx=4)
        ttk.Button(btns, text="Calcola", command=self._calc).pack(side="right", padx=4)

        # Risultati
        res = ttk.LabelFrame(self, text="Risultati"); res.pack(fill="both", expand=True, padx=12, pady=(4,12))
        cols = ("Riga","D","S","H","L","σ","CSL","EOQ","Ord","Hold","Totale","ROP","Safety Stock")
        self.tree = ttk.Treeview(res, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=90, anchor="center", stretch=True)
        yscroll = ttk.Scrollbar(res, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set); self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        self.status = ttk.Label(self, text="Pronto. Default CSL=0.95 (se vuoto).", foreground="#555")
        self.status.pack(anchor="w", padx=12, pady=(0,8))

    def _add_row(self):
        r = self._rows + 1
        e_anno = ttk.Label(self.entries_frame, text=f"{r}")
        eD = ttk.Entry(self.entries_frame, width=12)
        eS = ttk.Entry(self.entries_frame, width=12)
        eH = ttk.Entry(self.entries_frame, width=12)
        eL = ttk.Entry(self.entries_frame, width=10)
        eSig = ttk.Entry(self.entries_frame, width=10)
        eCSL = ttk.Entry(self.entries_frame, width=12)
        e_anno.grid(row=r, column=0, padx=6, pady=4, sticky="w")
        eD.grid(row=r, column=1, padx=6, pady=4, sticky="ew")
        eS.grid(row=r, column=2, padx=6, pady=4, sticky="ew")
        eH.grid(row=r, column=3, padx=6, pady=4, sticky="ew")
        eL.grid(row=r, column=4, padx=6, pady=4, sticky="ew")
        eSig.grid(row=r, column=5, padx=6, pady=4, sticky="ew")
        eCSL.grid(row=r, column=6, padx=6, pady=4, sticky="ew")
        self.entries.append({"D":eD,"S":eS,"H":eH,"L":eL,"sigma":eSig,"csl":eCSL}); self._rows += 1

    # File ops
    def _new(self):
        if not self._confirm(): return
        self._clear()
    def _open(self):
        p = filedialog.askopenfilename(filetypes=[("EOQ Project","*.json")], title="Apri progetto")
        if not p: return
        try:
            with open(p,"r",encoding="utf-8") as f: data=json.load(f)
            self._clear()
            rows = data.get("rows", [])
            for i, row in enumerate(rows):
                if i >= self._rows: self._add_row()
                self.entries[i]["D"].insert(0, str(row.get("D","")))
                self.entries[i]["S"].insert(0, str(row.get("S","")))
                self.entries[i]["H"].insert(0, str(row.get("H","")))
                self.entries[i]["L"].insert(0, str(row.get("L","")))
                self.entries[i]["sigma"].insert(0, str(row.get("sigma","")))
                self.entries[i]["csl"].insert(0, str(row.get("csl","")))
            brand = data.get("brand"); 
            if brand: self.brand.update(brand)
            messagebox.showinfo("Progetto", f"Caricato: {os.path.basename(p)}")
        except Exception as ex:
            messagebox.showerror("Errore apertura", str(ex))
    def _save(self):
        rows = [{"D":w["D"].get().strip(),"S":w["S"].get().strip(),"H":w["H"].get().strip(),
                 "L":w["L"].get().strip(),"sigma":w["sigma"].get().strip(),"csl":w["csl"].get().strip()} for w in self.entries]
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("EOQ Project","*.json")], title="Salva progetto")
        if not p: return
        try:
            with open(p,"w",encoding="utf-8") as f:
                json.dump({"rows":rows,"brand":self.brand,"saved_at":datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Progetto", f"Salvato in:\n{p}")
        except Exception as ex:
            messagebox.showerror("Errore salvataggio", str(ex))

    def _import_csv(self):
        p = filedialog.askopenfilename(filetypes=[("CSV","*.csv")], title="Importa CSV (D;S;H;L;sigma;csl)")
        if not p: return
        try:
            with open(p,"r",encoding="utf-8") as f: rows=list(csv.reader(f, delimiter=";"))
            header = rows[0] if rows else []
            start = 1 if header and any(h.lower() in ("d","domanda","s","h","l","sigma","csl") for h in header) else 0
            rows = rows[start:]
            if not rows: messagebox.showwarning("Import","Nessun dato."); return
            self._clear()
            for i, r in enumerate(rows):
                if i >= self._rows: self._add_row()
                vals = (r + ["","","","",""])[:6]
                self.entries[i]["D"].insert(0, vals[0])
                self.entries[i]["S"].insert(0, vals[1])
                self.entries[i]["H"].insert(0, vals[2])
                self.entries[i]["L"].insert(0, vals[3])
                self.entries[i]["sigma"].insert(0, vals[4])
                self.entries[i]["csl"].insert(0, vals[5])
            messagebox.showinfo("Import", f"Importate {len(rows)} righe.")
        except Exception as ex:
            messagebox.showerror("Errore import", str(ex))

    def _export_csv(self):
        if not self.tree.get_children():
            messagebox.showwarning("Esporta CSV", "Calcola prima i risultati."); return
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="Esporta risultati CSV")
        if not p: return
        try:
            with open(p,"w",newline="",encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Riga","D","S","H","L","sigma","CSL","EOQ","Costo_ordinazione","Costo_mantenimento","Costo_totale","ROP","Safety_Stock"])
                for item in self.tree.get_children():
                    w.writerow(self.tree.item(item,"values"))
            messagebox.showinfo("Esporta CSV", f"Esportato in:\n{p}")
        except Exception as ex:
            messagebox.showerror("Errore export", str(ex))

    # Calcolo
    def _calc(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        errors, computed = [], []
        for idx, w in enumerate(self.entries, start=1):
            raw = {k:w[k].get().strip() for k in ("D","S","H","L","sigma","csl")}
            if not any(raw.values()): continue
            try:
                D = parse_number(raw["D"]); S = parse_number(raw["S"]); H = parse_number(raw["H"])
                L = parse_number(raw["L"], allow_zero=True) if raw["L"] else 0.0
                sigma = parse_number(raw["sigma"], allow_zero=True) if raw["sigma"] else 0.0
                csl = float(raw["csl"].replace(",", ".")) if raw["csl"] else 0.95
                if not (0.5 < csl < 0.9999): raise ValueError("CSL fuori range (0.5–0.999)")
                Q, c_ord, c_hold, c_tot = eoq_only(D,S,H)
                rop, ss = rop_and_safety(D,L,sigma,csl)
                computed.append((idx,D,S,H,L,sigma,csl,Q,c_ord,c_hold,c_tot,rop,ss))
            except Exception as ex:
                errors.append(f"Riga {idx}: {ex}")
        if errors: messagebox.showerror("Errori di input", "\n".join(errors))
        for row in computed:
            vals = [row[0], f"{row[1]:.2f}", f"{row[2]:.2f}", f"{row[3]:.2f}", f"{row[4]:.2f}", f"{row[5]:.2f}",
                    f"{row[6]:.3f}", f"{row[7]:.2f}", f"{row[8]:.2f}", f"{row[9]:.2f}", f"{row[10]:.2f}",
                    f"{row[11]:.2f}", f"{row[12]:.2f}"]
            self.tree.insert("", "end", values=vals)
        self.status.config(text=f"Calcolo completato. Righe valide: {len(computed)}.")

    # Report
    def _export_html(self):
        if not self.tree.get_children(): messagebox.showwarning("Report","Calcola prima i risultati."); return
        p = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML","*.html")], title="Esporta report HTML")
        if not p: return
        try:
            rows = [self.tree.item(i,"values") for i in self.tree.get_children()]
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            html = self._build_html(rows, now)
            with open(p,"w",encoding="utf-8") as f: f.write(html)
            messagebox.showinfo("Report", f"Report salvato in:\n{p}")
        except Exception as ex:
            messagebox.showerror("Errore report", str(ex))

    def _build_html(self, rows, timestamp: str) -> str:
        logo_html = ""
        if self.brand.get("logo_path") and os.path.exists(self.brand["logo_path"]):
            try:
                import base64
                with open(self.brand["logo_path"],"rb") as imgf:
                    b64 = base64.b64encode(imgf.read()).decode("ascii")
                ext = "png" if self.brand["logo_path"].lower().endswith(".png") else "svg+xml"
                logo_html = f'<img alt="logo" style="height:48px;vertical-align:middle" src="data:image/{ext};base64,{b64}">'
            except Exception: logo_html = ""
        primary = self.brand.get("color","#0F6FFF"); name = self.brand.get("name","EOQ Pro")
        head = f"""<!doctype html><html lang='it'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'><title>Report EOQ - {name}</title>
<style>
:root {{ --primary: {primary}; }}
body {{ font-family: Arial, sans-serif; margin: 24px; }}
.header {{ display:flex; align-items:center; gap:12px; }}
.brand {{ font-size: 22px; font-weight: 700; color: var(--primary); }}
table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
th {{ background: #f4f4f4; }}
.small {{ font-size: 12px; color:#666; }}
.code {{ background:#f8f8f8; padding:8px; border:1px solid #eee; }}
</style></head><body>"""
        header = f"<div class='header'>{logo_html}<div class='brand'>{name}</div></div><div class='small'>Generato il {timestamp}</div>"
        th = ["Riga","D","S","H","L","σ","CSL","EOQ","Costo Ord.","Costo Hold","Totale","ROP","Safety Stock"]
        table = "<table><tr>" + "".join(f"<th>{h}</th>" for h in th) + "</tr>" + \
                "\n".join("<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in rows) + "</table>"
        formulas = """
<h3>Formule</h3>
<div class="code">
EOQ = sqrt( 2 D S / H )<br>
Costo Ordinazione = (D / EOQ) * S<br>
Costo Mantenimento = (EOQ / 2) * H<br>
Costo Totale = Costo Ordinazione + Costo Mantenimento<br>
Domanda media giornaliera μ_d = D / 365<br>
Scorta di Sicurezza = z * σ_d * sqrt(L)<br>
ROP = μ_d * L + Scorta di Sicurezza
</div>"""
        return head + header + table + formulas + "</body></html>"

    def _export_pdf(self):
        if not HAS_PDF: messagebox.showwarning("Report PDF","Installa 'reportlab' (pip install reportlab)."); return
        if not self.tree.get_children(): messagebox.showwarning("Report PDF","Calcola prima i risultati."); return
        p = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")], title="Esporta report PDF")
        if not p: return
        try:
            c = pdfcanvas.Canvas(p, pagesize=A4); width, height = A4; margin = 2 * cm; y = height - margin
            c.setFont("Helvetica-Bold", 16)
            def hex_to_rgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
            r,g,b = hex_to_rgb(self.brand.get("color","#0F6FFF")); c.setFillColorRGB(r,g,b)
            c.drawString(margin, y, self.brand.get("name","EOQ Pro")); y -= 8; c.setFillColorRGB(0,0,0)
            c.setFont("Helvetica", 9); c.drawString(margin, y, f"Report EOQ • {datetime.now().strftime('%Y-%m-%d %H:%M')}"); y -= 18
            logo = self.brand.get("logo_path")
            if logo and os.path.exists(logo) and logo.lower().endswith(".png"):
                try: c.drawImage(logo, width - margin - 2.5*cm, height - margin - 2.5*cm, 2.5*cm, 2.5*cm, preserveAspectRatio=True, mask='auto')
                except Exception: pass
            headers = ["Riga","D","S","H","L","σ","CSL","EOQ","Ord","Hold","Totale","ROP","SS"]
            data = [headers] + [list(map(str, self.tree.item(i,"values"))) for i in self.tree.get_children()]
            colw = [1.1*cm,1.7*cm,1.7*cm,1.7*cm,1.4*cm,1.5*cm,1.5*cm,1.8*cm,1.8*cm,1.8*cm,1.8*cm,1.8*cm,1.8*cm]
            x0 = margin; rowh = 0.66*cm
            for r_i, row in enumerate(data):
                x = x0
                if y < margin + 5*rowh:
                    c.showPage(); y = height - margin
                    c.setFont("Helvetica-Bold", 16); c.setFillColorRGB(r,g,b)
                    c.drawString(margin, y, self.brand.get("name","EOQ Pro")); y -= 18; c.setFillColorRGB(0,0,0); c.setFont("Helvetica", 9)
                for i, cell in enumerate(row):
                    c.setFont("Helvetica-Bold", 8) if r_i == 0 else c.setFont("Helvetica", 8)
                    c.rect(x, y - rowh, colw[i], rowh, stroke=1, fill=0)
                    c.drawString(x+2, y - rowh + 2, str(cell)[:18]); x += colw[i]
                y -= rowh
            c.save(); messagebox.showinfo("Report PDF", f"Report salvato in:\n{p}")
        except Exception as ex:
            messagebox.showerror("Errore PDF", str(ex))

    # Grafico
    def _plot_cost_curve(self):
        if not HAS_MPL: messagebox.showwarning("Grafico","Installa matplotlib: pip install matplotlib"); return
        for w in self.entries:
            try:
                D = parse_number(w["D"].get().strip()); S = parse_number(w["S"].get().strip()); H = parse_number(w["H"].get().strip())
                break
            except Exception: continue
        else:
            messagebox.showwarning("Grafico", "Inserisci almeno una riga valida (D, S, H)."); return
        Qstar = math.sqrt(2.0 * D * S / H); q_min, q_max = max(1.0, Qstar*0.2), Qstar*3.0
        steps = 80; Qs = [q_min + i*(q_max-q_min)/steps for i in range(steps+1)]
        TCs = [(D/q)*S + (q/2.0)*H for q in Qs]
        import matplotlib.pyplot as plt
        plt.figure(); plt.plot(Qs, TCs, label="Costo totale annuo"); plt.axvline(Qstar, linestyle="--", label=f"EOQ ≈ {Qstar:.2f}")
        plt.xlabel("Q (quantità per ordine)"); plt.ylabel("Costo totale annuo"); plt.title(f"Curva costi vs Q • {self.brand.get('name','EOQ Pro')}")
        plt.legend(); plt.tight_layout(); plt.show()

    # Helpers
    def _confirm(self)->bool:
        if any(w[k].get().strip() for w in self.entries for k in ("D","S","H","L","sigma","csl")):
            return messagebox.askyesno("Conferma","I dati non salvati andranno persi. Continuare?")
        return True
    def _clear(self):
        for w in self.entries:
            for k in ("D","S","H","L","sigma","csl"): w[k].delete(0, tk.END)
        for i in self.tree.get_children(): self.tree.delete(i)
        self.status.config(text="Pronto. Default CSL=0.95 (se vuoto).")
    def _set_brand(self):
        win = tk.Toplevel(self); win.title("Imposta brand"); win.resizable(False, False)
        ttk.Label(win, text="Nome brand").grid(row=0,column=0,sticky="e",padx=6,pady=6)
        ttk.Label(win, text="Colore primario (hex)").grid(row=1,column=0,sticky="e",padx=6,pady=6)
        ttk.Label(win, text="Percorso logo (PNG/SVG)").grid(row=2,column=0,sticky="e",padx=6,pady=6)
        e_name = ttk.Entry(win, width=36); e_name.insert(0, self.brand["name"])
        e_color = ttk.Entry(win, width=36); e_color.insert(0, self.brand["color"])
        e_logo = ttk.Entry(win, width=36); e_logo.insert(0, self.brand.get("logo_path",""))
        def choose_logo():
            p = filedialog.askopenfilename(filetypes=[("Immagini","*.png;*.svg")], title="Seleziona logo")
            if p: e_logo.delete(0, tk.END); e_logo.insert(0, p)
        ttk.Button(win, text="Scegli…", command=choose_logo).grid(row=2,column=2,padx=4,pady=6)
        e_name.grid(row=0,column=1,padx=6,pady=6); e_color.grid(row=1,column=1,padx=6,pady=6); e_logo.grid(row=2,column=1,padx=6,pady=6)
        def apply():
            self.brand["name"]=e_name.get().strip() or "EOQ Pro"
            self.brand["color"]=e_color.get().strip() or "#0F6FFF"
            self.brand["logo_path"]=e_logo.get().strip(); win.destroy()
        ttk.Button(win, text="Applica", command=apply).grid(row=3, column=0, columnspan=3, pady=10)
    def _help(self):
        messagebox.showinfo("Guida rapida","1) Inserisci D, S, H (obbligatori). Opzionali: L, σ, CSL.\n2) Clicca Calcola.\n3) File: Import/Export CSV, Report HTML/PDF, Salva/Apri progetto.\nSuggerimento: se lasci CSL vuoto, uso 0.95.")
    def _about(self):
        messagebox.showinfo("Info","EOQ Pro • Versione Semplice\nDipendenze opzionali: matplotlib (grafici), reportlab (PDF)")


def main():
    app = EOQProSimple()
    app.mainloop()

if __name__ == "__main__":
    main()
