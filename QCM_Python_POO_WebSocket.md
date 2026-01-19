# QCM – Évaluation Python & POO

Ce QCM vise à évaluer la compréhension de Python et de la Programmation Orientée Objet (POO)
à partir du code fourni (classes Message, WSClient, WSServer).

---

## Partie 1 – Concepts généraux Python & POO

### Question 1
Quel est le rôle principal de la classe `MessageType` ?

A. Créer des instances de messages
**B. Simuler une énumération de types de messages**
C. Sérialiser des messages en JSON
D. Gérer les WebSockets  

---

### Question 2
Pourquoi `MessageType` n'hérite-t-elle pas de `Enum` ?

A. Parce que `Enum` est obsolète
B. Parce que Python ne supporte pas les enums
**C. Parce qu'il s'agit d'un choix de conception simplifié**
D. Parce que les enums ne peuvent pas contenir de chaînes  

---

### Question 3
Dans le constructeur de `Message`, que représente le paramètre `receiver=None` ?

A. Une valeur obligatoire
B. Une surcharge de méthode
**C. Un paramètre optionnel avec valeur par défaut**
D. Un attribut statique  

---

## Partie 2 – Méthodes et encapsulation

### Question 4
Quel est l'intérêt de la méthode statique `default_message()` ?

A. Modifier l'état d'un message existant
B. Créer une instance sans appeler le constructeur
**C. Fournir une instance par défaut de `Message`**
D. Lire un message depuis un fichier  

---

### Question 5
Pourquoi `default_message()` est-elle décorée avec `@staticmethod` ?

A. Elle utilise `self`
B. Elle agit sur la classe et non sur une instance
**C. Elle ne dépend ni de l'instance ni de la classe**
D. Elle est plus rapide  

---

### Question 6
Quel problème potentiel existe dans `default_message()` ?

**A. Le type du message n'est pas cohérent avec `MessageType`**
B. Le JSON est mal formé
C. La méthode n'est jamais appelée
D. Le receiver est obligatoire  

---

## Partie 3 – Sérialisation JSON

### Question 7
Quel est le rôle de la méthode `to_json()` ?

A. Lire un message depuis un socket
B. Convertir un message en dictionnaire Python
**C. Convertir un message en chaîne JSON**
D. Envoyer un message sur le réseau  

---

### Question 8
Pourquoi `import json` est-il placé à l'intérieur des méthodes ?

**A. Pour réduire la portée de l'import**
B. Pour accélérer le programme
C. Pour éviter les conflits de noms
D. Ce n'est pas autorisé en Python  

---

### Question 9
Que fait la méthode `from_json()` ?

A. Elle modifie un message existant
**B. Elle crée une instance de `Message` à partir d'une chaîne JSON**
C. Elle valide le schéma JSON
D. Elle envoie un message  

---

### Question 10
À quoi sert l'instruction `assert` dans ce code ?

A. Gérer les exceptions
**B. Tester l'égalité logique de deux messages**
C. Forcer la conversion JSON
D. Optimiser les performances  

---

## Partie 4 – WebSocket Client

### Question 11
Quel est le rôle principal de la classe `WSClient` ?

A. Héberger un serveur WebSocket
B. Gérer la configuration réseau
**C. Se connecter à un serveur WebSocket et échanger des messages**
D. Sérialiser les messages  

---

### Question 12
Pourquoi les méthodes `on_open`, `on_message`, etc. sont-elles passées au constructeur de `WebSocketApp` ?

A. Pour respecter une interface imposée
**B. Pour être appelées automatiquement lors des événements WebSocket**
C. Pour améliorer les performances
D. Pour éviter l'héritage  

---

## Partie 5 – WebSocket Server

### Question 13
Quel est le rôle de la classe `WSServer` ?

A. Se connecter à un serveur distant
**B. Gérer plusieurs clients WebSocket**
C. Créer des messages JSON
D. Tester le client  

---

### Question 14
Pourquoi utilise-t-on des méthodes statiques `dev()` et `prod()` ?

A. Pour changer dynamiquement le code source
**B. Pour fournir des configurations différentes du serveur**
C. Pour améliorer la sécurité
D. Pour éviter l'instanciation  

---

### Question 15
Quel principe POO est principalement illustré par les classes `WSClient` et `WSServer` ?

A. Héritage
B. Polymorphisme
**C. Encapsulation**
D. Surcharge  

---

## Bonus – Question ouverte

### Question 16
Citez deux améliorations possibles à apporter à ce code (structure, robustesse, typage, sécurité, etc.).

**Réponses possibles :**

1. **Gestion d'erreurs** : Ajouter des try/except pour gérer les erreurs JSON et les erreurs réseau.

2. **Utiliser une vraie Enum** : Remplacer `MessageType` par `from enum import Enum` pour valider les types de messages.

---

**Fin du QCM**
