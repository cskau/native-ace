#!/usr/bin/env python


import sys
import os

from py.editor_app import EditorApp


if __name__ == '__main__':
  na_dir = os.path.dirname(os.path.realpath(__file__))
  app = EditorApp(sys.argv, na_dir)
  sys.exit(
      app.run()
      )