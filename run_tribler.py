import os
import sys
import multiprocessing
import logging  # TODO: Remove this import

if __name__ == "__main__":
    multiprocessing.freeze_support()

    from TriblerGUI.tribler_app import TriblerApplication
    from TriblerGUI.tribler_window import TriblerWindow

    app = TriblerApplication("triblerapp", sys.argv)

    # TODO: Remove these logging lines (suppresses Tribler spamming of the console)
    logger = logging.getLogger()
    logger.disabled = True

    if app.is_running():
        for arg in sys.argv[1:]:
            if os.path.exists(arg):
                app.send_message("file:%s" % arg)
            elif arg.startswith('magnet'):
                app.send_message(arg)
        sys.exit(1)

    window = TriblerWindow()
    window.setWindowTitle("Tribler")
    app.set_activation_window(window)
    app.parse_sys_args(sys.argv)
    sys.exit(app.exec_())
