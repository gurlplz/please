# Profile Picture Generator

A layered SVG avatar generator that combines traits (backgrounds, faces, eyes, mouths, hair, accessories, special features) into unique profile pictures. Each trait is a separate SVG file positioned for correct stacking.

## Features

- **Layered SVG traits** — All traits use `viewBox="0 0 100 100"` for consistent sizing
- **Random combinations** — Generate unique avatars with one click
- **Compatibility rules** — Monster faces pair with monster eyes/mouth; egg faces with cracks
- **Custom selection** — Override any trait via dropdowns
- **Download PNG** — Export your avatar

## Trait Categories

| Layer | Examples |
|-------|----------|
| Background | Solid colors, gradients |
| Face | Round, oval, egg (human & monster) |
| Eyes | Default, big, slanted, closed, happy, monster, alien |
| Mouth | Smile, neutral, smirk, grin, monster |
| Hair | Short, long, curly, spiky, mohawk, bob, bald |
| Accessory | None, hat, glasses, bow, headphones |
| Special | None, horns, antennae, egg cracks, alien ears, monster spikes |

## Run

```bash
npm start
```

Then open http://localhost:3000

Or use Python:
```bash
python3 -m http.server 3000
```

## Structure

```
traits/
  backgrounds/   # bg-solid-*.svg, bg-gradient-*.svg
  faces/         # face-round-*, face-oval-*, face-egg-*, face-monster-*
  eyes/          # eyes-default, eyes-big, eyes-monster, eyes-alien, etc.
  mouths/        # mouth-smile, mouth-neutral, mouth-monster, etc.
  hair/          # hair-short-*, hair-long-*, hair-spiky-*, hair-bald
  accessories/   # acc-none, acc-hat, acc-glasses, acc-bow, acc-headphones
  special/       # special-none, special-horns, special-antennae, etc.
  manifest.json  # Layer order + trait lists + compatibility
```
