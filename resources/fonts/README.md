# Embedding custom fonts (optional)

Questline ships using the device **system fonts** (see `source/ui/Fonts.mc`),
which keeps the project compiling everywhere with zero binary assets. The visual
spec calls for two embedded faces; wiring them in is a drop-in change.

## What the design asks for

- **Numbers / data** (countdown `09H 24M`, points, `1/3`, `1.7K`): a monospaced
  face such as **JetBrains Mono**.
- **Titles / labels**: a rounded, sturdy sans such as **Fredoka**, **Baloo 2**
  or **Poppins SemiBold**.

## Steps

1. Build a Connect IQ bitmap font (`.fnt` + companion `.png`) for each size you
   use. The usual path is [BMFont](https://www.angelcode.com/products/bmfont/)
   (or the `fontgen` style tooling) against the licensed `.ttf`.
2. Drop the files here, e.g. `JetBrainsMono-24.fnt` / `JetBrainsMono-24.png`.
3. Declare them in a `fonts.xml` resource:

   ```xml
   <fonts>
       <font id="MonoMedium"  filename="JetBrainsMono-24.fnt"/>
       <font id="RoundTitle"  filename="Fredoka-28.fnt"/>
   </fonts>
   ```

4. In `source/ui/Fonts.mc`, return the embedded font with a system fallback:

   ```monkeyc
   function mono() {
       return WatchUi.loadResource(Rez.Fonts.MonoMedium);
   }
   ```

Because everything in `Fonts.mc` is funnelled through one module, no view code
changes. Confirm the font license permits redistribution before shipping.
