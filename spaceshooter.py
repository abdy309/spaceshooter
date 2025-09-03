# space_shooter.py
import sys
import os
import json
import random
import pygame

# ====================================
# ---------- CRUD FUNCTIONS ----------
# ====================================
FILE = "players.json"

def _ensure_file():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({}, f)

def load_players():
    _ensure_file()
    with open(FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_players(players):
    with open(FILE, "w") as f:
        json.dump(players, f, indent=2)

def create_player(name):
    name = name.strip()
    if not name:
        return False
    players = load_players()
    if name in players:
        return False
    players[name] = {"score": 0}
    save_players(players)
    return True

def read_players():
    return load_players()

def update_score(name, new_score):
    players = load_players()
    if name in players:
        players[name]["score"] = max(players[name]["score"], new_score)
        save_players(players)

def delete_player(name):
    players = load_players()
    if name in players:
        del players[name]
        save_players(players)
        return True
    return False


# ====================================
# --------- TEXT MENU SYSTEM ---------
# ====================================
def choose_player():
    while True:
        players = read_players()
        print("\n=== Player Profiles ===")
        if not players:
            print("No players yet.")
        else:
            for idx, name in enumerate(players.keys(), start=1):
                print(f"{idx}. {name} (High score: {players[name]['score']})")

        print("\nOptions:")
        print("[number] Select player")
        print("[n]      New player")
        print("[d]      Delete player")
        print("[q]      Quit")

        choice = input("Choose option: ").strip().lower()

        if choice == "q":
            raise SystemExit

        if choice == "n":
            name = input("Enter new player name: ").strip()
            if create_player(name):
                print(f"Created player '{name}'.")
                return name
            else:
                print("Could not create player (maybe exists or empty).")
                continue

        if choice == "d":
            del_name = input("Enter EXACT player name to delete: ").strip()
            if delete_player(del_name):
                print(f"Deleted '{del_name}'.")
            else:
                print("No such player.")
            continue

        try:
            idx = int(choice) - 1
            players_list = list(players.keys())
            if 0 <= idx < len(players_list):
                selected = players_list[idx]
                print(f"Selected '{selected}'.")
                return selected
            else:
                print("Invalid number.")
        except ValueError:
            print("Invalid input.")


# ====================================
# ----------- PYGAME GAME ------------
# ====================================
WIDTH, HEIGHT = 720, 480
PLAYER_SPEED = 6
BULLET_SPEED = 10
ENEMY_SPEED_MIN, ENEMY_SPEED_MAX = 2, 4
SHOOT_COOLDOWN_MS = 220
SPAWN_ENEMY_EVERY_MS = 800

class Bullet(pygame.Rect):
    def __init__(self, x, y):
        super().__init__(x - 2, y - 10, 4, 10)

class Enemy(pygame.Rect):
    def __init__(self):
        w, h = 40, 24
        x = random.randint(0, WIDTH - w)
        super().__init__(x, -h, w, h)
        self.speed = random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)

def draw_text(surface, text, size, x, y):
    font = pygame.font.SysFont("arial", size, bold=True)
    s = font.render(text, True, (255, 255, 255))
    rect = s.get_rect()
    rect.topleft = (x, y)
    surface.blit(s, rect)

def game_over_screen(screen, clock, score, highscore, player_name):
    elapsed = 0
    while elapsed < 1800:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        screen.fill((10, 10, 16))
        draw_text(screen, "GAME OVER", 48, WIDTH // 2 - 140, HEIGHT // 2 - 60)
        draw_text(screen, f"Player: {player_name}", 24, WIDTH // 2 - 100, HEIGHT // 2)
        draw_text(screen, f"Score: {score}", 24, WIDTH // 2 - 100, HEIGHT // 2 + 30)
        draw_text(screen, f"High Score: {highscore}", 24, WIDTH // 2 - 100, HEIGHT // 2 + 60)
        pygame.display.flip()
        dt = clock.tick(60)
        elapsed += dt

def main():
    player_name = choose_player()
    players = read_players()
    starting_high = players.get(player_name, {}).get("score", 0)

    pygame.init()
    pygame.display.set_caption("Space Shooter (with CRUD)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    player = pygame.Rect(WIDTH // 2 - 20, HEIGHT - 60, 44, 26)
    bullets = []
    enemies = []

    last_shot = 0
    spawn_timer = 0
    score = 0

    while True:
        dt = clock.tick(60)
        spawn_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                update_score(player_name, score)
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if player.left > 0:
                player.move_ip(-PLAYER_SPEED, 0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if player.right < WIDTH:
                player.move_ip(PLAYER_SPEED, 0)

        if keys[pygame.K_SPACE]:
            now = pygame.time.get_ticks()
            if now - last_shot >= SHOOT_COOLDOWN_MS:
                bullets.append(Bullet(player.centerx, player.top))
                last_shot = now

        if spawn_timer >= SPAWN_ENEMY_EVERY_MS:
            enemies.append(Enemy())
            spawn_timer = 0

        for b in bullets[:]:
            b.y -= BULLET_SPEED
            if b.bottom < 0:
                bullets.remove(b)

        for e in enemies[:]:
            e.y += e.speed
            if e.top > HEIGHT:
                enemies.remove(e)
            if e.colliderect(player):
                update_score(player_name, score)
                players = read_players()
                high = players.get(player_name, {}).get("score", 0)
                game_over_screen(screen, clock, score, high, player_name)
                pygame.quit()
                sys.exit()

        for b in bullets[:]:
            hit = next((e for e in enemies if b.colliderect(e)), None)
            if hit:
                enemies.remove(hit)
                bullets.remove(b)
                score += 10

        screen.fill((10, 10, 16))

        for i in range(40):
            x = (i * 17 + pygame.time.get_ticks() // 10) % WIDTH
            y = (i * 29) % HEIGHT
            screen.fill((40, 40, 60), (x, y, 2, 2))

        pygame.draw.rect(screen, (200, 220, 255), player, border_radius=4)
        pygame.draw.rect(screen, (255, 255, 255), (player.centerx - 4, player.top - 6, 8, 6))

        for b in bullets:
            pygame.draw.rect(screen, (255, 255, 255), b)

        for e in enemies:
            pygame.draw.rect(screen, (255, 90, 90), e, border_radius=3)
            screen.fill((0, 0, 0), (e.centerx - 3, e.centery - 3, 6, 6))

        draw_text(screen, f"Player: {player_name}", 20, 10, 10)
        draw_text(screen, f"Score: {score}", 20, 10, 34)
        live_high = max(starting_high, score)
        draw_text(screen, f"High: {live_high}", 20, WIDTH - 150, 10)

        pygame.display.flip()

if __name__ == "__main__":
    main()
