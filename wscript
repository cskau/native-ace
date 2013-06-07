#!/usr/bin/env python
#encoding: utf-8


top = '.'
out = 'build'


def configure(ctx):
  pass

def build(ctx):
  # copy over pre-built Ace files from submodule
  ctx(
      rule='cp ${SRC} ${TGT}',
      source='submodules/ace-builds/src-min-noconflict/*',
      target='js/ace/',
      )