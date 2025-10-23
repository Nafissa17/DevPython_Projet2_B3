# 💳 Challenge - Bank Account

## 🎯 Objectifs
Modéliser un **compte bancaire** afin d'améliorer vos compétences en **programmation orientée objet (OOP)**.

---

## 📌 Consignes
Écrire une classe **`Account`** qui possède les caractéristiques suivantes :

- Le compte contient plusieurs données :  
  - **Nom du titulaire**  
  - **Numéro de compte**  
  - **Solde actuel** (par défaut : **2000**)

- Trois opérations possibles sur un compte :  
  1. **Retrait** (withdraw money)  
  2. **Dépôt** (deposit money)  
  3. **Affichage des informations** du compte (dump)
     
---

## ✨ Fonctionnalités Supplémentaires
Nous avons rajouté les fonctionnalités suivantes :

  - **Nom du titulaire**  
  - **Numéro de compte**  
  - **Solde actuel** (par défaut : **2000**)
  - **Sauvegarde des données avec un fichier json**
  - **Frais de virement externe de 0,5 centimes**
  - **Limite de retrait journalière de 1000 euros**
  - **Historique pour l'utilisateur**
  - **Graphique pour visualiser les transactions**

---

## 🏦 Exemple d'utilisation

Instancier deux comptes bancaires pour **Ross** et **Rachel** avec des numéros de compte aléatoires.  
Effectuer plusieurs dépôts et retraits, puis afficher les informations des comptes.

Exemple attendu :

```python
ross_account.dump()
# Ross, 9502018482, 1350

rachel_account.dump()
# Rachel, 1945729572, 3450













