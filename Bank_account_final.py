import tkinter as tk
from tkinter import messagebox, simpledialog
import matplotlib.pyplot as plt

# === Classe Compte ===
class Account:
    def __init__(self, name, account_number, password, balance=0, output_widget=None):
        self.name = name
        self.account_number = account_number
        self.password = password
        self.balance = balance
        self.historique = []
        self.output_widget = output_widget
        self.daily_withdrawn = 0  # Suivi des retraits journaliers

    def _log(self, message, reset=False):
        if self.output_widget:
            if reset:
                self.output_widget.delete("1.0", "end")  # vide avant chaque message
            self.output_widget.insert("end", message + "\n")
            self.output_widget.see("end")
        else:
            print(message)

    def withdraw(self, amount):
        if amount > self.balance:
            self._log("⚠️ Fonds insuffisants.", reset=True)
        elif self.daily_withdrawn + amount > 1000:
            self._log("⚠️ Limite de retrait journalier de 1000€ atteinte.", reset=True)
        else:
            self.balance -= amount
            self.daily_withdrawn += amount
            self.historique.append(f"-{amount}€ retirés")
            self._log(f"💸 {amount}€ retirés. Nouveau solde: {self.balance}€", reset=True)

    def deposit(self, amount):
        if amount <= 0:
            self._log("⚠️ Montant invalide.", reset=True)
        else:
            self.balance += amount
            self.historique.append(f"+{amount}€ déposés")
            self._log(f"💰 {amount}€ déposés. Nouveau solde: {self.balance}€", reset=True)

    def dump(self):
        self._log(f"\n👤 {self.name}, Compte n°{self.account_number}, Solde: {self.balance}€", reset=True)
        self._log(f"📜 Historique: {self.historique}", reset=False)

    def transfer_to(self, target_account, amount, external=False):
        frais = 0.5 if external else 0
        total_amount = amount + frais
        if amount <= 0:
            self._log("⚠️ Montant invalide pour virement.", reset=True)
            return
        if total_amount > self.balance:
            self._log("⚠️ Fonds insuffisants pour le virement.", reset=True)
            return

        self.balance -= total_amount
        target_account.balance += amount
        if external:
            self.historique.append(f"Virement externe de -{amount}€ + {frais}€ frais vers {target_account.name} ({target_account.account_number})")
            target_account.historique.append(f"Virement reçu +{amount}€ de {self.name} ({self.account_number})")
            self._log(f"🌍 Virement externe de {amount}€ effectué (+{frais}€ frais) vers {target_account.name}", reset=True)
        else:
            self.historique.append(f"Virement de -{amount}€ vers {target_account.name} ({target_account.account_number})")
            target_account.historique.append(f"Virement reçu +{amount}€ de {self.name} ({self.account_number})")
            self._log(f"🔄 Virement de {amount}€ effectué vers {target_account.name} ({target_account.account_number})", reset=True)

# === Interface Tkinter ===
root = tk.Tk()
root.title("Gestionnaire bancaire")
root.geometry("900x650")
root.configure(bg="black")

main_frame = tk.Frame(root, bg="black")
main_frame.place(relx=0.5, rely=0.5, anchor="center")

accounts = {}
livrets = {}
current_account = None
selected_account = None

main_frame = tk.Frame(root, bg="black")
main_frame.pack(fill="both", expand=True)

log_text = tk.Text(root, bg="black", fg="#C0A060",
                   font=("Consolas", 12), relief="flat")

# === Pages ===
def show_login_page():
    global current_account
    current_account = None
    for widget in main_frame.winfo_children():
        widget.destroy()
    log_text.pack_forget()

    tk.Label(main_frame, text="🏦 Gestionnaire Bancaire",fg="#C0A060", bg="black", font=("Arial", 26, "bold")).pack(pady=40)
    tk.Button(main_frame, text="Connexion", command=open_login, font=("Arial", 16, "bold"), bg="#C0A060", fg="black",relief="flat", width=15, height=2).pack(pady=20)

def open_login():
    login_win = tk.Toplevel(root)
    login_win.title("Connexion")
    login_win.geometry("400x250")
    login_win.configure(bg="black")

    tk.Label(login_win, text="Numéro de compte :", fg="#C0A060", bg="black", font=("Arial", 12)).pack(pady=5)
    entry_num = tk.Entry(login_win, font=("Arial", 12))
    entry_num.pack(pady=5)

    tk.Label(login_win, text="Mot de passe :", fg="#C0A060", bg="black", font=("Arial", 12)).pack(pady=5)
    entry_pwd = tk.Entry(login_win, show="*", font=("Arial", 12))
    entry_pwd.pack(pady=5)

    def try_login():
        global current_account
        num = entry_num.get()
        pwd = entry_pwd.get()

        if not (num.isdigit() and len(num) == 9):
            messagebox.showerror("Erreur", "Le numéro de compte doit contenir exactement 9 chiffres.")
            return
        if not (pwd.isdigit() and len(pwd) == 4):
            messagebox.showerror("Erreur", "Le mot de passe doit contenir exactement 4 chiffres.")
            return

        if num in accounts and accounts[num].password == pwd:
            current_account = accounts[num]
            messagebox.showinfo("Succès", f"Bienvenue {accounts[num].name} !")
            login_win.destroy()
            show_account_choice()
        else:
            messagebox.showerror("Erreur", "Numéro ou mot de passe invalide.")

    tk.Button(login_win, text="Se connecter", command=try_login,
              bg="#C0A060", fg="black", font=("Arial", 12, "bold"), relief="flat").pack(pady=15)

# === Graphique de l'évolution des comptes ===
def show_graph():
    if not current_account.historique:
        messagebox.showinfo("Info", "Aucune opération à afficher.")
        return

    solde_courant = current_account.balance
    solde_livret = livrets[current_account.account_number].balance if current_account.account_number in livrets else 0

    labels = []
    compte_courant_values = []
    livret_values = []
    total_values = []

    courant = solde_courant - sum(
        float(h.split("€")[0].replace("+","").replace("-","")) for h in current_account.historique
    )
    courant_tmp = courant
    livret_tmp = solde_livret

    for i, h in enumerate(current_account.historique):
        labels.append(f"Opération {i+1}")
        if "dép" in h.lower() or "retir" in h.lower():
            montant = float(h.split("€")[0].replace("+","").replace("-",""))
            if h.startswith("+"):
                courant_tmp += montant
            else:
                courant_tmp -= montant
        elif "Virement" in h:
            montant = float(h.split("€")[0].replace("+","").replace("-",""))
            if "vers" in h and current_account.name in h:
                courant_tmp += montant
            elif "vers" in h:
                courant_tmp -= montant

        compte_courant_values.append(courant_tmp)

        if current_account.account_number in livrets:
            livret_tmp = livrets[current_account.account_number].balance
            for lh in livrets[current_account.account_number].historique:
                montant = float(lh.split("€")[0].replace("+","").replace("-",""))
                if "reçu" in lh.lower():
                    livret_tmp += montant
                elif "Virement de" in lh:
                    livret_tmp -= montant
            livret_values.append(livret_tmp)
        else:
            livret_values.append(0)

        total_values.append(compte_courant_values[-1] + livret_values[-1])

    plt.figure(figsize=(10,6))
    plt.plot(labels, compte_courant_values, marker='o', label="Compte Courant")
    plt.plot(labels, livret_values, marker='o', label="Livret A")
    plt.plot(labels, total_values, marker='o', label="Solde Total")
    plt.title("Évolution des comptes par opération")
    plt.ylabel("Montant (€)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

# === Choix de compte ===
def show_account_choice():
    global selected_account
    selected_account = None
    for widget in main_frame.winfo_children():
        widget.destroy()

    tk.Label(main_frame, text=f"👤 Bienvenue {current_account.name}",
             fg="#C0A060", bg="black", font=("Arial", 22, "bold")).pack(pady=(20, 5))
    tk.Label(main_frame, text=f"Compte n° {current_account.account_number}",
             fg="white", bg="black", font=("Arial", 14)).pack(pady=(0, 10))
    tk.Label(main_frame, text=f"💼 Solde Compte Courant : {current_account.balance}€",
             fg="white", bg="black", font=("Arial", 14, "bold")).pack(pady=5)

    if current_account.account_number in livrets:
        solde_livret = livrets[current_account.account_number].balance
        tk.Label(main_frame, text=f"📂 Solde Livret A : {solde_livret}€",
                 fg="white", bg="black", font=("Arial", 14, "bold")).pack(pady=5)
        livret_btn_text = "📂 Livret A"
    else:
        livret_btn_text = "📂 Ouvrir un Livret A"

    btn_style = {"bg": "#C0A060", "fg": "black", "font": ("Arial", 14, "bold"),
                 "relief": "flat", "width": 20, "height": 2}

    def open_courant():
        global selected_account
        selected_account = current_account
        open_dashboard()

    def open_livret():
        global selected_account
        if current_account.account_number in livrets:
            selected_account = livrets[current_account.account_number]
            open_dashboard()
        else:
            res = messagebox.askyesno("Livret A", "Aucun Livret A. Voulez-vous en créer un ?")
            if res:
                livret = Account("Livret A de " + current_account.name,
                                 "LIV" + current_account.account_number,
                                 current_account.password,
                                 balance=0,
                                 output_widget=log_text)
                livrets[current_account.account_number] = livret
                selected_account = livret
                open_dashboard()

    tk.Button(main_frame, text="💼 Compte Courant", command=open_courant, **btn_style).pack(pady=10)
    tk.Button(main_frame, text=livret_btn_text, command=open_livret, **btn_style).pack(pady=10)
    tk.Button(main_frame, text="🚪 Quitter (Déconnexion)", command=show_login_page, **btn_style).pack(pady=20)

# === Tableau de bord ===
def open_dashboard():
    for widget in main_frame.winfo_children():
        widget.destroy()
    log_text.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(main_frame, text=f"Gestion de {selected_account.name}",
             fg="#C0A060", bg="black", font=("Arial", 20, "bold")).pack(pady=5)
    tk.Label(main_frame, text=f"Compte n° {selected_account.account_number}",
             fg="white", bg="black", font=("Arial", 14)).pack(pady=(0, 15))

    btn_style = {"bg": "#C0A060", "fg": "black", "font": ("Arial", 14, "bold"),
                 "relief": "flat", "width": 22, "height": 2}

    def deposit_money():
        amt = simpledialog.askfloat("Dépôt", "Montant à déposer :")
        if amt: selected_account.deposit(float(amt))

    def withdraw_money():
        amt = simpledialog.askfloat("Retrait", "Montant à retirer :")
        if amt: selected_account.withdraw(float(amt))

    def transfer_money():
        transfer_win = tk.Toplevel(root)
        transfer_win.title("Virement")
        transfer_win.geometry("350x200")
        transfer_win.configure(bg="black")

        tk.Label(transfer_win, text="Choisissez le type de virement :", fg="#C0A060",
                 bg="black", font=("Arial", 14)).pack(pady=15)

        def virement_livret():
            amt = simpledialog.askfloat("Virement", "Montant à transférer :")
            if not amt: return
            if selected_account.account_number.startswith("LIV"):
                target = current_account
            else:
                if current_account.account_number not in livrets:
                    messagebox.showerror("Erreur", "Vous n’avez pas de Livret A.")
                    return
                target = livrets[current_account.account_number]
            selected_account.transfer_to(target, float(amt))
            transfer_win.destroy()

        def virement_externe():
            amt = simpledialog.askfloat("Virement", "Montant à transférer :")
            if not amt: return
            target_num = simpledialog.askstring("Virement externe", "Numéro du compte destinataire (9 chiffres) :")
            if not target_num or target_num not in accounts:
                messagebox.showerror("Erreur", "Compte destinataire introuvable.")
                return
            target = accounts[target_num]
            selected_account.transfer_to(target, float(amt), external=True)
            transfer_win.destroy()

        tk.Button(transfer_win, text="📂 Virement vers Livret A/Compte Courant", command=virement_livret,
                  bg="#C0A060", fg="black", font=("Arial", 12, "bold"), relief="flat").pack(pady=10)
        tk.Button(transfer_win, text="🌍 Virement vers Compte Externe", command=virement_externe,
                  bg="#C0A060", fg="black", font=("Arial", 12, "bold"), relief="flat").pack(pady=10)

    def show_history():
        selected_account.dump()

    def quit_account():
        show_account_choice()

    tk.Button(main_frame, text="💰 Déposer", command=deposit_money, **btn_style).pack(pady=5)
    tk.Button(main_frame, text="💸 Retirer", command=withdraw_money, **btn_style).pack(pady=5)
    tk.Button(main_frame, text="🔄 Virement", command=transfer_money, **btn_style).pack(pady=5)
    tk.Button(main_frame, text="📜 Historique", command=show_history, **btn_style).pack(pady=5)    
    tk.Button(main_frame, text="📊 Voir Graphique", command=show_graph, **btn_style).pack(pady=5)
    tk.Button(main_frame, text="⬅️ Retour choix de compte", command=quit_account, **btn_style).pack(pady=15)

# === Comptes de test ===
accounts["950201848"] = Account("Ross", "950201848", "1350", balance=2000, output_widget=log_text)  
accounts["194572957"] = Account("Rachel", "194572957", "3450", balance=2000, output_widget=log_text)

# === Lancement ===
show_login_page()
root.mainloop()
