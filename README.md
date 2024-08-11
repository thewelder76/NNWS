# NNWS - No Name Wall System
## Version 0.1-beta

This is yet another Wall System.

Keep in mind that I haven't tested all possibilities. Please refrain from printing a whole wall yet; this is more to gather feedback for now.

I took a different approach for creating this. Instead of providing .STL files and letting people try to re-engineer compatible accessories, I created a Fusion 360 Add-In that lets users generate the Wall and the Base Accessories that are compatible. These anchors and inserts (as I called them and that I will explain later) are a direct fit to the wall system, and accessories can be designed on top of these.

## What This Wall System Is Trying to Achieve (Pros)
- **Decouple the anchoring and the accessories:** This means that the Wall system can be anchored to the wall, cabinet, etc., without interfering with the accessories.
- **Accessories are firmly held to the wall system:** All are screw-driven. Accessories can take a good amount of weight before giving up, and it will most likely be the plastic that gives up first.
- **Simplicity:** The wall system itself is simple, only a few parts are needed, and they can be re-used over and over.
- **Compatible with [Gridfinity](https://youtu.be/ra_9zU-mnl8?si=yMzSUbPgD5LrzTYr):** The whole design was based on being compatible, and the width of the wall units is 42 mm. 
- **Integration with FusionGridfinityGenerator:** This Add-In works with the [FusionGridfinityGenerator Add-In](https://github.com/Le0Michine/FusionGridfinityGenerator). The base inserts are created offset to the origin to allow a Gridfinity base to be created and connected. It has been tested with the Full and Skeleton and default settings. You can generate the baseplate using this plugin and then generate inserts for the width of the baseplate.

## What This Wall System Is Not (Cons)
- **Not lightweight:** The wall itself is a bit heavier on filament. This is arguable and listed as a con, but considering the simplicity and reusability of the anchors and main screw, savings are done on the accessories.
- **Not directly compatible with existing wall systems:** The goal was to have something different. This could be easily addressed by making an accessory with NNWS insert. While not in the future plan, I'm not against it and would be willing to integrate it into the Add-In if someone wants to make a PR. Another option would be to generate inserts, CAD the adapter, and publish the .STL.

The plugin has a dropdown menu for different accessories with different settings. Current options: (TODO: Video)
- **Main Screw**: The main wall anchering method for inserts.
- **Base Insert**: This is what is held by the Main Screw in the wall
- **Shelf Support**: Shelf support that let snap-in for different needs
- **Shelf Insert** : Customizable snap-in insert for Shelf, no need to re-print the whole thing.
- **Fastening Anchor**: Wall anchering to wall, pegbord, ...
- **Offset Fastening Anchor**: Same as Fastening Anchor, bet let you offset the screw for aligning to pegboard for

## Future Improvements
- **Dual-Sided Screw System for Insert Mounting**: Provide a way to have an insert and screw system that will allow screwing from the front and also from the back of an insert. This will remove the need for extra spacing to insert the wall screw into inserts of shelves and accessories.
- **Border Generation:** My plan was to add Border Generation and Offset for wall Generation. I still want to add this, but it is not a top priority right now. I focused on a basic wall and the accessories so this can start to be used; will get to that at some point.
- **Border Offset:** This is to offset a row of wall so different shapes can be done, like going around a light switch. I decided that this was low priority as someone can always use Fusion to modify the wall to their needs, but it is still in the plan to do.
- **Screw Definitions:** Need to add more screw definitions for the anchors. Did not test all definitions; they might have to be adjusted.
- **Wall Offset:** This one might require a Wall change. I'll keep the wall compatible with existing accessories, but the current wall won't be able to be offset right now.
- **Save user's settings.**

## Fusion 360 Add-In Installation
- **From source:** (TODO: Insert images)
  1. Get the code locally (Only available trought git right now) ```git clone https://github.com/thewelder76/NNWS_fusion360```
  2. Open the `Sript and Add-Ins` Dialog
  3. Choose the `Add-Ins` tab and click the + besides `My Add-ins`
  4. Choose the path of the repo cloned at step 1 and click `Open`
- **From Autodesk App Store?:** Not published yet, will see if it's worth it.

Supported OS: macOS (Should work on Windows, but I did not test it and I don't have a machine available to test it). I would need help with that. I'm not using anything OS-related, so it should work.

## Known Issues
- Fillet cannot be created when the shelf length is just over the insert attachment.
- Main screw creation fails sometimes. I don't know why; it's random. The workaround is to select another accessory and select main screw again or to uncheck/check the preview option, and it will most likely work, Sometimes it takes a few tries.

PRs are welcome. The goal is to share with the community and work together. It's quite possible that the Add-In has issues; I haven't tested all combinations. Please create a bug report if you find something.

## TODO
- Publish on Autodesk Add-In.