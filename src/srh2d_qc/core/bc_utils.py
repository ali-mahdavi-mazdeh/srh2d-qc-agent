def find_bc_elements(bc_nodes, mesh):
    bc_nodes = set(bc_nodes)
    bc_elements = []

    # mesh.elements is a list aligned with mesh.element_ids
    for eid, conn in zip(mesh.element_ids, mesh.elements):
        if any(n in bc_nodes for n in conn):
            bc_elements.append(eid)

    return bc_elements
