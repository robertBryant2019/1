"""
Metal Slug Roguelike - 合金弹头肉鸽射击游戏
一个横向卷轴Roguelike射击游戏，包含丰富的武器、技能、敌人和关卡系统
"""

import pygame
import random
import math
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# 初始化Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)
CYAN = (0, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# 游戏状态
class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    UPGRADE = 4
    SHOP = 5
    GAME_OVER = 6
    VICTORY = 7

# 武器类型
class WeaponType(Enum):
    PISTOL = "手枪"
    MACHINE_GUN = "机枪"
    SHOTGUN = "霰弹枪"
    ROCKET_LAUNCHER = "火箭筒"
    LASER = "激光枪"
    PLASMA = "等离子炮"
    FLAMETHROWER = "火焰喷射器"
    RAILGUN = "电磁炮"
    GRENADE_LAUNCHER = "榴弹发射器"
    LIGHTNING = "闪电枪"
    ICE_BEAM = "冰冻射线"
    ACID_SPRAYER = "酸液喷射器"

# 敌人类型
class EnemyType(Enum):
    SOLDIER = 1
    HEAVY_SOLDIER = 2
    JETPACK_SOLDIER = 3
    TANK = 4
    HELICOPTER = 5
    DRONE = 6
    MECH = 7
    TURRET = 8
    SNIPER = 9
    KAMIKAZE = 10
    SHIELD_BEARER = 11
    ELITE_SOLDIER = 12
    BOSS_TANK = 13
    BOSS_HELICOPTER = 14
    BOSS_MECH = 15

# 技能类型
class SkillType(Enum):
    DASH = "冲刺"
    DOUBLE_JUMP = "二段跳"
    SHIELD = "护盾"
    TIME_SLOW = "子弹时间"
    GRENADE = "手榴弹"
    AIR_STRIKE = "空袭"
    HEALING = "治疗"
    RAGE_MODE = "狂暴模式"
    TELEPORT = "传送"
    TURRET = "部署炮台"

# 粒子效果
class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime, size=3):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 500 * dt  # 重力
        self.lifetime -= dt

    def draw(self, surface, camera_x):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            color = (*self.color[:3], alpha)
            pygame.draw.circle(surface, self.color,
                             (int(self.x - camera_x), int(self.y)),
                             int(self.size * (self.lifetime / self.max_lifetime)))

    def is_alive(self):
        return self.lifetime > 0

# 子弹类
class Bullet:
    def __init__(self, x, y, vx, vy, damage, color=YELLOW, size=4, piercing=0, explosive=False, explosion_radius=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.color = color
        self.size = size
        self.piercing = piercing
        self.explosive = explosive
        self.explosion_radius = explosion_radius
        self.lifetime = 3.0  # 3秒后消失

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt

    def draw(self, surface, camera_x):
        pygame.draw.circle(surface, self.color,
                         (int(self.x - camera_x), int(self.y)),
                         self.size)

    def is_alive(self):
        return self.lifetime > 0 and 0 < self.y < SCREEN_HEIGHT

# 武器类
@dataclass
class WeaponStats:
    name: str
    damage: int
    fire_rate: float  # 每秒射击次数
    ammo_per_shot: int
    bullet_speed: float
    spread: float  # 散射角度
    bullets_per_shot: int
    bullet_color: Tuple[int, int, int]
    piercing: int
    explosive: bool
    explosion_radius: int
    special_effect: Optional[str] = None

class Weapon:
    def __init__(self, weapon_type: WeaponType):
        self.type = weapon_type
        self.stats = self._get_stats()
        self.ammo = 300
        self.max_ammo = 300
        self.cooldown = 0
        self.level = 1

    def _get_stats(self) -> WeaponStats:
        stats_dict = {
            WeaponType.PISTOL: WeaponStats("手枪", 15, 3, 1, 800, 0, 1, YELLOW, 0, False, 0),
            WeaponType.MACHINE_GUN: WeaponStats("机枪", 10, 10, 1, 1000, 5, 1, ORANGE, 0, False, 0),
            WeaponType.SHOTGUN: WeaponStats("霰弹枪", 8, 1.5, 1, 600, 30, 8, RED, 0, False, 0),
            WeaponType.ROCKET_LAUNCHER: WeaponStats("火箭筒", 100, 0.5, 5, 500, 0, 1, RED, 0, True, 80),
            WeaponType.LASER: WeaponStats("激光枪", 20, 8, 2, 1500, 0, 1, CYAN, 3, False, 0),
            WeaponType.PLASMA: WeaponStats("等离子炮", 35, 2, 3, 700, 0, 1, PURPLE, 1, True, 40),
            WeaponType.FLAMETHROWER: WeaponStats("火焰喷射器", 5, 20, 1, 400, 20, 3, ORANGE, 0, False, 0, "burn"),
            WeaponType.RAILGUN: WeaponStats("电磁炮", 80, 0.8, 5, 2000, 0, 1, CYAN, 999, False, 0),
            WeaponType.GRENADE_LAUNCHER: WeaponStats("榴弹发射器", 60, 1, 4, 600, 10, 1, GREEN, 0, True, 100),
            WeaponType.LIGHTNING: WeaponStats("闪电枪", 25, 4, 2, 1200, 0, 1, YELLOW, 2, False, 0, "chain"),
            WeaponType.ICE_BEAM: WeaponStats("冰冻射线", 15, 6, 2, 800, 5, 1, CYAN, 1, False, 0, "freeze"),
            WeaponType.ACID_SPRAYER: WeaponStats("酸液喷射器", 12, 8, 1, 500, 15, 2, GREEN, 0, False, 0, "poison"),
        }
        return stats_dict.get(self.type, stats_dict[WeaponType.PISTOL])

    def can_fire(self):
        return self.cooldown <= 0 and self.ammo >= self.stats.ammo_per_shot

    def fire(self, x, y, direction) -> List[Bullet]:
        if not self.can_fire():
            return []

        self.ammo -= self.stats.ammo_per_shot
        self.cooldown = 1.0 / self.stats.fire_rate

        bullets = []
        for i in range(self.stats.bullets_per_shot):
            angle = math.radians(self.stats.spread * (i - self.stats.bullets_per_shot / 2) / max(1, self.stats.bullets_per_shot - 1))

            if direction > 0:
                vx = self.stats.bullet_speed * math.cos(angle)
                vy = self.stats.bullet_speed * math.sin(angle)
            else:
                vx = -self.stats.bullet_speed * math.cos(angle)
                vy = self.stats.bullet_speed * math.sin(angle)

            bullets.append(Bullet(
                x, y, vx, vy,
                self.stats.damage * self.level,
                self.stats.bullet_color,
                4,
                self.stats.piercing,
                self.stats.explosive,
                self.stats.explosion_radius
            ))

        return bullets

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt

    def add_ammo(self, amount):
        self.ammo = min(self.ammo + amount, self.max_ammo)

    def upgrade(self):
        self.level += 1
        self.max_ammo += 50
        self.ammo = self.max_ammo

# 技能类
class Skill:
    def __init__(self, skill_type: SkillType):
        self.type = skill_type
        self.cooldown = 0
        self.max_cooldown = self._get_max_cooldown()
        self.duration = 0
        self.level = 1

    def _get_max_cooldown(self) -> float:
        cooldowns = {
            SkillType.DASH: 2.0,
            SkillType.DOUBLE_JUMP: 0.5,
            SkillType.SHIELD: 10.0,
            SkillType.TIME_SLOW: 15.0,
            SkillType.GRENADE: 3.0,
            SkillType.AIR_STRIKE: 20.0,
            SkillType.HEALING: 30.0,
            SkillType.RAGE_MODE: 25.0,
            SkillType.TELEPORT: 5.0,
            SkillType.TURRET: 15.0,
        }
        return cooldowns.get(self.type, 5.0)

    def can_use(self):
        return self.cooldown <= 0

    def use(self):
        if self.can_use():
            self.cooldown = self.max_cooldown
            return True
        return False

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.duration > 0:
            self.duration -= dt

# 玩家类
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 60
        self.vx = 0
        self.vy = 0
        self.speed = 300
        self.jump_force = 500
        self.on_ground = False
        self.direction = 1  # 1=右, -1=左

        # 属性
        self.max_health = 100
        self.health = 100
        self.armor = 0
        self.coins = 0
        self.score = 0
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 100

        # 武器和技能
        self.weapons = [Weapon(WeaponType.PISTOL)]
        self.current_weapon_index = 0
        self.skills = []

        # 状态
        self.invincible = 0
        self.shield_active = False
        self.time_slow_active = False
        self.rage_mode_active = False
        self.double_jump_available = False
        self.dash_cooldown = 0

        # 统计
        self.enemies_killed = 0
        self.shots_fired = 0
        self.damage_dealt = 0

    def add_weapon(self, weapon_type: WeaponType):
        # 检查是否已有该武器
        for weapon in self.weapons:
            if weapon.type == weapon_type:
                weapon.upgrade()
                return
        self.weapons.append(Weapon(weapon_type))

    def add_skill(self, skill_type: SkillType):
        # 检查是否已有该技能
        for skill in self.skills:
            if skill.type == skill_type:
                skill.level += 1
                skill.max_cooldown *= 0.9  # 减少冷却时间
                return
        self.skills.append(Skill(skill_type))

    def get_current_weapon(self) -> Weapon:
        return self.weapons[self.current_weapon_index]

    def switch_weapon(self, direction):
        self.current_weapon_index = (self.current_weapon_index + direction) % len(self.weapons)

    def move(self, dx, dy):
        self.vx = dx * self.speed
        if dy < 0 and self.on_ground:
            self.vy = dy * self.jump_force
            self.on_ground = False

    def fire(self) -> List[Bullet]:
        weapon = self.get_current_weapon()
        bullets = weapon.fire(
            self.x + self.width // 2 + self.direction * 20,
            self.y + self.height // 2,
            self.direction
        )
        if bullets:
            self.shots_fired += len(bullets)
        return bullets

    def use_skill(self, skill_type: SkillType):
        for skill in self.skills:
            if skill.type == skill_type:
                return skill.use()
        return False

    def take_damage(self, damage):
        if self.invincible > 0 or self.shield_active:
            return False

        actual_damage = max(1, damage - self.armor)
        self.health -= actual_damage
        self.invincible = 1.0  # 1秒无敌时间

        if self.health <= 0:
            return True  # 玩家死亡
        return False

    def heal(self, amount):
        self.health = min(self.health + amount, self.max_health)

    def add_exp(self, amount):
        self.exp += amount
        self.score += amount

        while self.exp >= self.exp_to_next_level:
            self.exp -= self.exp_to_next_level
            self.level_up()

    def level_up(self):
        self.level += 1
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
        self.max_health += 10
        self.health = self.max_health
        return True  # 触发升级界面

    def update(self, dt, platforms):
        # 重力
        if not self.on_ground:
            self.vy += 1500 * dt

        # 移动
        self.x += self.vx * dt
        self.y += self.vy * dt

        # 碰撞检测
        self.on_ground = False
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        for platform in platforms:
            if player_rect.colliderect(platform):
                # 从上方碰撞
                if self.vy > 0 and player_rect.bottom > platform.top and player_rect.bottom < platform.top + 20:
                    self.y = platform.top - self.height
                    self.vy = 0
                    self.on_ground = True
                    self.double_jump_available = True

        # 边界检查
        if self.y > SCREEN_HEIGHT:
            self.take_damage(999)  # 掉落死亡

        if self.y + self.height > SCREEN_HEIGHT - 100:
            self.y = SCREEN_HEIGHT - 100 - self.height
            self.vy = 0
            self.on_ground = True
            self.double_jump_available = True

        # 更新状态
        if self.invincible > 0:
            self.invincible -= dt

        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt

        # 更新武器
        for weapon in self.weapons:
            weapon.update(dt)

        # 更新技能
        for skill in self.skills:
            skill.update(dt)

    def draw(self, surface, camera_x):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y)

        # 无敌闪烁
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return

        # 绘制玩家
        color = BLUE
        if self.rage_mode_active:
            color = RED
        elif self.shield_active:
            color = CYAN

        pygame.draw.rect(surface, color, (screen_x, screen_y, self.width, self.height))

        # 绘制方向指示
        if self.direction > 0:
            pygame.draw.polygon(surface, YELLOW, [
                (screen_x + self.width, screen_y + self.height // 2),
                (screen_x + self.width - 10, screen_y + self.height // 2 - 10),
                (screen_x + self.width - 10, screen_y + self.height // 2 + 10)
            ])
        else:
            pygame.draw.polygon(surface, YELLOW, [
                (screen_x, screen_y + self.height // 2),
                (screen_x + 10, screen_y + self.height // 2 - 10),
                (screen_x + 10, screen_y + self.height // 2 + 10)
            ])

        # 绘制血条
        health_bar_width = self.width
        health_bar_height = 5
        health_percentage = self.health / self.max_health

        pygame.draw.rect(surface, RED,
                        (screen_x, screen_y - 10, health_bar_width, health_bar_height))
        pygame.draw.rect(surface, GREEN,
                        (screen_x, screen_y - 10, health_bar_width * health_percentage, health_bar_height))

# 敌人基类
class Enemy:
    def __init__(self, x, y, enemy_type: EnemyType):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.width = 40
        self.height = 50
        self.vx = 0
        self.vy = 0
        self.direction = -1

        # 根据类型设置属性
        self._set_stats()

        self.health = self.max_health
        self.shoot_cooldown = 0
        self.ai_timer = 0
        self.state = "idle"
        self.target_x = x

    def _set_stats(self):
        stats = {
            EnemyType.SOLDIER: (30, 100, 10, 2.0, 15),
            EnemyType.HEAVY_SOLDIER: (50, 150, 15, 3.0, 25),
            EnemyType.JETPACK_SOLDIER: (40, 120, 12, 2.5, 20),
            EnemyType.TANK: (100, 300, 30, 5.0, 50),
            EnemyType.HELICOPTER: (60, 200, 20, 3.0, 40),
            EnemyType.DRONE: (30, 80, 8, 1.5, 15),
            EnemyType.MECH: (120, 400, 40, 4.0, 60),
            EnemyType.TURRET: (80, 250, 25, 2.0, 35),
            EnemyType.SNIPER: (50, 100, 50, 3.0, 30),
            EnemyType.KAMIKAZE: (40, 60, 0, 0, 20),
            EnemyType.SHIELD_BEARER: (70, 200, 15, 3.0, 30),
            EnemyType.ELITE_SOLDIER: (80, 180, 20, 2.0, 40),
            EnemyType.BOSS_TANK: (200, 1000, 50, 8.0, 200),
            EnemyType.BOSS_HELICOPTER: (150, 800, 40, 6.0, 150),
            EnemyType.BOSS_MECH: (250, 1500, 60, 10.0, 250),
        }

        data = stats.get(self.type, (30, 100, 10, 2.0, 15))
        self.max_health = data[0]
        self.speed = data[1]
        self.damage = data[2]
        self.fire_rate = data[3]
        self.exp_value = data[4]

        # 特殊尺寸
        if self.type in [EnemyType.TANK, EnemyType.BOSS_TANK]:
            self.width, self.height = 80, 60
        elif self.type in [EnemyType.MECH, EnemyType.BOSS_MECH]:
            self.width, self.height = 100, 120
        elif self.type in [EnemyType.HELICOPTER, EnemyType.BOSS_HELICOPTER]:
            self.width, self.height = 60, 40
        elif self.type == EnemyType.DRONE:
            self.width, self.height = 30, 30

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0

    def can_shoot(self):
        return self.shoot_cooldown <= 0 and self.fire_rate > 0

    def shoot(self, player_x, player_y) -> Optional[Bullet]:
        if not self.can_shoot():
            return None

        self.shoot_cooldown = 1.0 / self.fire_rate

        # 计算射击方向
        dx = player_x - self.x
        dy = player_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance == 0:
            return None

        speed = 600
        vx = (dx / distance) * speed
        vy = (dy / distance) * speed

        return Bullet(self.x + self.width // 2, self.y + self.height // 2,
                     vx, vy, self.damage, RED, 5)

    def update(self, dt, player, platforms):
        self.shoot_cooldown -= dt
        self.ai_timer += dt

        # AI行为
        if self.type in [EnemyType.SOLDIER, EnemyType.HEAVY_SOLDIER, EnemyType.ELITE_SOLDIER]:
            self._soldier_ai(dt, player)
        elif self.type == EnemyType.JETPACK_SOLDIER:
            self._jetpack_ai(dt, player)
        elif self.type in [EnemyType.TANK, EnemyType.BOSS_TANK]:
            self._tank_ai(dt, player)
        elif self.type in [EnemyType.HELICOPTER, EnemyType.BOSS_HELICOPTER, EnemyType.DRONE]:
            self._flying_ai(dt, player)
        elif self.type == EnemyType.TURRET:
            self._turret_ai(dt, player)
        elif self.type == EnemyType.KAMIKAZE:
            self._kamikaze_ai(dt, player)

        # 物理更新
        self.x += self.vx * dt
        self.y += self.vy * dt

        # 边界检查
        if self.y > SCREEN_HEIGHT:
            self.health = 0

    def _soldier_ai(self, dt, player):
        dx = player.x - self.x

        if abs(dx) > 400:
            # 靠近玩家
            self.vx = self.speed if dx > 0 else -self.speed
            self.direction = 1 if dx > 0 else -1
        elif abs(dx) > 200:
            # 保持距离并射击
            self.vx = 0
        else:
            # 后退
            self.vx = -self.speed if dx > 0 else self.speed

        # 重力
        self.vy += 1000 * dt

    def _jetpack_ai(self, dt, player):
        dx = player.x - self.x
        dy = player.y - self.y

        # 飞行移动
        if abs(dx) > 300:
            self.vx = self.speed * 0.7 * (1 if dx > 0 else -1)
        else:
            self.vx = 0

        if abs(dy) > 100:
            self.vy = self.speed * 0.5 * (1 if dy > 0 else -1)
        else:
            self.vy = 0

    def _tank_ai(self, dt, player):
        dx = player.x - self.x

        if abs(dx) > 500:
            self.vx = self.speed * 0.5 * (1 if dx > 0 else -1)
        else:
            self.vx = 0

        self.vy += 1000 * dt

    def _flying_ai(self, dt, player):
        dx = player.x - self.x
        dy = player.y - self.y

        # 盘旋在玩家周围
        if abs(dx) > 400:
            self.vx = self.speed * 0.8 * (1 if dx > 0 else -1)
        else:
            self.vx = math.sin(self.ai_timer * 2) * self.speed * 0.3

        target_y = player.y - 200
        if abs(self.y - target_y) > 50:
            self.vy = self.speed * 0.5 * (1 if target_y > self.y else -1)
        else:
            self.vy = math.cos(self.ai_timer * 2) * self.speed * 0.2

    def _turret_ai(self, dt, player):
        self.vx = 0
        self.vy = 0

    def _kamikaze_ai(self, dt, player):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance > 0:
            self.vx = (dx / distance) * self.speed * 1.5
            self.vy = (dy / distance) * self.speed * 1.5

    def draw(self, surface, camera_x):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y)

        # 选择颜色
        color = RED
        if self.type in [EnemyType.HEAVY_SOLDIER, EnemyType.TANK]:
            color = DARK_GRAY
        elif self.type in [EnemyType.JETPACK_SOLDIER, EnemyType.HELICOPTER]:
            color = ORANGE
        elif self.type == EnemyType.ELITE_SOLDIER:
            color = PURPLE
        elif "BOSS" in self.type.name:
            color = (128, 0, 128)

        # 绘制敌人
        pygame.draw.rect(surface, color, (screen_x, screen_y, self.width, self.height))

        # 绘制血条
        health_bar_width = self.width
        health_bar_height = 4
        health_percentage = self.health / self.max_health

        pygame.draw.rect(surface, DARK_GRAY,
                        (screen_x, screen_y - 8, health_bar_width, health_bar_height))
        pygame.draw.rect(surface, RED,
                        (screen_x, screen_y - 8, health_bar_width * health_percentage, health_bar_height))

# 道具类
class Pickup:
    def __init__(self, x, y, pickup_type):
        self.x = x
        self.y = y
        self.type = pickup_type  # "health", "ammo", "coin", "weapon", "skill"
        self.width = 30
        self.height = 30
        self.lifetime = 10.0
        self.data = None  # 额外数据（武器类型等）

    def update(self, dt):
        self.lifetime -= dt
        self.y += math.sin(pygame.time.get_ticks() * 0.005) * 0.5

    def is_alive(self):
        return self.lifetime > 0

    def draw(self, surface, camera_x):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y)

        color = GREEN
        if self.type == "health":
            color = RED
        elif self.type == "ammo":
            color = YELLOW
        elif self.type == "coin":
            color = (255, 215, 0)
        elif self.type == "weapon":
            color = ORANGE
        elif self.type == "skill":
            color = PURPLE

        pygame.draw.rect(surface, color, (screen_x, screen_y, self.width, self.height))
        pygame.draw.rect(surface, WHITE, (screen_x, screen_y, self.width, self.height), 2)

# 关卡生成器
class LevelGenerator:
    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.section_length = 2000
        self.current_section = 0

    def generate_platforms(self, start_x, end_x) -> List[pygame.Rect]:
        platforms = []

        # 地面
        platforms.append(pygame.Rect(start_x, SCREEN_HEIGHT - 100, end_x - start_x, 100))

        # 随机平台
        num_platforms = 5 + self.difficulty
        for i in range(num_platforms):
            x = start_x + random.randint(200, end_x - start_x - 400)
            y = random.randint(200, SCREEN_HEIGHT - 250)
            width = random.randint(150, 300)
            platforms.append(pygame.Rect(x, y, width, 20))

        return platforms

    def generate_enemies(self, start_x, end_x, is_boss_section=False) -> List[Enemy]:
        enemies = []

        if is_boss_section:
            # Boss战
            boss_types = [EnemyType.BOSS_TANK, EnemyType.BOSS_HELICOPTER, EnemyType.BOSS_MECH]
            boss_type = random.choice(boss_types)
            boss_x = start_x + (end_x - start_x) // 2
            boss_y = SCREEN_HEIGHT - 300
            enemies.append(Enemy(boss_x, boss_y, boss_type))

            # 添加一些小怪
            for i in range(3 + self.difficulty // 2):
                x = start_x + random.randint(300, end_x - start_x - 300)
                y = SCREEN_HEIGHT - 200
                enemy_type = random.choice([EnemyType.SOLDIER, EnemyType.DRONE, EnemyType.JETPACK_SOLDIER])
                enemies.append(Enemy(x, y, enemy_type))
        else:
            # 普通敌人
            num_enemies = 5 + self.difficulty * 2

            enemy_types = [
                EnemyType.SOLDIER, EnemyType.SOLDIER,  # 更多普通士兵
                EnemyType.HEAVY_SOLDIER, EnemyType.JETPACK_SOLDIER,
                EnemyType.DRONE, EnemyType.TURRET,
                EnemyType.KAMIKAZE, EnemyType.SNIPER
            ]

            if self.difficulty >= 3:
                enemy_types.extend([EnemyType.ELITE_SOLDIER, EnemyType.MECH, EnemyType.TANK])

            for i in range(num_enemies):
                x = start_x + random.randint(300, end_x - start_x - 300)

                enemy_type = random.choice(enemy_types)

                if enemy_type in [EnemyType.HELICOPTER, EnemyType.DRONE]:
                    y = random.randint(100, 300)
                elif enemy_type == EnemyType.TURRET:
                    y = SCREEN_HEIGHT - 200
                else:
                    y = SCREEN_HEIGHT - 200

                enemies.append(Enemy(x, y, enemy_type))

        return enemies

    def next_section(self, is_boss=False):
        self.current_section += 1
        start_x = self.current_section * self.section_length
        end_x = start_x + self.section_length

        platforms = self.generate_platforms(start_x, end_x)
        enemies = self.generate_enemies(start_x, end_x, is_boss)

        return platforms, enemies

# 主游戏类
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Metal Slug Roguelike - 合金弹头肉鸽")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU

        # 字体
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 72)

        # 游戏对象
        self.player = None
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.particles = []
        self.pickups = []
        self.platforms = []

        # 关卡
        self.level_generator = None
        self.camera_x = 0
        self.current_wave = 1
        self.enemies_killed_this_wave = 0
        self.wave_complete = False

        # 永久升级
        self.permanent_upgrades = {
            "max_health": 0,
            "damage": 0,
            "fire_rate": 0,
            "speed": 0,
            "armor": 0,
            "luck": 0,
        }

        # 统计
        self.total_runs = 0
        self.best_score = 0
        self.total_kills = 0

        self._load_save_data()

    def _load_save_data(self):
        """加载存档数据"""
        save_file = "metal_slug_save.json"
        if os.path.exists(save_file):
            try:
                with open(save_file, 'r') as f:
                    data = json.load(f)
                    self.permanent_upgrades = data.get("upgrades", self.permanent_upgrades)
                    self.total_runs = data.get("total_runs", 0)
                    self.best_score = data.get("best_score", 0)
                    self.total_kills = data.get("total_kills", 0)
            except:
                pass

    def _save_data(self):
        """保存数据"""
        save_file = "metal_slug_save.json"
        data = {
            "upgrades": self.permanent_upgrades,
            "total_runs": self.total_runs,
            "best_score": self.best_score,
            "total_kills": self.total_kills,
        }
        with open(save_file, 'w') as f:
            json.dump(data, f)

    def new_game(self):
        """开始新游戏"""
        self.player = Player(100, SCREEN_HEIGHT - 300)

        # 应用永久升级
        self.player.max_health += self.permanent_upgrades["max_health"] * 10
        self.player.health = self.player.max_health
        self.player.armor = self.permanent_upgrades["armor"] * 5
        self.player.speed += self.permanent_upgrades["speed"] * 20

        # 初始武器和技能
        self.player.add_skill(SkillType.DASH)
        self.player.add_skill(SkillType.GRENADE)

        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.particles = []
        self.pickups = []
        self.platforms = []

        self.level_generator = LevelGenerator(1)
        self.camera_x = 0
        self.current_wave = 1
        self.enemies_killed_this_wave = 0
        self.wave_complete = False

        # 生成初始关卡
        platforms, enemies = self.level_generator.next_section(False)
        self.platforms.extend(platforms)
        self.enemies.extend(enemies)

        self.state = GameState.PLAYING
        self.total_runs += 1

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        self.new_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                    elif event.key == pygame.K_q:
                        self.player.switch_weapon(-1)
                    elif event.key == pygame.K_e:
                        self.player.switch_weapon(1)

                    # 技能快捷键
                    elif event.key == pygame.K_1:
                        if self.player.use_skill(SkillType.DASH):
                            self.player.dash_cooldown = 0.3
                            self.player.vx = self.player.direction * 800
                    elif event.key == pygame.K_2:
                        if self.player.use_skill(SkillType.GRENADE):
                            self._throw_grenade()
                    elif event.key == pygame.K_3:
                        if self.player.use_skill(SkillType.SHIELD):
                            self.player.shield_active = True
                    elif event.key == pygame.K_4:
                        if self.player.use_skill(SkillType.HEALING):
                            self.player.heal(50)

                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_q:
                        self.state = GameState.MENU

                elif self.state == GameState.UPGRADE:
                    if event.key == pygame.K_1:
                        self._choose_upgrade(0)
                    elif event.key == pygame.K_2:
                        self._choose_upgrade(1)
                    elif event.key == pygame.K_3:
                        self._choose_upgrade(2)

                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.MENU

    def _throw_grenade(self):
        """投掷手榴弹"""
        grenade_x = self.player.x + self.player.width // 2
        grenade_y = self.player.y

        vx = self.player.direction * 400
        vy = -300

        grenade = Bullet(grenade_x, grenade_y, vx, vy, 80, ORANGE, 8, 0, True, 120)
        grenade.vy = vy  # 手榴弹有初始向上速度
        self.bullets.append(grenade)

    def _choose_upgrade(self, choice):
        """选择升级"""
        if choice == 0:
            # 随机武器
            weapon_types = list(WeaponType)
            new_weapon = random.choice(weapon_types)
            self.player.add_weapon(new_weapon)
        elif choice == 1:
            # 随机技能
            skill_types = list(SkillType)
            new_skill = random.choice(skill_types)
            self.player.add_skill(new_skill)
        elif choice == 2:
            # 属性提升
            self.player.max_health += 20
            self.player.health = self.player.max_health
            self.player.armor += 5

        self.state = GameState.PLAYING

    def update(self, dt):
        """更新游戏逻辑"""
        if self.state != GameState.PLAYING:
            return

        # 更新玩家
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
            self.player.direction = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
            self.player.direction = 1
        if keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]:
            dy = -1

        self.player.move(dx, dy)
        self.player.update(dt, self.platforms)

        # 射击
        if keys[pygame.K_j] or pygame.mouse.get_pressed()[0]:
            new_bullets = self.player.fire()
            self.bullets.extend(new_bullets)

        # 更新相机
        target_camera_x = self.player.x - SCREEN_WIDTH // 3
        self.camera_x += (target_camera_x - self.camera_x) * 0.1
        self.camera_x = max(0, self.camera_x)

        # 更新敌人
        for enemy in self.enemies[:]:
            enemy.update(dt, self.player, self.platforms)

            # 敌人射击
            if enemy.can_shoot() and abs(enemy.x - self.player.x) < 600:
                bullet = enemy.shoot(self.player.x + self.player.width // 2,
                                   self.player.y + self.player.height // 2)
                if bullet:
                    self.enemy_bullets.append(bullet)

            # 自杀式攻击检测
            if enemy.type == EnemyType.KAMIKAZE:
                player_rect = pygame.Rect(self.player.x, self.player.y,
                                         self.player.width, self.player.height)
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)

                if player_rect.colliderect(enemy_rect):
                    self.player.take_damage(50)
                    enemy.health = 0
                    self._create_explosion(enemy.x, enemy.y, 100)

        # 更新子弹
        for bullet in self.bullets[:]:
            bullet.update(dt)

            if not bullet.is_alive():
                self.bullets.remove(bullet)
                continue

            bullet_rect = pygame.Rect(bullet.x - bullet.size, bullet.y - bullet.size,
                                     bullet.size * 2, bullet.size * 2)

            # 子弹与敌人碰撞
            for enemy in self.enemies[:]:
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)

                if bullet_rect.colliderect(enemy_rect):
                    if enemy.take_damage(bullet.damage):
                        self._on_enemy_killed(enemy)
                        self.enemies.remove(enemy)

                    self.player.damage_dealt += bullet.damage

                    # 爆炸效果
                    if bullet.explosive:
                        self._create_explosion(bullet.x, bullet.y, bullet.explosion_radius)
                        self._damage_in_radius(bullet.x, bullet.y, bullet.explosion_radius, bullet.damage)

                    # 穿透
                    if bullet.piercing > 0:
                        bullet.piercing -= 1
                    else:
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                    break

        # 更新敌人子弹
        for bullet in self.enemy_bullets[:]:
            bullet.update(dt)

            if not bullet.is_alive():
                self.enemy_bullets.remove(bullet)
                continue

            bullet_rect = pygame.Rect(bullet.x - bullet.size, bullet.y - bullet.size,
                                     bullet.size * 2, bullet.size * 2)
            player_rect = pygame.Rect(self.player.x, self.player.y,
                                     self.player.width, self.player.height)

            if bullet_rect.colliderect(player_rect):
                if self.player.take_damage(bullet.damage):
                    self._game_over()
                if bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(bullet)

        # 更新粒子
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.is_alive():
                self.particles.remove(particle)

        # 更新道具
        for pickup in self.pickups[:]:
            pickup.update(dt)

            if not pickup.is_alive():
                self.pickups.remove(pickup)
                continue

            pickup_rect = pygame.Rect(pickup.x, pickup.y, pickup.width, pickup.height)
            player_rect = pygame.Rect(self.player.x, self.player.y,
                                     self.player.width, self.player.height)

            if pickup_rect.colliderect(player_rect):
                self._collect_pickup(pickup)
                self.pickups.remove(pickup)

        # 检查关卡进度
        if len(self.enemies) == 0 and not self.wave_complete:
            self.wave_complete = True
            self.current_wave += 1

            # 每3波一个Boss
            is_boss_wave = self.current_wave % 3 == 0

            platforms, enemies = self.level_generator.next_section(is_boss_wave)
            self.platforms.extend(platforms)
            self.enemies.extend(enemies)

            # 升级难度
            if is_boss_wave:
                self.level_generator.difficulty += 1

            self.wave_complete = False

            # 显示升级选项
            if self.current_wave % 2 == 0:
                self.state = GameState.UPGRADE

        # 生成新关卡内容
        if self.player.x > self.level_generator.current_section * self.level_generator.section_length - 500:
            platforms, enemies = self.level_generator.next_section(False)
            self.platforms.extend(platforms)
            self.enemies.extend(enemies)

    def _create_explosion(self, x, y, radius):
        """创建爆炸效果"""
        for i in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 300)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice([RED, ORANGE, YELLOW])
            self.particles.append(Particle(x, y, vx, vy, color, 0.5, random.randint(3, 8)))

    def _damage_in_radius(self, x, y, radius, damage):
        """范围伤害"""
        for enemy in self.enemies[:]:
            dx = enemy.x + enemy.width // 2 - x
            dy = enemy.y + enemy.height // 2 - y
            distance = math.sqrt(dx*dx + dy*dy)

            if distance < radius:
                actual_damage = int(damage * (1 - distance / radius))
                if enemy.take_damage(actual_damage):
                    self._on_enemy_killed(enemy)
                    self.enemies.remove(enemy)

    def _on_enemy_killed(self, enemy):
        """敌人被击杀"""
        self.player.enemies_killed += 1
        self.player.add_exp(enemy.exp_value)
        self.enemies_killed_this_wave += 1
        self.total_kills += 1

        # 掉落道具
        drop_chance = random.random()

        if drop_chance < 0.3:  # 30%掉落金币
            pickup = Pickup(enemy.x, enemy.y, "coin")
            self.pickups.append(pickup)
        elif drop_chance < 0.5:  # 20%掉落弹药
            pickup = Pickup(enemy.x, enemy.y, "ammo")
            self.pickups.append(pickup)
        elif drop_chance < 0.6:  # 10%掉落血包
            pickup = Pickup(enemy.x, enemy.y, "health")
            self.pickups.append(pickup)
        elif drop_chance < 0.65:  # 5%掉落武器
            pickup = Pickup(enemy.x, enemy.y, "weapon")
            weapon_types = list(WeaponType)
            pickup.data = random.choice(weapon_types)
            self.pickups.append(pickup)

        # 死亡粒子效果
        for i in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(enemy.x, enemy.y, vx, vy, RED, 0.5))

    def _collect_pickup(self, pickup):
        """收集道具"""
        if pickup.type == "health":
            self.player.heal(30)
        elif pickup.type == "ammo":
            self.player.get_current_weapon().add_ammo(100)
        elif pickup.type == "coin":
            self.player.coins += 10
        elif pickup.type == "weapon" and pickup.data:
            self.player.add_weapon(pickup.data)
        elif pickup.type == "skill" and pickup.data:
            self.player.add_skill(pickup.data)

    def _game_over(self):
        """游戏结束"""
        self.state = GameState.GAME_OVER

        if self.player.score > self.best_score:
            self.best_score = self.player.score

        self._save_data()

    def draw(self):
        """绘制游戏"""
        self.screen.fill(BLACK)

        if self.state == GameState.MENU:
            self._draw_menu()
        elif self.state == GameState.PLAYING:
            self._draw_game()
        elif self.state == GameState.PAUSED:
            self._draw_game()
            self._draw_pause()
        elif self.state == GameState.UPGRADE:
            self._draw_game()
            self._draw_upgrade()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_menu(self):
        """绘制主菜单"""
        title = self.font_large.render("Metal Slug Roguelike", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        subtitle = self.font_medium.render("合金弹头肉鸽射击", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)

        instructions = [
            "SPACE - 开始游戏",
            "",
            "操作说明:",
            "WASD/方向键 - 移动",
            "J/鼠标左键 - 射击",
            "Q/E - 切换武器",
            "1-4 - 使用技能",
            "",
            f"最佳分数: {self.best_score}",
            f"总游戏次数: {self.total_runs}",
            f"总击杀数: {self.total_kills}",
        ]

        y = 300
        for line in instructions:
            text = self.font_small.render(line, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 35

    def _draw_game(self):
        """绘制游戏画面"""
        # 绘制平台
        for platform in self.platforms:
            if platform.x + platform.width > self.camera_x and platform.x < self.camera_x + SCREEN_WIDTH:
                pygame.draw.rect(self.screen, GRAY,
                               (platform.x - self.camera_x, platform.y,
                                platform.width, platform.height))

        # 绘制道具
        for pickup in self.pickups:
            if pickup.x > self.camera_x - 50 and pickup.x < self.camera_x + SCREEN_WIDTH + 50:
                pickup.draw(self.screen, self.camera_x)

        # 绘制敌人
        for enemy in self.enemies:
            if enemy.x > self.camera_x - 200 and enemy.x < self.camera_x + SCREEN_WIDTH + 200:
                enemy.draw(self.screen, self.camera_x)

        # 绘制子弹
        for bullet in self.bullets + self.enemy_bullets:
            if bullet.x > self.camera_x - 50 and bullet.x < self.camera_x + SCREEN_WIDTH + 50:
                bullet.draw(self.screen, self.camera_x)

        # 绘制粒子
        for particle in self.particles:
            particle.draw(self.screen, self.camera_x)

        # 绘制玩家
        self.player.draw(self.screen, self.camera_x)

        # 绘制UI
        self._draw_ui()

    def _draw_ui(self):
        """绘制UI"""
        # 血条
        health_text = self.font_small.render(f"HP: {self.player.health}/{self.player.max_health}",
                                             True, WHITE)
        self.screen.blit(health_text, (10, 10))

        health_bar_width = 200
        health_bar_height = 20
        health_percentage = self.player.health / self.player.max_health

        pygame.draw.rect(self.screen, DARK_GRAY, (10, 35, health_bar_width, health_bar_height))
        pygame.draw.rect(self.screen, RED, (10, 35, health_bar_width * health_percentage, health_bar_height))
        pygame.draw.rect(self.screen, WHITE, (10, 35, health_bar_width, health_bar_height), 2)

        # 武器信息
        weapon = self.player.get_current_weapon()
        weapon_text = self.font_small.render(
            f"武器: {weapon.stats.name} Lv.{weapon.level}", True, YELLOW)
        self.screen.blit(weapon_text, (10, 65))

        ammo_text = self.font_small.render(f"弹药: {weapon.ammo}/{weapon.max_ammo}", True, WHITE)
        self.screen.blit(ammo_text, (10, 90))

        # 玩家信息
        level_text = self.font_small.render(f"等级: {self.player.level}", True, WHITE)
        self.screen.blit(level_text, (10, 120))

        exp_text = self.font_small.render(
            f"经验: {self.player.exp}/{self.player.exp_to_next_level}", True, WHITE)
        self.screen.blit(exp_text, (10, 145))

        score_text = self.font_small.render(f"分数: {self.player.score}", True, YELLOW)
        self.screen.blit(score_text, (10, 170))

        coins_text = self.font_small.render(f"金币: {self.player.coins}", True, (255, 215, 0))
        self.screen.blit(coins_text, (10, 195))

        # 关卡信息
        wave_text = self.font_medium.render(f"Wave {self.current_wave}", True, WHITE)
        wave_rect = wave_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
        self.screen.blit(wave_text, wave_rect)

        # 敌人数量
        enemy_text = self.font_small.render(f"敌人: {len(self.enemies)}", True, RED)
        self.screen.blit(enemy_text, (SCREEN_WIDTH - 150, 10))

        # 技能CD
        y = SCREEN_HEIGHT - 150
        for skill in self.player.skills:
            cd_text = f"{skill.type.value}: "
            if skill.cooldown > 0:
                cd_text += f"{skill.cooldown:.1f}s"
            else:
                cd_text += "Ready"

            color = GREEN if skill.cooldown <= 0 else GRAY
            text = self.font_small.render(cd_text, True, color)
            self.screen.blit(text, (SCREEN_WIDTH - 200, y))
            y += 30

    def _draw_pause(self):
        """绘制暂停界面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render("PAUSED", True, YELLOW)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(pause_text, pause_rect)

        continue_text = self.font_medium.render("ESC - 继续", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(continue_text, continue_rect)

        quit_text = self.font_medium.render("Q - 退出到菜单", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(quit_text, quit_rect)

    def _draw_upgrade(self):
        """绘制升级界面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("LEVEL UP!", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        subtitle = self.font_medium.render("选择一个升级 (按 1/2/3)", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 170))
        self.screen.blit(subtitle, subtitle_rect)

        # 升级选项
        options = [
            ("1 - 随机武器", "获得或升级一个随机武器", ORANGE),
            ("2 - 随机技能", "获得或升级一个随机技能", PURPLE),
            ("3 - 属性提升", "+20 最大生命值, +5 护甲", GREEN),
        ]

        y = 250
        for i, (title, desc, color) in enumerate(options):
            # 绘制选项框
            box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, y, 600, 100)
            pygame.draw.rect(self.screen, color, box_rect, 3)

            title_text = self.font_medium.render(title, True, color)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, y + 30))
            self.screen.blit(title_text, title_rect)

            desc_text = self.font_small.render(desc, True, WHITE)
            desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH // 2, y + 65))
            self.screen.blit(desc_text, desc_rect)

            y += 130

    def _draw_game_over(self):
        """绘制游戏结束界面"""
        self.screen.fill(BLACK)

        game_over_text = self.font_large.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(game_over_text, game_over_rect)

        stats = [
            f"最终分数: {self.player.score}",
            f"击杀数: {self.player.enemies_killed}",
            f"到达关卡: {self.current_wave}",
            f"最高等级: {self.player.level}",
            f"造成伤害: {self.player.damage_dealt}",
            f"射击次数: {self.player.shots_fired}",
            "",
            f"历史最佳: {self.best_score}",
            "",
            "SPACE - 返回菜单",
        ]

        y = 250
        for line in stats:
            color = YELLOW if "最终分数" in line or "历史最佳" in line else WHITE
            text = self.font_medium.render(line, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 40

    def run(self):
        """主游戏循环"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
