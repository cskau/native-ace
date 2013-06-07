#!/usr/bin/env python


import os

from PyQt4 import (
    QtCore,
    QtGui,
    QtWebKit,
    )


MODES = [
  'ace/mode/abap',
  'ace/mode/asciidoc',
  'ace/mode/c9search',
  'ace/mode/c_cpp',
  'ace/mode/clojure',
  'ace/mode/coffee',
  'ace/mode/coldfusion',
  'ace/mode/csharp',
  'ace/mode/css',
  'ace/mode/curly',
  'ace/mode/dart',
  'ace/mode/diff',
  'ace/mode/django',
  'ace/mode/dot',
  'ace/mode/glsl',
  'ace/mode/golang',
  'ace/mode/groovy',
  'ace/mode/haml',
  'ace/mode/haxe',
  'ace/mode/html',
  'ace/mode/jade',
  'ace/mode/java',
  'ace/mode/javascript',
  'ace/mode/json',
  'ace/mode/jsp',
  'ace/mode/jsx',
  'ace/mode/latex',
  'ace/mode/less',
  'ace/mode/liquid',
  'ace/mode/lisp',
  'ace/mode/livescript',
  'ace/mode/lua',
  'ace/mode/luapage',
  'ace/mode/lucene',
  'ace/mode/makefile',
  'ace/mode/markdown',
  'ace/mode/objectivec',
  'ace/mode/ocaml',
  'ace/mode/perl',
  'ace/mode/pgsql',
  'ace/mode/php',
  'ace/mode/powershell',
  'ace/mode/python',
  'ace/mode/r',
  'ace/mode/rdoc',
  'ace/mode/rhtml',
  'ace/mode/ruby',
  'ace/mode/scad',
  'ace/mode/scala',
  'ace/mode/scheme',
  'ace/mode/scss',
  'ace/mode/sh',
  'ace/mode/sql',
  'ace/mode/stylus',
  'ace/mode/svg',
  'ace/mode/tcl',
  'ace/mode/tex',
  'ace/mode/text',
  'ace/mode/textile',
  'ace/mode/tm_snippet',
  'ace/mode/typescript',
  'ace/mode/vbscript',
  'ace/mode/xml',
  'ace/mode/xquery',
  'ace/mode/yaml',
]

EXT_MODE = {
  '.py': 'ace/mode/python',
  '.css': 'ace/mode/css',
  '.svg': 'ace/mode/svg',
  '.htm': 'ace/mode/html',
  '.html': 'ace/mode/html',
  '.js': 'ace/mode/javascript',
}


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

  state_change = QtCore.pyqtSignal()

  def __init__(self, parent=None, frame=None):
    super(WebBridge, self).__init__(parent)
#    self.setObjectName("WebBridge")
    self.frame = frame

  def call(self, func_args):
    """Method for calling functions in JavaScript from Python"""
    return self.frame.evaluateJavaScript(func_args)

#  def _pyVersion(self):
#    return sys.version
#  pyVersion = QtCore.pyqtProperty(str, fget = _pyVersion)

  # Python methods callable from JavaScript

#  @QtCore.pyqtSignature('QString')
  @QtCore.pyqtSlot(str)
  def msg(self, msg):
    QtGui.QMessageBox.information(None, "Info", msg)

  @QtCore.pyqtSlot(str, result=str)
  def open_file(self, path):
    return open(path).read()

  @QtCore.pyqtSlot()
  def signal_state_change(self):
    self.state_change.emit()


class StatusLabel(QtGui.QLabel):
  """"""

  choice = QtCore.pyqtSignal(str)

  def __init__(self, label='', parent=None):
    QtGui.QLabel.__init__(self, label, parent=parent)

    self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.connect(
        self,
        QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'),
        self.on_context_menu,
        )

    # Popup Menu
    self.popMenu = QtGui.QMenu(self)
#    self.popMenu.addSeparator()
    for syntax in MODES:
      action = self.popMenu.addAction(syntax)
      self.connect(
          action,
          QtCore.SIGNAL('triggered()'),
          lambda s=syntax: self.choice.emit(s),
          )

  def on_context_menu(self, point):
    self.popMenu.exec_(self.mapToGlobal(point))


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
    self.web_bridge.call(
        'onCursorChange(WebBridge.signal_state_change)'
        )
    root, ext = os.path.splitext(file_path)
    mode = 'ace/mode/text'
    if ext in EXT_MODE:
      mode = EXT_MODE[ext]
    self.web_bridge.call(
        'setMode(\'{}\')'.format(mode)
        )

  def save(self):
    file_content = self.web_bridge.call("getContent()")
    file_path = self.web_bridge.call("getFilePath()")
    if file_path is None:
      file_path = QtGui.QFileDialog.getSaveFileName(None)
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

    self.label_position = StatusLabel()
    self.label_spell = StatusLabel()
    self.label_indent = StatusLabel()
    self.label_highlight = StatusLabel()

    self.label_highlight.choice.connect(self.change_syntax)

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

    new_editor_tab.web_bridge.state_change.connect(self.update_status_bar)

  def open(self):
    file_name = QtGui.QFileDialog.getOpenFileName(
#        self.tab_widget,
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
    current_widget = self.tab_widget.currentWidget()
    if current_widget:
        cursor_position = current_widget.web_bridge.call(
            "getCursorPosition()"
            )
        mode = current_widget.web_bridge.call(
            "getMode()"
            )
        indent = current_widget.web_bridge.call(
            "getIndent()"
            )
        if cursor_position:
          self.label_position.setText(
              'INSERT MODE, Line {}, Column {}'.format(
                  int(cursor_position['row']) + 1,
                  int(cursor_position['column']) + 1,
                  )
              )
        self.label_spell.setText(
            'Spelling who?'
            )
        if indent:
          self.label_indent.setText(
              (
                  'Spaces: {}'
                  if indent['useSoftTabs']
                  else 'Tabs'
                  ).format(
                      int(indent['tabSize'])
                      )
              )
        if mode:
          self.label_highlight.setText(
              mode
              )

  def change_syntax(self, choice):
    self.tab_widget.currentWidget().web_bridge.call(
        'setMode(\'{}\')'.format(choice)
        )
