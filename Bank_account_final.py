import tkinter as tk                       # Import de Tkinter pour l'interface graphique
from tkinter import messagebox, simpledialog  # Boîtes de dialogue et messages
import matplotlib.pyplot as plt           # Pour tracer les graphiques
import datetime                            # Pour gérer les dates et heures
import json                                # Pour la sauvegarde et le chargement en JSON
import os                                  # Pour vérifier l'existence de fichiers


# === Fichier de données ===
DATA_FILE = "accounts.json"               # Nom du fichier JSON pour stocker les comptes

# === Classe Compte ===
class Account:
    """
    Classe représentant un compte bancaire avec fonctionnalités de dépôt, retrait,
    virement, historique et affichage des opérations.
    """
    def __init__(self, name, account_number, password, balance=0, output_widget=None):
        self.name = name                      # Nom du propriétaire
        self.account_number = account_number  # Numéro du compte
        self.password = password              # Mot de passe du compte
        self.balance = balance                # Solde initial
        self.historique = []                  # Historique des opérations
        self.output_widget = output_widget    # Widget Text pour afficher les logs
        self.daily_withdrawn = 0              # Limite de retrait journalier

    def _log(self, message, reset=False):
        """
        Affiche un message dans le widget de log ou dans la console si aucun widget.
        """
        if self.output_widget:
            if reset:
                self.output_widget.delete("1.0", "end")
            self.output_widget.insert("end", message + "\n")
            self.output_widget.see("end")
        else:
            print(message)

    def _add_history(self, operation, amount):
        """
        Ajoute une opération à l'historique avec la date et le montant.
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.historique.append({
            "date": now,
            "operation": operation,
            "montant": amount
        })

    def withdraw(self, amount):
        """
        Retrait d'argent avec vérification du solde et limite journalière.
        """
        if amount > self.balance:
            self._log("⚠️ Fonds insuffisants.", reset=True)
        elif self.daily_withdrawn + amount > 1000:
            self._log("⚠️ Limite de retrait journalier de 1000€ atteinte.", reset=True)
        else:
            self.balance -= amount
            self.daily_withdrawn += amount
            self._add_history("Retrait", -amount)
            self._log(f"💸 {amount}€ retirés. Nouveau solde: {self.balance}€", reset=True)
            save_data()  # Sauvegarde après chaque opération

    def deposit(self, amount):
        """
        Dépôt d'argent sur le compte.
        """
        if amount <= 0:
            self._log("⚠️ Montant invalide.", reset=True)
        else:
            self.balance += amount
            self._add_history("Dépôt", amount)
            self._log(f"💰 {amount}€ déposés. Nouveau solde: {self.balance}€", reset=True)
            save_data()

    def transfer_to(self, target_account, amount, external=False):
        """
        Virement vers un autre compte.
        - external=True ajoute des frais de 0.5€
        """
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
            self._add_history(f"Virement externe vers {target_account.name}", -amount - frais)
            target_account._add_history(f"Virement reçu de {self.name}", amount)
            self._log(f"🌍 Virement externe de {amount}€ effectué (+{frais}€ frais) vers {target_account.name}", reset=True)
        else:
            self._add_history(f"Virement vers {target_account.name}", -amount)
            target_account._add_history(f"Virement reçu de {self.name}", amount)
            self._log(f"🔄 Virement de {amount}€ effectué vers {target_account.name}", reset=True)
        save_data()

    def dump(self):
        """
        Affiche l'historique complet du compte.
        """
        self._log(f"\n👤 {self.name}, Compte n°{self.account_number}, Solde: {self.balance}€", reset=True)
        for h in self.historique:
            self._log(f"{h['date']} | {h['operation']} | {h['montant']}€", reset=False)

# === Sauvegarde / Chargement ===
def save_data():
    """
    Sauvegarde tous les comptes et livrets dans un fichier JSON.
    """
    data = {"accounts": {}, "livrets": {}}
    for num, acc in accounts.items():
        data["accounts"][num] = {
            "name": acc.name,
            "account_number": acc.account_number,
            "password": acc.password,
            "balance": acc.balance,
            "historique": acc.historique
        }
    for num, liv in livrets.items():
        data["livrets"][num] = {
            "name": liv.name,
            "account_number": liv.account_number,
            "password": liv.password,
            "balance": liv.balance,
            "historique": liv.historique
        }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_data():
    """
    Charge les comptes et livrets depuis le fichier JSON.
    """
    global accounts, livrets
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    for num, acc in data.get("accounts", {}).items():
        accounts[num] = Account(acc["name"], acc["account_number"], acc["password"], acc["balance"])
        accounts[num].historique = acc.get("historique", [])
    for num, liv in data.get("livrets", {}).items():
        livrets[num] = Account(liv["name"], liv["account_number"], liv["password"], liv["balance"])
        livrets[num].historique = liv.get("historique", [])

# === Interface Tkinter ===
root = tk.Tk()
root.title("Gestionnaire bancaire")
root.geometry("900x650")
root.configure(bg="black")

main_frame = tk.Frame(root, bg="black")
main_frame.pack(fill="both", expand=True)

log_text = tk.Text(root, bg="black", fg="#C0A060",
                   font=("Consolas", 12), relief="flat")

accounts = {}  # Dictionnaire de comptes courants
livrets = {}   # Dictionnaire de livrets
current_account = None
selected_account = None

# === Graphique des comptes ===
def show_graph():
    """
    Affiche un graphique de l'évolution du solde du compte sélectionné.
    """
    if not selected_account.historique:
        messagebox.showinfo("Info", "Aucune opération à afficher.")
        return

    labels = []
    values = []
    solde = 2000  # Solde de départ pour le graphique (exemple)
    for i, h in enumerate(selected_account.historique):
        labels.append(f"Opération {i+1}")
        solde += h["montant"]
        values.append(solde)

    plt.figure(figsize=(10,6))
    plt.plot(labels, values, marker='o', label="Solde")
    plt.title("Évolution du compte")
    plt.ylabel("Montant (€)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

# === Pages ===
def show_login_page():
    """
    Affiche la page d'accueil avec bouton de connexion.
    """
    global current_account
    current_account = None
    for widget in main_frame.winfo_children():
        widget.destroy()
    log_text.pack_forget()

    tk.Label(main_frame, text="🏦 Gestionnaire Bancaire",fg="#C0A060", bg="black", font=("Arial", 26, "bold")).pack(pady=40)
    tk.Button(main_frame, text="Connexion", command=open_login, font=("Arial", 16, "bold"), bg="#C0A060", fg="black",relief="flat", width=15, height=2).pack(pady=20)

def open_login():
    """
    Ouvre une fenêtre de connexion pour saisir le numéro et le mot de passe.
    """
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
        if num in accounts and accounts[num].password == pwd:
            current_account = accounts[num]
            current_account.output_widget = log_text
            log_text.delete("1.0", "end")
            messagebox.showinfo("Succès", f"Bienvenue {accounts[num].name} !")
            login_win.destroy()
            show_account_choice()
        else:
            messagebox.showerror("Erreur", "Numéro ou mot de passe invalide.")

    tk.Button(login_win, text="Se connecter", command=try_login,
              bg="#C0A060", fg="black", font=("Arial", 12, "bold"), relief="flat").pack(pady=15)

# === Choix de compte ===
def show_account_choice():
    """
    Affiche le choix entre Compte Courant et Livret A après connexion.
    """
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
        selected_account.output_widget = log_text
        log_text.delete("1.0", "end")
        open_dashboard()

    def open_livret():
        global selected_account
        if current_account.account_number in livrets:
            selected_account = livrets[current_account.account_number]
            selected_account.output_widget = log_text
            log_text.delete("1.0", "end")
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
                save_data()
                open_dashboard()

    tk.Button(main_frame, text="💼 Compte Courant", command=open_courant, **btn_style).pack(pady=10)
    tk.Button(main_frame, text=livret_btn_text, command=open_livret, **btn_style).pack(pady=10)
    tk.Button(main_frame, text="🚪 Quitter (Déconnexion)", command=show_login_page, **btn_style).pack(pady=20)

# === Tableau de bord ===
def open_dashboard():
    """
    Affiche le tableau de bord pour le compte sélectionné avec toutes les actions.
    """
    for widget in main_frame.winfo_children():
        widget.destroy()
    log_text.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(main_frame, text=f"Gestion de {selected_account.name}",
             fg="#C0A060", bg="black", font=("Arial", 20, "bold")).pack(pady=5)
    tk.Label(main_frame, text=f"Compte n° {selected_account.account_number}",
             fg="white", bg="black", font=("Arial", 14)).pack(pady=(0, 15))

    btn_style = {"bg": "#C0A060", "fg": "black", "font": ("Arial", 14, "bold"),
                 "relief": "flat", "width": 22, "height": 2}

    # Dépôt d'argent
    def deposit_money():
        amt = simpledialog.askfloat("Dépôt", "Montant à déposer :")
        if amt: 
            selected_account.deposit(float(amt))

    # Retrait d'argent
    def withdraw_money():
        amt = simpledialog.askfloat("Retrait", "Montant à retirer :")
        if amt: 
            selected_account.withdraw(float(amt))

    # Virement
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

            frais = 0.5
            if messagebox.askyesno("Frais virement", f"Un frais de {frais}€ sera ajouté au virement. Continuer ?"):
                target = accounts[target_num]
                selected_account.transfer_to(target, float(amt), external=True)
                transfer_win.destroy()

        tk.Button(transfer_win, text="📂 Virement vers Livret A/Compte Courant", command=virement_livret,
                  bg="#C0A060", fg="black", font=("Arial", 12, "bold"), relief="flat").pack(pady=10)
        tk.Button(transfer_win, text="🌍 Virement vers Compte Externe", command=virement_externe,
                  bg="#C0A060", fg="black", font=("Arial", 12, "bold"), relief="flat").pack(pady=10)

    # Affichage de l'historique
    def show_history():
        selected_account.dump()

    # Retour au choix de compte
    def quit_account():
        show_account_choice()

    # Boutons principaux du tableau de bord
    tk.Button(main_frame, text="💰 Déposer", command=deposit_money, **btn_style).pack(pady=5)
    tk.Button(main_frame, text="💸 Retirer", command=withdraw_money, **btn_style).pack(pady=5)
    tk.Button(main_frame, text="🔄 Virement", command=transfer_money, **btn_style).pack(pady=5)
    tk.Button(main_frame, text="📜 Historique", command=show_history, **btn_style).pack(pady=5)    
    tk.Button(main_frame, text="📊 Voir Graphique", command=show_graph, **btn_style).pack(pady=5)
    tk.Button(main_frame, text="⬅️ Retour choix de compte", command=quit_account, **btn_style).pack(pady=15)

# === Chargement des comptes existants ou création test ===
load_data()
if not accounts:
    accounts["950201848"] = Account("Ross", "950201848", "1350", balance=2000, output_widget=log_text)  
    accounts["194572957"] = Account("Rachel", "194572957", "3450", balance=2000, output_widget=log_text)
    save_data()

# === Lancement ===
show_login_page()  # Affiche la page de connexion
root.mainloop()    # Lancement de la boucle Tkinter
