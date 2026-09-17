import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)
from edu_air.ui import ClassroomWindow, make_session
from edu_air import i18n

sess = make_session(mode="demo")
win = ClassroomWindow(sess)
win.show()

results = {}
log = []


def step1():
    win._change_language("nl")
    log.append(("nl_title", win.windowTitle()))
    log.append(("nl_mode_btn", win._mode_btn.text()))
    log.append(("nl_sens", [win.sensitivity_combo.itemText(i)
                            for i in range(win.sensitivity_combo.count())]))
    log.append(("nl_lang", [win.lang_combo.itemText(i)
                            for i in range(win.lang_combo.count())]))
    log.append(("nl_status_mode", win._status_labels["mode"].text()))
    log.append(("nl_status_tool", win._status_labels["tool"].text()))
    QTimer.singleShot(300, step2)


def step2():
    win._change_language("ar")
    log.append(("ar_title", win.windowTitle()))
    log.append(("ar_dir", str(win.layoutDirection())))
    log.append(("ar_sub", win._sub_lbl.text()))
    log.append(("ar_tool_draw", win._tool_buttons["draw"].text()))
    log.append(("ar_hint", win._hint_lbl.text()))
    QTimer.singleShot(300, step3)


def step3():
    win._change_language("en")
    log.append(("en_title", win.windowTitle()))
    results["ok"] = True
    app.quit()


QTimer.singleShot(200, step1)
app.exec()
win.close()
for k, v in log:
    print(f"{k} = {v}")
sys.exit(0 if results.get("ok") else 1)