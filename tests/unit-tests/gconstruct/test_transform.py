"""
    Copyright 2023 Contributors

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import pytest
import inspect

import numpy as np
from numpy.testing import assert_equal, assert_almost_equal, assert_raises

from graphstorm.gconstruct.transform import (_feat_astype,
                                             _get_output_dtype,
                                             NumericalMinMaxTransform,
                                             CategoricalTransform,
                                             Noop)

def test_get_output_dtype():
    assert _get_output_dtype("float16") == np.float16
    assert _get_output_dtype("float32") == np.float32
    assert_raises(Exception, _get_output_dtype, "int32")

def test_feat_astype():
    feats = np.random.randn(10)
    feats = _feat_astype(feats, np.float32)
    assert feats.dtype == np.float32

    feats = _feat_astype(feats, np.float16)
    assert feats.dtype == np.float16

def test_fp_transform():
    # test NumericalMinMaxTransform pre-process
    transform = NumericalMinMaxTransform("test", "test")
    feats = np.random.randn(100)

    max_val, min_val = transform.pre_process(feats)["test"]
    max_v = np.amax(feats)
    min_v = np.amin(feats)
    assert len(max_val.shape) == 1
    assert len(min_val.shape) == 1
    assert_equal(max_val[0], max_v)
    assert_equal(min_val[0], min_v)

    feats = np.random.randn(100, 1)
    max_val, min_val = transform.pre_process(feats)["test"]
    max_v = np.amax(feats)
    min_v = np.amin(feats)
    assert len(max_val.shape) == 1
    assert len(min_val.shape) == 1
    assert_equal(max_val[0], max_v)
    assert_equal(min_val[0], min_v)

    feats = np.random.randn(100, 10)
    max_val, min_val = transform.pre_process(feats)["test"]
    assert len(max_val.shape) == 1
    assert len(min_val.shape) == 1
    assert len(max_val) == 10
    assert len(min_val) == 10
    for i in range(10):
        max_v = np.amax(feats[:,i])
        min_v = np.amin(feats[:,i])
        assert_equal(max_val[i], max_v)
        assert_equal(min_val[i], min_v)

    feats = np.random.randn(100)
    feats[0] = 10.
    feats[1] = -10.
    transform = NumericalMinMaxTransform("test", "test", max_bound=5., min_bound=-5.)
    max_val, min_val = transform.pre_process(feats)["test"]
    max_v = np.amax(feats)
    min_v = np.amin(feats)
    assert len(max_val.shape) == 1
    assert len(min_val.shape) == 1
    assert_equal(max_val[0], 5.)
    assert_equal(min_val[0], -5.)

    feats = np.random.randn(100, 1)
    feats[0][0] = 10.
    feats[1][0] = -10.
    transform = NumericalMinMaxTransform("test", "test", max_bound=5., min_bound=-5.)
    max_val, min_val = transform.pre_process(feats)["test"]
    max_v = np.amax(feats)
    min_v = np.amin(feats)
    assert len(max_val.shape) == 1
    assert len(min_val.shape) == 1
    assert_equal(max_val[0], 5.)
    assert_equal(min_val[0], -5.)

    feats = np.random.randn(100, 10)
    feats[0] = 10.
    feats[1] = -10.
    transform = NumericalMinMaxTransform("test", "test", max_bound=5., min_bound=-5.)
    max_val, min_val = transform.pre_process(feats)["test"]
    assert len(max_val.shape) == 1
    assert len(min_val.shape) == 1
    assert len(max_val) == 10
    assert len(min_val) == 10
    for i in range(10):
        max_v = np.amax(feats[:,i])
        min_v = np.amin(feats[:,i])
        assert_equal(max_val[i], 5.)
        assert_equal(min_val[i], -5.)

    # Test collect info
    transform = NumericalMinMaxTransform("test", "test")
    info = [(np.array([1.]), np.array([-1.])),
            (np.array([2.]), np.array([-0.5])),
            (np.array([0.5]), np.array([-0.1]))]
    transform.update_info(info)
    assert len(transform._max_val) == 1
    assert len(transform._min_val) == 1
    assert_equal(transform._max_val[0], 2.)
    assert_equal(transform._min_val[0], -1.)

    info = [(np.array([1., 2., 3.]), np.array([-1., -2., 0.5])),
            (np.array([2., 1., 3.]), np.array([-0.5, -3., 0.1])),
            (np.array([0.5, 3., 1.]), np.array([-0.1, -2., 0.3]))]
    transform.update_info(info)
    assert len(transform._max_val) == 3
    assert len(transform._min_val) == 3
    assert_equal(transform._max_val[0], 2.)
    assert_equal(transform._min_val[0], -1.)

@pytest.mark.parametrize("out_dtype", [None, np.float16])
def test_fp_min_max_transform(out_dtype):
    transform = NumericalMinMaxTransform("test", "test", out_dtype=out_dtype)
    max_val = np.array([2.])
    min_val = np.array([-1.])
    transform._max_val = max_val
    transform._min_val = min_val
    feats = np.random.randn(100)
    norm_feats = transform(feats)["test"]
    if out_dtype is not None:
        assert norm_feats.dtype == np.float16
    else:
        assert norm_feats.dtype != np.float16
    feats[feats > max_val] = max_val
    feats[feats < min_val] = min_val
    feats = (feats-min_val)/(max_val-min_val)
    feats = feats if out_dtype is None else feats.astype(out_dtype)
    assert_almost_equal(norm_feats, feats, decimal=6)

    feats = np.random.randn(100, 1)
    norm_feats = transform(feats)["test"]
    if out_dtype is not None:
        assert norm_feats.dtype == np.float16
    else:
        assert norm_feats.dtype != np.float16
    feats[feats > max_val] = max_val
    feats[feats < min_val] = min_val
    feats = (feats-min_val)/(max_val-min_val)
    feats = feats if out_dtype is None else feats.astype(out_dtype)
    assert_almost_equal(norm_feats, feats, decimal=6)

    transform = NumericalMinMaxTransform("test", "test", out_dtype=out_dtype)
    max_val = np.array([2., 3., 0.])
    min_val = np.array([-1., 1., -0.5])
    transform._max_val = max_val
    transform._min_val = min_val
    feats = np.random.randn(10, 3)
    norm_feats = transform(feats)["test"]
    if out_dtype is not None:
        assert norm_feats.dtype == np.float16
    else:
        assert norm_feats.dtype != np.float16
    for i in range(3):
        new_feats = feats[:,i]
        new_feats[new_feats > max_val[i]] = max_val[i]
        new_feats[new_feats < min_val[i]] = min_val[i]
        new_feats = (new_feats-min_val[i])/(max_val[i]-min_val[i])
        new_feats = new_feats if out_dtype is None else new_feats.astype(out_dtype)
        assert_almost_equal(norm_feats[:,i], new_feats, decimal=6)

def test_categorize_transform():
    # Test a single categorical value.
    transform_conf = {
        "name": "to_categorical"
    }
    transform = CategoricalTransform("test1", "test", transform_conf=transform_conf)
    str_ids = [str(i) for i in np.random.randint(0, 10, 1000)]
    str_ids = str_ids + [str(i) for i in range(10)]
    res = transform.pre_process(np.array(str_ids))
    assert "test" in res
    assert len(res["test"]) == 10
    for i in range(10):
        assert str(i) in res["test"]

    info = [ np.array([str(i) for i in range(6)]),
            np.array([str(i) for i in range(4, 10)]) ]
    transform.update_info(info)
    feat = np.array([str(i) for i in np.random.randint(0, 10, 100)])
    cat_feat = transform(feat)
    assert "test" in cat_feat
    for feat, str_i in zip(cat_feat["test"], feat):
        # make sure one value is 1
        assert feat[int(str_i)] == 1
        # after we set the value to 0, the entire vector has 0 values.
        feat[int(str_i)] = 0
        assert np.all(feat == 0)
    assert "mapping" in transform_conf
    assert len(transform_conf["mapping"]) == 10

    # Test categorical values with empty strings.
    transform = CategoricalTransform("test1", "test", separator=',')
    str_ids = [f"{i},{i+1}" for i in np.random.randint(0, 9, 1000)] + [",0"]
    str_ids = str_ids + [str(i) for i in range(9)]
    res = transform.pre_process(np.array(str_ids))
    assert "test" in res
    assert len(res["test"]) == 11

    # Test multiple categorical values.
    transform = CategoricalTransform("test1", "test", separator=',')
    str_ids = [f"{i},{i+1}" for i in np.random.randint(0, 9, 1000)]
    str_ids = str_ids + [str(i) for i in range(9)]
    res = transform.pre_process(np.array(str_ids))
    assert "test" in res
    assert len(res["test"]) == 10
    for i in range(10):
        assert str(i) in res["test"]

    info = [ np.array([str(i) for i in range(6)]),
            np.array([str(i) for i in range(4, 10)]) ]
    transform.update_info(info)
    feat = np.array([f"{i},{i+1}" for i in np.random.randint(0, 9, 100)])
    cat_feat = transform(feat)
    assert "test" in cat_feat
    for feat, str_feat in zip(cat_feat["test"], feat):
        # make sure two elements are 1
        i = str_feat.split(",")
        assert feat[int(i[0])] == 1
        assert feat[int(i[1])] == 1
        # after removing the elements, the vector has only 0 values.
        feat[int(i[0])] = 0
        feat[int(i[1])] = 0
        assert np.all(feat == 0)

    # Test transformation with existing mapping.
    transform = CategoricalTransform("test1", "test", transform_conf=transform_conf)
    str_ids = [str(i) for i in np.random.randint(0, 10, 1000)]
    str_ids = str_ids + [str(i) for i in range(10)]
    res = transform.pre_process(np.array(str_ids))
    assert len(res) == 0

    transform.update_info([])
    feat = np.array([str(i) for i in np.random.randint(0, 10, 100)])
    cat_feat = transform(feat)
    assert "test" in cat_feat
    for feat, str_i in zip(cat_feat["test"], feat):
        # make sure one value is 1
        idx = transform_conf["mapping"][str_i]
        assert feat[idx] == 1
        # after we set the value to 0, the entire vector has 0 values.
        feat[idx] = 0
        assert np.all(feat == 0)

@pytest.mark.parametrize("out_dtype", [None, np.float16])
def test_noop_transform(out_dtype):
    transform = Noop("test", "test", out_dtype=out_dtype)
    feats = np.random.randn(100).astype(np.float32)
    norm_feats = transform(feats)
    if out_dtype is not None:
        assert norm_feats["test"].dtype == out_dtype
    else:
        assert norm_feats["test"].dtype == np.float32

if __name__ == '__main__':
    test_categorize_transform()
    test_feat_astype()
    test_get_output_dtype()
    test_fp_transform()
    test_fp_min_max_transform(None)
    test_fp_min_max_transform(np.float16)
    test_noop_transform(None)
    test_noop_transform(np.float16)