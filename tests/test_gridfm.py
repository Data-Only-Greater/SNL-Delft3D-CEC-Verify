# -*- coding: utf-8 -*-

import numpy as np
import xarray as xr

from snl_d3d_cec_verify.gridfm import write_gridfm_rectangle


def test_write_gridfm_rectangle(tmp_path):
    
    out_path = tmp_path / "FlowFM_net.nc"
    write_gridfm_rectangle(out_path, 1.1, 1.1, 0, 2, 0, 2)
    
    assert out_path.exists()
    
    ds = xr.open_dataset(out_path)
    
    assert len(ds.mesh2d_nNodes) == 9
    assert len(ds.mesh2d_nEdges) == 12
    assert len(ds.mesh2d_nFaces) == 4
    assert np.isclose(min(ds.mesh2d_node_x), 0)
    assert np.isclose(max(ds.mesh2d_node_x), 2)
    assert np.isclose(min(ds.mesh2d_node_y), 0)
    assert np.isclose(max(ds.mesh2d_node_y), 2)
    assert np.isnan(np.unique(ds.mesh2d_node_z.values))
