# Play! · Con amigos

Fork: https://github.com/IsidroEmirPelli/play-con-amigos
Upstream: https://github.com/jpd002/Play-
Base: 505dac73149fece41b04dd961078ce3011a8bed5
Branch: codex/bt3-webgl-framebuffer

## Shader cache key regression

`SHADERCAPS` uses `uint64` storage. Its alpha-fail and depth-fetch fields occupy the upper word. `SetRenderingContext` compared the caps through `uint32`, so changing those fields could leave the previous shader selected even when the GS test register changed. Both comparisons now use `ShaderCapsInt`, preserving the full key.

`python3 tests/test_opengl_shader_caps.py` compiles the actual C++ caps declaration and cache comparison expressions, without a GPU dependency. It checks alpha-fail modes, depth-fetch flags, lower-bit changes and unchanged state. The test fails on the original implementation and passes with the full-width comparison.

This verifies the cache bug, not full Tenkaichi rendering correctness. Validate a 3D fight before calling the game's visual corruption fixed.

## Reproducible browser build

Install Emscripten 4.0.1, CMake >=3.18 and Ninja. Initialize all submodules, activate Emscripten, then:

```sh
emcmake cmake -S . -B build-web -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF -DBUILD_PSFPLAYER=OFF -DUSE_QT=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build-web --target Play --parallel 4
```

Artifacts: `build-web/Source/ui_js/Play.js` and `Play.wasm`. The Con amigos workflow attaches both binaries, source revision, submodule revisions and SHA-256 hashes to each branch build. It does not deploy a website or upload game data.

## Browser regression checkpoints

The fork adds non-blocking `saveState(path)`, `loadState(path)` and `pollStateOperation()` exports. Start functions return false if the VM is absent or another operation is pending. Poll returns 0 while pending, 1 on success, -1 on failure and -2 when idle. State bytes stay in the emulator's filesystem and can be read or written with `module.FS`. Never wait synchronously on a VM operation from the browser thread: graphics calls may need that thread.

Keep checkpoints and game files local. These APIs are intended to compare the same scene across renderer builds. A load resets GPU caches, so also validate scene entry from boot when investigating stale framebuffer data.
