# Anthropomorphic (Bipedal Animal) Character Design Theory

Source: "How to Draw Furries, aka Anthropomorphic Characters" (Envato Tuts+,
https://design.tutsplus.com/articles/how-to-draw-furries-aka-anthropomorphic-characters--cms-30243).
A written article, not a video -- read directly, not transcribed. No hard numeric ratios are
given (the article deliberately avoids them, see below), so treat this as design judgment
calls, not formulas to plug into `base_body.py`.

Also checked: "Creating an anthropomorphic animal in Blender 2.92 using the mirror modifier"
(YouTube, https://www.youtube.com/watch?v=HpkXcir-fkg) -- auto-captions fetched but this one
didn't pan out: it's live, un-planned manual box-modeling with no reference sheet ("downside of
not using a reference image directly here in blender," said mid-video) and no extractable
proportion rules beyond generic reminders (sloping shoulders, leave space between the legs,
don't make legs too fat). Not worth a dedicated skill entry; noting here so we don't re-fetch it.

## Core principle: standing an animal on two legs is not enough

"Simply making an animal stand on two legs makes it automatically look human-like" is called
out as the lazy version. Human legs have specific structural adaptations for upright
locomotion that a straight animal leg lacks -- a bipedal character needs its leg structure
actually modified toward human proportions, not just re-oriented vertically. This validates
`base_body.py`'s existing approach (Zayn's legs are a deliberate humanoid-bipedal build, not a
camel's actual quadruped leg literally stood on end) rather than being an oversight.

## Blending process (their recommended method)

1. Study skeletal proportions of the human and the target animal SEPARATELY first.
2. Sketch a simplified skeleton for each, from multiple angles.
3. Learn the "recipe" of RELATIVE bone-length ratios for each (their example: "the forearm is
   slightly shorter than the upper arm") -- relative, not absolute measurements.
4. Combine the two recipes deliberately, weighing locomotion function alongside appearance,
   rather than pasting one skeleton onto the other.

## Shape derivation order

Final silhouette comes from **muscle, then fat, then fur, in that order** -- fur direction
follows the muscle/fat form underneath, so if we ever add fur/hair geometry to Zayn, it should
be authored to follow the existing body silhouette's flow, not applied as a uniform shell.

## Non-negotiable "make it read as expressive" features

- Mobile eyebrows -- can be reskinned from an animal's own features (their example: repurposing
  whisker-like tufts as brow shapes) rather than added as a foreign human element.
- Flexible/mobile lips, for both speech and emotion.
- Visible eye whites -- needed for the audience to read gaze direction.
- Larger eyes generally read as more expressive.

**Relevance to Zayn**: all four of these are already present in the current design --
brow-ridge geometry, the added mouth, white sclera on the eyes (explicitly called out in
`base_body.py` as "the cheapest single fix for making the head read as a face"), and the
2026-08-17 eye-enlargement pass. This article is independent confirmation the existing design
calls were the right ones, not a new to-do list.

## Design philosophy

Every simplified/added detail (foot pads, jewelry, accessories) should serve a "purposeful"
role tied to the character's lifestyle, not be added arbitrarily. Relevant lens for evaluating
Zayn's cap+straws prop: it passes this test (ties to "camel stores water" as a joke/character
trait), but any future prop additions should be checked against the same bar.
