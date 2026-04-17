def fix_missing_materials(model):
    """
    Assign default material ID to any element with missing material (-1).
    Only applies when exactly one material exists.
    """

    mesh = model.mesh
    mats = model.materials

    # If multiple materials exist, do nothing (LLM will handle later)
    if len(mats["names"]) != 1:
        return False  # no fix applied

    default_mid = list(mats["names"].keys())[0]

    missing = (mesh.material_ids == -1)
    num_missing = missing.sum()

    if num_missing == 0:
        return False  # nothing to fix

    mesh.material_ids[missing] = default_mid
    return True  # fix applied
