{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  nativeBuildInputs = with pkgs; [
    (python3.withPackages(ps: with ps; [
      pillow
      gphoto2
    ]))
  ];
}
