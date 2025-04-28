import threading
import checkcoord
import main
import mainbot

if __name__ == "__main__":
    threading.Thread(target=mainbot.start_bot).start()
    main.start_site()
    print("zxc")