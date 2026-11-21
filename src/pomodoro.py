
import time
import msvcrt

try:
    import winsound
except ImportError:
    winsound = None

# -----------------------------
# FocusGuard AI - Pomodoro v2
# -----------------------------

TEST_MODE = True

if TEST_MODE:
    STUDY_DURATION = 25
    SHORT_BREAK = 5
    LONG_BREAK = 10
else:
    STUDY_DURATION = 25 * 60
    SHORT_BREAK = 5 * 60
    LONG_BREAK = 15 * 60

LONG_BREAK_EVERY = 4

mode = "STUDY"
remaining_time = STUDY_DURATION
running = False
completed_sessions = 0


def play_sound():
    if winsound:
        winsound.Beep(1000, 500)


def reset_timer():
    global remaining_time, running

    if mode == "STUDY":
        remaining_time = STUDY_DURATION
    elif mode == "SHORT BREAK":
        remaining_time = SHORT_BREAK
    else:
        remaining_time = LONG_BREAK

    running = False


def display_timer():
    minutes = remaining_time // 60
    seconds = remaining_time % 60

    print(
        f"\rMode: {mode:<12} | "
        f"Timer: {minutes:02d}:{seconds:02d} | "
        f"Completed: {completed_sessions} | "
        f"{'RUNNING' if running else 'PAUSED'}   ",
        end="",
        flush=True
    )


print("===================================")
print("   FOCUSGUARD AI - POMODORO v2")
print("===================================")
print("S = Start / Pause")
print("R = Reset")
print("Q = Quit")
print("-----------------------------------")

while True:

    display_timer()

    # Keyboard controls
    if msvcrt.kbhit():

        key = msvcrt.getch().decode(
            "utf-8", errors="ignore"
        ).lower()

        if key == "s":
            running = not running

        elif key == "r":
            reset_timer()

        elif key == "q":
            print("\nPomodoro timer stopped.")
            break

    # Countdown
    if running:

        time.sleep(1)
        remaining_time -= 1

        if remaining_time <= 0:

            play_sound()
            running = False

            if mode == "STUDY":

                completed_sessions += 1

                print("\n\nStudy session completed!")

                if completed_sessions % LONG_BREAK_EVERY == 0:
                    mode = "LONG BREAK"
                    remaining_time = LONG_BREAK
                    print("You've completed 4 sessions! Take a long break.")
                else:
                    mode = "SHORT BREAK"
                    remaining_time = SHORT_BREAK
                    print("Time for a short break!")

            else:

                print("\n\nBreak completed! Back to studying.")
                mode = "STUDY"
                remaining_time = STUDY_DURATION

    else:
        time.sleep(0.1)

print("\n========== POMODORO SUMMARY ==========")
print(f"Completed study sessions: {completed_sessions}")
print("===================================")
