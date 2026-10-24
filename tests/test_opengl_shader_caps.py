"""Compile the renderer's actual private caps and cache comparisons without a GL context.

Run: python3 tests/test_opengl_shader_caps.py
This intentionally extracts existing C++ declarations/expressions instead of maintaining
another copy of the shader key layout or a Python model of the comparison.
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
header = (root / 'Source/gs/GSH_OpenGL/GSH_OpenGL.h').read_text()
source = (root / 'Source/gs/GSH_OpenGL/GSH_OpenGL.cpp').read_text()
caps = header.split('struct SHADERCAPS :', 1)[1].split('static_assert', 1)[0].strip()
caps = 'struct SHADERCAPS :' + caps
changed = re.search(r'bool shaderChanged = ([^;]+);', source).group(1)
equal = re.search(r'\(static_cast<[^>]+>\(m_renderState.shaderCaps\) == static_cast<[^>]+>\(shaderCaps\)\)', source).group(0)
program = '''
#include <cassert>
#include "Types.h"
#include "Convertible.h"
using ShaderCapsInt = uint64;
enum {TEXTURE_SOURCE_MODE_IDX4=2, TEXTURE_SOURCE_MODE_IDX8=3};
CAPS
static_assert(sizeof(SHADERCAPS) == sizeof(ShaderCapsInt));
struct State { bool isValid = true; SHADERCAPS shaderCaps; };
bool changed(State m_renderState, SHADERCAPS shaderCaps) {return CHANGED;}
bool equal(State m_renderState, SHADERCAPS shaderCaps) {return EQUAL;}
int main() {
 const auto base=make_convertible<SHADERCAPS>(0);
 const State cached{true,base};
 assert(!changed(cached,base) && equal(cached,base));
 for(unsigned mode=1;mode<4;mode++) {
  auto next=base; next.alphaFailMethod=mode;
  assert(static_cast<ShaderCapsInt>(next) != static_cast<ShaderCapsInt>(base));
  assert(changed(cached,next) && !equal(cached,next));
 }
 auto next=base; next.alphaTestDepthTest_DepthFetch=1;
 assert(changed(cached,next) && !equal(cached,next));
 next=base; next.alphaTestDepthTestEqual_DepthFetch=1;
 assert(changed(cached,next) && !equal(cached,next));
 next=base; next.texFunction=1;
 assert(changed(cached,next) && !equal(cached,next));
 assert(changed(State{false,base},base));
}
'''.replace('\nCAPS\n', '\n'+caps+'\n').replace('CHANGED', changed).replace('EQUAL', equal)
with tempfile.TemporaryDirectory(prefix='play-shader-caps-') as tmp:
    src=Path(tmp)/'caps.cpp'
    src.write_text(program)
    binary=Path(tmp)/'caps-test'
    subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-fno-strict-aliasing',
                    '-I'+str(root/'deps/Framework/include'),str(src),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
print('OpenGL shader cache: complete 64-bit keys passed')
