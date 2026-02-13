{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Python and essential build tools
    (python313.withPackages (ps: with ps; [
      setuptools
      wheel
      pip
      tkinter
      pyqt6
      
      # Python dependencies available in Nixpkgs
      altgraph
      appdirs
      asttokens
      bleak
      click
      devtools
      executing
      loguru
      macholib
      markdown-it-py
      mdurl
      packaging
      pillow
      pycairo
      pygments
      pyinstaller
      rich
      six
      wand
    ]))

    # Native System Libraries (Needed for C-extensions)
    cairo
    pkg-config
    imagemagick
    zlib
    libjpeg
  ];

  shellHook = ''
    echo "NixOS Python Dev Environment Loaded"
  '';
}