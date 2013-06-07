#!/usr/bin/env python
#encoding: utf-8


top = '.'
out = '.'


def configure(ctx):
  pass

def build(bld):
  bld(
      rule='mkdir -p ${TGT}',
      target='js/ace/',
      )
  bld(
      rule='cp ${SRC} ${TGT}',
      source=bld.path.ant_glob('submodules/ace-builds/src-min-noconflict/*'),
      target='js/ace/',
      )