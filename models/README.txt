Models live here. models/registry.json says which file each check uses:

  "skin": { "model": "skin_model.keras", "classes": "skin_classes.json", "threshold": 0.70, "interpolation": "nearest" }

To add Infection or Nail: put the .keras file and the classes .json here and add an entry to registry.json.
A check with no entry shows "Coming soon" in the app. No other code change is needed.
