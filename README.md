# SolaX Local - Intégration Home Assistant

Une intégration [Home Assistant](https://www.home-assistant.io/) pour contrôler et monitorer votre onduleur **SolaX** en local via le protocole HTTP.

## 🌟 Fonctionnalités

- 📊 **Monitoring en temps réel** : Puissance MPPT, production d'énergie, température
- 🔄 **Contrôle de l'onduleur** : Allumage/extinction via switch
- 📈 **Tracking de production** : Production du jour et cumulative
- 🕐 **Historique** : Timestamp de la dernière mise à jour
- 🌍 **Support multi-inverter** : X1 Micro 2-in-1
- 🔐 **Connexion locale** : Pas de cloud, entièrement en local
- 🇫🇷 **Interface localisée** : Français et anglais (traduction complète des entités selon la langue de Home Assistant)
- ⚙️ **Modifiable après coup** : changez l'adresse IP ou l'intervalle de scan sans recréer l'intégration

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
2. Sélectionner `SolaX Local: Refresh all inverters`
3. Cliquer **Exécuter**

## 🚀 Installation

### Prérequis

- Home Assistant 2023.12+
- Accès réseau à l'onduleur SolaX
- Adresse IP et numéro de série de l'onduleur

### Via HACS (recommandé)

**Lien direct HACS** : 
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs/?repository=https://github.com/Knetus56/solax_local&category=integration)

Ou manuellement :
1. Ouvrir Home Assistant
2. Aller à **HACS** > **Intégrations**
3. Cliquer sur le **menu** (⋯) > **Dépôts personnalisés**
4. Ajouter l'URL: `https://github.com/Knetus56/solax_local`
5. Chercher "SolaX Local"
6. Cliquer **Installer**
7. Redémarrer Home Assistant

### Installation manuelle

1. Télécharger la dernière [version](https://github.com/Knetus56/solax_local/releases)
2. Extraire dans `custom_components/solax_local/`
3. Redémarrer Home Assistant

## ⚙️ Configuration

### Via interface Home Assistant

1. **Paramètres** > **Appareils et services** > **Intégrations**
2. Cliquer **Créer une intégration**
3. Chercher et sélectionner **SolaX Local**
4. Remplir les informations :
   - **IP** : Adresse IP de l'onduleur (ex: `192.168.1.100`)
   - **Type d'onduleur** : Sélectionner le modèle
   - **Numéro de série** : Numéro de série de l'onduleur
   - **Intervalle de scan** (optionnel) : Fréquence de mise à jour en secondes (défaut: 300s)

> Le numéro de série est automatiquement normalisé en majuscules.

### Modifier la configuration après installation

Il n'est plus nécessaire de supprimer/recréer l'intégration pour changer l'adresse IP ou l'intervalle de scan :

1. **Paramètres** > **Appareils et services**
2. Repérer la carte **SolaX Local** > cliquer **Configurer** (icône ⚙️)
3. Mettre à jour l'**hôte** et/ou l'**intervalle de scan**
4. Valider — l'intégration se recharge automatiquement avec les nouvelles valeurs

Le type d'onduleur et le numéro de série restent fixes après la création (ils identifient l'appareil) ; pour les changer, il faut recréer l'intégration.

## 🔧 Configuration avancée

### Intervalle de mise à jour

Par défaut, l'intégration interroge l'onduleur toutes les **300 secondes** (5 minutes). Vous pouvez l'ajuster lors de la configuration.

### Entités DIAGNOSTIC

Les entités suivantes sont masquées par défaut (onglet Avancé) :
- État du mode
- Adresse IP
- Numéro de série
- Dernière mise à jour

Pour les afficher : **Paramètres** > **Appareils et services** > Sélectionner le device > **Afficher les entités masquées**


### Les capteurs affichent "Inconnu"

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

- **v1.3.1** (2026-08-28) - Correction du schéma de traduction des noms d'entités (structure imbriquée `{"name": ...}` requise par HA — les noms ne se résolvaient pas sans ça) ; renommage MPPT 1/MPPT 2 → MPPT1/MPPT2
- **v1.3.0** (2026-08-28) - Flow d'options (modifier IP/intervalle de scan sans recréer l'intégration), numéro de série normalisé en majuscules, traductions d'entités correctement câblées (noms adaptés à la langue de HA), correction des messages d'erreur du formulaire de configuration, migration réseau vers `aiohttp` (session partagée HA au lieu de threads bloquants), nettoyage interne (dédoublonnage `device_info`, suppression de code mort)
- **v1.3.2** (2026-08-28) - Capteur `mode` passé en type énuméré (`sensor.enum`) : seules `WaitMode`/`CheckMode`/`NormalMode` sont des valeurs valides, traduites en FR/EN ; il repasse à "Inconnu" à chaque erreur de requête (reflète uniquement le dernier poll réussi, plus de valeur inventée type "Offline"). `prod_auj`/`prod_total` gardent leur dernière valeur connue en cas d'erreur de requête au lieu de retomber à 0 (évite de fausser les statistiques long terme)
- **v1.2.2** (2026-07-22) - Ajout de l'icône personnalisée pour HACS
- **v1.2.1** (2026-07-22) - Ajout du service refresh_all pour actualiser tous les onduleurs
- **v1.2.0** (2026-07-22) - Ajout des capteurs tension/courant MPPT et métriques onduleur
- **v1.1.0** (2026-07-22) - Fix clés MPPT et initialisation du modèle


## 🙏 Remerciements

- https://github.com/CurlyMoo grace a son reverse ici : https://github.com/squishykid/solax/issues/191
