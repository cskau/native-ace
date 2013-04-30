#!/usr/bin/env python


import os

from PyQt4 import (
    QtCore,
    QtGui,
    QtWebKit,
    )


class FileDropZone(object):
  """Accept all file dropped on object and open URLs in new tabs"""

  editor = None

  def dragEnterEvent(self, event):
    event.accept()

  def dragMoveEvent(self, event):
    event.accept()

  def dropEvent(self, event):
    event.accept()
    if event.mimeData().hasUrls():
      for url in event.mimeData().urls():
        self.editor.add_new_tab(url.path())
    elif event.mimeData().hasText():
      text = event.mimeData().text()
      # TODO: new document with text


class WebBridge(QtCore.QObject):
  """Bridge object with javascript call-able python methods"""
  def __init__(self, parent=None, frame=None):
    super(WebBridge, self).__init__(parent)
#    self.setObjectName("WebBridge")
    self.frame = frame

#  def _pyVersion(self):
#    return sys.version
#  pyVersion = QtCore.pyqtProperty(str, fget = _pyVersion)

#  @QtCore.pyqtSignature('QString')
  @QtCore.pyqtSlot(str)
  def msg(self, msg):
    QtGui.QMessageBox.information(None, "Info", msg)

  @QtCore.pyqtSlot(str, result=str)
  def open_file(self, path):
    return open(path).read()

  def call(self, func_args):
    self.frame.evaluateJavaScript(func_args)


class EditorWidget(QtWebKit.QWebView, FileDropZone):
  """"""
  def __init__(self, parent=None, na_dir=None):
    super(EditorWidget, self).__init__(parent)
    self.load_ace(na_dir)
    self.web_bridge = WebBridge(frame=self.page().mainFrame())
    # attach "bridge" object with javascript call-able python methods
    self.page().mainFrame().addToJavaScriptWindowObject(
        'WebBridge',
        self.web_bridge,
        )

  def load_ace(self, na_dir):
    self.load(
        QtCore.QUrl(
            os.path.abspath(
                os.path.join(
                    na_dir,
                    "./html/ace.html",
                    )
                )
            )
        )

  def open_file(self, file_path):
    self.page().mainFrame().loadFinished.connect(
        lambda: self.on_load_finished(file_path)
        )

  def on_load_finished(self, file_path):
    self.web_bridge.call(
        'openFile("{}")'.format(file_path),
        )

  def save(self):
    file_content = self.web_bridge.call("getContent()")
    file_path = self.web_bridge.call("getFilePath()")
    if file_path is None:
      file_path = QtGui.QFileDialog.getSaveFileName(self)
    if file_path:
      open(file_path, 'w').write(file_content)


class EditorTabWidget(QtGui.QTabWidget, FileDropZone):
  """Dummy class to combine QtGui.QTabWidget and FileDropZone"""
  pass


class EditorApp(object):
  """"""

  done = QtCore.pyqtSignal()

  def __init__(self, sys_argv, na_dir, style_sheet='./css/app.css'):
    self.app = QtGui.QApplication(sys_argv)
    self.main_window = QtGui.QMainWindow()
    self.status_bar = self.main_window.statusBar()
    self.tab_widget = EditorTabWidget()

    self.na_dir = na_dir

#    self.app.setWindowIcon()
    try:
      self.main_window.setStyleSheet(
          open(
              os.path.abspath(
                  os.path.join(
                      na_dir,
                      style_sheet,
                      )
                  )
              ).read()
          )
    except Exception as e:
      pass
      #raise e

    self.main_window.resize(800, 600)

    self.label_position = QtGui.QLabel('')
    self.label_spell = QtGui.QLabel('')
    self.label_indent = QtGui.QLabel('')
    self.label_highlight = QtGui.QLabel('')

    # far left of first permanent, obscured by temp msg
#    self.status_bar.addWidget(
    # far right, not obscured by temp msg
#    self.status_bar.addPermanentWidget(

    self.status_bar.addPermanentWidget(
        self.label_position,
        stretch=True,
        )
    self.status_bar.addPermanentWidget(
        self.label_spell,
        stretch=False,
        )
    self.status_bar.addPermanentWidget(
        self.label_indent,
        stretch=False,
        )
    self.status_bar.addPermanentWidget(
        self.label_highlight,
        stretch=False,
        )

    self.settings = QtWebKit.QWebSettings.globalSettings()
    self.settings.setAttribute(
        QtWebKit.QWebSettings.JavascriptEnabled,
        True
        )
    self.settings.setAttribute(
        QtWebKit.QWebSettings.DeveloperExtrasEnabled,
        True
        )

    self.tab_widget.setTabsClosable(True)
    self.tab_widget.setMovable(True)
    self.tab_widget.setUsesScrollButtons(True)
    self.tab_widget.setAcceptDrops(True)
    self.tab_widget.setWindowTitle('Native Ace')
#    self.tab_widget.setIconSize(QtCore.QSize(72, 72))
    self.tab_widget.setTabShape(
#        QtGui.QTabWidget.Rounded, # 0; default
        QtGui.QTabWidget.Triangular, # 1
        )
    self.tab_widget.editor = self
    
    # Work-around for render bug (?) with draggable tabs
    self.tab_widget.setDocumentMode(True)

    self.tab_widget.tabCloseRequested.connect(
        self.close_tab
        )

    QtGui.QShortcut(
        QtGui.QKeySequence("Ctrl+O"),
        self.tab_widget,
        self.open,
        )
    QtGui.QShortcut(
        QtGui.QKeySequence("Ctrl+T"),
        self.tab_widget,
        self.add_new_tab,
        )
    QtGui.QShortcut(
        QtGui.QKeySequence("Ctrl+N"),
        self.tab_widget,
        self.add_new_tab,
        )
    QtGui.QShortcut(
        QtGui.QKeySequence("Ctrl+W"),
        self.tab_widget,
        self.close_tab,
        )
    QtGui.QShortcut(
        QtGui.QKeySequence("Ctrl+S"),
        self.tab_widget,
        self.save_tab,
        )
    QtGui.QShortcut(
        QtGui.QKeySequence("Ctrl+G"),
        self.tab_widget,
        self.update_status_bar,
        )

    for file_path in sys_argv[1:]:
      self.add_new_tab(file_path)

    self.main_window.setCentralWidget(self.tab_widget)

    self.update_status_bar()

  def run(self):
    self.main_window.show()
    # Quit when done
#    self.done.connect(self.app.quit)
    return self.app.exec_()

  def exit(self, ok):
    self.done.emit()

  def add_new_tab(self, file_path=None):
    new_editor_tab = EditorWidget(na_dir=self.na_dir)
    new_editor_tab.setAcceptDrops(True)

    if file_path:
      new_editor_tab.open_file(file_path)

    # FileDropZone
    new_editor_tab.editor = self

    tab_name = 'untitled'
    if file_path:
      tab_name = os.path.basename(file_path)

    new_tab_index = self.tab_widget.addTab(new_editor_tab, tab_name)
    self.tab_widget.setCurrentIndex(new_tab_index)
    
    self.update_status_bar()

  def open(self):
    file_name = QtGui.QFileDialog.getOpenFileName(
        self.tab_widget,
#        'Open File',
        )
    if not file_name:
      return
    self.add_new_tab(file_name)

  def close_tab(self, tab_index=None):
    self.tab_widget.removeTab(
        tab_index if tab_index else self.tab_widget.currentIndex()
        )

  def save_tab(self, tab_index=None):
    self.tab_widget.currentWidget().save()

  def update_status_bar(self):
#    self.status_bar.showMessage('I\'m a status bar!')
    if self.tab_widget.currentWidget():
        cursor_position = self.tab_widget.currentWidget().web_bridge.call(
            "getCursorPosition()"
            )
        self.label_position.setText('')
        self.label_spell.setText('')
        self.label_indent.setText('')
        self.label_highlight.setText('')
