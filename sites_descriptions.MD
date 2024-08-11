
NNWS - No Name Wall System V0.1 - Beta

This is yet another Wall System. Please refrain from printing a whole wall yet; this is more to gather feedback for now.

I took a different approach for creating this. Instead of providing .STL files and letting people try to re-engineer compatible accessories, I created a Fusion 360 Add-In that lets users generate the Wall and the Base Accessories that are compatible. These anchors and inserts (as I called them and that I will explain later) are a direct fit to the wall system, and accessories can be designed on top of these.

I've included some base .stl files if you don't want to use Fusion 360. Some accessories will need to be generated with Fusion 360 or at least modified to be useful. I’m thinking of the shelf system; I haven’t generated any useful inserts yet but will work on that later. (or people can start generating some, that’s the goal of this, to be open-source and community-driven)

STLs are divided into 2 main sections:

- Wall:
  - Walls can have notches or not. Notches let inserts "lock" in place and are positioned at 45 degrees inside the insert receiver. I’ve uploaded different wall sizes for notched and non-notched walls. I prefer printing the notched version as they don’t interfere with anything, but it takes a bit more time to print, which I think is negligible at this point.

- Accessories:
  - Main Screw: The main wall anchoring method for inserts.
    - Only 1 main screw, no other option.
  - Base Insert: This is held by the Main Screw in the wall.
    - No files for this; it is useless on its own. Accessories use this to be screwed to the wall, but something needs to be designed on it to be useful. This option is more for the Fusion 360 plugin.
  - Shelf Support: Shelf support that snaps in for different needs.
    - Contains various sizes of shelf support, all matching Gridfinity size to be compatible and allow better spacing between different shelves.
  - Shelf Insert: The actual insert on which you can design a shelf or other accessories.
    - Contains various sizes of insert with a plain top where accessories can be designed.
  - Fastening Anchor: An insert that lets you add a screw to an existing insert.
    - Contains various options for different screw definitions.
  - Offset Anchor: Same as Fastening Anchor, but lets you offset the screw for aligning to pegboard.
    - Same idea as the Fastening Anchor for different screw definitions.

What This Wall System Is Trying to Achieve (Pros):

- Decouple the anchoring and the accessories: This means that the Wall system can be anchored to the wall, cabinet, etc., without interfering with the accessories.
- Accessories are firmly held to the wall system: All are screw-driven. Accessories can take a good amount of weight before giving up, and it will most likely be the plastic that gives up first.
- Simplicity: The wall system itself is simple, only a few parts are needed, and they can be re-used over and over.
- Compatible with Gridfinity: The whole design was based on being compatible, and the width of the wall units is 42 mm.
- Integration with FusionGridfinityGenerator: This Add-In works with the FusionGridfinityGenerator Add-In. The base inserts are created offset to the origin to allow a Gridfinity base to be created and connected. It has been tested with the Full and Skeleton and default settings. You can generate the baseplate using this plugin and then generate inserts for the width of the baseplate.

What This Wall System Is Not (Cons):

- Not lightweight: The wall itself is a bit heavier on filament. This is arguable and listed as a con, but considering the simplicity and reusability of the anchors and main screw, savings are done on the accessories.
- Not directly compatible with existing wall systems: The goal was to have something different. This could be easily addressed by making an accessory with NNWS insert. While not in the future plan, I’m not against it and would be willing to integrate it into the Add-In if someone wants to make a PR. Another option would be to generate inserts, CAD the adapter, and publish the .STL.

Fusion 360 Add-in and full documentation can be found here: https://github.com/thewelder76/NNWS
