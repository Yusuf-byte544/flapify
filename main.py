import pygame
import random
import sys
import math
import json
import os

# --- DOSYA KAYIT SİSTEMİ (SAVE SYSTEM) ---
SAVE_FILE = "save_game.json"

def load_game():
    global total_coins, high_score, selected_skin_index
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                total_coins = data.get("total_coins", 0)
                high_score = data.get("high_score", 0)
                selected_skin_index = data.get("selected_skin_index", 0)
                unlocked_status = data.get("unlocked_skins", [])
                
                skin_index = 0
                for item in skins:
                    if item["type"] == "skin":
                        if skin_index < len(unlocked_status):
                            item["unlocked"] = unlocked_status[skin_index]
                        skin_index += 1
        except Exception:
            pass

def save_game():
    data = {
        "total_coins": total_coins,
        "high_score": high_score,
        "selected_skin_index": selected_skin_index,
        "unlocked_skins": [item["unlocked"] for item in skins if item["type"] == "skin"]
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

# --- ANDROID REKLAM KONTROLÜ ---
try:
    from jnius import autoclass
    ANDROID = True
except ImportError:
    ANDROID = False

if ANDROID:
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        MobileAds = autoclass('com.google.android.gms.ads.MobileAds')
        MobileAds.initialize(activity)
    except Exception:
        pass

# Pygame ve Ses Mikserini Başlatma
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

# Ses Efektleri Oluşturma
def create_beep_sound(frequency, duration, volume=0.3):
    sample_rate = 22050
    num_samples = int(sample_rate * (duration / 1000.0))
    buffer = bytearray()
    for i in range(num_samples):
        t = i / sample_rate
        value = int(32767 * volume * math.sin(2 * math.pi * frequency * t))
        buffer.extend(value.to_bytes(2, byteorder='little', signed=True))
    return pygame.mixer.Sound(buffer=bytes(buffer))

jump_sound = create_beep_sound(440, 80)     
score_sound = create_beep_sound(880, 120)   
hit_sound = create_beep_sound(150, 200)     
click_sound = create_beep_sound(600, 50)    
coin_sound = create_beep_sound(1200, 100)   
powerup_sound = create_beep_sound(1500, 150)

# Ekran Ayarları
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flapify - Profesyonel Sürüm")
clock = pygame.time.Clock()

# Renkler
SKY_BLUE = (135, 206, 235)
YELLOW = (255, 204, 0)
ORANGE = (255, 128, 0)
RED = (230, 0, 0)
BLUE = (0, 128, 255)
PURPLE = (128, 0, 128)
GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
BULLET_COLOR = (200, 0, 0)
BUTTON_COLOR = (50, 150, 250)
SHIELD_COLOR = (0, 255, 255)

# Kostümler ve Güçler
skins = [
    {"type": "skin", "name_tr": "Sarı Kuş", "name_en": "Yellow Bird", "color": YELLOW, "price": 0, "unlocked": True, "effect": "none"},
    {"type": "skin", "name_tr": "Kırmızı Kuş", "name_en": "Red Bird", "color": RED, "price": 0, "unlocked": True, "effect": "none"},
    {"type": "skin", "name_tr": "Yeşil Kuş", "name_en": "Green Bird", "color": GREEN, "price": 0, "unlocked": True, "effect": "none"},
    {"type": "skin", "name_tr": "Mavi Kuş", "name_en": "Blue Bird", "color": BLUE, "price": 0, "unlocked": True, "effect": "none"},
    {"type": "skin", "name_tr": "Alev Krallığı", "name_en": "Flame King", "color": RED, "price": 200, "unlocked": False, "effect": "fire"},
    {"type": "skin", "name_tr": "Göklerin Efendisi", "name_en": "Sky Master", "color": BLUE, "price": 200, "unlocked": False, "effect": "sparkle"},
    {"type": "skin", "name_tr": "Sihirli Mor", "name_en": "Magic Purple", "color": PURPLE, "price": 200, "unlocked": False, "effect": "rainbow"},
    {"type": "power", "name_tr": "Kalkan (1 Hak)", "name_en": "Shield (1 Hit)", "price": 50, "effect": "shield_power"},
    {"type": "power", "name_tr": "Yavaşlatıcı", "name_en": "Slow-Mo", "price": 75, "effect": "slow_power"},
    {"type": "power", "name_tr": "Çift Altın (2x)", "name_en": "Double Coin (2x)", "price": 100, "effect": "double_coin_power"}
]

# Oyun Değişkenleri
GRAVITY = 0.25
bird_movement = 0
bird_rect = pygame.Rect(80, 250, 34, 24)

pipe_list = []
pipe_dirs = {}
bullet_list = []

SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, 1200)

SPAWNBULLET = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWNBULLET, 1500)

pipe_height = [200, 300, 400]

score = 0
high_score = 0
total_coins = 0  
selected_skin_index = 0
current_score_counted = False
insufficient_coin_timer = 0
player_name = "Oyuncu"

# Kayıtlı verileri yükle
load_game()

# --- REKLAM VE SAYAC DEĞİŞKENLERİ ---
yanma_sayaci = 0   
reklam_mesaji = "" 
reklam_mesaj_timer = 0

has_shield = False
has_slowmo = False
slowmo_timer = 0
double_coin_active = False

font = pygame.font.SysFont("Arial", 26, bold=True)
font_small = pygame.font.SysFont("Arial", 18, bold=True)
font_tiny = pygame.font.SysFont("Arial", 14, bold=True)

current_language = 'TR'

translations = {
    'TR': {
        'name_prompt': "Adını Gir:",
        'play': "OYNA",
        'shop': "DÜKKAN",
        'score': "Skor",
        'high_score': "En Yüksek",
        'game_over': "OYUN BİTTİ",
        'restart': "Tekrar Oyna",
        'menu': "Ana Menü",
        'shop_title': "DÜKKAN (KOSTÜMLER & GÜÇLER)",
        'back': "Geri Dön",
        'equipped': "Aktif",
        'select': "Seç",
        'buy': "Al",
        'not_enough': "Yetersiz Altın!",
        'tutorial_title': "OYUN REHBERİ",
        't1': "• Ekrana dokunarak veya boşlukla zıpla.",
        't2': "• Skor 30 olunca borular hareket eder!",
        't3': "• Skor 50 olunca mermiler gelir!",
        't4': "• Dükkandan güç alarak hayatta kal!",
        'start_game': "Oyuna Başla",
        'watch_ad': "📺 Reklam İzle (+5 Altın)"
    },
    'EN': {
        'name_prompt': "Enter Name:",
        'play': "PLAY",
        'shop': "SHOP",
        'score': "Score",
        'high_score': "High Score",
        'game_over': "GAME OVER",
        'restart': "Restart",
        'menu': "Main Menu",
        'shop_title': "SHOP (SKINS & POWERS)",
        'back': "Back",
        'equipped': "Active",
        'select': "Select",
        'buy': "Buy",
        'not_enough': "Not Enough Coins!",
        'tutorial_title': "GAME GUIDE",
        't1': "• Tap screen or press SPACE to jump.",
        't2': "• Pipes move after 30 score!",
        't3': "• Bullets appear after 50 score!",
        't4': "• Buy powers from shop to survive!",
        'start_game': "Start Game",
        'watch_ad': "📺 Watch Ad (+5 Coins)"
    }
}

game_state = 'name_entry'

shop_button_rect = pygame.Rect(WIDTH//2 - 100, 320, 200, 45)
back_button_rect = pygame.Rect(WIDTH//2 - 100, 550, 200, 35)
lang_button_rect = pygame.Rect(WIDTH - 70, 20, 50, 35)
tutorial_start_btn = pygame.Rect(WIDTH//2 - 100, 420, 200, 45)
tutorial_back_btn = pygame.Rect(WIDTH//2 - 100, 475, 200, 45)
ad_button_rect = pygame.Rect(20, 470, WIDTH - 40, 38)

def t(key):
    return translations[current_language][key]

def goster_banner_reklam():
    if not ANDROID:
        banner_rect = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)
        pygame.draw.rect(screen, (50, 50, 50), banner_rect)
        pygame.draw.rect(screen, (200, 200, 200), banner_rect, 1)
        banner_text = font_tiny.render("[BANNER REKLAM - 50x400]", True, (180, 180, 180))
        screen.blit(banner_text, banner_text.get_rect(center=banner_rect.center))

def goster_gecis_reklami():
    if not ANDROID:
        pass

def goster_odullu_reklam():
    global total_coins, reklam_mesaji, reklam_mesaj_timer
    total_coins += 5
    coin_sound.play()
    reklam_mesaji = "Reklam İzlendi! +5 Altın Eklendi 🪙" if current_language == 'TR' else "Ad Watched! +5 Coins Added 🪙"
    reklam_mesaj_timer = 120
    save_game()

def draw_coin_display():
    pygame.draw.circle(screen, GOLD, (WIDTH - 45, 75), 12)
    pygame.draw.circle(screen, (200, 160, 0), (WIDTH - 45, 75), 12, 2)
    coin_surf = font_small.render(str(total_coins), True, WHITE)
    screen.blit(coin_surf, (WIDTH - 75 - coin_surf.get_width(), 63))

def create_pipe():
    random_pipe_pos = random.choice(pipe_height)
    bottom_pipe = pygame.Rect(WIDTH + 10, random_pipe_pos, 60, HEIGHT - random_pipe_pos - 50)
    top_pipe = pygame.Rect(WIDTH + 10, 0, 60, random_pipe_pos - 150)
    pipe_dirs[id(bottom_pipe)] = 1
    pipe_dirs[id(top_pipe)] = 1
    return bottom_pipe, top_pipe

def move_pipes(pipes, current_score):
    speed = 2 if (has_slowmo and slowmo_timer > 0) else 3
    for pipe in pipes:
        pipe.centerx -= speed
        if current_score >= 30:
            p_id = id(pipe)
            if p_id not in pipe_dirs:
                pipe_dirs[p_id] = 1
            pipe.y += pipe_dirs[p_id] * 1.5
            if pipe.top <= 20 or pipe.bottom >= HEIGHT - 60:
                pipe_dirs[p_id] *= -1
    return [pipe for pipe in pipes if pipe.right > -50]

def draw_pipes(pipes):
    for pipe in pipes:
        pygame.draw.rect(screen, GREEN, pipe)
        pygame.draw.rect(screen, (0, 100, 0), pipe, 3)

def create_bullet():
    bullet_y = random.randint(100, HEIGHT - 120)
    return pygame.Rect(WIDTH + 10, bullet_y, 25, 10)

def move_bullets(bullets):
    speed = 3 if (has_slowmo and slowmo_timer > 0) else 5
    for bullet in bullets:
        bullet.centerx -= speed
    return [bullet for bullet in bullets if bullet.right > -50]

def draw_bullets(bullets):
    for bullet in bullets:
        pygame.draw.rect(screen, BULLET_COLOR, bullet, border_radius=4)
        pygame.draw.circle(screen, (255, 165, 0), (bullet.x, bullet.centery), 4)

def draw_bird(rect, skin):
    body_color = skin["color"]
    wing_color = ORANGE if body_color != ORANGE else (200, 100, 0)
    effect = skin.get("effect", "none")
    time_tick = pygame.time.get_ticks()

    if effect == "fire":
        glow_size = int(22 + math.sin(time_tick * 0.015) * 4)
        pygame.draw.circle(screen, (255, 100, 0), rect.center, glow_size, 3)
    elif effect == "sparkle":
        glow_size = int(24 + math.cos(time_tick * 0.02) * 5)
        pygame.draw.circle(screen, (0, 200, 255), rect.center, glow_size, 2)
    elif effect == "rainbow":
        r = int((math.sin(time_tick * 0.01) + 1) * 127)
        g = int((math.sin(time_tick * 0.01 + 2) + 1) * 127)
        b = int((math.sin(time_tick * 0.01 + 4) + 1) * 127)
        pygame.draw.circle(screen, (r, g, b), rect.center, 24, 3)

    pygame.draw.ellipse(screen, body_color, rect)
    wing_rect = pygame.Rect(rect.x + 4, rect.y + 10, 14, 10)
    pygame.draw.ellipse(screen, wing_color, wing_rect)
    pygame.draw.circle(screen, BLACK, (rect.x + 24, rect.y + 8), 3)
    pygame.draw.circle(screen, WHITE, (rect.x + 25, rect.y + 7), 1)
    beak_rect = pygame.Rect(rect.x + rect.width - 4, rect.y + 8, 10, 8)
    pygame.draw.polygon(screen, (255, 140, 0), [(beak_rect.x, beak_rect.y), (beak_rect.x + 10, beak_rect.y + 4), (beak_rect.x, beak_rect.y + 8)])
    
    global has_shield
    if has_shield:
        pygame.draw.circle(screen, SHIELD_COLOR, rect.center, 26, 2)

def check_collision(pipes, bullets):
    global has_shield, yanma_sayaci
    hit_detected = False

    for pipe in pipes:
        if bird_rect.colliderect(pipe):
            if has_shield:
                has_shield = False
                pipe.right = 0 
                powerup_sound.play()
                return True
            hit_detected = True
            break

    for bullet in bullets:
        if bird_rect.colliderect(bullet):
            if has_shield:
                has_shield = False
                bullet.right = 0
                powerup_sound.play()
                return True
            hit_detected = True
            break

    if bird_rect.top <= -50 or bird_rect.bottom >= HEIGHT - 50:
        if has_shield:
            has_shield = False
            bird_rect.centery = 250
            powerup_sound.play()
            return True
        hit_detected = True

    if hit_detected:
        yanma_sayaci += 1
        if yanma_sayaci >= 3:
            goster_gecis_reklami()
            yanma_sayaci = 0
        return False

    return True

score_passed_tracker = []

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if game_state == 'name_entry':
                if event.key == pygame.K_RETURN:
                    if len(player_name.strip()) > 0:
                        game_state = 'menu'
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    if len(player_name) < 12:
                        player_name += event.unicode

            elif game_state == 'playing':
                if event.key == pygame.K_SPACE:
                    bird_movement = 0
                    bird_movement -= 6.5
                    jump_sound.play()
            elif game_state == 'game_over':
                if event.key == pygame.K_SPACE:
                    click_sound.play()
                    game_state = 'tutorial'

        if event.type == pygame.MOUSEBUTTONDOWN:
            click_sound.play()
            
            if game_state == 'playing':
                bird_movement = 0
                bird_movement -= 6.5
                jump_sound.play()

            elif lang_button_rect.collidepoint(event.pos):
                current_language = 'EN' if current_language == 'TR' else 'TR'

            elif game_state == 'menu':
                if shop_button_rect.collidepoint(event.pos):
                    game_state = 'shop'
                elif pygame.Rect(WIDTH//2 - 100, 255, 200, 45).collidepoint(event.pos):
                    game_state = 'tutorial'

            elif game_state == 'tutorial':
                if tutorial_start_btn.collidepoint(event.pos):
                    game_state = 'playing'
                    pipe_list.clear()
                    bullet_list.clear()
                    score_passed_tracker.clear()
                    bird_rect.center = (80, 250)
                    bird_movement = 0
                    score = 0
                    current_score_counted = False
                elif tutorial_back_btn.collidepoint(event.pos):
                    game_state = 'menu'

            elif game_state == 'game_over':
                if pygame.Rect(WIDTH//2 - 100, 310, 200, 45).collidepoint(event.pos):
                    game_state = 'tutorial'
                    pipe_list.clear()
                    bullet_list.clear()
                    score_passed_tracker.clear()
                    bird_rect.center = (80, 250)
                    bird_movement = 0
                    score = 0
                    current_score_counted = False
                elif pygame.Rect(WIDTH//2 - 100, 370, 200, 45).collidepoint(event.pos):
                    game_state = 'menu'
                    pipe_list.clear()
                    bullet_list.clear()
                    score_passed_tracker.clear()
                    bird_rect.center = (80, 250)
                    bird_movement = 0
                    score = 0
                    current_score_counted = False

            elif game_state == 'shop':
                if back_button_rect.collidepoint(event.pos):
                    game_state = 'menu'
                elif ad_button_rect.collidepoint(event.pos):
                    goster_odullu_reklam()
                else:
                    y_offset = 60
                    for i, item in enumerate(skins):
                        item_box = pygame.Rect(20, y_offset, WIDTH - 40, 32)
                        if item_box.collidepoint(event.pos):
                            if item["type"] == "skin":
                                if item["unlocked"]:
                                    selected_skin_index = i
                                    save_game()
                                else:
                                    if total_coins >= item["price"]:
                                        total_coins -= item["price"]
                                        item["unlocked"] = True
                                        selected_skin_index = i
                                        coin_sound.play()
                                        save_game()
                                    else:
                                        insufficient_coin_timer = 60
                            elif item["type"] == "power":
                                if total_coins >= item["price"]:
                                    total_coins -= item["price"]
                                    powerup_sound.play()
                                    save_game()
                                    if item["effect"] == "shield_power":
                                        has_shield = True
                                    elif item["effect"] == "slow_power":
                                        has_slowmo = True
                                        slowmo_timer = 300
                                    elif item["effect"] == "double_coin_power":
                                        double_coin_active = True
                                else:
                                    insufficient_coin_timer = 60
                        y_offset += 38

        if event.type == SPAWNPIPE and game_state == 'playing':
            pipe_list.extend(create_pipe())

        if event.type == SPAWNBULLET and game_state == 'playing' and score >= 50:
            bullet_list.append(create_bullet())

    screen.fill(SKY_BLUE)

    pygame.draw.rect(screen, (80, 80, 80), lang_button_rect, border_radius=6)
    lang_surf = font_small.render(current_language, True, WHITE)
    screen.blit(lang_surf, lang_surf.get_rect(center=lang_button_rect.center))

    if game_state == 'name_entry':
        title_surf = font.render("FLAPIFY", True, WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, 120)))

        prompt_surf = font_small.render(t('name_prompt'), True, WHITE)
        screen.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH//2, 200)))

        box_rect = pygame.Rect(WIDTH//2 - 120, 240, 240, 50)
        pygame.draw.rect(screen, WHITE, box_rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, box_rect, 2, border_radius=8)

        name_surf = font.render(player_name + "|", True, BLACK)
        screen.blit(name_surf, (box_rect.x + 15, box_rect.y + 10))

        enter_btn = pygame.Rect(WIDTH//2 - 100, 330, 200, 45)
        pygame.draw.rect(screen, (46, 204, 113), enter_btn, border_radius=8)
        enter_txt = font_small.render("DEVAM ET", True, WHITE)
        screen.blit(enter_txt, enter_txt.get_rect(center=enter_btn.center))

    elif game_state == 'menu':
        draw_coin_display()

        title_surf = font.render("FLAPIFY", True, WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, 100)))

        welcome_surf = font_small.render(f"Oyuncu: {player_name}", True, GOLD)
        screen.blit(welcome_surf, welcome_surf.get_rect(center=(WIDTH//2, 150)))

        draw_bird(pygame.Rect(WIDTH//2 - 20, 180, 40, 30), skins[selected_skin_index])

        play_btn_rect = pygame.Rect(WIDTH//2 - 100, 255, 200, 45)
        pygame.draw.rect(screen, (46, 204, 113), play_btn_rect, border_radius=10)
        play_surf = font_small.render(t('play'), True, WHITE)
        screen.blit(play_surf, play_surf.get_rect(center=play_btn_rect.center))

        pygame.draw.rect(screen, BUTTON_COLOR, shop_button_rect, border_radius=10)
        shop_surf = font_small.render(t('shop'), True, WHITE)
        screen.blit(shop_surf, shop_surf.get_rect(center=shop_button_rect.center))

    elif game_state == 'tutorial':
        tut_title = font.render(t('tutorial_title'), True, GOLD)
        screen.blit(tut_title, tut_title.get_rect(center=(WIDTH//2, 70)))

        instructions = [t('t1'), t('t2'), t('t3'), t('t4')]
        y_pos = 140
        for line in instructions:
            line_surf = font_tiny.render(line, True, WHITE)
            screen.blit(line_surf, (40, y_pos))
            y_pos += 50

        pygame.draw.rect(screen, (46, 204, 113), tutorial_start_btn, border_radius=8)
        start_txt = font_small.render(t('start_game'), True, WHITE)
        screen.blit(start_txt, start_txt.get_rect(center=tutorial_start_btn.center))

        pygame.draw.rect(screen, (200, 50, 50), tutorial_back_btn, border_radius=8)
        back_txt = font_small.render(t('back'), True, WHITE)
        screen.blit(back_txt, back_txt.get_rect(center=tutorial_back_btn.center))

    elif game_state == 'playing':
        if slowmo_timer > 0:
            slowmo_timer -= 1

        bird_movement += GRAVITY
        bird_rect.centery += bird_movement
        draw_bird(bird_rect, skins[selected_skin_index])

        pipe_list = move_pipes(pipe_list, score)
        draw_pipes(pipe_list)

        if score >= 50:
            bullet_list = move_bullets(bullet_list)
            draw_bullets(bullet_list)

        if not check_collision(pipe_list, bullet_list):
            hit_sound.play()
            game_state = 'game_over'

        for pipe in pipe_list:
            if pipe.top == 0 and pipe.right < bird_rect.left:
                if pipe not in score_passed_tracker:
                    score += 1
                    score_passed_tracker.append(pipe)
                    score_sound.play()

        score_surface = font.render(f"{t('score')}: {int(score)}", True, WHITE)
        screen.blit(score_surface, score_surface.get_rect(center=(WIDTH // 2, 50)))

        if score >= 30:
            move_info = font_tiny.render("HAREKETLİ ENGEL AKTİF!", True, RED)
            screen.blit(move_info, move_info.get_rect(center=(WIDTH//2, 90)))

        goster_banner_reklam()

    elif game_state == 'game_over':
        if not current_score_counted:
            earned = int(score // 5)
            if double_coin_active:
                earned *= 2
                double_coin_active = False
            total_coins += earned
            if score > high_score:
                high_score = score
            current_score_counted = True
            save_game()

        over_surf = font.render(t('game_over'), True, RED)
        screen.blit(over_surf, over_surf.get_rect(center=(WIDTH//2, 90)))

        score_surf = font_small.render(f"{t('score')}: {int(score)}", True, WHITE)
        screen.blit(score_surf, score_surf.get_rect(center=(WIDTH//2, 150)))

        high_surf = font_small.render(f"{t('high_score')}: {int(high_score)}", True, WHITE)
        screen.blit(high_surf, high_surf.get_rect(center=(WIDTH//2, 190)))

        restart_btn = pygame.Rect(WIDTH//2 - 100, 310, 200, 45)
        pygame.draw.rect(screen, (46, 204, 113), restart_btn, border_radius=8)
        r_text = font_small.render(t('restart'), True, WHITE)
        screen.blit(r_text, r_text.get_rect(center=restart_btn.center))

        menu_btn = pygame.Rect(WIDTH//2 - 100, 370, 200, 45)
        pygame.draw.rect(screen, BUTTON_COLOR, menu_btn, border_radius=8)
        m_text = font_small.render(t('menu'), True, WHITE)
        screen.blit(m_text, m_text.get_rect(center=menu_btn.center))

    elif game_state == 'shop':
        draw_coin_display()

        shop_title = font_small.render(t('shop_title'), True, GOLD)
        screen.blit(shop_title, shop_title.get_rect(center=(WIDTH//2, 30)))

        y_offset = 60
        for i, item in enumerate(skins):
            item_box = pygame.Rect(20, y_offset, WIDTH - 40, 32)
            
            if item["type"] == "skin":
                box_color = (60, 120, 60) if i == selected_skin_index else (70, 70, 90)
            else:
                box_color = (120, 80, 40)

            pygame.draw.rect(screen, box_color, item_box, border_radius=6)

            name = item["name_tr"] if current_language == 'TR' else item["name_en"]
            if item["type"] == "skin":
                if i == selected_skin_index:
                    status = t('equipped')
                elif item["unlocked"]:
                    status = t('select')
                else:
                    status = f"{t('buy')} ({item['price']}G)"
            else:
                status = f"{t('buy')} ({item['price']}G)"

            text = f"{name} - [{status}]"
            item_surf = font_tiny.render(text, True, WHITE)
            screen.blit(item_surf, (item_box.x + 8, item_box.y + 8))
            y_offset += 38

        pygame.draw.rect(screen, (34, 139, 34), ad_button_rect, border_radius=8)
        ad_text_press = t('watch_ad')
        ad_text_surf = font_small.render(ad_text_press, True, WHITE)
        screen.blit(ad_text_surf, ad_text_surf.get_rect(center=ad_button_rect.center))

        if insufficient_coin_timer > 0:
            warn_surf = font_tiny.render(t('not_enough'), True, RED)
            screen.blit(warn_surf, warn_surf.get_rect(center=(WIDTH//2, 520)))
            insufficient_coin_timer -= 1

        if reklam_mesaj_timer > 0:
            msg_surf = font_tiny.render(reklam_mesaji, True, GOLD)
            screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH//2, 510)))
            reklam_mesaj_timer -= 1

        pygame.draw.rect(screen, (200, 50, 50), back_button_rect, border_radius=8)
        back_surf = font_small.render(t('back'), True, WHITE)
        screen.blit(back_surf, back_surf.get_rect(center=back_button_rect.center))

    pygame.display.update()
    clock.tick(60)
