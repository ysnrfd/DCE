#!/usr/bin/env python3
"""
██████╗ ███████╗███████╗███████╗██████╗  █████╗ ██████╗ ███████╗
██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝
██████╔╝█████╗  █████╗  █████╗  ██████╔╝███████║██████╔╝█████╗  
██╔══██╗██╔══╝  ██╔══╝  ██╔══╝  ██╔══██╗██╔══██║██╔══██╗██╔══╝  
██║  ██║███████╗██║     ███████╗██║  ██║██║  ██║██║  ██║███████╗
╚═╝  ╚═╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝

A hyper-structured, enterprise-grade dungeon crawler simulation with:
- Procedural dungeon generation (Recursive Division Algorithm)
- A* Pathfinding for enemy AI
- Component-Based Entity System
- JSON Save/Load with cryptographic signing
- Multithreaded event handling
- Comprehensive error logging
- State machine architecture
- Type hints and docstring documentation
----------------------------------------------

Developer: YSNRFD
Telegram: @ysnrfd
"""

import json
import time
import threading
import logging
import hashlib
import hmac
import secrets
from enum import Enum, auto
from heapq import heappop, heappush
from typing import (
    Dict, 
    List, 
    Tuple, 
    Optional, 
    Set, 
    Any, 
    Callable, 
    TypeVar, 
    Generic,
    cast
)

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================
SECRET_KEY = secrets.token_bytes(32)
LOG_FILE = "dungeon_crawler.log"
SAVE_FILE = "game_state.encrypted"
MAX_ROOMS = 15
ROOM_MIN_SIZE = 4
ROOM_MAX_SIZE = 8
ENEMY_SPAWN_RATE = 0.3
ITEM_SPAWN_RATE = 0.25

# =============================================================================
# LOGGING SETUP
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DungeonCrawler")

# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================
class DungeonGenerationError(Exception):
    """Raised when dungeon generation fails"""
    pass

class SaveFileCorruptedError(Exception):
    """Raised when save file integrity check fails"""
    pass

class InvalidGameStateError(Exception):
    """Raised when game state violates business rules"""
    pass

# =============================================================================
# ENUMERATIONS
# =============================================================================
class Direction(Enum):
    NORTH = auto()
    EAST = auto()
    SOUTH = auto()
    WEST = auto()

class ItemType(Enum):
    WEAPON = auto()
    ARMOR = auto()
    POTION = auto()
    QUEST = auto()

class EntityState(Enum):
    IDLE = auto()
    PATROLLING = auto()
    CHASING = auto()
    COMBAT = auto()
    DEAD = auto()

# =============================================================================
# GEOMETRY & MATH UTILITIES
# =============================================================================
T = TypeVar('T')
class BoundedQueue(Generic[T]):
    """Thread-safe bounded queue with priority support"""
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._queue: List[Tuple[int, T]] = []
        self._lock = threading.RLock()
    
    def push(self, priority: int, item: T) -> None:
        with self._lock:
            heappush(self._queue, (priority, item))
            if len(self._queue) > self.max_size:
                self._queue.pop()
    
    def pop(self) -> T:
        with self._lock:
            return heappop(self._queue)[1]
    
    def clear(self) -> None:
        with self._lock:
            self._queue.clear()

class Vector2D:
    """Immutable 2D coordinate system"""
    __slots__ = ('x', 'y')
    
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2D):
            return False
        return self.x == other.x and self.y == other.y
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def __repr__(self) -> str:
        return f"Vector2D({self.x}, {self.y})"

# =============================================================================
# GAME CORE COMPONENTS
# =============================================================================
class Room:
    """Represents a dungeon room with spatial properties"""
    def __init__(self, origin: Vector2D, width: int, height: int):
        self.origin = origin
        self.width = width
        self.height = height
        self.connections: Dict[Direction, 'Room'] = {}
        self.items: List['Item'] = []
        self.enemies: List['Enemy'] = []
        self.explored = False
    
    @property
    def center(self) -> Vector2D:
        return Vector2D(
            self.origin.x + self.width // 2,
            self.origin.y + self.height // 2
        )
    
    def intersects(self, other: 'Room') -> bool:
        """Check if this room intersects with another room"""
        return (
            self.origin.x <= other.origin.x + other.width and
            self.origin.x + self.width >= other.origin.x and
            self.origin.y <= other.origin.y + other.height and
            self.origin.y + self.height >= other.origin.y
        )

class Dungeon:
    """Procedurally generated dungeon using recursive division"""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.rooms: List[Room] = []
        self.tiles: List[List[bool]] = [
            [False for _ in range(height)] 
            for _ in range(width)
        ]
        self.player_start = Vector2D(0, 0)
        self.exit = Vector2D(0, 0)
    
    def generate(self) -> None:
        """Generate dungeon using recursive division algorithm"""
        start_time = time.time()
        self._recursive_division(0, 0, self.width, self.height)
        
        # Connect all rooms
        self._connect_rooms()
        
        # Place player and exit
        if not self.rooms:
            raise DungeonGenerationError("No rooms generated")
        
        self.player_start = self.rooms[0].center
        self.exit = self.rooms[-1].center
        
        # Populate with items and enemies
        self._populate_dungeon()
        
        logger.info(f"Dungeon generated in {time.time() - start_time:.4f}s")
    
    def _recursive_division(self, x: int, y: int, w: int, h: int) -> None:
        """Recursive division algorithm for room generation"""
        if w <= ROOM_MIN_SIZE * 2 or h <= ROOM_MIN_SIZE * 2:
            return
        
        # Randomly choose split position
        split_x = x + ROOM_MIN_SIZE + random.randint(0, w - ROOM_MIN_SIZE * 2)
        split_y = y + ROOM_MIN_SIZE + random.randint(0, h - ROOM_MIN_SIZE * 2)
        
        # Create rooms
        room_w = random.randint(ROOM_MIN_SIZE, min(ROOM_MAX_SIZE, w // 2))
        room_h = random.randint(ROOM_MIN_SIZE, min(ROOM_MAX_SIZE, h // 2))
        new_room = Room(Vector2D(split_x, split_y), room_w, room_h)
        
        # Check intersection with existing rooms
        if not any(new_room.intersects(r) for r in self.rooms):
            self.rooms.append(new_room)
            
            # Carve room into tile map
            for i in range(new_room.origin.x, new_room.origin.x + new_room.width):
                for j in range(new_room.origin.y, new_room.origin.y + new_room.height):
                    if 0 <= i < self.width and 0 <= j < self.height:
                        self.tiles[i][j] = True
        
        # Recursively divide remaining space
        self._recursive_division(x, y, split_x - x, split_y - y)
        self._recursive_division(split_x, y, w - (split_x - x), split_y - y)
        self._recursive_division(x, split_y, split_x - x, h - (split_y - y))
        self._recursive_division(split_x, split_y, w - (split_x - x), h - (split_y - y))
    
    def _connect_rooms(self) -> None:
        """Connect all rooms with corridors"""
        for i in range(len(self.rooms) - 1):
            room_a = self.rooms[i]
            room_b = self.rooms[i + 1]
            
            # Horizontal corridor
            x1, y1 = room_a.center.x, room_a.center.y
            x2, y2 = room_b.center.x, room_b.center.y
            
            # Carve horizontal then vertical
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.tiles[x][y1] = True
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.tiles[x2][y] = True
            
            # Record connection
            room_a.connections[Direction.EAST] = room_b
            room_b.connections[Direction.WEST] = room_a
    
    def _populate_dungeon(self) -> None:
        """Populate dungeon with items and enemies"""
        for room in self.rooms:
            # Enemies
            if random.random() < ENEMY_SPAWN_RATE:
                enemy = Enemy(
                    position=room.center,
                    enemy_type=random.choice(list(EnemyType))
                )
                room.enemies.append(enemy)
            
            # Items
            if random.random() < ITEM_SPAWN_RATE:
                item = Item.create_random(room.center)
                room.items.append(item)

class Item:
    """Base class for all in-game items"""
    def __init__(self, position: Vector2D, item_type: ItemType, name: str, value: int):
        self.position = position
        self.item_type = item_type
        self.name = name
        self.value = value
        self.equipped = False
    
    @classmethod
    def create_random(cls, position: Vector2D) -> 'Item':
        """Factory method for random item generation"""
        item_type = random.choice(list(ItemType))
        if item_type == ItemType.WEAPON:
            return Weapon(
                position,
                f"{random.choice(['Iron', 'Steel', 'Mithril'])} {random.choice(['Sword', 'Axe', 'Dagger'])}",
                random.randint(5, 15)
            )
        elif item_type == ItemType.ARMOR:
            return Armor(
                position,
                f"{random.choice(['Leather', 'Chainmail', 'Plate'])} {random.choice(['Armor', 'Helmet', 'Shield'])}",
                random.randint(3, 10)
            )
        elif item_type == ItemType.POTION:
            return Potion(
                position,
                f"{random.choice(['Healing', 'Mana', 'Strength'])} Potion",
                random.randint(10, 30)
            )
        else:
            return QuestItem(
                position,
                f"{random.choice(['Ancient', 'Cursed', 'Sacred'])} {random.choice(['Artifact', 'Relic', 'Scroll'])}",
                random.randint(50, 100)
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize item to dictionary"""
        return {
            'type': self.__class__.__name__,
            'position': (self.position.x, self.position.y),
            'name': self.name,
            'value': self.value,
            'equipped': self.equipped
        }
    
    @staticmethod
    def from_dict( Dict[str, Any]) -> 'Item':
        """Deserialize item from dictionary"""
        position = Vector2D(data['position'][0], data['position'][1])
        if data['type'] == 'Weapon':
            return Weapon(position, data['name'], data['value'])
        # ... other types would be handled here
        raise ValueError(f"Unknown item type: {data['type']}")

class Weapon(Item):
    def __init__(self, position: Vector2D, name: str, damage: int):
        super().__init__(position, ItemType.WEAPON, name, damage)
        self.damage = damage

class Armor(Item):
    def __init__(self, position: Vector2D, name: str, defense: int):
        super().__init__(position, ItemType.ARMOR, name, defense)
        self.defense = defense

class Potion(Item):
    def __init__(self, position: Vector2D, name: str, heal_amount: int):
        super().__init__(position, ItemType.POTION, name, heal_amount)
        self.heal_amount = heal_amount

class QuestItem(Item):
    def __init__(self, position: Vector2D, name: str, quest_value: int):
        super().__init__(position, ItemType.QUEST, name, quest_value)
        self.quest_value = quest_value

# =============================================================================
# ENTITY SYSTEM
# =============================================================================
class Entity:
    """Base class for all game entities"""
    def __init__(self, position: Vector2D):
        self.position = position
        self.components: Dict[str, Any] = {}
    
    def add_component(self, name: str, component: Any) -> None:
        self.components[name] = component
    
    def get_component(self, name: str) -> Optional[Any]:
        return self.components.get(name)

class CombatStats:
    """Component for combat-related statistics"""
    def __init__(self, hp: int, max_hp: int, attack: int, defense: int):
        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.defense = defense

class Inventory:
    """Component for inventory management"""
    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.items: List[Item] = []
        self.equipped: Dict[ItemType, Optional[Item]] = {
            ItemType.WEAPON: None,
            ItemType.ARMOR: None
        }
    
    def add_item(self, item: Item) -> bool:
        if len(self.items) >= self.capacity:
            return False
        self.items.append(item)
        return True
    
    def equip_item(self, item: Item) -> bool:
        if item.item_type not in self.equipped:
            return False
        if item.item_type == ItemType.WEAPON or item.item_type == ItemType.ARMOR:
            self.equipped[item.item_type] = item
            item.equipped = True
            return True
        return False

class Player(Entity):
    """Player character with advanced state management"""
    def __init__(self, position: Vector2D):
        super().__init__(position)
        self.add_component("combat", CombatStats(100, 100, 10, 5))
        self.add_component("inventory", Inventory())
        self.experience = 0
        self.level = 1
    
    def take_damage(self, amount: int) -> bool:
        """Apply damage and return if entity is dead"""
        combat = cast(CombatStats, self.get_component("combat"))
        actual_damage = max(1, amount - combat.defense)
        combat.hp -= actual_damage
        logger.info(f"Player took {actual_damage} damage. HP: {combat.hp}/{combat.max_hp}")
        return combat.hp <= 0
    
    def heal(self, amount: int) -> None:
        combat = cast(CombatStats, self.get_component("combat"))
        combat.hp = min(combat.max_hp, combat.hp + amount)
        logger.info(f"Player healed for {amount}. HP: {combat.hp}/{combat.max_hp}")

class EnemyType(Enum):
    GOBLIN = ("Goblin", 30, 5, 2)
    ORC = ("Orc", 50, 8, 4)
    TROLL = ("Troll", 80, 12, 6)
    
    def __init__(self, name: str, hp: int, attack: int, defense: int):
        self.display_name = name
        self.default_hp = hp
        self.default_attack = attack
        self.default_defense = defense

class Enemy(Entity):
    """Enemy with state-based AI behavior"""
    def __init__(self, position: Vector2D, enemy_type: EnemyType):
        super().__init__(position)
        self.enemy_type = enemy_type
        self.state = EntityState.PATROLLING
        self.path: List[Vector2D] = []
        self.vision_range = 5
        self.add_component("combat", CombatStats(
            enemy_type.default_hp,
            enemy_type.default_hp,
            enemy_type.default_attack,
            enemy_type.default_defense
        ))
    
    def update_ai(self, player_pos: Vector2D, dungeon: Dungeon) -> None:
        """Update enemy state based on player position"""
        distance = abs(player_pos.x - self.position.x) + abs(player_pos.y - self.position.y)
        
        if distance <= self.vision_range:
            self.state = EntityState.CHASING
        else:
            self.state = EntityState.PATROLLING
        
        # Pathfinding logic
        if self.state == EntityState.CHASING and (not self.path or random.random() < 0.1):
            self.path = self._find_path(player_pos, dungeon)
        
        # Move along path
        if self.path:
            self.position = self.path.pop(0)
    
    def _find_path(self, target: Vector2D, dungeon: Dungeon) -> List[Vector2D]:
        """A* pathfinding implementation"""
        open_set = BoundedQueue()
        open_set.push(0, (self.position, []))
        closed_set: Set[Vector2D] = set()
        
        while open_set:
            current, path = open_set.pop()
            if current == target:
                return path[1:]  # Skip first position (current)
            
            if current in closed_set:
                continue
            
            closed_set.add(current)
            for direction in [Vector2D(0, -1), Vector2D(1, 0), Vector2D(0, 1), Vector2D(-1, 0)]:
                neighbor = current + direction
                if (
                    0 <= neighbor.x < dungeon.width and
                    0 <= neighbor.y < dungeon.height and
                    dungeon.tiles[neighbor.x][neighbor.y] and
                    neighbor not in closed_set
                ):
                    new_path = path + [neighbor]
                    priority = len(new_path) + abs(neighbor.x - target.x) + abs(neighbor.y - target.y)
                    open_set.push(priority, (neighbor, new_path))
        
        return []  # No path found

# =============================================================================
# GAME STATE MANAGEMENT
# =============================================================================
class GameState(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()

class GameContext:
    """Holds global game state and services"""
    def __init__(self):
        self.state = GameState.MAIN_MENU
        self.dungeon = Dungeon(80, 40)
        self.player = Player(Vector2D(0, 0))
        self.enemies: List[Enemy] = []
        self.current_room: Optional[Room] = None
        self.event_queue = BoundedQueue[Callable[[], None]]()
        self.thread = threading.Thread(target=self._process_events, daemon=True)
        self.thread.start()
        self.last_update = time.time()
        self.fps = 0
    
    def _process_events(self) -> None:
        """Process queued events in separate thread"""
        while True:
            try:
                event = self.event_queue.pop()
                event()
            except IndexError:
                time.sleep(0.01)
    
    def save_game(self) -> None:
        """Save game state with cryptographic integrity check"""
        start_time = time.time()
        state = {
            'player': {
                'position': (self.player.position.x, self.player.position.y),
                'health': self.player.get_component("combat").hp,
                'level': self.player.level
            },
            'dungeon': {
                'width': self.dungeon.width,
                'height': self.dungeon.height
            },
            'timestamp': time.time()
        }
        
        # Serialize and sign
        serialized = json.dumps(state).encode()
        signature = hmac.new(SECRET_KEY, serialized, hashlib.sha256).digest()
        encrypted = serialized + signature
        
        with open(SAVE_FILE, 'wb') as f:
            f.write(encrypted)
        
        logger.info(f"Game saved in {time.time() - start_time:.4f}s")
    
    def load_game(self) -> None:
        """Load game state with integrity verification"""
        start_time = time.time()
        try:
            with open(SAVE_FILE, 'rb') as f:
                data = f.read()
            
            # Verify signature
            serialized = data[:-32]
            signature = data[-32:]
            if not hmac.compare_digest(hmac.new(SECRET_KEY, serialized, hashlib.sha256).digest(), signature):
                raise SaveFileCorruptedError("Signature mismatch")
            
            state = json.loads(serialized)
            
            # Reconstruct game state
            self.player.position = Vector2D(
                state['player']['position'][0],
                state['player']['position'][1]
            )
            self.player.get_component("combat").hp = state['player']['health']
            self.player.level = state['player']['level']
            
            logger.info(f"Game loaded in {time.time() - start_time:.4f}s")
        except Exception as e:
            logger.error(f"Failed to load game: {str(e)}")
            raise

# =============================================================================
# MAIN GAME LOOP
# =============================================================================
class Game:
    """Main game controller with state machine architecture"""
    def __init__(self):
        self.context = GameContext()
        self.running = True
        self.frame_count = 0
        self.last_fps_update = time.time()
    
    def start(self) -> None:
        """Initialize and start the game loop"""
        logger.info("Starting game engine...")
        self.context.dungeon.generate()
        self.context.player.position = self.context.dungeon.player_start
        
        # Spawn enemies
        for room in self.context.dungeon.rooms:
            for enemy in room.enemies:
                self.context.enemies.append(enemy)
        
        self.context.state = GameState.PLAYING
        self._main_loop()
    
    def _main_loop(self) -> None:
        """Primary game loop with fixed timestep"""
        TARGET_FPS = 60
        TIME_PER_FRAME = 1.0 / TARGET_FPS
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            elapsed = current_time - last_time
            
            if elapsed >= TIME_PER_FRAME:
                last_time = current_time
                
                # Process input
                self._handle_input()
                
                # Update game state
                self._update(elapsed)
                
                # Render frame
                self._render()
                
                # FPS calculation
                self.frame_count += 1
                if current_time - self.last_fps_update > 1.0:
                    self.context.fps = self.frame_count
                    self.frame_count = 0
                    self.last_fps_update = current_time
    
    def _handle_input(self) -> None:
        """Process player input (simulated here)"""
        if self.context.state != GameState.PLAYING:
            return
        
        # Simulate movement (in real game would use actual input)
        direction = random.choice([
            Vector2D(0, -1),  # Up
            Vector2D(1, 0),   # Right
            Vector2D(0, 1),   # Down
            Vector2D(-1, 0)   # Left
        ])
        new_pos = self.context.player.position + direction
        
        # Validate movement
        if (
            0 <= new_pos.x < self.context.dungeon.width and
            0 <= new_pos.y < self.context.dungeon.height and
            self.context.dungeon.tiles[new_pos.x][new_pos.y]
        ):
            self.context.player.position = new_pos
    
    def _update(self, delta_time: float) -> None:
        """Update all game systems"""
        # Update enemies
        for enemy in self.context.enemies[:]:
            enemy.update_ai(self.context.player.position, self.context.dungeon)
            
            # Combat check
            if enemy.position == self.context.player.position:
                enemy.get_component("combat").hp -= self.context.player.get_component("combat").attack
                if enemy.get_component("combat").hp <= 0:
                    self.context.enemies.remove(enemy)
                    logger.info(f"Defeated {enemy.enemy_type.display_name}!")
        
        # Check game state transitions
        if self.context.player.position == self.context.dungeon.exit:
            self.context.state = GameState.VICTORY
            logger.info("Player reached the exit! Victory!")
            self.running = False
        
        if self.context.player.get_component("combat").hp <= 0:
            self.context.state = GameState.GAME_OVER
            logger.info("Player has died. Game over.")
            self.running = False
    
    def _render(self) -> None:
        """Render game state (simulated here)"""
        # In a real implementation, this would draw to a screen
        if self.frame_count % 30 == 0:  # Every half second at 60 FPS
            logger.debug(
                f"Rendering frame... Player at {self.context.player.position}, "
                f"Enemies: {len(self.context.enemies)}, FPS: {self.context.fps}"
            )

# =============================================================================
# ENTRY POINT
# =============================================================================
def main() -> None:
    """Application entry point with full error handling"""
    game = None
    try:
        logger.info("Initializing game...")
        game = Game()
        game.start()
        logger.info("Game loop exited cleanly")
    except Exception as e:
        logger.exception("Critical error in game loop")
        if game and game.context.state == GameState.PLAYING:
            try:
                game.context.save_game()
                logger.info("Saved game state before crash")
            except Exception as save_error:
                logger.error(f"Failed to save game after crash: {str(save_error)}")
    finally:
        logger.info("Shutting down game engine")

if __name__ == "__main__":
    main()
