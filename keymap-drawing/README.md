# Keymap picture

`cosmos.svg` / `cosmos.png` are drawn from `../boards/shields/cosmos/cosmos.keymap` with [keymap-drawer](https://github.com/caksoylar/keymap-drawer). Rerun after keymap edits (from `zmk-config-cosmos/`):

```sh
KD="uvx --from keymap-drawer --with tree-sitter==0.24.* --with tree-sitter-devicetree<0.15"
$KD keymap -c keymap-drawing/config.yaml parse -z boards/shields/cosmos/cosmos.keymap -o keymap-drawing/cosmos.yaml
$KD keymap -c keymap-drawing/config.yaml draw keymap-drawing/cosmos.yaml -d boards/shields/cosmos/cosmos-layouts.dtsi -s Base Lower Sym -o keymap-drawing/cosmos.svg
rsvg-convert -z 2 -b white keymap-drawing/cosmos.svg -o keymap-drawing/cosmos.png
```

The tree-sitter pins work around a keymap-drawer/tree-sitter version clash. Studio-saved changes are not in the `.keymap` file, so they don't appear here.
