# DCE

# 🕹️ Dungeon-Crawler-Engine

Modular dungeon crawler simulation for **AI-driven gameplay**, **pathfinding experiments**, and **cryptographic save testing**.  
**Under development** by **YSNRFD**

---

## 🧠 DCE_ysnrfd – Procedural Dungeon Crawler Engine with AI & Secure Save System

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Game Engine](https://img.shields.io/badge/Engine-Modular-lightgreen.svg)]()
[![Save System](https://img.shields.io/badge/Saves-Cryptographically%20Signed-critical.svg)]()

---

## 🚀 Overview

**DCE_ysnrfd** is an extensible, modular dungeon crawler simulation built in pure Python.  
It includes a secure save/load system using cryptographic HMACs, procedurally generated dungeons, an intelligent A\* enemy AI, and a structured turn-based system.  
Perfect for prototyping **game mechanics**, **AI behavior**, and **simulation loops**.

This project is for **educational purposes**, AI/ML pathfinding demos, and ethical development only.

---

## ✨ Features

- 🧱 **Procedural Dungeon Generation**  
  Uses recursive division with controlled randomness to generate interconnected dungeon layouts.

- 🧠 **A\* Pathfinding**  
  Enemies use a priority queue with Manhattan heuristics for navigation and targeting.

- ⚙️ **Component-Based Entity System**  
  Players, enemies, and items are all modeled with clean, modular class structures.

- 🔒 **Cryptographic Save/Load**  
  Uses HMAC-SHA256 to verify save integrity. Saves are rejected if tampered.

- ⏱️ **Turn-Based State Machine**  
  Robust finite state system for clean transitions (menu → gameplay → endgame).

- 🧃 **Inventory & Items System**  
  Supports armor, weapons, potions, and quest items with metadata and effects.

- 📜 **Type-Hinted & Extensible**  
  Fully annotated for IDE support and future expansion.

- 📓 **Verbose Logging System**  
  Game states and events are logged to `dungeon_crawler.log`.

---

## 📦 Installation

**1. Clone the repository**

```bash
git clone https://github.com/ysnrfd/DCE.git
cd DCE
```

**2. Run the program**

Linux:
```python
python3 dungeon_crawler.py
```
Windows:
```python
python dungeon_crawler.py
```




## 🔧 Usage Examples

**Run the main game loop**
```python
python dungeon_crawler.py
```

**Use the map generation module alone**

```python
from dungeon_crawler import DungeonGenerator
map_data = DungeonGenerator(width=40, height=20).generate()
print(map_data)
```

**Save and verify game state**

```python
from dungeon_crawler import SaveSystem, GameState

state = GameState(...)
SaveSystem.save(state, "game_state.encrypted")
verified = SaveSystem.load("game_state.encrypted")
```


## 📂 Project Structure
```structure
dungeon-crawler-engine/
│── dungeon_crawler.py        # Main game engine
│── #dungeon_crawler.log       # Log output
│── #game_state.encrypted      # Cryptographically signed game save
│── README.md                # This file
│── LICENSE
```


## 🔐 Save System Details
- **Based on HMAC-SHA256 with secret key**  

- **Includes timestamp and anti-replay protection**  

- **Invalid or tampered saves are automatically discarded**  


## 🧠 Algorithms & Internals
- **Pathfinding: A with open/closed sets, priority queues (heapq)**  

- **Dungeon Generation: Recursive division + random room linking**  

- **State Machine: Enum-based game states and transitions**  

- **Secure Save: JSON serialization + hmac + secrets**


## 🛣️ Roadmap
**✅ Cryptographic save/load system**  

**✅ Procedural generation engine**  

**✅ A pathfinding and enemy AI** 

**🔲 GUI version with Pygame or Pyxel**  

**🔲 Quest/dialogue system**  

**🔲 Plugin API for modding**  

**🔲 Fog of war and minimap**  



## ⚠️ Ethical Usage Notice
This engine is intended for learning, game prototyping, and academic experiments only.  
You are not permitted to use this code in unethical simulations or closed-source game repackaging without preserving attribution.

## 📝 License
This project is licensed under the **YSNRFD License.**  
You are free to fork and build upon it with proper credit and within ethical guidelines.  
Redistribution without credit is strictly forbidden.  

## 👨‍💻 Author
**Developer: YSNRFD**  
**Telegram: @ysnrfd**

## ⭐ Support This Project
**If you enjoyed this project or learned something useful, please star it on GitHub and share it with others!**
