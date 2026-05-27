# Google Threat Intelligence (GTI) API — Documentación Completa

> **Fuente:** https://gtidocs.virustotal.com/reference/api-overview  
> **Total de páginas:** 752  
> **Categorías:** 17  
> **Generado:** 2026-03-26

---

## 📊 Resumen por Categoría

| # | Categoría | Total | Endpoints |
|---|-----------|-------|-----------|
| 1 | [API Introduction](#api-introduction) | 9 | 0 |
| 2 | [Global Landscape](#global-landscape) | 51 | 33 |
| 3 | [IoC Investigation](#ioc-investigation) | 102 | 76 |
| 4 | [YARA Hunting](#yara-hunting) | 33 | 29 |
| 5 | [Reports & Analysis](#reports-and-analysis) | 16 | 15 |
| 6 | [Private Scanning](#private-scanning) | 35 | 30 |
| 7 | [Vulnerability Intelligence](#vulnerability-intelligence) | 15 | 14 |
| 8 | [ASM (ATTACK SURFACE MANAGEMENT)](#asm--attack-surface-management) | 63 | 50 |
| 9 | [DTM (DIGITAL THREAT MONITORING)](#dtm--digital-threat-monitoring) | 49 | 41 |
| 10 | [Threat Graph](#threat-graph) | 19 | 17 |
| 11 | [Users and group management](#users-and-group-management) | 31 | 24 |
| 12 | [IoC Feeds](#ioc-feeds) | 20 | 15 |
| 13 | [Categorised Threat Lists](#categorised-threat-lists) | 5 | 4 |
| 14 | [Dashboards](#dashboards) | 2 | 0 |
| 15 | [GTI Alerts](#gti-alerts) | 34 | 0 |
| 16 | [API OBJECTS](#api-objects) | 265 | 0 |
| 17 | [Widget](#widget) | 3 | 1 |

---

## 📋 Tabla de Contenidos

1. [API Introduction](#api-introduction) (9 páginas)
2. [Global Landscape](#global-landscape) (51 páginas)
3. [IoC Investigation](#ioc-investigation) (102 páginas)
4. [YARA Hunting](#yara-hunting) (33 páginas)
5. [Reports & Analysis](#reports-and-analysis) (16 páginas)
6. [Private Scanning](#private-scanning) (35 páginas)
7. [Vulnerability Intelligence](#vulnerability-intelligence) (15 páginas)
8. [ASM (ATTACK SURFACE MANAGEMENT)](#asm-attack-surface-management) (63 páginas)
9. [DTM (DIGITAL THREAT MONITORING)](#dtm-digital-threat-monitoring) (49 páginas)
10. [Threat Graph](#threat-graph) (19 páginas)
11. [Users and group management](#users-and-group-management) (31 páginas)
12. [IoC Feeds](#ioc-feeds) (20 páginas)
13. [Categorised Threat Lists](#categorised-threat-lists) (5 páginas)
14. [Dashboards](#dashboards) (2 páginas)
15. [GTI Alerts](#gti-alerts) (34 páginas)
16. [API OBJECTS](#api-objects) (265 páginas)
17. [Widget](#widget) (3 páginas)

---


## API Introduction

*9 páginas · 0 endpoints*


### 📄 [Google Threat Intelligence API Overview](https://gtidocs.virustotal.com/reference/api-overview)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/api-overview)

---

### 📄 [API responses](https://gtidocs.virustotal.com/reference/api-responses)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/api-responses)

---

### 📄 [Key concepts](https://gtidocs.virustotal.com/reference/introduction-key-concepts)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/introduction-key-concepts)

---

### 📄 [Objects](https://gtidocs.virustotal.com/reference/introduction-objects)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/introduction-objects)

---

### 📄 [Errors](https://gtidocs.virustotal.com/reference/introduction-errors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/introduction-errors)

---

### 📄 [Relationships](https://gtidocs.virustotal.com/reference/introduction-relationships)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/introduction-relationships)

---

### 📄 [Collections](https://gtidocs.virustotal.com/reference/introduction-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/introduction-collections)

---

### 📄 [OpenAPI Specifications](https://gtidocs.virustotal.com/reference/openapi-specs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/openapi-specs)

---

### 📄 [STIX responses](https://gtidocs.virustotal.com/reference/stix-responses)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/stix-responses)

---

## Global Landscape

*51 páginas · 33 endpoints*


### 📄 [Threat Actors, Malware & Tools, Campaigns, IoC Collections](https://gtidocs.virustotal.com/reference/threat-actors-malware-tools-campaigns-ioc-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/threat-actors-malware-tools-campaigns-ioc-collections)

---

### 📄 [List collections](https://gtidocs.virustotal.com/reference/list-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-collections)

---

### 🔵 [Create a new IoC collection](https://gtidocs.virustotal.com/reference/create-ioc-collection)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-ioc-collection)

---

### 📄 [Get a collection](https://gtidocs.virustotal.com/reference/get-collection)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-collection)

---

### 🔴 [Delete an IoC collection](https://gtidocs.virustotal.com/reference/delete-ioc-collection)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-ioc-collection)

---

### 🟠 [Update an IoC collection](https://gtidocs.virustotal.com/reference/update-ioc-collection)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/update-ioc-collection)

---

### 🟢 [Get Hunting rulesets associated with an IoC Collection](https://gtidocs.virustotal.com/reference/get-related-hunting-rulesets)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-related-hunting-rulesets)

---

### 🔴 [Delete Hunting rulesets association from IoC collection](https://gtidocs.virustotal.com/reference/delete-hunting-rulesets-relationship)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-hunting-rulesets-relationship)

---

### 🔵 [Add Hunting rulesets association to an IoC Collection](https://gtidocs.virustotal.com/reference/add-hunting-rulesets-relationship)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/add-hunting-rulesets-relationship)

---

### 🟢 [Get object descriptors related to a threat](https://gtidocs.virustotal.com/reference/get-threat-related-descriptors)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-related-descriptors)

---

### 🔴 [Delete items from an IoC collection](https://gtidocs.virustotal.com/reference/delete-element-from-ioc-collection)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-element-from-ioc-collection)

---

### 🔵 [Add new items to an IoC collection](https://gtidocs.virustotal.com/reference/add-element-to-ioc-collection)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/add-element-to-ioc-collection)

---

### 🟢 [Get objects related to a threat](https://gtidocs.virustotal.com/reference/get-threat-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-relationships)

---

### 📄 [Get comments from a collection](https://gtidocs.virustotal.com/reference/get-collection-comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-collection-comments)

---

### 📄 [Add a comment to a collection](https://gtidocs.virustotal.com/reference/create-collection-comment)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-collection-comment)

---

### 🟢 [Get MITRE tactics and techniques associated with a threat](https://gtidocs.virustotal.com/reference/get-threat-mitre-tree)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-mitre-tree)

---

### 🟢 [Search IoCs inside a threat](https://gtidocs.virustotal.com/reference/search-iocs-inside-a-threat)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/search-iocs-inside-a-threat)

---

### 🟢 [Get a Threat's observed actions list](https://gtidocs.virustotal.com/reference/get-threat-timeline-events)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-timeline-events)

---

### 🟢 [Export IOCs from a threat](https://gtidocs.virustotal.com/reference/export-threat-iocs)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/export-threat-iocs)

---

### 🟢 [Export aggregations / commonalities from a threat](https://gtidocs.virustotal.com/reference/export-threat-aggregations)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/export-threat-aggregations)

---

### 🟢 [Export IOCs from a given threat's relationship](https://gtidocs.virustotal.com/reference/export-iocs-threat-relationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/export-iocs-threat-relationship)

---

### 🔵 [Subscribe to a threat object](https://gtidocs.virustotal.com/reference/create-threat-subscription-preferences)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-threat-subscription-preferences)

---

### 🟢 [Check subscription preferences from threat object](https://gtidocs.virustotal.com/reference/get-threat-subscription-preferences)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-subscription-preferences)

---

### 🔴 [Delete subscription from a threat object](https://gtidocs.virustotal.com/reference/delete-threat-subscription-preferences)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-threat-subscription-preferences)

---

### 📄 [Threat Profiles](https://gtidocs.virustotal.com/reference/threat-profiles)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/threat-profiles)

---

### 🟢 [List Threat Profiles](https://gtidocs.virustotal.com/reference/list-threat-profiles)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-threat-profiles)

---

### 🔵 [Create a Threat Profile](https://gtidocs.virustotal.com/reference/create-threat-profile)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-threat-profile)

---

### 🟢 [Get a Threat Profile](https://gtidocs.virustotal.com/reference/get-threat-profile)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-profile)

---

### 🟠 [Update a Threat Profiles](https://gtidocs.virustotal.com/reference/update-threat-profile)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/update-threat-profile)

---

### 🔴 [Delete a Threat Profile](https://gtidocs.virustotal.com/reference/delete-threat-profile)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-threat-profile)

---

### 🟢 [Get recommendations of a Threat Profile](https://gtidocs.virustotal.com/reference/get-threat-profile-recommendations)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-profile-recommendations)

---

### 🟢 [Get a Threat Profile's recommendations descriptors](https://gtidocs.virustotal.com/reference/get-threat-profile-recommendations-descriptors)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-profile-recommendations-descriptors)

---

### 🔴 [Delete objects from a Threat Profile](https://gtidocs.virustotal.com/reference/delete-threat-profile-recommendations)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-threat-profile-recommendations)

---

### 🔵 [Add objects to a Threat Profile](https://gtidocs.virustotal.com/reference/add-threat-profile-recommendations)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/add-threat-profile-recommendations)

---

### 🟢 [Get objects related to a Threat Profile](https://gtidocs.virustotal.com/reference/get-threat-profile-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-profile-relationships)

---

### 🟢 [Get object descriptors related to a Threat Profile](https://gtidocs.virustotal.com/reference/get-threat-profile-related-descriptors)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-profile-related-descriptors)

---

### 🔴 [Delete items from a Threat Profile](https://gtidocs.virustotal.com/reference/delete-threat-profile-relationships)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-threat-profile-relationships)

---

### 🔵 [Add or update relationships between a Threat Profile and other objects](https://gtidocs.virustotal.com/reference/add-threat-profile-relationships)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/add-threat-profile-relationships)

---

### 🟢 [Get a Threat Profile's timeline associations](https://gtidocs.virustotal.com/reference/get-threat-profile-timeline-associations)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-threat-profile-timeline-associations)

---

### 📄 [Dark Web](https://gtidocs.virustotal.com/reference/dark-web)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dark-web)

---

### 📄 [List Dark Web Communications](https://gtidocs.virustotal.com/reference/list-ddw-communications)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-ddw-communications)

---

### 📄 [Get a Dark Web Communication object](https://gtidocs.virustotal.com/reference/get-ddw-communication)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-communication)

---

### 📄 [Get objects related to a Dark Web Communication object](https://gtidocs.virustotal.com/reference/get-ddw-communication-relationships)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-communication-relationships)

---

### 📄 [Get a Dark Web Communication Channel object](https://gtidocs.virustotal.com/reference/get-ddw-communication-channel)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-communication-channel)

---

### 📄 [Get Next Communication in a Channel](https://gtidocs.virustotal.com/reference/get-ddw-channel-next-communications)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-channel-next-communications)

---

### 📄 [Get Previous Communication in a Channel](https://gtidocs.virustotal.com/reference/get-ddw-channel-previous-communications)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-channel-previous-communications)

---

### 📄 [Get a Dark Web User Profile](https://gtidocs.virustotal.com/reference/get-ddw-user-profile)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-user-profile)

---

### 📄 [Get a Dark Web Service object](https://gtidocs.virustotal.com/reference/get-ddw-service)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-service)

---

### 📄 [Get objects related to a Dark Web Service object](https://gtidocs.virustotal.com/reference/get-ddw-service-relationships)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-service-relationships)

---

### 📄 [Get Next Communication in a Thread](https://gtidocs.virustotal.com/reference/get-ddw-thread-next-communications)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-thread-next-communications)

---

### 📄 [Get Previous Communication in a Thread](https://gtidocs.virustotal.com/reference/get-ddw-thread-previous-communications)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ddw-thread-previous-communications)

---

## IoC Investigation

*102 páginas · 76 endpoints*


### 📄 [IP addresses](https://gtidocs.virustotal.com/reference/ip-addresses)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-addresses)

---

### 🟢 [Get an IP address report](https://gtidocs.virustotal.com/reference/ip-info)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-info)

---

### 🟢 [Get comments on an IP address](https://gtidocs.virustotal.com/reference/ip-comments-get)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-comments-get)

---

### 🔵 [Request an IP address rescan (re-analyse)](https://gtidocs.virustotal.com/reference/ip-analyse)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-analyse)

---

### 🔵 [Add a comment to an IP address](https://gtidocs.virustotal.com/reference/ip-comments-post)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-comments-post)

---

### 🟢 [Get object descriptors related to an IP address](https://gtidocs.virustotal.com/reference/ip-relationships-ids)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-relationships-ids)

---

### 🟢 [Get votes on an IP address](https://gtidocs.virustotal.com/reference/ip-votes)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-votes)

---

### 🔵 [Add a vote to an IP address](https://gtidocs.virustotal.com/reference/ip-votes-post)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-votes-post)

---

### 🟢 [Get objects related to an IP address](https://gtidocs.virustotal.com/reference/ip-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-relationships)

---

### 📄 [Domains & Resolutions](https://gtidocs.virustotal.com/reference/domains-resolutions)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-resolutions)

---

### 🟢 [Get a domain report](https://gtidocs.virustotal.com/reference/domain-info)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-info)

---

### 🟢 [Get comments on a domain](https://gtidocs.virustotal.com/reference/domains-comments-get)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-comments-get)

---

### 🔵 [Request an domain rescan](https://gtidocs.virustotal.com/reference/domains-rescan)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-rescan)

---

### 🔵 [Add a comment to a domain](https://gtidocs.virustotal.com/reference/domains-comments-post)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-comments-post)

---

### 🟢 [Get object descriptors related to a domain](https://gtidocs.virustotal.com/reference/domains-relationships-ids)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-relationships-ids)

---

### 🟢 [Get votes on a domain](https://gtidocs.virustotal.com/reference/domains-votes-get)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-votes-get)

---

### 🔵 [Add a vote to a domain](https://gtidocs.virustotal.com/reference/domain-votes-post)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-votes-post)

---

### 🟢 [Get objects related to a domain](https://gtidocs.virustotal.com/reference/domains-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-relationships)

---

### 🟢 [Get a DNS resolution object](https://gtidocs.virustotal.com/reference/get-resolution-by-id)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-resolution-by-id)

---

### 📄 [Files](https://gtidocs.virustotal.com/reference/files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files)

---

### 🟢 [Get a URL for uploading large files](https://gtidocs.virustotal.com/reference/files-upload-url)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-upload-url)

---

### 🔵 [Upload a file](https://gtidocs.virustotal.com/reference/files-scan)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-scan)

---

### 🟢 [Get a file report](https://gtidocs.virustotal.com/reference/file-info)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-info)

---

### 🔵 [Request a file rescan (re-analyse)](https://gtidocs.virustotal.com/reference/files-analyse)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-analyse)

---

### 🟢 [Get comments on a file](https://gtidocs.virustotal.com/reference/files-comments-get)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-comments-get)

---

### 🔵 [Add a comment to a file](https://gtidocs.virustotal.com/reference/files-comments-post)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-comments-post)

---

### 🟢 [Download a file](https://gtidocs.virustotal.com/reference/files-download)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-download)

---

### 🟢 [Get a file’s download URL](https://gtidocs.virustotal.com/reference/files-download-url)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-download-url)

---

### 🟢 [Get object descriptors related to a file](https://gtidocs.virustotal.com/reference/files-relationships-ids)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-relationships-ids)

---

### 🟢 [Get votes on a file](https://gtidocs.virustotal.com/reference/files-votes-get)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-votes-get)

---

### 🔵 [Add a vote on a file](https://gtidocs.virustotal.com/reference/files-votes-post)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-votes-post)

---

### 🟢 [Get objects related to a file](https://gtidocs.virustotal.com/reference/files-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-relationships)

---

### 🟢 [Get a crowdsourced Sigma rule object](https://gtidocs.virustotal.com/reference/get-sigma-rules)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-sigma-rules)

---

### 🟢 [Get a crowdsourced YARA ruleset](https://gtidocs.virustotal.com/reference/get-yara-rulesets)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-yara-rulesets)

---

### 📄 [Files Behaviours](https://gtidocs.virustotal.com/reference/files-behaviours)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-behaviours)

---

### 🟢 [Get a file behavior report from a sandbox](https://gtidocs.virustotal.com/reference/get-file-behaviour-id)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-file-behaviour-id)

---

### 🟢 [Get the EVTX file generated during a file’s behavior analysis](https://gtidocs.virustotal.com/reference/file-behaviour-evtx)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-evtx)

---

### 🟢 [Get a detailed HTML behaviour report](https://gtidocs.virustotal.com/reference/get-file-behaviour-html)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-file-behaviour-html)

---

### 🟢 [Get the memdump file generated during a file’s behavior analysis](https://gtidocs.virustotal.com/reference/file-behaviour-memdump)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-memdump)

---

### 🟢 [Get the PCAP file generated during a file’s behavior analysis](https://gtidocs.virustotal.com/reference/file_behaviours_pcap)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file_behaviours_pcap)

---

### 🟢 [Get object descriptors related to a behaviour report](https://gtidocs.virustotal.com/reference/file_behaviourssandbox_idrelationshipsrelationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file_behaviourssandbox_idrelationshipsrelationship)

---

### 🟢 [Get objects related to a behaviour report](https://gtidocs.virustotal.com/reference/file_behaviourssandbox_idrelationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file_behaviourssandbox_idrelationship)

---

### 🟢 [Get a summary of all MITRE ATT&CK techniques observed in a file](https://gtidocs.virustotal.com/reference/get-a-summary-of-all-mitre-attck-techniques-observed-in-a-file)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-a-summary-of-all-mitre-attck-techniques-observed-in-a-file)

---

### 🟢 [Get a summary of all behavior reports for a file](https://gtidocs.virustotal.com/reference/file-all-behaviours-summary)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-all-behaviours-summary)

---

### 🟢 [Get all behavior reports for a file](https://gtidocs.virustotal.com/reference/get-all-behavior-reports-for-a-file)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-all-behavior-reports-for-a-file)

---

### 📄 [URLs](https://gtidocs.virustotal.com/reference/urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls)

---

### 🔵 [Scan URL](https://gtidocs.virustotal.com/reference/scan-url)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/scan-url)

---

### 🟢 [Get a URL report](https://gtidocs.virustotal.com/reference/url-info)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-info)

---

### 🔵 [Request a URL rescan (re-analyse)](https://gtidocs.virustotal.com/reference/urls-analyse)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-analyse)

---

### 🟢 [Get comments on a URL](https://gtidocs.virustotal.com/reference/urls-comments-get)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-comments-get)

---

### 🔵 [Add a comment on a URL](https://gtidocs.virustotal.com/reference/urls-comments-post)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-comments-post)

---

### 🟢 [Get object descriptors related to a URL](https://gtidocs.virustotal.com/reference/urls-relationships-ids)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-relationships-ids)

---

### 🟢 [Get votes on a URL](https://gtidocs.virustotal.com/reference/urls-votes-get)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-votes-get)

---

### 🔵 [Add a vote on a URL](https://gtidocs.virustotal.com/reference/urls-votes-post)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-votes-post)

---

### 🟢 [Get objects related to a URL](https://gtidocs.virustotal.com/reference/urls-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-relationships)

---

### 📄 [Comments](https://gtidocs.virustotal.com/reference/comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/comments)

---

### 🟢 [Get latest comments](https://gtidocs.virustotal.com/reference/get-comments)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-comments)

---

### 🔴 [Delete a comment](https://gtidocs.virustotal.com/reference/comment-id-delete)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/comment-id-delete)

---

### 🟢 [Get a comment object](https://gtidocs.virustotal.com/reference/get-comment)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-comment)

---

### 🟢 [Get object descriptors related to a comment](https://gtidocs.virustotal.com/reference/comments-relationships-ids)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/comments-relationships-ids)

---

### 🔵 [Add a vote to a comment](https://gtidocs.virustotal.com/reference/vote-comment)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/vote-comment)

---

### 🟢 [Get objects related to a comment](https://gtidocs.virustotal.com/reference/comments-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/comments-relationships)

---

### 📄 [Analyses, Submissions & Operations](https://gtidocs.virustotal.com/reference/analyses-submissions-operations)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/analyses-submissions-operations)

---

### 🟢 [Get a URL / file analysis](https://gtidocs.virustotal.com/reference/analysis)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/analysis)

---

### 🟢 [Get object descriptors related to an analysis](https://gtidocs.virustotal.com/reference/analyses-get-descriptors)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/analyses-get-descriptors)

---

### 🟢 [Get objects related to an analysis](https://gtidocs.virustotal.com/reference/analyses-get-objects)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/analyses-get-objects)

---

### 🟢 [Get a submission object](https://gtidocs.virustotal.com/reference/get-submission)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-submission)

---

### 🟢 [Get an operation object](https://gtidocs.virustotal.com/reference/get-operations-id)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-operations-id)

---

### 📄 [Attack Tactics](https://gtidocs.virustotal.com/reference/attack-tactics)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack-tactics)

---

### 🟢 [Get an attack tactic object](https://gtidocs.virustotal.com/reference/attack_tacticsid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack_tacticsid)

---

### 🟢 [Get object descriptors related to an attack tactic](https://gtidocs.virustotal.com/reference/attack_tacticsidrelationshipsrelationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack_tacticsidrelationshipsrelationship)

---

### 🟢 [Get objects related to an attack tactic](https://gtidocs.virustotal.com/reference/attack_tacticsidrelationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack_tacticsidrelationship)

---

### 📄 [Attack Techniques](https://gtidocs.virustotal.com/reference/attack-techniques)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack-techniques)

---

### 🟢 [Get an attack technique object](https://gtidocs.virustotal.com/reference/attack_techniqueid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack_techniqueid)

---

### 🟢 [Get object descriptors related to an attack technique](https://gtidocs.virustotal.com/reference/attack_techniquesidrelationshipsrelationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack_techniquesidrelationshipsrelationship)

---

### 🟢 [Get objects related to an attack technique](https://gtidocs.virustotal.com/reference/attack_techniqueidrelationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack_techniqueidrelationship)

---

### 📄 [Popular Threat Categories](https://gtidocs.virustotal.com/reference/popular-threat-categories)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/popular-threat-categories)

---

### 🟢 [Get a list of popular threat categories](https://gtidocs.virustotal.com/reference/popular_threat_categories)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/popular_threat_categories)

---

### 📄 [Zipping files](https://gtidocs.virustotal.com/reference/zipping-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/zipping-files)

---

### 🔵 [Create a password-protected ZIP with Google Threat Intelligence files](https://gtidocs.virustotal.com/reference/zip_files)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/zip_files)

---

### 🟢 [Check a ZIP file’s status](https://gtidocs.virustotal.com/reference/get-zip-file)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-zip-file)

---

### 🟢 [Download a ZIP file](https://gtidocs.virustotal.com/reference/zip-files-download)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/zip-files-download)

---

### 🟢 [Get a ZIP file’s download URL](https://gtidocs.virustotal.com/reference/zip-files-download-url)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/zip-files-download-url)

---

### 📄 [Search & Metadata](https://gtidocs.virustotal.com/reference/search-metadata)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/search-metadata)

---

### 🟢 [Advanced corpus search](https://gtidocs.virustotal.com/reference/intelligence-search)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/intelligence-search)

---

### 🟢 [Get file content search snippets](https://gtidocs.virustotal.com/reference/intelligence-search-snippets)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/intelligence-search-snippets)

---

### 🟢 [Get Google Threat Intel metadata](https://gtidocs.virustotal.com/reference/metadata)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/metadata)

---

### 🟢 [Search for files, URLs, domains, IPs and comments](https://gtidocs.virustotal.com/reference/api-search)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/api-search)

---

### 📄 [Code Insights](https://gtidocs.virustotal.com/reference/code-insights)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/code-insights)

---

### 📄 [Analyse code blocks with Code Insights](https://gtidocs.virustotal.com/reference/analyse-binary)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/analyse-binary)

---

### 📄 [Saved Searches](https://gtidocs.virustotal.com/reference/saved-searches)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/saved-searches)

---

### 📄 [List Saved Searches](https://gtidocs.virustotal.com/reference/list-saved-searches)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-saved-searches)

---

### 📄 [Get a Saved Search](https://gtidocs.virustotal.com/reference/get-saved-searches)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-saved-searches)

---

### 📄 [Create a Saved Search](https://gtidocs.virustotal.com/reference/create-saved-searches)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-saved-searches)

---

### 📄 [Share a Saved Search](https://gtidocs.virustotal.com/reference/share-saved-searches)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/share-saved-searches)

---

### 📄 [Update a Saved Search](https://gtidocs.virustotal.com/reference/update-saved-searches)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/update-saved-searches)

---

### 📄 [Delete a Saved Search](https://gtidocs.virustotal.com/reference/delete-saved-searches)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-saved-searches)

---

### 📄 [Revoke access to a Saved Search](https://gtidocs.virustotal.com/reference/revoke-saved-searches-access)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/revoke-saved-searches-access)

---

### 📄 [Get object descriptors related to a Saved Search](https://gtidocs.virustotal.com/reference/get-saved-searches-related-descriptors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-saved-searches-related-descriptors)

---

### 📄 [Get objects related to a Saved Search](https://gtidocs.virustotal.com/reference/get-saved-searches-relationships)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-saved-searches-relationships)

---

### 📄 [IOC Summary](https://gtidocs.virustotal.com/reference/ioc-summary)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ioc-summary)

---

### 📄 [Retrieve summary for a list of IoCs](https://gtidocs.virustotal.com/reference/get-ioc-summary)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-ioc-summary)

---

## YARA Hunting

*33 páginas · 29 endpoints*


### 📄 [YARA Rules](https://gtidocs.virustotal.com/reference/yara-rules)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/yara-rules)

---

### 🟢 [List Crowdsourced YARA Rules](https://gtidocs.virustotal.com/reference/list-crowdsourced-yara-rules)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-crowdsourced-yara-rules)

---

### 🟢 [Get a Crowdsourced YARA rule](https://gtidocs.virustotal.com/reference/get-a-crowdsourced-yara-rule)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-a-crowdsourced-yara-rule)

---

### 🟢 [Get objects descriptors related to a Crowdsourced YARA rule](https://gtidocs.virustotal.com/reference/crowdsourced-yara-rule-relationship-descriptors-endpoint)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/crowdsourced-yara-rule-relationship-descriptors-endpoint)

---

### 🟢 [Get objects related to a Crowdsourced YARA rule](https://gtidocs.virustotal.com/reference/crowdsourced-yara-rule-relationship-endpoint)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/crowdsourced-yara-rule-relationship-endpoint)

---

### 📄 [IoC Stream](https://gtidocs.virustotal.com/reference/ioc-stream)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ioc-stream)

---

### 🔴 [Delete notifications from the IoC Stream](https://gtidocs.virustotal.com/reference/delete-notifications-from-the-ioc-stream)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-notifications-from-the-ioc-stream)

---

### 🟢 [Get objects from the IoC Stream](https://gtidocs.virustotal.com/reference/get-objects-from-the-ioc-stream)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-objects-from-the-ioc-stream)

---

### 🔴 [Delete an IoC Stream notification](https://gtidocs.virustotal.com/reference/delete-an-ioc-stream-notification)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-an-ioc-stream-notification)

---

### 🟢 [Get an IoC Stream notification](https://gtidocs.virustotal.com/reference/get-an-ioc-stream-notification)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-an-ioc-stream-notification)

---

### 📄 [Livehunt](https://gtidocs.virustotal.com/reference/livehunt)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/livehunt)

---

### 🔴 [Remove all Livehunt rulesets](https://gtidocs.virustotal.com/reference/delete-all-hunting-rulesets)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-all-hunting-rulesets)

---

### 🟢 [Get Livehunt rulesets](https://gtidocs.virustotal.com/reference/list-hunting-rulesets)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-hunting-rulesets)

---

### 🔵 [Create a new Livehunt ruleset](https://gtidocs.virustotal.com/reference/create-hunting-ruleset)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-hunting-ruleset)

---

### 🔴 [Delete a Livehunt ruleset](https://gtidocs.virustotal.com/reference/delete-hunting-ruleset)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-hunting-ruleset)

---

### 🟢 [Get a Livehunt ruleset](https://gtidocs.virustotal.com/reference/get-hunting-ruleset)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-hunting-ruleset)

---

### 🟠 [Update a Livehunt ruleset](https://gtidocs.virustotal.com/reference/modify-hunting-ruleset)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/modify-hunting-ruleset)

---

### 🔴 [Delete IoC Collections association from Hunting ruleset](https://gtidocs.virustotal.com/reference/delete-ioc-collections-relationship)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-ioc-collections-relationship)

---

### 🟢 [Get IoC Collections associated with a Hunting ruleset](https://gtidocs.virustotal.com/reference/get-related-ioc-collections)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-related-ioc-collections)

---

### 🔵 [Add IoC Collectios association to a Hunting ruleset](https://gtidocs.virustotal.com/reference/add-ioc-collections-relationship)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/add-ioc-collections-relationship)

---

### 🔵 [Grant Livehunt ruleset edit permissions for a user or group](https://gtidocs.virustotal.com/reference/edit-hunting-ruleset-relationship)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/edit-hunting-ruleset-relationship)

---

### 🔴 [Revoke Livehunt ruleset edit permission from a user or group](https://gtidocs.virustotal.com/reference/delete-hunting-ruleset-editor)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-hunting-ruleset-editor)

---

### 🟢 [Check if a user or group is a Livehunt ruleset editor](https://gtidocs.virustotal.com/reference/check-user-hunting-ruleset-editor)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/check-user-hunting-ruleset-editor)

---

### 🔵 [Transfer Livehunt ruleset to another user](https://gtidocs.virustotal.com/reference/transfer-livehunt-ruleset-to-another-user)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/transfer-livehunt-ruleset-to-another-user)

---

### 🟢 [Get object descriptors related to a Livehunt ruleset](https://gtidocs.virustotal.com/reference/get-hunting-ruleset-relationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-hunting-ruleset-relationship)

---

### 🟢 [Get objects related to a Livehunt ruleset](https://gtidocs.virustotal.com/reference/get-hunting-ruleset-full-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-hunting-ruleset-full-relationships)

---

### 📄 [Retrohunt](https://gtidocs.virustotal.com/reference/retrohunt)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/retrohunt)

---

### 🟢 [Get a list of Retrohunt jobs](https://gtidocs.virustotal.com/reference/get-retrohunt-jobs)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-retrohunt-jobs)

---

### 🔵 [Create a new Retrohunt job](https://gtidocs.virustotal.com/reference/create-retrohunt-job)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-retrohunt-job)

---

### 🔴 [Delete a Retrohunt job](https://gtidocs.virustotal.com/reference/delete-retrohunt-job)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-retrohunt-job)

---

### 🟢 [Get a Retrohunt job object](https://gtidocs.virustotal.com/reference/get-retrohunt-job)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-retrohunt-job)

---

### 🔵 [Abort a Retrohunt job](https://gtidocs.virustotal.com/reference/abort-retrohunt-job)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/abort-retrohunt-job)

---

### 🟢 [Retrieve matches for a Retrohunt job](https://gtidocs.virustotal.com/reference/get-retrohunt-job-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-retrohunt-job-relationships)

---

## Reports & Analysis

*16 páginas · 15 endpoints*


### 📄 [Reports](https://gtidocs.virustotal.com/reference/reports)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/reports)

---

### 🟢 [List reports](https://gtidocs.virustotal.com/reference/list-reports)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-reports)

---

### 🟢 [Get a report](https://gtidocs.virustotal.com/reference/get-report)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-report)

---

### 🟢 [Get object descriptors related to a report](https://gtidocs.virustotal.com/reference/get-report-related-descriptors)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-report-related-descriptors)

---

### 🟢 [Get objects related to a report](https://gtidocs.virustotal.com/reference/get-report-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-report-relationships)

---

### 🟢 [Get comments from a report](https://gtidocs.virustotal.com/reference/get-report-comments)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-report-comments)

---

### 🔵 [Add a comment to a report](https://gtidocs.virustotal.com/reference/create-report-comment)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-report-comment)

---

### 🟢 [Get MITRE tactics and techniques associated with a report](https://gtidocs.virustotal.com/reference/get-report-mitre-tree)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-report-mitre-tree)

---

### 🟢 [Search IoCs inside a report](https://gtidocs.virustotal.com/reference/search-iocs-inside-a-report)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/search-iocs-inside-a-report)

---

### 🟢 [Export IOCs from a report](https://gtidocs.virustotal.com/reference/export-report-iocs)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/export-report-iocs)

---

### 🟢 [Export aggregations / commonalities from a report](https://gtidocs.virustotal.com/reference/export-report-aggregations)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/export-report-aggregations)

---

### 🟢 [Export IOCs from a given report's relationship](https://gtidocs.virustotal.com/reference/export-iocs-report-relationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/export-iocs-report-relationship)

---

### 🟢 [Download a Report](https://gtidocs.virustotal.com/reference/download-report)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/download-report)

---

### 🔵 [Subscribe to a report](https://gtidocs.virustotal.com/reference/create-report-subscription-preferences)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-report-subscription-preferences)

---

### 🟢 [Check subscription preferences from a report](https://gtidocs.virustotal.com/reference/get-report-subscription-preferences)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-report-subscription-preferences)

---

### 🔴 [Delete subscription from a report](https://gtidocs.virustotal.com/reference/delete-report-subscription-preferences)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-report-subscription-preferences)

---

## Private Scanning

*35 páginas · 30 endpoints*


### 📄 [Private Files](https://gtidocs.virustotal.com/reference/private-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-files)

---

### 🔵 [Upload a file](https://gtidocs.virustotal.com/reference/upload-file-private-scanning)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/upload-file-private-scanning)

---

### 🟢 [List private files](https://gtidocs.virustotal.com/reference/list-private-files)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-private-files)

---

### 🟢 [Get a URL for uploading large files](https://gtidocs.virustotal.com/reference/private-files-upload-url)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-files-upload-url)

---

### 🔴 [Delete a private file report](https://gtidocs.virustotal.com/reference/delete-file-private-scanning)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-file-private-scanning)

---

### 🟢 [Get a private file report](https://gtidocs.virustotal.com/reference/private-files-info)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-files-info)

---

### 🟢 [Get object descriptors related to a file](https://gtidocs.virustotal.com/reference/privatefilesidrelationshipsrelationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/privatefilesidrelationshipsrelationship)

---

### 🟢 [Get objects related to a private file](https://gtidocs.virustotal.com/reference/private-files-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-files-relationships)

---

### 🔵 [Rescan a private file](https://gtidocs.virustotal.com/reference/rescan-a-private-file)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/rescan-a-private-file)

---

### 📄 [Private Files Behaviours](https://gtidocs.virustotal.com/reference/private-files-behaviours)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-files-behaviours)

---

### 🟢 [Get the behaviour reports from a private file](https://gtidocs.virustotal.com/reference/get-all-behaviour-reports-from-a-private-file)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-all-behaviour-reports-from-a-private-file)

---

### 🟢 [Get a behaviour report from a private file](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-id)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-id)

---

### 🟢 [Get the EVTX file generated during a private file’s behavior analysis](https://gtidocs.virustotal.com/reference/file-behaviourssandbox-idevtx)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviourssandbox-idevtx)

---

### 🟢 [Get a detailed HTML behaviour report](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-idhtml)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-idhtml)

---

### 🟢 [Get the memdump file generated during a private file’s behavior analysis](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-idpcap)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-idpcap)

---

### 🟢 [Get the PCAP file generated during a private file’s behavior analysis](https://gtidocs.virustotal.com/reference/file-behaviourssandbox-idmemdump)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviourssandbox-idmemdump)

---

### 🟢 [Get object descriptors related to a private file's behaviour report](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-idrelationshipsrelationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-idrelationshipsrelationship)

---

### 🟢 [Get objects related to a private file's behaviour report](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-idrelationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/privatefile-behaviourssandbox-idrelationship)

---

### 🟢 [Get a summary of all MITRE ATT&CK techniques observed in a file](https://gtidocs.virustotal.com/reference/get-summary-all-mitre-attack-techniques-observed-in-a-file)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-summary-all-mitre-attack-techniques-observed-in-a-file)

---

### 🟢 [Get a summary of all behavior reports for a file](https://gtidocs.virustotal.com/reference/privatefilesidbehaviour-summary)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/privatefilesidbehaviour-summary)

---

### 📄 [Private Analyses](https://gtidocs.virustotal.com/reference/private-analyses)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-analyses)

---

### 🟢 [List private analyses](https://gtidocs.virustotal.com/reference/list-private-analyses)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-private-analyses)

---

### 🟢 [Get a private analysis](https://gtidocs.virustotal.com/reference/private-analysis)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-analysis)

---

### 🟢 [Get object descriptors related to a private analysis](https://gtidocs.virustotal.com/reference/private-analyses-relationships-descriptor)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-analyses-relationships-descriptor)

---

### 🟢 [Get objects related to a private analysis](https://gtidocs.virustotal.com/reference/private-analyses-relationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-analyses-relationship)

---

### 📄 [Private URLs](https://gtidocs.virustotal.com/reference/private-urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-urls)

---

### 🔵 [Private Scan URL](https://gtidocs.virustotal.com/reference/private-scan-url)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-scan-url)

---

### 🟢 [Get a URL analysis report](https://gtidocs.virustotal.com/reference/get-a-private-url-analysis-report)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-a-private-url-analysis-report)

---

### 🟢 [Get objects related to a private URL](https://gtidocs.virustotal.com/reference/private-get-objects-related-to-a-url)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-get-objects-related-to-a-url)

---

### 🟢 [Get object descriptors related to a private URL](https://gtidocs.virustotal.com/reference/private-get-object-descriptors-related-to-a-url)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-get-object-descriptors-related-to-a-url)

---

### 📄 [Private Zipping files](https://gtidocs.virustotal.com/reference/private-zipping-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-zipping-files)

---

### 🔵 [Create a password-protected ZIP with Google Threat Intelligence files](https://gtidocs.virustotal.com/reference/private-scanning-zip-files)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-scanning-zip-files)

---

### 🟢 [Check a ZIP file’s status](https://gtidocs.virustotal.com/reference/private-scanning-get-zip-file)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-scanning-get-zip-file)

---

### 🟢 [Download a ZIP file](https://gtidocs.virustotal.com/reference/private-scanning-download-zip-file)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-scanning-download-zip-file)

---

### 🟢 [Get a ZIP file’s download URL](https://gtidocs.virustotal.com/reference/private-scanning-get-zip-download-url)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-scanning-get-zip-download-url)

---

## Vulnerability Intelligence

*15 páginas · 14 endpoints*


### 📄 [Vulnerabilities](https://gtidocs.virustotal.com/reference/vulnerabilities)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/vulnerabilities)

---

### 🟢 [List vulnerabilities](https://gtidocs.virustotal.com/reference/list-vulnerabilities)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-vulnerabilities)

---

### 🟢 [Get a vulnerability](https://gtidocs.virustotal.com/reference/get-vulnerability)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-vulnerability)

---

### 🟢 [Get object descriptors related to a vulnerability](https://gtidocs.virustotal.com/reference/get-vulnerability-related-descriptors)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-vulnerability-related-descriptors)

---

### 🟢 [Get objects related to a vulnerability](https://gtidocs.virustotal.com/reference/get-vulnerability-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-vulnerability-relationships)

---

### 🟢 [Get comments from a vulnerability](https://gtidocs.virustotal.com/reference/get-vulnerability-comments)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-vulnerability-comments)

---

### 🔵 [Add a comment to a vulnerability](https://gtidocs.virustotal.com/reference/create-vulnerability-comment)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-vulnerability-comment)

---

### 🟢 [Get MITRE tactics and techniques associated with a vulnerability](https://gtidocs.virustotal.com/reference/get-vulnerability-mitre-tree)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-vulnerability-mitre-tree)

---

### 🟢 [Search IoCs inside a vulnerability](https://gtidocs.virustotal.com/reference/search-iocs-inside-a-vulnerability)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/search-iocs-inside-a-vulnerability)

---

### 🟢 [Export IOCs from a vulnerability](https://gtidocs.virustotal.com/reference/export-vulnerability-iocs)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/export-vulnerability-iocs)

---

### 🟢 [Export aggregations / commonalities from a vulnerability](https://gtidocs.virustotal.com/reference/export-vulnerability-aggregations)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/export-vulnerability-aggregations)

---

### 🟢 [Export IOCs from a given vulnerability's relationship](https://gtidocs.virustotal.com/reference/export-iocs-vulnerability-relationship)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/export-iocs-vulnerability-relationship)

---

### 🔵 [Subscribe to a vulnerability](https://gtidocs.virustotal.com/reference/create-vulnerability-subscription-preferences)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-vulnerability-subscription-preferences)

---

### 🟢 [Check subscription preferences from a vulnerability](https://gtidocs.virustotal.com/reference/get-vulnerability-subscription-preferences)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-vulnerability-subscription-preferences)

---

### 🔴 [Delete subscription from a vulnerability](https://gtidocs.virustotal.com/reference/delete-vulnerability-subscription-preferences)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-vulnerability-subscription-preferences)

---

## ASM (ATTACK SURFACE MANAGEMENT)

*63 páginas · 50 endpoints*


### 📄 [Projects](https://gtidocs.virustotal.com/reference/projects)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/projects)

---

### 🟢 [Index](https://gtidocs.virustotal.com/reference/get_projects)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_projects)

---

### 🔵 [Create](https://gtidocs.virustotal.com/reference/post_projects)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post_projects)

---

### 🔴 [Delete](https://gtidocs.virustotal.com/reference/delete_projects-uuid)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete_projects-uuid)

---

### 📄 [ASM Collections](https://gtidocs.virustotal.com/reference/asm-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/asm-collections)

---

### 🟢 [Index](https://gtidocs.virustotal.com/reference/get_user-collections)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_user-collections)

---

### 🔵 [Create](https://gtidocs.virustotal.com/reference/post_user-collections)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post_user-collections)

---

### 🟢 [Read](https://gtidocs.virustotal.com/reference/get_user-collections-uuid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_user-collections-uuid)

---

### 🔴 [Delete](https://gtidocs.virustotal.com/reference/delete_user-collections-uuid)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete_user-collections-uuid)

---

### 🟠 [Archive](https://gtidocs.virustotal.com/reference/patch_user-collections-uuid-archive)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch_user-collections-uuid-archive)

---

### 🟠 [Unarchive](https://gtidocs.virustotal.com/reference/patch_user-collections-uuid-unarchive)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch_user-collections-uuid-unarchive)

---

### 📄 [Collection Runs](https://gtidocs.virustotal.com/reference/collection-runs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/collection-runs)

---

### 🟢 [Index](https://gtidocs.virustotal.com/reference/get_collections-collection-uuid-collection-runs)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_collections-collection-uuid-collection-runs)

---

### 🔵 [Create](https://gtidocs.virustotal.com/reference/post_collections-collection-uuid-collection-runs)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post_collections-collection-uuid-collection-runs)

---

### 📄 [Entities](https://gtidocs.virustotal.com/reference/entities)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/entities)

---

### 🟢 [Search Entities](https://gtidocs.virustotal.com/reference/get_search-entities-search-string)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_search-entities-search-string)

---

### 🟢 [Get Detail](https://gtidocs.virustotal.com/reference/get_entities-entity-uid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_entities-entity-uid)

---

### 🟢 [Get Full Detail](https://gtidocs.virustotal.com/reference/get_entities-entity-uid-raw)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_entities-entity-uid-raw)

---

### 📄 [Issues](https://gtidocs.virustotal.com/reference/issues)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/issues)

---

### 🟢 [Search Issues](https://gtidocs.virustotal.com/reference/get_search-issues-search-string)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_search-issues-search-string)

---

### 🟢 [Get Detail](https://gtidocs.virustotal.com/reference/get_issues-id)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_issues-id)

---

### 🔵 [Set Status](https://gtidocs.virustotal.com/reference/post_issues-id-status)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post_issues-id-status)

---

### 📄 [Time Series](https://gtidocs.virustotal.com/reference/time-series)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/time-series)

---

### 🟢 [Get Entity point in time](https://gtidocs.virustotal.com/reference/get_time-series-point-in-time-entities-uid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_time-series-point-in-time-entities-uid)

---

### 🟢 [Get Entity points in time](https://gtidocs.virustotal.com/reference/get_time-series-points-in-time-entities-uid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_time-series-points-in-time-entities-uid)

---

### 🟢 [Get Issue points in time](https://gtidocs.virustotal.com/reference/get_time-series-points-in-time-issues-uid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_time-series-points-in-time-issues-uid)

---

### 🟢 [Get Issue point in time](https://gtidocs.virustotal.com/reference/get_time-series-point-in-time-issues-uid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_time-series-point-in-time-issues-uid)

---

### 📄 [Technologies](https://gtidocs.virustotal.com/reference/technologies)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/technologies)

---

### 🟢 [Search Technologies](https://gtidocs.virustotal.com/reference/get_search-technologies-search-string)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_search-technologies-search-string)

---

### 📄 [Notes](https://gtidocs.virustotal.com/reference/notes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/notes)

---

### 🟢 [Index](https://gtidocs.virustotal.com/reference/get_notes-item-type-item-uid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_notes-item-type-item-uid)

---

### 🔵 [Create](https://gtidocs.virustotal.com/reference/post_notes-item-type-item-uid)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post_notes-item-type-item-uid)

---

### 🔴 [Delete](https://gtidocs.virustotal.com/reference/delete_notes-item-type-item-uid-note-uid)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete_notes-item-type-item-uid-note-uid)

---

### 📄 [Tags](https://gtidocs.virustotal.com/reference/tags)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/tags)

---

### 🟢 [Index](https://gtidocs.virustotal.com/reference/get_tags-item-type-item-uid)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_tags-item-type-item-uid)

---

### 🔵 [Create](https://gtidocs.virustotal.com/reference/post_tags-item-type-item-uid)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post_tags-item-type-item-uid)

---

### 🔴 [Delete](https://gtidocs.virustotal.com/reference/delete_tags-item-type-item-uid-tag-name)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete_tags-item-type-item-uid-tag-name)

---

### 📄 [Seeds](https://gtidocs.virustotal.com/reference/seeds)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/seeds)

---

### 🟢 [Index](https://gtidocs.virustotal.com/reference/get_user-collections-collection-uuid-user-entities)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_user-collections-collection-uuid-user-entities)

---

### 🔵 [Create](https://gtidocs.virustotal.com/reference/post_user-collections-collection-uuid-user-entities)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post_user-collections-collection-uuid-user-entities)

---

### 🔴 [Delete](https://gtidocs.virustotal.com/reference/delete_entities-entity-id)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete_entities-entity-id)

---

### 📄 [ASM Integrations](https://gtidocs.virustotal.com/reference/asm-integrations)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/asm-integrations)

---

### 🔵 [Create](https://gtidocs.virustotal.com/reference/post_projects-uuid-integrations)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post_projects-uuid-integrations)

---

### 🟢 [Index](https://gtidocs.virustotal.com/reference/get_projects-uuid-integrations)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_projects-uuid-integrations)

---

### 🟢 [Jira projects](https://gtidocs.virustotal.com/reference/get_projects-uuid-integrations-jira-projects)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_projects-uuid-integrations-jira-projects)

---

### 🔴 [Destroy](https://gtidocs.virustotal.com/reference/delete_integrations-uuid)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete_integrations-uuid)

---

### 📄 [Integration Collections](https://gtidocs.virustotal.com/reference/integration-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/integration-collections)

---

### 🟢 [Index](https://gtidocs.virustotal.com/reference/get_integration-collections)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_integration-collections)

---

### 🔴 [Destroy](https://gtidocs.virustotal.com/reference/delete_integration-collections-uuid)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete_integration-collections-uuid)

---

### 🔵 [Create](https://gtidocs.virustotal.com/reference/post_user-collections-collection-uuid-integration-collections)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post_user-collections-collection-uuid-integration-collections)

---

### 📄 [Library](https://gtidocs.virustotal.com/reference/library)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/library)

---

### 🟢 [Entities List](https://gtidocs.virustotal.com/reference/get_library-entities)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-entities)

---

### 🟢 [Entities Stats](https://gtidocs.virustotal.com/reference/get_library-entities-stats)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-entities-stats)

---

### 🟢 [Issues List](https://gtidocs.virustotal.com/reference/get_library-issues)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-issues)

---

### 🟢 [Issues List - Specific Isssue](https://gtidocs.virustotal.com/reference/get_library-issues-issue-name)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-issues-issue-name)

---

### 🟢 [Issues Stats](https://gtidocs.virustotal.com/reference/get_library-issues-stats)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-issues-stats)

---

### 🟢 [Tasks List](https://gtidocs.virustotal.com/reference/get_library-tasks)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-tasks)

---

### 🟢 [Tasks Stats](https://gtidocs.virustotal.com/reference/get_library-tasks-stats)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-tasks-stats)

---

### 🟢 [Fingerprints List](https://gtidocs.virustotal.com/reference/get_library-fingerprints)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-fingerprints)

---

### 🟢 [Fingerprint Stats](https://gtidocs.virustotal.com/reference/get_library-fingerprints-stats)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-fingerprints-stats)

---

### 🟢 [Issues List - Export as CSV](https://gtidocs.virustotal.com/reference/get_library-issues-export-csv)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-issues-export-csv)

---

### 🟢 [Tasks List - Export as CSV](https://gtidocs.virustotal.com/reference/get_library-tasks-export-csv)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-tasks-export-csv)

---

### 🟢 [Catalog Stats](https://gtidocs.virustotal.com/reference/get_library-catalog-stats)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get_library-catalog-stats)

---

## DTM (DIGITAL THREAT MONITORING)

*49 páginas · 41 endpoints*


### 📄 [DTM Pagination](https://gtidocs.virustotal.com/reference/dtm-pagination)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dtm-pagination)

---

### 📄 [DTM Alerts](https://gtidocs.virustotal.com/reference/dtm-alerts)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dtm-alerts)

---

### 🟢 [List alerts](https://gtidocs.virustotal.com/reference/get-alerts)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-alerts)

---

### 🟢 [Get an existing alert by its ID](https://gtidocs.virustotal.com/reference/get-alerts-id)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-alerts-id)

---

### 🟠 [Update field(s) of an alert](https://gtidocs.virustotal.com/reference/patch-alerts-id)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch-alerts-id)

---

### 🟢 [List child alerts for a given aggregated alert bucket](https://gtidocs.virustotal.com/reference/get-agg-child-alerts)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-agg-child-alerts)

---

### 🔵 [Synchronously bulk update alerts](https://gtidocs.virustotal.com/reference/post-alerts-bulk)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-alerts-bulk)

---

### 🔵 [Asynchronously bulk update alerts using query params to target the alerts](https://gtidocs.virustotal.com/reference/post-alerts-bulk-apply)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-alerts-bulk-apply)

---

### 📄 [Alert Analysis](https://gtidocs.virustotal.com/reference/alert-analysis)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/alert-analysis)

---

### 🟡 [Update the analysis text on an alert](https://gtidocs.virustotal.com/reference/put-alert-analysis)

**Método:** `PUT`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/put-alert-analysis)

---

### 🟢 [List the file attachments for the alert](https://gtidocs.virustotal.com/reference/get-alert-analysis-attachments)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-alert-analysis-attachments)

---

### 🔵 [Upload attachments to an alert's analysis](https://gtidocs.virustotal.com/reference/post-alert-analysis-attachment)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-alert-analysis-attachment)

---

### 🔴 [Delete a file attachment from an alert](https://gtidocs.virustotal.com/reference/delete-alert-attachment)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-alert-attachment)

---

### 🟢 [Download a file attachment from an alert](https://gtidocs.virustotal.com/reference/download-alert-analysis-attachment)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/download-alert-analysis-attachment)

---

### 📄 [Alert Audit](https://gtidocs.virustotal.com/reference/alert-audit)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/alert-audit)

---

### 🟢 [List audit records for a given alert](https://gtidocs.virustotal.com/reference/get-alert-audit)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-alert-audit)

---

### 🟢 [List alert audit records](https://gtidocs.virustotal.com/reference/get-all-alert-audit)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-all-alert-audit)

---

### 📄 [Monitors](https://gtidocs.virustotal.com/reference/monitors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/monitors)

---

### 🟢 [List monitors](https://gtidocs.virustotal.com/reference/get-monitors)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-monitors)

---

### 🔵 [Create a new monitor](https://gtidocs.virustotal.com/reference/post-monitor)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-monitor)

---

### 🔴 [Delete an existing monitor](https://gtidocs.virustotal.com/reference/delete-monitor-id)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-monitor-id)

---

### 🟢 [Get a monitor by its ID](https://gtidocs.virustotal.com/reference/get-monitor-id)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-monitor-id)

---

### 🟠 [Partial update an existing monitor](https://gtidocs.virustotal.com/reference/patch-monitor-id)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch-monitor-id)

---

### 🟡 [Update an existing monitor](https://gtidocs.virustotal.com/reference/put-monitor-id)

**Método:** `PUT`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/put-monitor-id)

---

### 🟠 [Asynchronously backfill alerts for new domains](https://gtidocs.virustotal.com/reference/patch-monitor-backfill)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch-monitor-backfill)

---

### 🔵 [Asynchronously backfill alerts for the monitor](https://gtidocs.virustotal.com/reference/post-monitor-backfill)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-monitor-backfill)

---

### 🟠 [Estimate how many alerts will be created for the backfill of an updated monitor](https://gtidocs.virustotal.com/reference/patch-monitor-backfill-estimate)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch-monitor-backfill-estimate)

---

### 🔵 [Estimate how many alerts will be created for the backfill of a newly created monitor](https://gtidocs.virustotal.com/reference/post-monitor-backfill-estimate)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-monitor-backfill-estimate)

---

### 🟢 [List monitor templates for top DTM use cases](https://gtidocs.virustotal.com/reference/get-monitor-templates)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-monitor-templates)

---

### 📄 [Email Settings](https://gtidocs.virustotal.com/reference/email-settings)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/email-settings)

---

### 🟢 [List email settings](https://gtidocs.virustotal.com/reference/list-settings-email)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-settings-email)

---

### 🔵 [Create email settings](https://gtidocs.virustotal.com/reference/post-settings-email)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-settings-email)

---

### 🔴 [Delete email settings](https://gtidocs.virustotal.com/reference/delete-settings-email-id)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-settings-email-id)

---

### 🟢 [Fetch an email setting](https://gtidocs.virustotal.com/reference/get-settings-email-id)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-settings-email-id)

---

### 🟠 [Update email settings](https://gtidocs.virustotal.com/reference/patch-settings-email-id)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch-settings-email-id)

---

### 🔵 [Reverify one or more email recipients](https://gtidocs.virustotal.com/reference/post-settings-email-id-reverify)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-settings-email-id-reverify)

---

### 📄 [Verified Domains](https://gtidocs.virustotal.com/reference/verified-domains)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/verified-domains)

---

### 🟢 [List verified domains for the current organization](https://gtidocs.virustotal.com/reference/get-verified-domains)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-verified-domains)

---

### 🔵 [Add a new verified domain](https://gtidocs.virustotal.com/reference/post-domain)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-domain)

---

### 🔴 [Delete an existing verified domain.](https://gtidocs.virustotal.com/reference/delete-domain-id)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-domain-id)

---

### 🟢 [Get a verified domain by ID](https://gtidocs.virustotal.com/reference/get-verified-domain)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-verified-domain)

---

### 🔵 [Perform a synchronous verification check for the domain's TXT record code.](https://gtidocs.virustotal.com/reference/reverify-domain-id)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/reverify-domain-id)

---

### 🔵 [Add new verified domains](https://gtidocs.virustotal.com/reference/post-domain-bulk)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-domain-bulk)

---

### 🟢 [Download all verified domains with their TXT verification code in CSV format](https://gtidocs.virustotal.com/reference/get-verified-domains-csv)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-verified-domains-csv)

---

### 📄 [DTM Docs](https://gtidocs.virustotal.com/reference/dtm-docs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dtm-docs)

---

### 🟢 [Retrieve an indexed document by its type and ID](https://gtidocs.virustotal.com/reference/get-docs-type-id)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-docs-type-id)

---

### 🟢 [Fetch the labels for an existing document](https://gtidocs.virustotal.com/reference/get-docs-type-id-labels)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-docs-type-id-labels)

---

### 🟢 [Fetch the topics for an existing document](https://gtidocs.virustotal.com/reference/get-docs-type-id-topics)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-docs-type-id-topics)

---

### 🔵 [Search for documents](https://gtidocs.virustotal.com/reference/post-docs-search)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-docs-search)

---

## Threat Graph

*19 páginas · 17 endpoints*


### 📄 [Threat Graphs](https://gtidocs.virustotal.com/reference/threat-graphs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/threat-graphs)

---

### 🟢 [Search graphs](https://gtidocs.virustotal.com/reference/graphs)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs)

---

### 🔵 [Create a graph](https://gtidocs.virustotal.com/reference/create-graphs)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-graphs)

---

### 🔴 [Delete a graph](https://gtidocs.virustotal.com/reference/graphs-delete)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-delete)

---

### 🟢 [Get a graph object](https://gtidocs.virustotal.com/reference/graphs-info)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-info)

---

### 🟠 [Update a graph object](https://gtidocs.virustotal.com/reference/graphs-update)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-update)

---

### 🟢 [Get comments on a graph](https://gtidocs.virustotal.com/reference/get-graph-comments)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-graph-comments)

---

### 🔵 [Add a comment to a graph](https://gtidocs.virustotal.com/reference/post-graphs-comments)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/post-graphs-comments)

---

### 🟢 [Get object descriptors related to a graph](https://gtidocs.virustotal.com/reference/graphs-relationships-ids)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-relationships-ids)

---

### 🟢 [Get objects related to a graph](https://gtidocs.virustotal.com/reference/graphs-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-relationships)

---

### 📄 [Threat Graphs Permissions & ACL](https://gtidocs.virustotal.com/reference/threat-graphs-permissions-acl)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/threat-graphs-permissions-acl)

---

### 🟢 [Get users and groups that can edit a graph](https://gtidocs.virustotal.com/reference/graphs-editors)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-editors)

---

### 🔵 [Grant users and groups permission to edit a graph](https://gtidocs.virustotal.com/reference/graphs-add-editor)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-add-editor)

---

### 🔴 [Revoke edit graph permissions from a user or group](https://gtidocs.virustotal.com/reference/graphs-delete-editor)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-delete-editor)

---

### 🟢 [Check if a user or group can edit a graph](https://gtidocs.virustotal.com/reference/graphs-check-editor)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-check-editor)

---

### 🔴 [Revoke view permission from a user or group](https://gtidocs.virustotal.com/reference/graphs-delete-viewer)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-delete-viewer)

---

### 🟢 [Check if a user or group can view a graph](https://gtidocs.virustotal.com/reference/graphs-check-viewer)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-check-viewer)

---

### 🟢 [Get users and groups that can view a graph](https://gtidocs.virustotal.com/reference/graphs-viewers)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-viewers)

---

### 🔵 [Grant users and groups permission to see a graph](https://gtidocs.virustotal.com/reference/graphs-add-viewer)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graphs-add-viewer)

---

## Users and group management

*31 páginas · 24 endpoints*


### 📄 [User Management](https://gtidocs.virustotal.com/reference/user-management)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-management)

---

### 🔴 [Delete a user](https://gtidocs.virustotal.com/reference/delete-user-id)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-user-id)

---

### 🟢 [Get a user object](https://gtidocs.virustotal.com/reference/user)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user)

---

### 🟠 [Update a user object](https://gtidocs.virustotal.com/reference/patch-user-id)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch-user-id)

---

### 🟢 [Get object descriptors related to a user](https://gtidocs.virustotal.com/reference/get-users-relationships-ids)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-users-relationships-ids)

---

### 🟢 [Get objects related to a user](https://gtidocs.virustotal.com/reference/users-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/users-relationships)

---

### 📄 [Group Management](https://gtidocs.virustotal.com/reference/group-management)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/group-management)

---

### 🟢 [Get a group object](https://gtidocs.virustotal.com/reference/groups)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/groups)

---

### 🟠 [Update a group object](https://gtidocs.virustotal.com/reference/patch-group)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch-group)

---

### 🟢 [Get administrators for a group](https://gtidocs.virustotal.com/reference/get-group-administrators)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-group-administrators)

---

### 📄 [Manage Roles](https://gtidocs.virustotal.com/reference/patch-group-users-roles)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/patch-group-users-roles)

---

### 🟢 [Check if a user is a group admin](https://gtidocs.virustotal.com/reference/check-user-group-administrator)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/check-user-group-administrator)

---

### 🟢 [Get group users](https://gtidocs.virustotal.com/reference/get-group-users)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-group-users)

---

### 🔵 [Add users to a group](https://gtidocs.virustotal.com/reference/update-group-users)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/update-group-users)

---

### 🔴 [Remove a user from a group](https://gtidocs.virustotal.com/reference/delete-user-from-group)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/delete-user-from-group)

---

### 🟢 [Check if a user is a group member](https://gtidocs.virustotal.com/reference/check-user-in-group)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/check-user-in-group)

---

### 🟢 [Get object descriptors related to a group](https://gtidocs.virustotal.com/reference/groups-relationships-ids)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/groups-relationships-ids)

---

### 🟢 [Get objects related to a group](https://gtidocs.virustotal.com/reference/groups-relationships)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/groups-relationships)

---

### 🟢 [Get SAML configuration details of a group.](https://gtidocs.virustotal.com/reference/groups-get-samlconfig)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/groups-get-samlconfig)

---

### 🟠 [Update SAML configuration of a group.](https://gtidocs.virustotal.com/reference/groups-patch-samlconfig)

**Método:** `PATCH`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/groups-patch-samlconfig)

---

### 🔴 [Delete SAML configuration of a group.](https://gtidocs.virustotal.com/reference/groups-del-samlconfig)

**Método:** `DELETE`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/groups-del-samlconfig)

---

### 📄 [Quota Management](https://gtidocs.virustotal.com/reference/quota-management)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/quota-management)

---

### 🟢 [Get a user’s API usage](https://gtidocs.virustotal.com/reference/user-api-usage)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-api-usage)

---

### 🟢 [Get a group’s API usage](https://gtidocs.virustotal.com/reference/group-api-usage)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/group-api-usage)

---

### 🟢 [Get a group's certain feature usage](https://gtidocs.virustotal.com/reference/get-group-usage)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-group-usage)

---

### 📄 [Service Account Management](https://gtidocs.virustotal.com/reference/service-account-management)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/service-account-management)

---

### 🟢 [Get Service Accounts of a group](https://gtidocs.virustotal.com/reference/get-service-accounts-of-a-group)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-service-accounts-of-a-group)

---

### 🔵 [Create a new Service Account](https://gtidocs.virustotal.com/reference/create-a-new-service-account)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/create-a-new-service-account)

---

### 🟢 [Get a Service Account object](https://gtidocs.virustotal.com/reference/get-a-service-account-object)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-a-service-account-object)

---

### 📄 [Audit Logs](https://gtidocs.virustotal.com/reference/audit-logs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/audit-logs)

---

### 📄 [Get Activity Logs](https://gtidocs.virustotal.com/reference/get-activity-log)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-activity-log)

---

## IoC Feeds

*20 páginas · 15 endpoints*


### 📄 [File intelligence feed](https://gtidocs.virustotal.com/reference/file-intelligence-feed)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-intelligence-feed)

---

### 🟢 [Get a hourly file feed batch](https://gtidocs.virustotal.com/reference/feeds-file-hourly)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feeds-file-hourly)

---

### 🟢 [Get a per-minute file feed batch](https://gtidocs.virustotal.com/reference/feeds-file)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feeds-file)

---

### 🟢 [Download a file published in the file feed](https://gtidocs.virustotal.com/reference/file-feed-download)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-feed-download)

---

### 📄 [Sandbox analyses feed](https://gtidocs.virustotal.com/reference/sandbox-analyses-feed)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/sandbox-analyses-feed)

---

### 🟢 [Get an hourly file behaviour feed batch](https://gtidocs.virustotal.com/reference/feeds-file-behaviour-hourly)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feeds-file-behaviour-hourly)

---

### 🟢 [Get a per-minute file behaviour feed batch](https://gtidocs.virustotal.com/reference/feeds-file-behaviour)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feeds-file-behaviour)

---

### 🟢 [Get the EVTX file generated during a file’s behavior analysis](https://gtidocs.virustotal.com/reference/file-behaviour-feed-evtx)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-feed-evtx)

---

### 🟢 [Get a file behaviour's detailed HTML report](https://gtidocs.virustotal.com/reference/file-behaviour-feed-html)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-feed-html)

---

### 🟢 [Get the memdump file generated during a file’s behavior analysis](https://gtidocs.virustotal.com/reference/file-behaviour-feed-memdump)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-feed-memdump)

---

### 🟢 [Get the PCAP file generated during a file’s behavior analysis](https://gtidocs.virustotal.com/reference/file-behaviour-feed-pcap)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-feed-pcap)

---

### 📄 [Domain intelligence feed](https://gtidocs.virustotal.com/reference/domain-intelligence-feed)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-intelligence-feed)

---

### 🟢 [Get an hourly domain feed batch](https://gtidocs.virustotal.com/reference/feedsdomainshourly2time)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feedsdomainshourly2time)

---

### 🟢 [Get a minutely domain feed batch](https://gtidocs.virustotal.com/reference/feedsdomains2time)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feedsdomains2time)

---

### 📄 [IP intelligence feed](https://gtidocs.virustotal.com/reference/ip-intelligence-feed)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-intelligence-feed)

---

### 🟢 [Get an hourly IP address feed batch](https://gtidocs.virustotal.com/reference/feedsip_addresseshourly2time)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feedsip_addresseshourly2time)

---

### 🟢 [Get a minutely IP address feed batch](https://gtidocs.virustotal.com/reference/feedsip_addressestime)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feedsip_addressestime)

---

### 📄 [URL intelligence feed](https://gtidocs.virustotal.com/reference/url-intelligence-feed)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-intelligence-feed)

---

### 🟢 [Get an hourly URL feed batch](https://gtidocs.virustotal.com/reference/feeds-url-hourly)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feeds-url-hourly)

---

### 🟢 [Get a minutely URL feed batch](https://gtidocs.virustotal.com/reference/feeds-url)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/feeds-url)

---

## Categorised Threat Lists

*5 páginas · 4 endpoints*


### 📄 [Threat Lists](https://gtidocs.virustotal.com/reference/threat-lists)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/threat-lists)

---

### 🔵 [Generate a personal Authorization Token](https://gtidocs.virustotal.com/reference/get-auth-token)

**Método:** `POST`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-auth-token)

---

### 🟢 [List provisioned Categorised Threat Lists](https://gtidocs.virustotal.com/reference/list-provisioned-threat-lists)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-provisioned-threat-lists)

---

### 🟢 [Get the latest Threat List](https://gtidocs.virustotal.com/reference/get-latest-threat-list)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-latest-threat-list)

---

### 🟢 [Get an hourly Threat List](https://gtidocs.virustotal.com/reference/get-hourly-threat-list)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-hourly-threat-list)

---

## Dashboards

*2 páginas · 0 endpoints*


### 📄 [Dashboards](https://gtidocs.virustotal.com/reference/dashboards)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dashboards)

---

### 📄 [Export Dashboard Data](https://gtidocs.virustotal.com/reference/dashboards-download)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dashboards-download)

---

## GTI Alerts

*34 páginas · 0 endpoints*


### 📄 [Get Started](https://gtidocs.virustotal.com/reference/ti-get-started)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ti-get-started)

---

### 📄 [Authentication](https://gtidocs.virustotal.com/reference/ti-authentication)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ti-authentication)

---

### 📄 [Key Concepts](https://gtidocs.virustotal.com/reference/ti-key-concepts)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ti-key-concepts)

---

### 📄 [Alerts](https://gtidocs.virustotal.com/reference/alerts)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/alerts)

---

### 📄 [Overview](https://gtidocs.virustotal.com/reference/alerts-overview)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/alerts-overview)

---

### 📄 [Get Alert](https://gtidocs.virustotal.com/reference/get-alert)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-alert)

---

### 📄 [List Alerts](https://gtidocs.virustotal.com/reference/list-alerts)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-alerts)

---

### 📄 [Enumerate Facets](https://gtidocs.virustotal.com/reference/enumerate-alert-facets)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/enumerate-alert-facets)

---

### 📄 [Triage Alerts](https://gtidocs.virustotal.com/reference/triage-alerts)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/triage-alerts)

---

### 📄 [Mark as Benign](https://gtidocs.virustotal.com/reference/markalertasbenign)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/markalertasbenign)

---

### 📄 [Mark as Duplicate](https://gtidocs.virustotal.com/reference/markalertasduplicate)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/markalertasduplicate)

---

### 📄 [Mark as Escalated](https://gtidocs.virustotal.com/reference/markalertasescalated)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/markalertasescalated)

---

### 📄 [Mark as False Positive](https://gtidocs.virustotal.com/reference/markalertasfalsepositive)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/markalertasfalsepositive)

---

### 📄 [Mark as Not Actionable](https://gtidocs.virustotal.com/reference/markalertasnotactionable)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/markalertasnotactionable)

---

### 📄 [Mark as Read](https://gtidocs.virustotal.com/reference/markalertasread)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/markalertasread)

---

### 📄 [Mark as Resolved](https://gtidocs.virustotal.com/reference/markalertasresolved)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/markalertasresolved)

---

### 📄 [Mark as Triaged](https://gtidocs.virustotal.com/reference/markalertastriaged)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/markalertastriaged)

---

### 📄 [Mak as Externally Tracked](https://gtidocs.virustotal.com/reference/markalertastrackedexternally)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/markalertastrackedexternally)

---

### 📄 [Alert Documents](https://gtidocs.virustotal.com/reference/alert-documents)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/alert-documents)

---

### 📄 [Overview](https://gtidocs.virustotal.com/reference/alert-documents-overview)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/alert-documents-overview)

---

### 📄 [Get Document](https://gtidocs.virustotal.com/reference/get-alert-document)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-alert-document)

---

### 📄 [Configurations](https://gtidocs.virustotal.com/reference/configurations)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/configurations)

---

### 📄 [Overview](https://gtidocs.virustotal.com/reference/configurations-overview)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/configurations-overview)

---

### 📄 [Get Configuration](https://gtidocs.virustotal.com/reference/get-configuration)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-configuration)

---

### 📄 [List Configurations](https://gtidocs.virustotal.com/reference/list-configurations)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-configurations)

---

### 📄 [Upsert Configuration](https://gtidocs.virustotal.com/reference/upsert-configuration)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/upsert-configuration)

---

### 📄 [Configuration Revisions](https://gtidocs.virustotal.com/reference/configuration-revisions)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/configuration-revisions)

---

### 📄 [Overview](https://gtidocs.virustotal.com/reference/configuration-revisions-overview)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/configuration-revisions-overview)

---

### 📄 [List Revisions](https://gtidocs.virustotal.com/reference/list-configuration-revisions)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-configuration-revisions)

---

### 📄 [Findings](https://gtidocs.virustotal.com/reference/findings)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/findings)

---

### 📄 [Overview](https://gtidocs.virustotal.com/reference/findings-overview)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/findings-overview)

---

### 📄 [Get finding](https://gtidocs.virustotal.com/reference/get-finding)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-finding)

---

### 📄 [List Findings](https://gtidocs.virustotal.com/reference/list-findings)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/list-findings)

---

### 📄 [Search Findings](https://gtidocs.virustotal.com/reference/search-findings)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/search-findings)

---

## API OBJECTS

*265 páginas · 0 endpoints*


### 📄 [Activity Log](https://gtidocs.virustotal.com/reference/activity-log)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/activity-log)

---

### 📄 [Alerts](https://gtidocs.virustotal.com/reference/alerts-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/alerts-object)

---

### 📄 [Audit](https://gtidocs.virustotal.com/reference/audit-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/audit-object)

---

### 📄 [ConfidenceLevel](https://gtidocs.virustotal.com/reference/confidencelevel-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/confidencelevel-object)

---

### 📄 [RelevanceAnalysis](https://gtidocs.virustotal.com/reference/relevanceanalysis-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/relevanceanalysis-object)

---

### 📄 [SeverityAnalysis](https://gtidocs.virustotal.com/reference/severityanalysis-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/severityanalysis-object)

---

### 📄 [Analyses](https://gtidocs.virustotal.com/reference/analyses-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/analyses-object)

---

### 📄 [🔀 item](https://gtidocs.virustotal.com/reference/item)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/item)

---

### 📄 [Attack Tactics](https://gtidocs.virustotal.com/reference/object-attack-tactics)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/object-attack-tactics)

---

### 📄 [🔀 attack_techniques](https://gtidocs.virustotal.com/reference/attack_techniques)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack_techniques)

---

### 📄 [Attack Techniques](https://gtidocs.virustotal.com/reference/object-attack-techniques)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/object-attack-techniques)

---

### 📄 [🔀 attack_tactics](https://gtidocs.virustotal.com/reference/attack_tactics)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack_tactics)

---

### 📄 [🔀 parent_technique](https://gtidocs.virustotal.com/reference/parent_technique)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/parent_technique)

---

### 📄 [🔀 revoking_technique](https://gtidocs.virustotal.com/reference/revoking_technique)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/revoking_technique)

---

### 📄 [🔀 subtechniques](https://gtidocs.virustotal.com/reference/subtechniques)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/subtechniques)

---

### 📄 [🔀 threat_actors](https://gtidocs.virustotal.com/reference/attack-techniques-threat_actors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/attack-techniques-threat_actors)

---

### 📄 [Campaign](https://gtidocs.virustotal.com/reference/campaign-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/campaign-object)

---

### 📄 [Comments](https://gtidocs.virustotal.com/reference/comment-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/comment-object)

---

### 📄 [🔀 author](https://gtidocs.virustotal.com/reference/comment-object-author)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/comment-object-author)

---

### 📄 [Country Profile](https://gtidocs.virustotal.com/reference/country-profile-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/country-profile-object)

---

### 📄 [Dark Web](https://gtidocs.virustotal.com/reference/dark-web-objects)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dark-web-objects)

---

### 📄 [Dark Web Communication](https://gtidocs.virustotal.com/reference/dark-web-communication-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dark-web-communication-object)

---

### 📄 [Dark Web Communication Channel](https://gtidocs.virustotal.com/reference/dark-web-communication-channel-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dark-web-communication-channel-object)

---

### 📄 [Dark Web Conversation Thread](https://gtidocs.virustotal.com/reference/dark-web-conversation-thread-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dark-web-conversation-thread-object)

---

### 📄 [Dark Web Service](https://gtidocs.virustotal.com/reference/dark-web-service-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dark-web-service-object)

---

### 📄 [Dark Web User Profile](https://gtidocs.virustotal.com/reference/dark-web-user-profile-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/dark-web-user-profile-object)

---

### 📄 [Domains](https://gtidocs.virustotal.com/reference/domains-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-object)

---

### 📄 [🔀 communicating_files](https://gtidocs.virustotal.com/reference/domain-communicating_files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-communicating_files)

---

### 📄 [🔀 downloaded_files](https://gtidocs.virustotal.com/reference/domain-downloaded_files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-downloaded_files)

---

### 📄 [🔀 referrer_files](https://gtidocs.virustotal.com/reference/domain-referrer_files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-referrer_files)

---

### 📄 [🔀 graphs](https://gtidocs.virustotal.com/reference/domains-object-graphs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-object-graphs)

---

### 📄 [🔀 resolutions](https://gtidocs.virustotal.com/reference/domain-resolutions)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-resolutions)

---

### 📄 [🔀 siblings](https://gtidocs.virustotal.com/reference/siblings)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/siblings)

---

### 📄 [🔀 comments](https://gtidocs.virustotal.com/reference/domain-comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-comments)

---

### 📄 [🔀 related_comments](https://gtidocs.virustotal.com/reference/domain-related_comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-related_comments)

---

### 📄 [🔀 historical_ssl_certificates](https://gtidocs.virustotal.com/reference/domain-historical_ssl_certificates)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-historical_ssl_certificates)

---

### 📄 [🔀 historical_whois](https://gtidocs.virustotal.com/reference/domain-historical_whois)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-historical_whois)

---

### 📄 [🔀 immediate_parent](https://gtidocs.virustotal.com/reference/immediate_parent)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/immediate_parent)

---

### 📄 [🔀 parent](https://gtidocs.virustotal.com/reference/parent)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/parent)

---

### 📄 [🔀 subdomains](https://gtidocs.virustotal.com/reference/subdomains)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/subdomains)

---

### 📄 [🔀 urls](https://gtidocs.virustotal.com/reference/domain-urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domain-urls)

---

### 📄 [🔀 caa_records](https://gtidocs.virustotal.com/reference/caa_records)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/caa_records)

---

### 📄 [🔀 cname_records](https://gtidocs.virustotal.com/reference/cname_records)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/cname_records)

---

### 📄 [🔀 mx_records](https://gtidocs.virustotal.com/reference/mx_records)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/mx_records)

---

### 📄 [🔀 ns_records](https://gtidocs.virustotal.com/reference/ns_records)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ns_records)

---

### 📄 [🔀 soa_records](https://gtidocs.virustotal.com/reference/soa_records)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/soa_records)

---

### 📄 [🔀 votes](https://gtidocs.virustotal.com/reference/domains-object-votes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-object-votes)

---

### 📄 [🔀🧑‍💻 user_votes](https://gtidocs.virustotal.com/reference/domains-object-user_votes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-object-user_votes)

---

### 📄 [🔀 collections](https://gtidocs.virustotal.com/reference/domains-object-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-object-collections)

---

### 📄 [🔀 related_threat_actors](https://gtidocs.virustotal.com/reference/domains-object-related_threat_actors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/domains-object-related_threat_actors)

---

### 📄 [Files](https://gtidocs.virustotal.com/reference/file-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object)

---

### 📄 [exiftool](https://gtidocs.virustotal.com/reference/file-object-exiftool)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-exiftool)

---

### 📄 [ssdeep](https://gtidocs.virustotal.com/reference/file-object-ssdeep)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-ssdeep)

---

### 📄 [authentihash](https://gtidocs.virustotal.com/reference/file-object-authentihash)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-authentihash)

---

### 📄 [trid](https://gtidocs.virustotal.com/reference/file-object-trid)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-trid)

---

### 📄 [pe_info](https://gtidocs.virustotal.com/reference/file-object-pe-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-pe-info)

---

### 📄 [signature_info](https://gtidocs.virustotal.com/reference/file-object-signature-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-signature-info)

---

### 📄 [androguard](https://gtidocs.virustotal.com/reference/file-object-androguard)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-androguard)

---

### 📄 [asf_info](https://gtidocs.virustotal.com/reference/file-object-asf-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-asf-info)

---

### 📄 [rombios_info](https://gtidocs.virustotal.com/reference/file-object-rombios-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-rombios-info)

---

### 📄 [class_info](https://gtidocs.virustotal.com/reference/file-object-class-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-class-info)

---

### 📄 [bundle_info](https://gtidocs.virustotal.com/reference/file-object-bundle-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-bundle-info)

---

### 📄 [deb_info](https://gtidocs.virustotal.com/reference/file-object-deb-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-deb-info)

---

### 📄 [magic](https://gtidocs.virustotal.com/reference/file-object-magic)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-magic)

---

### 📄 [dmg_info](https://gtidocs.virustotal.com/reference/file-object-dmg-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-dmg-info)

---

### 📄 [elf_info](https://gtidocs.virustotal.com/reference/file-object-elf-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-elf-info)

---

### 📄 [image_code_injections](https://gtidocs.virustotal.com/reference/file-object-image-code-injections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-image-code-injections)

---

### 📄 [ipa_info](https://gtidocs.virustotal.com/reference/file-object-ipa-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-ipa-info)

---

### 📄 [jar_info](https://gtidocs.virustotal.com/reference/file-object-jar-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-jar-info)

---

### 📄 [javascript_info](https://gtidocs.virustotal.com/reference/file-object-javascript-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-javascript-info)

---

### 📄 [macho_info](https://gtidocs.virustotal.com/reference/file-object-macho-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-macho-info)

---

### 📄 [office_info](https://gtidocs.virustotal.com/reference/file-object-office-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-office-info)

---

### 📄 [openxml_info](https://gtidocs.virustotal.com/reference/file-object-openxml-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-openxml-info)

---

### 📄 [pdf_info](https://gtidocs.virustotal.com/reference/file-object-pdf-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-pdf-info)

---

### 📄 [packers](https://gtidocs.virustotal.com/reference/file-object-peid)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-peid)

---

### 📄 [rtf_info](https://gtidocs.virustotal.com/reference/file-object-rtf-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-rtf-info)

---

### 📄 [swf_info](https://gtidocs.virustotal.com/reference/file-object-swf-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-swf-info)

---

### 📄 [isoimage_info](https://gtidocs.virustotal.com/reference/file-object-isoimage-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-isoimage-info)

---

### 📄 [dot_net_assembly](https://gtidocs.virustotal.com/reference/file-object-dot-net-assembly)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-dot-net-assembly)

---

### 📄 [dot_net_guids](https://gtidocs.virustotal.com/reference/file-object-dot-net-guids)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-dot-net-guids)

---

### 📄 [password_info](https://gtidocs.virustotal.com/reference/file-object-password-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-password-info)

---

### 📄 [nsrl_info](https://gtidocs.virustotal.com/reference/file-object-nsrl-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-nsrl-info)

---

### 📄 [malware_config](https://gtidocs.virustotal.com/reference/file-object-malware-config)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-malware-config)

---

### 📄 [🔀 analyses](https://gtidocs.virustotal.com/reference/file-object-analyses)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-analyses)

---

### 📄 [🔀 comments](https://gtidocs.virustotal.com/reference/file-object-comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-comments)

---

### 📄 [🔀 carbonblack_children](https://gtidocs.virustotal.com/reference/file-object-carbonblack-children)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-carbonblack-children)

---

### 📄 [🔀 carbonblack_parents](https://gtidocs.virustotal.com/reference/file-object-carbonblack-parents)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-carbonblack-parents)

---

### 📄 [🔀 contacted_domains](https://gtidocs.virustotal.com/reference/file-object-contacted-domains)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-contacted-domains)

---

### 📄 [🔀 contacted_ips](https://gtidocs.virustotal.com/reference/file-object-contacted-ips)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-contacted-ips)

---

### 📄 [🔀 bundled_files](https://gtidocs.virustotal.com/reference/files-bundled_files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-bundled_files)

---

### 📄 [🔀 bundled_files](https://gtidocs.virustotal.com/reference/file-object-bundled-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-bundled-files)

---

### 📄 [🔀 dropped_files](https://gtidocs.virustotal.com/reference/file-object-dropped-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-dropped-files)

---

### 📄 [🔀 email_parents](https://gtidocs.virustotal.com/reference/file-object-email-parents)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-email-parents)

---

### 📄 [🔀 embedded_domains](https://gtidocs.virustotal.com/reference/file-object-embedded-domains)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-embedded-domains)

---

### 📄 [🔀 embedded_ips](https://gtidocs.virustotal.com/reference/file-object-embedded-ips)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-embedded-ips)

---

### 📄 [🔀 embedded_urls](https://gtidocs.virustotal.com/reference/files-embedded_urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/files-embedded_urls)

---

### 📄 [🔀 embedded_urls](https://gtidocs.virustotal.com/reference/file-object-embedded-urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-embedded-urls)

---

### 📄 [🔀 execution_parents](https://gtidocs.virustotal.com/reference/file-object-execution-parents)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-execution-parents)

---

### 📄 [🔀 graphs](https://gtidocs.virustotal.com/reference/file-object-graphs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-graphs)

---

### 📄 [🔀 memory_pattern_domains](https://gtidocs.virustotal.com/reference/file-object-memory-pattern-domains)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-memory-pattern-domains)

---

### 📄 [🔀 memory_pattern_ips](https://gtidocs.virustotal.com/reference/file-object-memory-pattern-ips)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-memory-pattern-ips)

---

### 📄 [🔀 memory_pattern_urls](https://gtidocs.virustotal.com/reference/file-object-memory-pattern-urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-memory-pattern-urls)

---

### 📄 [🔀 screenshots](https://gtidocs.virustotal.com/reference/file-object-screenshots)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-screenshots)

---

### 📄 [🔀 itw_urls](https://gtidocs.virustotal.com/reference/file-object-itw-urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-itw-urls)

---

### 📄 [🔀 itw_domains](https://gtidocs.virustotal.com/reference/file-object-itw-domains)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-itw-domains)

---

### 📄 [🔀 overlay_parents](https://gtidocs.virustotal.com/reference/file-object-overlay-parents)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-overlay-parents)

---

### 📄 [🔀 pcap_parents](https://gtidocs.virustotal.com/reference/file-object-pcap-parents)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-pcap-parents)

---

### 📄 [🔀 pe_resource_parents](https://gtidocs.virustotal.com/reference/file-object-pe-resource-parents)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-pe-resource-parents)

---

### 📄 [🔀 similar_files](https://gtidocs.virustotal.com/reference/file-object-similar-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-similar-files)

---

### 📄 [🔀 sigma_analysis](https://gtidocs.virustotal.com/reference/file-object-sigma-analysis)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-sigma-analysis)

---

### 📄 [🔀 submissions](https://gtidocs.virustotal.com/reference/file-object-submissions)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-submissions)

---

### 📄 [snort](https://gtidocs.virustotal.com/reference/file-object-snort)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-snort)

---

### 📄 [suricata](https://gtidocs.virustotal.com/reference/file-object-suricata)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-suricata)

---

### 📄 [traffic_inspection](https://gtidocs.virustotal.com/reference/file-object-traffic-inspection)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-traffic-inspection)

---

### 📄 [wireshark](https://gtidocs.virustotal.com/reference/file-object-wireshark)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-wireshark)

---

### 📄 [vba_info](https://gtidocs.virustotal.com/reference/file-object-vba-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-vba-info)

---

### 📄 [🔀 compressed_parents](https://gtidocs.virustotal.com/reference/file-object-compressed-parents)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-compressed-parents)

---

### 📄 [🔀 contacted_urls](https://gtidocs.virustotal.com/reference/file-object-contacted-urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-contacted-urls)

---

### 📄 [🔀 email_attachments](https://gtidocs.virustotal.com/reference/file-object-email-attachments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-email-attachments)

---

### 📄 [🔀 votes](https://gtidocs.virustotal.com/reference/file-object-votes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-votes)

---

### 📄 [monitor_info](https://gtidocs.virustotal.com/reference/file-object-monitor-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-monitor-info)

---

### 📄 [html_info](https://gtidocs.virustotal.com/reference/file-object-html-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-html-info)

---

### 📄 [🔀 itw_ips](https://gtidocs.virustotal.com/reference/file-object-itw-ips)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-itw-ips)

---

### 📄 [🔀 overlay_children](https://gtidocs.virustotal.com/reference/file-object-overlay-children)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-overlay-children)

---

### 📄 [🔀 pcap_children](https://gtidocs.virustotal.com/reference/file-object-pcap-children)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-pcap-children)

---

### 📄 [🔀  pe_resource_children](https://gtidocs.virustotal.com/reference/file-object-pe-resource-children)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-pe-resource-children)

---

### 📄 [telfhash](https://gtidocs.virustotal.com/reference/file-object-telfhash)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-telfhash)

---

### 📄 [tlsh](https://gtidocs.virustotal.com/reference/file-object-tlsh)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-tlsh)

---

### 📄 [🔀 urls_for_embedded_js](https://gtidocs.virustotal.com/reference/file-object-urls-for-embedded-js)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-urls-for-embedded-js)

---

### 📄 [known_distributors](https://gtidocs.virustotal.com/reference/file-object-known-distributors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-known-distributors)

---

### 📄 [lnk_info](https://gtidocs.virustotal.com/reference/file-object-lnk-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-lnk-info)

---

### 📄 [🔀🧑‍💻 user_votes](https://gtidocs.virustotal.com/reference/file-object-user-votes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-user-votes)

---

### 📄 [popular_threat_classification](https://gtidocs.virustotal.com/reference/file-object-popular-threat-classification)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-popular-threat-classification)

---

### 📄 [🔀 collections](https://gtidocs.virustotal.com/reference/file-object-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-collections)

---

### 📄 [🔀 related_threat_actors](https://gtidocs.virustotal.com/reference/file-object-related-threat-actors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-related-threat-actors)

---

### 📄 [crowdsourced_yara_results](https://gtidocs.virustotal.com/reference/file-object-crowdsourced-yara-results)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-crowdsourced-yara-results)

---

### 📄 [crowdsourced_ids_results](https://gtidocs.virustotal.com/reference/file-object-crowdsourced-ids-results)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-crowdsourced-ids-results)

---

### 📄 [crowdsourced_ids_stats](https://gtidocs.virustotal.com/reference/file-object-crowdsourced-ids-stats)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-crowdsourced-ids-stats)

---

### 📄 [sigma_analysis_stats](https://gtidocs.virustotal.com/reference/file-object-sigma-analysis-stats)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-sigma-analysis-stats)

---

### 📄 [sigma_analysis_results](https://gtidocs.virustotal.com/reference/file-object-sigma-analysis-results)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-sigma-analysis-results)

---

### 📄 [sandbox_verdicts](https://gtidocs.virustotal.com/reference/file-object-sandbox-verdicts)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-sandbox-verdicts)

---

### 📄 [detectiteasy](https://gtidocs.virustotal.com/reference/file-object-detectiteasy)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-detectiteasy)

---

### 📄 [powershell_info](https://gtidocs.virustotal.com/reference/file-object-powershell-info)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-object-powershell-info)

---

### 📄 [Files Behaviour](https://gtidocs.virustotal.com/reference/file-behaviour-summary-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-summary-object)

---

### 📄 [verdicts](https://gtidocs.virustotal.com/reference/file-behaviour-object-verdicts)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-verdicts)

---

### 📄 [files_dropped](https://gtidocs.virustotal.com/reference/file-behaviour-object-files-dropped)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-files-dropped)

---

### 📄 [files_copied](https://gtidocs.virustotal.com/reference/file-behaviour-object-files-copied)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-files-copied)

---

### 📄 [permissions_checked](https://gtidocs.virustotal.com/reference/file-behaviour-object-permissions-checked)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-permissions-checked)

---

### 📄 [http_conversations](https://gtidocs.virustotal.com/reference/file-behaviour-object-http-conversations)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-http-conversations)

---

### 📄 [dns_lookups](https://gtidocs.virustotal.com/reference/file-behaviour-object-dns-lookup)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-dns-lookup)

---

### 📄 [ip_traffic](https://gtidocs.virustotal.com/reference/file-behaviour-object-ip-traffic)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-ip-traffic)

---

### 📄 [processes_tree](https://gtidocs.virustotal.com/reference/file-behaviour-object-processes-tree)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-processes-tree)

---

### 📄 [sms_sent](https://gtidocs.virustotal.com/reference/file-behaviour-object-sms-sent)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-sms-sent)

---

### 📄 [🔀 file](https://gtidocs.virustotal.com/reference/file-behaviour-object-file)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-file)

---

### 📄 [🔀 attack_techniques](https://gtidocs.virustotal.com/reference/file-behaviour-object-attack-techniques)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-attack-techniques)

---

### 📄 [tags](https://gtidocs.virustotal.com/reference/file-behaviour-object-tags)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/file-behaviour-object-tags)

---

### 📄 [Graphs](https://gtidocs.virustotal.com/reference/graph-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graph-object)

---

### 📄 [🔀 comments](https://gtidocs.virustotal.com/reference/graph-comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graph-comments)

---

### 📄 [🔀 editors](https://gtidocs.virustotal.com/reference/graph-editors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graph-editors)

---

### 📄 [🔀 group](https://gtidocs.virustotal.com/reference/graph-group)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graph-group)

---

### 📄 [🔀 items](https://gtidocs.virustotal.com/reference/graph-items)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graph-items)

---

### 📄 [🔀 owner](https://gtidocs.virustotal.com/reference/graph-owner)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graph-owner)

---

### 📄 [🔀 viewers](https://gtidocs.virustotal.com/reference/graph-viewers)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/graph-viewers)

---

### 📄 [Groups](https://gtidocs.virustotal.com/reference/group-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/group-object)

---

### 📄 [🔀🧑‍💻 administrators](https://gtidocs.virustotal.com/reference/group-administrators)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/group-administrators)

---

### 📄 [🔀🧑‍💻 graphs](https://gtidocs.virustotal.com/reference/group-graphs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/group-graphs)

---

### 📄 [🔀🧑‍💻 users](https://gtidocs.virustotal.com/reference/group-users)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/group-users)

---

### 📄 [Hunting Notifications](https://gtidocs.virustotal.com/reference/hunting-notification-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/hunting-notification-object)

---

### 📄 [Hunting Rulesets](https://gtidocs.virustotal.com/reference/hunting-ruleset-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/hunting-ruleset-object)

---

### 📄 [Industry Profile](https://gtidocs.virustotal.com/reference/industry-profile-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/industry-profile-object)

---

### 📄 [IoC Collection](https://gtidocs.virustotal.com/reference/ioc-collection-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ioc-collection-object)

---

### 📄 [IoC-Stream Notifications](https://gtidocs.virustotal.com/reference/ioc-stream-notifications-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ioc-stream-notifications-object)

---

### 📄 [IP addresses](https://gtidocs.virustotal.com/reference/ip-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object)

---

### 📄 [🔀 comments](https://gtidocs.virustotal.com/reference/ip-object-comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-comments)

---

### 📄 [🔀 graphs](https://gtidocs.virustotal.com/reference/ip-object-graphs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-graphs)

---

### 📄 [🔀 historical_ssl_certificates](https://gtidocs.virustotal.com/reference/ip-object-historical-ssl-certificates)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-historical-ssl-certificates)

---

### 📄 [🔀 historical_whois](https://gtidocs.virustotal.com/reference/ip-object-historical-whois)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-historical-whois)

---

### 📄 [🔀 communicating_files](https://gtidocs.virustotal.com/reference/ip-object-communicating-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-communicating-files)

---

### 📄 [🔀 downloaded_files](https://gtidocs.virustotal.com/reference/ip-object-downloaded-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-downloaded-files)

---

### 📄 [🔀 referrer_files](https://gtidocs.virustotal.com/reference/ip-object-referrer-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-referrer-files)

---

### 📄 [🔀 resolutions](https://gtidocs.virustotal.com/reference/ip-object-resolutions)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-resolutions)

---

### 📄 [🔀 urls](https://gtidocs.virustotal.com/reference/ip-object-urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-urls)

---

### 📄 [🔀 related_comments](https://gtidocs.virustotal.com/reference/ip-object-related-comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-related-comments)

---

### 📄 [🔀 votes](https://gtidocs.virustotal.com/reference/ip-object-votes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-votes)

---

### 📄 [🔀🧑‍💻 user_votes](https://gtidocs.virustotal.com/reference/ip-object-user-votes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-user-votes)

---

### 📄 [🔀 collections](https://gtidocs.virustotal.com/reference/ip-object-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-collections)

---

### 📄 [🔀 related_threat_actors](https://gtidocs.virustotal.com/reference/ip-object-related-threat-actors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ip-object-related-threat-actors)

---

### 📄 [Malware Family](https://gtidocs.virustotal.com/reference/malware-family-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/malware-family-object)

---

### 📄 [Operations](https://gtidocs.virustotal.com/reference/operation-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/operation-object)

---

### 📄 [Private Analyses](https://gtidocs.virustotal.com/reference/private-analyses-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-analyses-object)

---

### 📄 [🔀 item](https://gtidocs.virustotal.com/reference/private-analyses-object-item)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-analyses-object-item)

---

### 📄 [🔀 submitter](https://gtidocs.virustotal.com/reference/submitter)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/submitter)

---

### 📄 [Private Files](https://gtidocs.virustotal.com/reference/private-files-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-files-object)

---

### 📄 [🔀 behaviours](https://gtidocs.virustotal.com/reference/behaviours)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/behaviours)

---

### 📄 [🔀 dropped_files](https://gtidocs.virustotal.com/reference/private-files-object-dropped_files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-files-object-dropped_files)

---

### 📄 [🔀 execution_parents](https://gtidocs.virustotal.com/reference/execution_parents)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/execution_parents)

---

### 📄 [🔀 embedded_urls](https://gtidocs.virustotal.com/reference/embedded_urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/embedded_urls)

---

### 📄 [🔀 embedded_domains](https://gtidocs.virustotal.com/reference/private-files-object-embedded_domains)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-files-object-embedded_domains)

---

### 📄 [🔀 embedded_ips](https://gtidocs.virustotal.com/reference/embedded_ips)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/embedded_ips)

---

### 📄 [Private Files Behaviours](https://gtidocs.virustotal.com/reference/private-file-behaviours-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-file-behaviours-object)

---

### 📄 [🔀 file](https://gtidocs.virustotal.com/reference/private-file-behaviours-file)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-file-behaviours-file)

---

### 📄 [🔀 attack_techniques](https://gtidocs.virustotal.com/reference/private-file-behaviours-attack_techniques)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-file-behaviours-attack_techniques)

---

### 📄 [Private URLs](https://gtidocs.virustotal.com/reference/private-urls-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-urls-object)

---

### 📄 [Private URLs Behaviours](https://gtidocs.virustotal.com/reference/private-url-behaviours-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/private-url-behaviours-object)

---

### 📄 [Report](https://gtidocs.virustotal.com/reference/report-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/report-object)

---

### 📄 [Retrohunt Jobs](https://gtidocs.virustotal.com/reference/retrohunt-job-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/retrohunt-job-object)

---

### 📄 [🔀🧑‍💻 matching_files](https://gtidocs.virustotal.com/reference/retrohunt-job-matching-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/retrohunt-job-matching-files)

---

### 📄 [🔀🧑‍💻 owner](https://gtidocs.virustotal.com/reference/retrohunt-job-owner)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/retrohunt-job-owner)

---

### 📄 [Resolutions](https://gtidocs.virustotal.com/reference/resolution-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/resolution-object)

---

### 📄 [Saved Searches](https://gtidocs.virustotal.com/reference/saved-search-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/saved-search-object)

---

### 📄 [Screenshots](https://gtidocs.virustotal.com/reference/screenshots-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/screenshots-object)

---

### 📄 [Service Accounts](https://gtidocs.virustotal.com/reference/service-accounts-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/service-accounts-object)

---

### 📄 [🔀🧑‍💻 api_quota_group](https://gtidocs.virustotal.com/reference/service-account-object-api-quota-group)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/service-account-object-api-quota-group)

---

### 📄 [🔀 comments](https://gtidocs.virustotal.com/reference/service-account-object-comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/service-account-object-comments)

---

### 📄 [🔀🧑‍💻 groups](https://gtidocs.virustotal.com/reference/service-account-object-groups)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/service-account-object-groups)

---

### 📄 [🔀🧑‍💻 intelligence_quota_group](https://gtidocs.virustotal.com/reference/service-account-object-intelligence-quota-group)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/service-account-object-intelligence-quota-group)

---

### 📄 [🔀 mentions](https://gtidocs.virustotal.com/reference/service-account-object-mentions)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/service-account-object-mentions)

---

### 📄 [Sigma Analyses](https://gtidocs.virustotal.com/reference/sigma-analyses-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/sigma-analyses-object)

---

### 📄 [🔀 rules](https://gtidocs.virustotal.com/reference/sigma-analyses-object-rules)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/sigma-analyses-object-rules)

---

### 📄 [Sigma Rules](https://gtidocs.virustotal.com/reference/sigma-rule-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/sigma-rule-object)

---

### 📄 [Software and Toolkit](https://gtidocs.virustotal.com/reference/software-toolkit-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/software-toolkit-object)

---

### 📄 [SSL Certificate](https://gtidocs.virustotal.com/reference/ssl-certificate-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/ssl-certificate-object)

---

### 📄 [Submissions](https://gtidocs.virustotal.com/reference/submission-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/submission-object)

---

### 📄 [Threat Actor](https://gtidocs.virustotal.com/reference/threat-actor-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/threat-actor-object)

---

### 📄 [Threat Profile](https://gtidocs.virustotal.com/reference/threat-profile-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/threat-profile-object)

---

### 📄 [URLs](https://gtidocs.virustotal.com/reference/url-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-object)

---

### 📄 [🔀 analyses](https://gtidocs.virustotal.com/reference/url-analyses)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-analyses)

---

### 📄 [🔀 comments](https://gtidocs.virustotal.com/reference/url-comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-comments)

---

### 📄 [🔀 related_comments](https://gtidocs.virustotal.com/reference/url-related_comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-related_comments)

---

### 📄 [🔀 contacted_domains](https://gtidocs.virustotal.com/reference/url-contacted_domains)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-contacted_domains)

---

### 📄 [🔀 contacted_ips](https://gtidocs.virustotal.com/reference/url-contacted_ips)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-contacted_ips)

---

### 📄 [🔀 downloaded_files](https://gtidocs.virustotal.com/reference/url-downloaded_files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-downloaded_files)

---

### 📄 [🔀 graphs](https://gtidocs.virustotal.com/reference/url-graphs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-graphs)

---

### 📄 [🔀 last_serving_ip_address](https://gtidocs.virustotal.com/reference/url-last_serving_ip_address)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-last_serving_ip_address)

---

### 📄 [🔀 network_location](https://gtidocs.virustotal.com/reference/url-network_location)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-network_location)

---

### 📄 [🔀 redirecting_urls](https://gtidocs.virustotal.com/reference/url-redirecting_urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-redirecting_urls)

---

### 📄 [🔀 redirects_to](https://gtidocs.virustotal.com/reference/url-redirects_to)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-redirects_to)

---

### 📄 [🔀 submissions](https://gtidocs.virustotal.com/reference/url-submissions)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/url-submissions)

---

### 📄 [🔀 embedded_js_files](https://gtidocs.virustotal.com/reference/urls-embedded_js_files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-embedded_js_files)

---

### 📄 [🔀 referrer_files](https://gtidocs.virustotal.com/reference/urls-referrer_files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-referrer_files)

---

### 📄 [🔀 referrer_urls](https://gtidocs.virustotal.com/reference/urls-referrer_urls)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-referrer_urls)

---

### 📄 [🔀 urls_related_by_tracker_id](https://gtidocs.virustotal.com/reference/urls-urls_related_by_tracker_id)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-urls_related_by_tracker_id)

---

### 📄 [🔀 communicating_files](https://gtidocs.virustotal.com/reference/urls-communicating_files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-communicating_files)

---

### 📄 [🔀 votes](https://gtidocs.virustotal.com/reference/votes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/votes)

---

### 📄 [🔀🧑‍💻 user_votes](https://gtidocs.virustotal.com/reference/urls-object-user_votes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-object-user_votes)

---

### 📄 [🔀 collections](https://gtidocs.virustotal.com/reference/urls-object-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-object-collections)

---

### 📄 [🔀 related_threat_actors](https://gtidocs.virustotal.com/reference/urls-object-related_threat_actors)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/urls-object-related_threat_actors)

---

### 📄 [Users](https://gtidocs.virustotal.com/reference/user-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object)

---

### 📄 [🔀 comments](https://gtidocs.virustotal.com/reference/user-object-comments)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-comments)

---

### 📄 [🔀🧑‍💻 groups](https://gtidocs.virustotal.com/reference/user-object-groups)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-groups)

---

### 📄 [🔀🧑‍💻 hunting_rulesets](https://gtidocs.virustotal.com/reference/user-object-hunting-rulesets)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-hunting-rulesets)

---

### 📄 [🔀🧑‍💻 hunting_notifications](https://gtidocs.virustotal.com/reference/user-object-hunting-notifications)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-hunting-notifications)

---

### 📄 [🔀🧑‍💻 hunting_notification_files](https://gtidocs.virustotal.com/reference/user-object-hunting-notification-files)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-hunting-notification-files)

---

### 📄 [🔀 mentions](https://gtidocs.virustotal.com/reference/user-object-mentions)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-mentions)

---

### 📄 [🔀 graphs](https://gtidocs.virustotal.com/reference/user-object-graphs)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-graphs)

---

### 📄 [🔀🧑‍💻 retrohunt_jobs](https://gtidocs.virustotal.com/reference/user-object-retrohunt-job)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-retrohunt-job)

---

### 📄 [🔀🧑‍💻 api_quota_group](https://gtidocs.virustotal.com/reference/user-object-api-quota-group)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-api-quota-group)

---

### 📄 [🔀🧑‍💻 intelligence_quota_group](https://gtidocs.virustotal.com/reference/user-object-intelligence-quota-group)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-intelligence-quota-group)

---

### 📄 [🔀 collections](https://gtidocs.virustotal.com/reference/user-object-collections)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-collections)

---

### 📄 [🔀 votes](https://gtidocs.virustotal.com/reference/user-object-votes)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/user-object-votes)

---

### 📄 [Votes](https://gtidocs.virustotal.com/reference/vote-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/vote-object)

---

### 📄 [Vulnerability](https://gtidocs.virustotal.com/reference/vulnerability-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/vulnerability-object)

---

### 📄 [Whois](https://gtidocs.virustotal.com/reference/whois-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/whois-object)

---

### 📄 [YARA Rules](https://gtidocs.virustotal.com/reference/yara-rule-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/yara-rule-object)

---

### 📄 [YARA Rulesets](https://gtidocs.virustotal.com/reference/yara-rulesets-object)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/yara-rulesets-object)

---

## Widget

*3 páginas · 1 endpoints*


### 📄 [Google Threat Intelligence Widget Quick guide](https://gtidocs.virustotal.com/reference/widget-quick-guide)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/widget-quick-guide)

---

### 📄 [Rendering URL](https://gtidocs.virustotal.com/reference/rendering-url)

📖 [Ver documentación](https://gtidocs.virustotal.com/reference/rendering-url)

---

### 🟢 [Get a widget rendering URL](https://gtidocs.virustotal.com/reference/get-widget-url)

**Método:** `GET`  
📖 [Ver documentación](https://gtidocs.virustotal.com/reference/get-widget-url)

---


---
*Documentación generada automáticamente desde https://gtidocs.virustotal.com*