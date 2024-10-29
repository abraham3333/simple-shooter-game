
import pygame
import random
import math
from pygame import gfxdraw
import time

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WIDTH = 1200
HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Advanced Space Shooter")
clock = pygame.time.Clock()

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def add_particle(self, x, y, color, size, lifetime):
        self.particles.append({
            'x': x,
            'y': y,
            'dx': random.uniform(-2, 2),
            'dy': random.uniform(-2, 2),
            'color': color,
            'size': size,
            'lifetime': lifetime,
            'age': 0
        })
        
    def update(self):
        for particle in self.particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['age'] += 1
            particle['size'] *= 0.95
            
            if particle['age'] >= particle['lifetime']:
                self.particles.remove(particle)
                
    def draw(self, surface):
        for particle in self.particles:
            alpha = 255 * (1 - particle['age'] / particle['lifetime'])
            color = (*particle['color'], int(alpha))
            pos = (int(particle['x']), int(particle['y']))
            pygame.draw.circle(surface, color, pos, int(particle['size']))

class Weapon:
    def __init__(self, damage, fire_rate, bullet_speed, bullet_size, color):
        self.damage = damage
        self.fire_rate = fire_rate
        self.bullet_speed = bullet_speed
        self.bullet_size = bullet_size
        self.color = color
        self.last_shot = 0
        
    def can_fire(self):
        now = time.time()
        if now - self.last_shot >= 1.0 / self.fire_rate:
            self.last_shot = now
            return True
        return False

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.speed = 8
        self.health = 100
        self.score = 0
        self.size = 40
        self.weapons = [
            Weapon(10, 2, 15, 5, BLUE),    # Basic weapon
            Weapon(20, 1, 20, 8, GREEN),   # Power weapon
            Weapon(5, 5, 12, 3, YELLOW)    # Rapid weapon
        ]
        self.current_weapon = 0
        self.shield_active = False
        self.shield_time = 0
        
    def move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.x > self.size:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < WIDTH - self.size:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > self.size:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < HEIGHT - self.size:
            self.y += self.speed
            
    def draw(self, surface):
        # Draw ship body
        points = [
            (self.x, self.y - self.size),
            (self.x - self.size, self.y + self.size),
            (self.x + self.size, self.y + self.size)
        ]
        pygame.draw.polygon(surface, BLUE, points)
        
        # Draw engine flames
        flame_points = [
            (self.x - 20, self.y + self.size),
            (self.x, self.y + self.size + 20),
            (self.x + 20, self.y + self.size)
        ]
        pygame.draw.polygon(surface, RED, flame_points)
        
        # Draw shield if active
        if self.shield_active:
            pygame.draw.circle(surface, (100, 200, 255, 128), 
                             (int(self.x), int(self.y)), 
                             self.size + 10, 2)

class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.type = enemy_type
        if enemy_type == 'basic':
            self.size = 30
            self.health = 20
            self.speed = 3
            self.color = RED
        elif enemy_type == 'elite':
            self.size = 40
            self.health = 40
            self.speed = 2
            self.color = PURPLE
        self.original_y = y
        self.move_time = 0
        
    def move(self):
        self.move_time += 0.05
        self.x += math.sin(self.move_time) * self.speed
        self.y = self.original_y + math.cos(self.move_time) * 20
        
    def draw(self, surface):
        if self.type == 'basic':
            pygame.draw.polygon(surface, self.color, [
                (self.x, self.y - self.size),
                (self.x - self.size, self.y + self.size),
                (self.x + self.size, self.y + self.size)
            ])
        else:  # elite
            pygame.draw.circle(surface, self.color, 
                             (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(surface, WHITE, 
                             (int(self.x), int(self.y)), self.size - 5, 2)

class Bullet:
    def __init__(self, x, y, weapon):
        self.x = x
        self.y = y
        self.weapon = weapon
        self.active = True
        
    def move(self):
        self.y -= self.weapon.bullet_speed
        if self.y < -10:
            self.active = False
            
    def draw(self, surface):
        pygame.draw.circle(surface, self.weapon.color, 
                         (int(self.x), int(self.y)), 
                         self.weapon.bullet_size)

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.type = power_type  # 'shield', 'health', 'weapon'
        self.size = 15
        self.active = True
        
    def draw(self, surface):
        if self.type == 'shield':
            color = (100, 200, 255)
        elif self.type == 'health':
            color = GREEN
        else:  # weapon
            color = YELLOW
            
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size - 3, 2)

def main():
    # Game objects
    player = Player()
    enemies = []
    bullets = []
    powerups = []
    particle_system = ParticleSystem()
    
    # Game state
    game_over = False
    spawn_timer = 0
    powerup_timer = 0
    score = 0
    level = 1
    
    # Create background stars
    stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) 
             for _ in range(100)]
    
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    weapon = player.weapons[player.current_weapon]
                    if weapon.can_fire():
                        bullets.append(Bullet(player.x, player.y - player.size, weapon))
                elif event.key == pygame.K_TAB:
                    player.current_weapon = (player.current_weapon + 1) % len(player.weapons)
                    
        if not game_over:
            # Update
            player.move()
            
            # Spawn enemies
            spawn_timer += 1
            if spawn_timer >= 60:
                spawn_timer = 0
                enemy_type = 'elite' if random.random() < 0.2 else 'basic'
                enemies.append(Enemy(
                    random.randint(50, WIDTH-50),
                    random.randint(50, HEIGHT//3),
                    enemy_type
                ))
                
            # Spawn powerups
            powerup_timer += 1
            if powerup_timer >= 300:  # Every 5 seconds
                powerup_timer = 0
                if random.random() < 0.3:  # 30% chance
                    powerup_type = random.choice(['shield', 'health', 'weapon'])
                    powerups.append(PowerUp(
                        random.randint(50, WIDTH-50),
                        random.randint(50, HEIGHT-50),
                        powerup_type
                    ))
                    
            # Update objects
            for enemy in enemies[:]:
                enemy.move()
                
                # Check collision with player
                dist = math.hypot(player.x - enemy.x, player.y - enemy.y)
                if dist < player.size + enemy.size:
                    if not player.shield_active:
                        player.health -= 20
                        if player.health <= 0:
                            game_over = True
                    enemies.remove(enemy)
                    # Add explosion particles
                    for _ in range(20):
                        particle_system.add_particle(
                            enemy.x, enemy.y, 
                            enemy.color, 5, 30
                        )
                        
            for bullet in bullets[:]:
                bullet.move()
                if not bullet.active:
                    bullets.remove(bullet)
                else:
                    for enemy in enemies[:]:
                        dist = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                        if dist < enemy.size + bullet.weapon.bullet_size:
                            enemy.health -= bullet.weapon.damage
                            bullets.remove(bullet)
                            if enemy.health <= 0:
                                enemies.remove(enemy)
                                score += 100 if enemy.type == 'basic' else 300
                                # Add explosion particles
                                for _ in range(20):
                                    particle_system.add_particle(
                                        enemy.x, enemy.y, 
                                        enemy.color, 5, 30
                                    )
                            break
                            
            # Check powerup collisions
            for powerup in powerups[:]:
                dist = math.hypot(player.x - powerup.x, player.y - powerup.y)
                if dist < player.size + powerup.size:
                    if powerup.type == 'shield':
                        player.shield_active = True
                        player.shield_time = time.time()
                    elif powerup.type == 'health':
                        player.health = min(100, player.health + 30)
                    elif powerup.type == 'weapon':
                        # Upgrade current weapon
                        current_weapon = player.weapons[player.current_weapon]
                        current_weapon.damage *= 1.2
                        current_weapon.bullet_size += 1
                    powerups.remove(powerup)
                    
            # Update shield timer
            if player.shield_active and time.time() - player.shield_time > 5:
                player.shield_active = False
                
            # Update particle system
            particle_system.update()
            
            # Level progression
            if score >= level * 1000:
                level += 1
                player.health = min(100, player.health + 20)
                
        # Drawing
        screen.fill(BLACK)
        
        # Draw stars
        for star in stars:
            pygame.draw.circle(screen, WHITE, star, 1)
            
        # Draw game objects
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for bullet in bullets:
            bullet.draw(screen)
        for powerup in powerups:
            powerup.draw(screen)
            
        # Draw particles
        particle_system.draw(screen)
        
        # Draw UI
        font = pygame.font.Font(None, 36)
        health_text = font.render(f"Health: {int(player.health)}", True, WHITE)
        score_text = font.render(f"Score: {score}", True, WHITE)
        level_text = font.render(f"Level: {level}", True, WHITE)
        weapon_text = font.render(f"Weapon: {player.current_weapon + 1}", True, WHITE)
        
        screen.blit(health_text, (10, 10))
        screen.blit(score_text, (10, 50))
        screen.blit(level_text, (10, 90))
        screen.blit(weapon_text, (10, 130))
        
        if game_over:
            go_text = font.render("GAME OVER", True, RED)
            screen.blit(go_text, (WIDTH//2 - 100, HEIGHT//2))
            
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()

if __name__ == "__main__":
    main()
