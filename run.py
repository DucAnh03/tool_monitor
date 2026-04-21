# Yêu cầu: pip install pyautogui keyboard pillow

import pyautogui
import keyboard
import time
import random
import threading
from PIL import ImageChops

# ─── Cấu hình ────────────────────────────────────────────────────────────────
STOP_KEYS    = ("a", "s", "d", "f")
TAB_INTERVAL = 600  # 10 phút (giây)

stop_event = threading.Event()


# ─── So sánh ảnh ─────────────────────────────────────────────────────────────

def img_diff(img1, img2):
    diff = ImageChops.difference(img1, img2)
    w, h = diff.size
    region = diff.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
    total, count = 0, 0
    for p in region.getdata():
        if isinstance(p, tuple):
            total += sum(p)
            count += len(p)
        else:
            total += p
            count += 1
    return total / count if count else 0


# ─── Di chuyển chuột ngẫu nhiên ──────────────────────────────────────────────

def random_mouse_for(seconds):
    sw, sh = pyautogui.size()
    end = time.time() + seconds
    while time.time() < end and not stop_event.is_set():
        x = random.randint(80, sw - 80)
        y = random.randint(80, sh - 80)
        try:
            pyautogui.moveTo(x, y, duration=random.uniform(0.15, 0.45))
        except pyautogui.FailSafeException:
            stop_event.set()
            return
        time.sleep(random.uniform(0.1, 0.4))


# ─── Cuộn xuống + click ──────────────────────────────────────────────────────

def scroll_down_and_click():
    sw, sh = pyautogui.size()
    cx, cy = sw // 2, sh // 2
    try:
        pyautogui.moveTo(cx, cy, duration=0.2)
        time.sleep(0.1)
        scroll_clicks = max(6, sh // 120)   # ~1/3 màn hình, nhanh hơn
        pyautogui.scroll(-scroll_clicks)
        time.sleep(0.15)
        pyautogui.click(cx, cy)
        time.sleep(0.1)
        pyautogui.click(cx, cy)
        print(f"[Scroll] Xuong {scroll_clicks} clicks + 2x click")
    except pyautogui.FailSafeException:
        stop_event.set()


# ─── Cuộn nhanh về đầu ───────────────────────────────────────────────────────

def scroll_to_top():
    sw, sh = pyautogui.size()
    try:
        pyautogui.click(sw // 2, sh // 2)
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "Home")   # Nhảy lên đầu trang
        time.sleep(0.5)
        print("[Scroll] Ve dau trang → lap lai")
    except pyautogui.FailSafeException:
        stop_event.set()


# ─── Thread chuyển tab mỗi 10 phút ──────────────────────────────────────────

def tab_loop():
    elapsed = 0
    while not stop_event.is_set():
        time.sleep(1)
        elapsed += 1
        if elapsed >= TAB_INTERVAL:
            elapsed = 0
            try:
                print("[Tab] Chuyen tab → ve lai")
                pyautogui.hotkey("ctrl", "tab")
                time.sleep(1.5)
                pyautogui.hotkey("ctrl", "tab")
            except Exception:
                pass


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = 0.03

    print("=" * 50)
    print("  Auto Scroll Tool")
    print("  Mo file cua ban truoc, tool se tu dong sau 10s")
    print("  Nhan A / S / D / F de dung")
    print("  Di chuot goc tren-trai = dung khan cap")
    print("=" * 50)

    for key in STOP_KEYS:
        keyboard.add_hotkey(key, stop_event.set)

    threading.Thread(target=tab_loop, daemon=True).start()

    print("[...] Cho 10s de ban chuan bi file...")
    for i in range(10, 0, -1):
        if stop_event.is_set():
            return
        print(f"  {i}s...", end="\r")
        time.sleep(1)
    print("[GO] Bat dau!")

    consecutive_static = 0

    try:
        while not stop_event.is_set():
            before = pyautogui.screenshot()

            random_mouse_for(4)
            if stop_event.is_set():
                break

            scroll_down_and_click()

            random_mouse_for(5)
            if stop_event.is_set():
                break

            after = pyautogui.screenshot()
            diff  = img_diff(before, after)
            print(f"[Check] Diff = {diff:.2f}")

            if diff < 2.0:
                consecutive_static += 1
                print(f"[!] Khong cuon dc ({consecutive_static}/2)")
                if consecutive_static >= 2:
                    scroll_to_top()
                    consecutive_static = 0
            else:
                consecutive_static = 0

    except pyautogui.FailSafeException:
        print("\n[!] Dung khan cap.")
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C.")
    finally:
        stop_event.set()
        keyboard.unhook_all()
        print("Da dung.")


if __name__ == "__main__":
    main()
