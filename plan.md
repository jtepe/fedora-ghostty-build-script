# Plan

I want you to write a Python script in the empty file `main.py`. The script should download the Ghostty terminal application source code. Then build and install it using the Zig
programming language as build dependency. Zig must also be downloaded beforehand, unless it has been previously downloaded.

## Detailed Tasks

[ ] The version of ghostty to download and build is provided as a command line parameter, but there should be a default of `1.2.0`
[ ] The download is a release zip file. It can be downloaded from https://release.files.ghostty.org/VERSION/ghostty-VERSION.tar.gz
[ ] The zip file signature must be downloaded from https://release.files.ghostty.org/VERSION/ghostty-VERSION.tar.gz.minisig
[ ] Validate the release zip file against the signature using the public key RWQlAjJC23149WL2sEpT/l0QKy7hMIFhYdQOFy0Z7z7PbneUgvlsnYcV
[ ] Download the Zig dependency to build the source from https://ziglang.org/download/0.14.1/zig-x86_64-linux-0.14.1.tar.xz
[ ] Extract Zig (.tar.xz) into a directory called `compiler`. The archive should contain the `zig` binary and a `lib` directory. They must be placed in `compiler`
[ ] Download an extract Zig only if there is not already a Zig binary in `compiler`
[ ] Extract ghostty.tar.gz into the root directory and build it from this directory with the command `zig build -p $HOME/.local -Doptimize=ReleaseFast`
[ ] Afterwards verify the built succeeded and the build artifact has indeed been placed in the `$HOME/.local` directory

## Further Notes

[ ] Provide detailed output messages while performing the tasks. Use colored output for the messages
[ ] Suppress the output from the build command. Only if there is an error should be the error message be output.
[ ] For Python project management `uv` is used. Dependencies, if any, can be managed with `uv`. For a dependency `foo` it can be added to the script by running `uv add --script main.py 'foo'`

## Desktop integration

[ ] Ghostty comes with a .desktop file. located in $GHOSTTY_EXTRACTED/dist/linux/app.desktop.in
    The file should be placed in $HOME/.local/share/applications/ghostty.desktop
    Variable replacements in the file:
      - @NAME@ => Ghostty
      - @GHOSTTY@ => ghostty
[ ] Standard Ghostty configuration options used are (located in $HOME/.config/ghostty/config)
    ```
    maximize = true
    font-size = 10
    ```
