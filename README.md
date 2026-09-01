# SolaX Local X1 Micro - Intégration Home Assistant

[![CI](https://github.com/Knetus56/solax_local_x1_micro/actions/workflows/ci.yml/badge.svg)](https://github.com/Knetus56/solax_local_x1_micro/actions/workflows/ci.yml)

Une intégration [Home Assistant](https://www.home-assistant.io/) pour contrôler et monitorer votre onduleur **SolaX** en local via le protocole HTTP.

## 🌟 Fonctionnalités

- 📊 **Monitoring en temps réel** : Puissance MPPT, production d'énergie, température
- 🔄 **Contrôle de l'onduleur** : Allumage/extinction via switch
- 📈 **Tracking de production** : Production du jour et cumulative
- 🕐 **Historique** : Timestamp de la dernière mise à jour
- 🌍 **Support multi-inverter** : X1 Micro 2-in-1
- 🔐 **Connexion locale** : Pas de cloud, entièrement en local
- 🇫🇷 **Interface localisée** : Français, anglais et néerlandais (traduction complète des entités selon la langue de Home Assistant)
- ⚙️ **Modifiable après coup** : changez l'adresse IP ou l'intervalle de scan sans recréer l'intégration
- 🌙 **Pause nocturne automatique** : pas de requête inutile pendant la nuit (basé sur le lever/coucher du soleil, marge d'1h)

## 📋 Capteurs (Sensors)

| Capteur | Description | Unité |
|---------|-------------|-------|
| `mppt1_puissance` | Puissance MPPT 1 | W |
| `mppt1_voltage` | Tension MPPT 1 | V |
| `mppt1_intensite` | Courant MPPT 1 | A |
| `mppt2_puissance` | Puissance MPPT 2 | W |
| `mppt2_voltage` | Tension MPPT 2 | V |
| `mppt2_intensite` | Courant MPPT 2 | A |
| `inverter_voltage` | Tension de sortie onduleur | V |
| `inverter_intensite` | Courant de sortie onduleur | A |
| `inverter_puissance` | Puissance de sortie onduleur | W |
| `inverter_freq` | Fréquence onduleur | Hz |
| `temp` | Température de l'onduleur | °C |
| `prod_auj` | Production du jour | kWh |
| `prod_total` | Production totale cumulative | kWh |
| `mode` | Mode de fonctionnement | WaitMode/CheckMode/NormalMode |
| `ip` | Adresse IP de l'onduleur | - |
| `num_inverter` | Numéro de série | - |
| `last_update` | Dernière mise à jour | timestamp |

## 🔌 Entités de Contrôle

- **Binary Sensor** : État en ligne/hors ligne
- **Switch** : Allumage/extinction de l'onduleur

## 🔄 Services

### Actualiser tous les onduleurs

Service: `solax_local.refresh_all`

Force la mise à jour immédiate de tous les onduleurs configurés sans attendre l'intervalle de scan.

**Utilisation dans une automatisation** :
```yaml
service: solax_local.refresh_all
```

**Ou dans les outils de développement** :
1. **Outils de développement** > **Services**
2. Sélectionner `SolaX Local X1 Micro: Refresh all inverters`
3. Cliquer **Exécuter**

## 🚀 Installation

### Prérequis

- Home Assistant 2023.12+
- Accès réseau à l'onduleur SolaX
- Adresse IP et numéro de série de l'onduleur

### Via HACS (recommandé)

**Une fois l'intégration acceptée dans le store officiel HACS** :
1. Ouvrir Home Assistant
2. Aller à **HACS** > **Intégrations** > **Explorer & télécharger**
3. Chercher "SolaX Local X1 Micro"
4. Cliquer **Télécharger**
5. Redémarrer Home Assistant

**En attendant cette validation** (ou pour suivre une branche/version précise), ajout en dépôt personnalisé :

**Lien direct HACS** : 
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Knetus56&repository=solax_local_x1_micro&category=integration)

Ou manuellement :
1. Ouvrir Home Assistant
2. Aller à **HACS** > **Intégrations**
3. Cliquer sur le **menu** (⋯) > **Dépôts personnalisés**
4. Ajouter l'URL: `https://github.com/Knetus56/solax_local_x1_micro`
5. Chercher "SolaX Local X1 Micro"
6. Cliquer **Installer**
7. Redémarrer Home Assistant

### Installation manuelle

1. Télécharger la dernière [version](https://github.com/Knetus56/solax_local_x1_micro/releases)
2. Extraire dans `custom_components/solax_local/`
3. Redémarrer Home Assistant

## ⚙️ Configuration

### Via interface Home Assistant

1. **Paramètres** > **Appareils et services** > **Intégrations**
2. Cliquer **Créer une intégration**
3. Chercher et sélectionner **SolaX Local X1 Micro**
4. Remplir les informations :
   - **IP** : Adresse IP de l'onduleur (ex: `192.168.1.100`)
   - **Type d'onduleur** : Sélectionner le modèle
   - **Numéro de série** : Numéro de série de l'onduleur
   - **Intervalle de scan** (optionnel) : Fréquence de mise à jour en secondes (défaut: 300s)

> Le numéro de série est automatiquement normalisé en majuscules.

### Modifier la configuration après installation

Il n'est plus nécessaire de supprimer/recréer l'intégration pour changer l'adresse IP ou l'intervalle de scan :

1. **Paramètres** > **Appareils et services**
2. Repérer la carte **SolaX Local X1 Micro** > cliquer **Configurer** (icône ⚙️)
3. Mettre à jour l'**hôte** et/ou l'**intervalle de scan**
4. Valider — l'intégration se recharge automatiquement avec les nouvelles valeurs

Le type d'onduleur et le numéro de série restent fixes après la création (ils identifient l'appareil) ; pour les changer, il faut recréer l'intégration.

## 🔧 Configuration avancée

### Intervalle de mise à jour

Par défaut, l'intégration interroge l'onduleur toutes les **300 secondes** (5 minutes). Vous pouvez l'ajuster lors de la configuration.

### Pause nocturne (basée sur `sun.sun`)

Les onduleurs SolaX coupent leur dongle Wi-Fi la nuit : chaque requête envoyée pendant cette période échoue de toute façon (timeout). L'intégration évite ces appels inutiles en s'appuyant sur l'entité **`sun.sun`**, intégrée nativement à Home Assistant (composant `sun`, quasi toujours présent — calcule le lever/coucher réel du soleil selon la position géographique et le fuseau horaire configurés dans **Paramètres > Système > Général**).

**Comment ça marche** : à chaque cycle de poll, l'intégration vérifie si le soleil est couché depuis plus d'1h *et* le restera pour au moins 1h de plus. Seulement dans ce cas — nuit "installée", loin de toute transition — la requête HTTP est carrément sautée. Cette double vérification (1h avant *et* 1h après l'instant présent) crée naturellement une marge symétrique d'**1 heure** autour du lever et du coucher réels, sans avoir besoin de calculer soi-même les horaires astronomiques :

```
                    coucher réel du soleil                lever réel du soleil
                            │                                      │
   ── requêtes normales ────┤── marge 1h ──┤ PAUSE (pas de requête) ├── marge 1h ──┤── requêtes normales ──
                                            │                       │
                                     coucher + 1h              lever - 1h
```

Concrètement : si le soleil se couche à 20h00, l'intégration continue d'interroger l'onduleur jusqu'à 21h00, puis se met en pause. Si le lever est à 07h00 le lendemain, elle reprend dès 06h00 — pour ne pas rater un onduleur qui démarrerait un peu plus tôt ou plus tard que prévu (nuages, saison, décalage de l'horloge interne de l'onduleur, etc.).

**Si l'entité `sun.sun` n'existe pas** (composant Soleil désactivé ou supprimé manuellement) : la pause nocturne se désactive automatiquement et silencieusement — l'intégration interroge normalement à **chaque** cycle de poll, jour et nuit, exactement comme avant l'ajout de cette fonctionnalité. Aucune configuration n'est nécessaire pour ce cas, aucune erreur n'est levée.

**Effet sur les capteurs pendant la pause** : identique à une erreur réseau classique — mesures instantanées (puissance, tension, courant, fréquence, température) à `0`, `mode` à "Inconnu", `prod_auj`/`prod_total` conservent leur dernière valeur connue (voir section suivante). Le capteur `binary_sensor.online` passe à `Off`.

Cette pause n'est pas configurable pour l'instant (pas de bascule marche/arrêt ni de réglage de marge dans l'UI) — si besoin, ouvrez une issue sur le repo.

### Entités DIAGNOSTIC

Les entités suivantes sont masquées par défaut (onglet Avancé) :
- État du mode
- Adresse IP
- Numéro de série
- Dernière mise à jour

Pour les afficher : **Paramètres** > **Appareils et services** > Sélectionner le device > **Afficher les entités masquées**


### Les capteurs affichent "Inconnu"

- Normal la nuit (pause nocturne automatique, voir plus haut) ou en cas d'erreur de requête ponctuelle — `mode` repasse à "Inconnu" jusqu'au prochain poll réussi
- Vérifier que l'adresse IP est correcte
- Vérifier que l'onduleur est **en ligne** et **alimenté**
- Vérifier la **connectivité réseau** entre HA et l'onduleur
- Augmenter l'`intervalle de scan` en cas de timeout réseau

### L'intégration ne charge pas

- Vérifier les logs : **Paramètres** > **Système** > **Journaux**
- Chercher les erreurs de connexion
- Redémarrer Home Assistant

### Le device n'affiche pas le modèle

- Cela signifie que le modèle sélectionné n'est pas reconnu
- Vérifier la sélection lors de la configuration


## 📦 Versions

- **v1.4.1** (2026-08-28) - Ajout de logs `debug` dans `parse_data()` (`solax_protocol.py`) : payload base64 brut reçu et bytes décodés en hexadécimal, pour faciliter le diagnostic des trames renvoyées par l'onduleur
- **v1.4.0** (2026-08-28) - Reprend plusieurs idées de la PR #1 (fork [webpatrick/solax_local](https://github.com/webpatrick/solax_local), fermée sans merge) : traduction néerlandaise (`nl.json`), `device_class` `connectivity`/`frequency` sur les capteurs `online`/`inverter_freq`, et un parsing des trames plus tolérant côté `solax_protocol.py` (paquets dès 80 octets au lieu de 112, type de paquet non vérifié — seul le numéro de série identifie la réponse). `mode`/`prod_auj`/`prod_total` restent à `None` (jamais un faux 0) quand leur registre n'est pas présent dans un paquet raccourci
- **v1.3.6** (2026-08-28) - Refactor interne de `coordinator.py` : la logique de persistance des valeurs (`prod_auj`/`prod_total`, reset à minuit) est extraite dans une méthode dédiée `_apply_persistence()`. Aucun changement de comportement, juste plus lisible
- **v1.3.5** (2026-08-28) - Ajout d'une CI GitHub Actions (`hassfest` + validation Python/JSON, voir section suivante). Valeurs du capteur `mode` passées en snake_case minuscule (`wait_mode`/`check_mode`/`normal_mode` au lieu de `WaitMode`/`CheckMode`/`NormalMode`) pour respecter le schéma officiel de traduction HA (`hassfest` l'exigeait) — sans impact visible : les libellés affichés restent identiques
- **v1.3.4** (2026-08-28) - `prod_auj` (production du jour) repasse automatiquement à 0 dès le changement de jour calendaire, même sans nouvelle donnée réelle (nuit, erreur réseau) — évite d'afficher encore la production d'hier après minuit. `prod_total` continue de persister normalement (compteur à vie, jamais réinitialisé)
- **v1.3.3** (2026-08-28) - Pause nocturne automatique basée sur `sun.sun` (marge d'1h autour du lever/coucher réel) : plus de requête réseau inutile pendant la nuit quand l'onduleur a coupé son Wi-Fi. Se désactive proprement si l'entité `sun.sun` est absente
- **v1.3.2** (2026-08-28) - Capteur `mode` passé en type énuméré (`sensor.enum`) : seules `WaitMode`/`CheckMode`/`NormalMode` sont des valeurs valides, traduites en FR/EN ; il repasse à "Inconnu" à chaque erreur de requête (reflète uniquement le dernier poll réussi, plus de valeur inventée type "Offline"). `prod_auj`/`prod_total` gardent leur dernière valeur connue en cas d'erreur de requête au lieu de retomber à 0 (évite de fausser les statistiques long terme)
- **v1.3.1** (2026-08-28) - Correction du schéma de traduction des noms d'entités (structure imbriquée `{"name": ...}` requise par HA — les noms ne se résolvaient pas sans ça) ; renommage MPPT 1/MPPT 2 → MPPT1/MPPT2
- **v1.3.0** (2026-08-28) - Flow d'options (modifier IP/intervalle de scan sans recréer l'intégration), numéro de série normalisé en majuscules, traductions d'entités correctement câblées (noms adaptés à la langue de HA), correction des messages d'erreur du formulaire de configuration, migration réseau vers `aiohttp` (session partagée HA au lieu de threads bloquants), nettoyage interne (dédoublonnage `device_info`, suppression de code mort)
- **v1.2.2** (2026-07-22) - Ajout de l'icône personnalisée pour HACS
- **v1.2.1** (2026-07-22) - Ajout du service refresh_all pour actualiser tous les onduleurs
- **v1.2.0** (2026-07-22) - Ajout des capteurs tension/courant MPPT et métriques onduleur
- **v1.1.0** (2026-07-22) - Fix clés MPPT et initialisation du modèle


## 🙏 Remerciements

- https://github.com/CurlyMoo grace a son reverse ici : https://github.com/squishykid/solax/issues/191
